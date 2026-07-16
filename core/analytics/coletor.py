import os
import json
import time
import requests
from datetime import datetime, timezone, timedelta
from loguru import logger
from dotenv import load_dotenv
from core.analytics.db import get_db
from core.config.state import carregar_estado

load_dotenv()

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
METRICAS_FILE = "analytics/dados/metricas.json"  # mantido como fallback local

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

def carregar_metricas():
    """
    Carrega as métricas de postagens. Tenta buscar do Firebase Firestore
    para obter todo o histórico acumulado e atualiza o arquivo local.
    Se o Firebase estiver indisponível, faz o fallback para o arquivo local.
    """
    db = get_db()
    if db is not None:
        try:
            logger.info("📥 Baixando métricas históricas do Firebase Firestore...")
            docs = db.collection("metricas_posts").stream()
            posts = {}
            for doc in docs:
                data = doc.to_dict()
                post_id = doc.id
                posts[post_id] = {
                    "info_post": data.get("info_post", {}),
                    "metricas": data.get("metricas", {}),
                    "ultima_atualizacao": data.get("ultima_atualizacao", "")
                }
            metricas = {"posts": posts}
            salvar_metricas_local(metricas)
            logger.success(f"✅ Sincronização concluída: {len(posts)} posts carregados do Firebase!")
            return metricas
        except Exception as e:
            logger.error(f"❌ Erro ao sincronizar métricas do Firebase: {e}")

    # Fallback local se o Firebase não estiver configurado/disponível
    logger.info("⚠️ Buscando métricas apenas do arquivo local...")
    return carregar_metricas_local()

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
            f"?fields=like_count,comments_count,media_type,caption,permalink,media_url"
            f"&access_token={IG_ACCESS_TOKEN}"
        )
        res_media = requests.get(url_media, timeout=15)
        if res_media.status_code == 200:
            data = res_media.json()
            metricas["likes"]      = data.get("like_count", 0)
            metricas["comments"]   = data.get("comments_count", 0)
            metricas["media_type"] = data.get("media_type", "UNKNOWN")
            metricas["caption"]    = data.get("caption", "")
            metricas["permalink"]  = data.get("permalink", "")
            metricas["media_url"]  = data.get("media_url", "")
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

def buscar_posts_recentes_api():
    """Busca os posts mais recentes diretamente do perfil do Instagram."""
    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID:
        logger.warning("Faltam credenciais (IG_ACCESS_TOKEN ou IG_ACCOUNT_ID) para buscar posts do perfil.")
        return []
    
    url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media?fields=id,media_type,timestamp,caption&access_token={IG_ACCESS_TOKEN}"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            data = res.json().get("data", [])
            posts_descobertos = []
            for item in data:
                try:
                    dt_obj = datetime.strptime(item.get("timestamp"), "%Y-%m-%dT%H:%M:%S%z")
                    data_str = dt_obj.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    data_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

                media_type = item.get("media_type", "")
                tipo = "feed"
                if media_type == "VIDEO":
                    tipo = "reels"
                elif media_type == "CAROUSEL_ALBUM":
                    tipo = "carousel"
                
                posts_descobertos.append({
                    "post_id": item.get("id"),
                    "data": data_str,
                    "tipo": tipo,
                    "tema": "Descoberto Automaticamente",
                    "caption": item.get("caption", "")
                })
            logger.info(f"🔎 Encontrados {len(posts_descobertos)} posts no perfil.")
            return posts_descobertos
        else:
            logger.error(f"Erro ao buscar posts do perfil: {res.text}")
            return []
    except Exception as e:
        logger.error(f"Exceção ao buscar posts do perfil: {e}")
        return []

def rodar_coleta():
    logger.info("📊 Iniciando coleta de métricas...")
    estado = carregar_estado()
    historico = estado.get("historico", [])
    metricas_salvas = carregar_metricas()

    # --- NOVO: Buscar posts externos e unir com o histórico ---
    posts_externos = buscar_posts_recentes_api()
    todos_posts_dict = {p.get("post_id"): p for p in posts_externos if p.get("post_id")}
    for p in historico:
        if p.get("post_id"):
            todos_posts_dict[p.get("post_id")] = p
    historico_unificado = list(todos_posts_dict.values())
    # ------------------------------------------------------------

    agora = datetime.now(timezone.utc)
    posts_processados = 0

    for post in historico_unificado:
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
        # Removido: if not is_story and agora - post_dt < timedelta(hours=24): continue
        # Agora coletamos as métricas no mesmo dia, sem esperar 24h.

        if agora - post_dt > timedelta(days=14):
            continue

        tipo_post = post.get("tipo", "feed")
        logger.info(f"📥 Coletando métricas: post {post_id} ({tipo_post} - {post.get('tema')})...")
        novas_metricas = buscar_metricas_api(post_id, tipo_post=tipo_post)

        if novas_metricas:
            # --- Calcula métricas derivadas e injeta nos dados brutos ---
            views       = novas_metricas.get("views", novas_metricas.get("plays", 0))
            impressions = novas_metricas.get("impressions", novas_metricas.get("reach", 0))
            saves       = novas_metricas.get("saved", 0)
            shares      = novas_metricas.get("shares", 0)
            follows     = novas_metricas.get("follows", 0)
            prof_visits = novas_metricas.get("profile_visits", 0)
            avg_watch   = novas_metricas.get("ig_reels_avg_watch_time", 0)  # em ms
            duracao     = post.get("duracao_video", 0)

            novas_metricas["CTR_feed"]              = round(views / impressions, 4) if impressions > 0 else 0
            novas_metricas["taxa_salvamento"]        = round(saves / views, 4) if views > 0 else 0
            novas_metricas["taxa_compartilhamento"]  = round(shares / views, 4) if views > 0 else 0
            novas_metricas["taxa_visita_perfil"]     = round(prof_visits / views, 4) if views > 0 else 0
            novas_metricas["conversao_perfil"]       = round(follows / prof_visits, 4) if prof_visits > 0 else 0
            novas_metricas["retencao_media_pct"]     = round((avg_watch / 1000) / duracao, 4) if (avg_watch > 0 and duracao > 0) else 0
            # -------------------------------------------------------------

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
    logger.success(f"Coleta finalizada. {posts_processados} posts atualizados.")
    return metricas_salvas

if __name__ == "__main__":
    rodar_coleta()

