import os
import json
import time
import requests
from datetime import datetime, timezone, timedelta
from loguru import logger
from dotenv import load_dotenv
from core.analytics.db import get_db

load_dotenv()

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
ESTADO_FILE = "estado.json"
METRICAS_FILE = "analytics/dados/metricas.json"  # mantido como fallback local

def carregar_estado():
    if os.path.exists(ESTADO_FILE):
        try:
            with open(ESTADO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao ler estado.json: {e}")
    return {"historico": []}

def carregar_metricas_local():
    if os.path.exists(METRICAS_FILE):
        try:
            with open(METRICAS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao ler metricas.json: {e}")
    return {"posts": {}}

def salvar_metricas_local(metricas):
    os.makedirs(os.path.dirname(METRICAS_FILE), exist_ok=True)
    with open(METRICAS_FILE, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=4, ensure_ascii=False)

def salvar_metricas_firebase(post_id, info_post, metricas):
    """Salva os dados do post e métricas no Firebase Firestore."""
    db = get_db()
    if db is None:
        logger.warning("Firebase indisponível. Dados salvos apenas localmente.")
        return

    try:
        doc_ref = db.collection("metricas_posts").document(post_id)
        doc_ref.set({
            "post_id": post_id,
            "info_post": info_post,
            "metricas": metricas,
            "ultima_atualizacao": datetime.now(timezone.utc).isoformat(),
        }, merge=True)
        logger.info(f"🔥 Métricas do post {post_id} salvas no Firebase!")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar métricas no Firebase: {e}")

def buscar_metricas_api(post_id, tipo_post="feed"):
    """
    Coleta métricas da API do Instagram de forma inteligente por tipo de post.
    
    Tipos de post e métricas exclusivas:
    - Feed/Carrossel: impressions, reach, saved, likes, comments, shares, profile_visits, follows
    - Reels:          plays, ig_reels_avg_watch_time, ig_reels_video_view_total_time, reach, saved, shares
    - Stories:        impressions, reach, taps_forward, taps_back, exits, replies, follows
    """
    if not IG_ACCESS_TOKEN or post_id.startswith("DRY_RUN") or post_id == "ID_TESTE_LOCAL":
        return None

    metricas = {}
    try:
        # --- Passo 1: Dados básicos da mídia (likes, comentários, tipo) ---
        url_media = (
            f"https://graph.facebook.com/v19.0/{post_id}"
            f"?fields=like_count,comments_count,media_type"
            f"&access_token={IG_ACCESS_TOKEN}"
        )
        res_media = requests.get(url_media, timeout=15)
        if res_media.status_code == 200:
            data = res_media.json()
            metricas["likes"]      = data.get("like_count", 0)
            metricas["comments"]   = data.get("comments_count", 0)
            metricas["media_type"] = data.get("media_type", "UNKNOWN")
        else:
            try:
                err_json = res_media.json()
                err_msg = err_json.get("error", {}).get("message", "")
                if "does not exist" in err_msg or "Unsupported get request" in err_msg:
                    logger.warning(f"Mídia {post_id} não acessível (pode ter expirado). Pulando...")
                    return None
            except:
                pass
            logger.error(f"Erro ao buscar mídia {post_id}: {res_media.text}")
            return None

        # --- Passo 2: Insights expandidos por tipo de post ---
        tipo_lower = tipo_post.lower()
        
        if "reel" in tipo_lower or "pexels" in tipo_lower:
            # Reels: métricas de retenção e tempo assistido
            metrics_query = "views,ig_reels_avg_watch_time,ig_reels_video_view_total_time,reach,saved,shares"
            logger.info(f"🎬 Coletando métricas de REELS para {post_id}")
        elif "story" in tipo_lower:
            # Stories: métricas de navegação e retenção
            metrics_query = "impressions,reach,navigation,replies,follows"
            logger.info(f"📱 Coletando métricas de STORY para {post_id}")
        else:
            # Feed e Carrossel: métricas de engajamento e descoberta
            metrics_query = "impressions,reach,saved,shares,profile_visits,follows"
            logger.info(f"🖼️ Coletando métricas de FEED para {post_id}")

        url_insights = (
            f"https://graph.facebook.com/v19.0/{post_id}/insights"
            f"?metric={metrics_query}"
            f"&access_token={IG_ACCESS_TOKEN}"
        )
        res_insights = requests.get(url_insights, timeout=15)

        if res_insights.status_code == 200:
            data = res_insights.json()
            for insight in data.get("data", []):
                name   = insight.get("name")
                values = insight.get("values", [])
                if values:
                    metricas[name] = values[0].get("value", 0)
                elif "value" in insight:
                    # Alguns insights retornam valor direto (sem array)
                    metricas[name] = insight.get("value", 0)
        else:
            logger.warning(f"Não foi possível obter insights para {post_id}: {res_insights.text}")

        logger.info(f"📊 Métricas coletadas para {post_id}: {list(metricas.keys())}")
        return metricas

    except Exception as e:
        logger.error(f"Erro ao coletar métricas para o post {post_id}: {e}")
        return None

def rodar_coleta():
    logger.info("📊 Iniciando coleta de métricas...")
    estado = carregar_estado()
    historico = estado.get("historico", [])
    metricas_salvas = carregar_metricas_local()

    agora = datetime.now(timezone.utc)
    posts_processados = 0

    for post in historico:
        post_id = post.get("post_id")
        data_str = post.get("data")

        if not post_id or post_id == "ID_TESTE_LOCAL" or post_id.startswith("DRY_RUN"):
            continue

        try:
            post_dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except:
            continue

        is_story = "story" in str(post.get('tipo', '')).lower()

        if is_story and agora - post_dt > timedelta(hours=24):
            continue
        if not is_story and agora - post_dt < timedelta(hours=24):
            continue
        if agora - post_dt > timedelta(days=14):
            continue

        tipo_post = post.get("tipo", "feed")
        logger.info(f"📥 Coletando métricas: post {post_id} ({tipo_post} - {post.get('tema')})...")
        novas_metricas = buscar_metricas_api(post_id, tipo_post=tipo_post)

        if novas_metricas:
            # Salva localmente (fallback)
            if post_id not in metricas_salvas["posts"]:
                metricas_salvas["posts"][post_id] = {}
            metricas_salvas["posts"][post_id]["info_post"] = post
            metricas_salvas["posts"][post_id]["metricas"] = novas_metricas
            metricas_salvas["posts"][post_id]["ultima_atualizacao"] = agora.strftime("%Y-%m-%d %H:%M:%S")

            # Salva no Firebase (principal)
            salvar_metricas_firebase(post_id, post, novas_metricas)
            posts_processados += 1

        time.sleep(2)

    salvar_metricas_local(metricas_salvas)
    logger.success(f"✅ Coleta finalizada. {posts_processados} posts atualizados.")
    return metricas_salvas

if __name__ == "__main__":
    rodar_coleta()
