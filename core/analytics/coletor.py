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
            # Reels: métricas de retenção, tempo assistido, engajamento e conversão de perfil
            metrics_query = "views,ig_reels_avg_watch_time,ig_reels_video_view_total_time,reach,saved,shares,profile_visits,follows"
            logger.info(f"🎬 Coletando métricas de REELS para {post_id}")
        elif "story" in tipo_lower:
            # Stories: métricas de navegação, retenção e conversão
            metrics_query = "impressions,reach,navigation,replies,profile_visits,follows"
            logger.info(f"📱 Coletando métricas de STORY para {post_id}")
        else:
            # Feed e Carrossel: métricas de engajamento, descoberta e conversão de perfil
            metrics_query = "reach,saved,shares,impressions,profile_visits,follows"
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
            err_text = res_insights.text
            logger.warning(f"Não foi possível obter insights para {post_id}: {err_text}")
            # Fallback: se a query completa falhou (métrica não disponível para o formato),
            # tenta buscar profile_visits e follows separadamente
            if "profile_visits" in err_text or "follows" in err_text or "OAuthException" in err_text:
                try:
                    metrics_fallback = "reach,saved,shares"
                    if "reel" in tipo_lower or "pexels" in tipo_lower:
                        metrics_fallback = "views,ig_reels_avg_watch_time,reach,saved,shares"
                    url_fallback = (
                        f"https://graph.facebook.com/v19.0/{post_id}/insights"
                        f"?metric={metrics_fallback}"
                        f"&access_token={IG_ACCESS_TOKEN}"
                    )
                    res_fb = requests.get(url_fallback, timeout=15)
                    if res_fb.status_code == 200:
                        for insight in res_fb.json().get("data", []):
                            name   = insight.get("name")
                            values = insight.get("values", [])
                            if values:
                                metricas[name] = values[0].get("value", 0)
                            elif "value" in insight:
                                metricas[name] = insight.get("value", 0)
                        logger.info(f"✅ Fallback de métricas sem profile_visits/follows aplicado para {post_id}")
                except Exception as ef:
                    logger.warning(f"Fallback de métricas também falhou para {post_id}: {ef}")

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

def buscar_insights_conta_api():
    """
    Busca insights consolidados da conta no Instagram (Reach e Impressions de 28 dias,
    Profile Views e Follows diários acumulados).
    """
    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID or IG_ACCOUNT_ID.startswith("DRY_RUN"):
        logger.warning("Faltam credenciais para buscar insights da conta do Instagram (ou em modo DRY_RUN).")
        return None

    dados_conta = {
        "reach_30d": 0,
        "impressions_30d": 0,
        "profile_views_30d": 0,
        "follower_count_30d": 0,
        "ultima_atualizacao": datetime.now(timezone.utc).isoformat()
    }

    # 1. Coleta Reach consolidado de 28 dias
    url_28d = (
        f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/insights"
        f"?metric=reach"
        f"&period=days_28"
        f"&access_token={IG_ACCESS_TOKEN}"
    )
    try:
        res = requests.get(url_28d, timeout=15)
        if res.status_code == 200:
            data = res.json().get("data", [])
            for insight in data:
                name = insight.get("name")
                values = insight.get("values", [])
                if values:
                    val = 0
                    for item in reversed(values):
                        v_val = item.get("value", 0)
                        if v_val > 0:
                            val = v_val
                            break
                    if val == 0:
                        val = values[-1].get("value", 0)

                    if name == "reach":
                        dados_conta["reach_30d"] = val
        else:
            logger.warning(f"Não foi possível obter insights 28d da conta: {res.text}")
    except Exception as e:
        logger.error(f"Erro ao buscar insights 28d da conta: {e}")

    # Auxiliar para extrair o valor total do insight, seja de total_value ou da soma de values diários
    def extrair_total(ins):
        if "total_value" in ins:
            return ins["total_value"].get("value", 0)
        vals = ins.get("values", [])
        if vals:
            return sum(item.get("value", 0) for item in vals)
        return 0

    # 2. Coleta Profile Views (Visitas ao perfil) e Follower Count (Novos seguidores) diários (últimos 30 dias)
    agora = datetime.now(timezone.utc)
    trinta_dias_atras = agora - timedelta(days=30)
    since_ts = int(trinta_dias_atras.timestamp())
    until_ts = int(agora.timestamp())

    # 2a. Profile Views (exige period=day e metric_type=total_value juntos)
    url_views = (
        f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/insights"
        f"?metric=profile_views"
        f"&period=day"
        f"&metric_type=total_value"
        f"&since={since_ts}"
        f"&until={until_ts}"
        f"&access_token={IG_ACCESS_TOKEN}"
    )
    try:
        res = requests.get(url_views, timeout=15)
        if res.status_code == 200:
            data = res.json().get("data", [])
            for insight in data:
                name = insight.get("name")
                total_val = extrair_total(insight)
                if name == "profile_views":
                    dados_conta["profile_views_30d"] = total_val
        else:
            logger.warning(f"Não foi possível obter insights de profile_views da conta: {res.text}")
    except Exception as e:
        logger.error(f"Erro ao buscar insights de profile_views da conta: {e}")

    # 2b. Follower Count (não suporta metric_type=total_value)
    url_followers = (
        f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/insights"
        f"?metric=follower_count"
        f"&period=day"
        f"&since={since_ts}"
        f"&until={until_ts}"
        f"&access_token={IG_ACCESS_TOKEN}"
    )
    try:
        res = requests.get(url_followers, timeout=15)
        if res.status_code == 200:
            data = res.json().get("data", [])
            for insight in data:
                name = insight.get("name")
                total_val = extrair_total(insight)
                if name == "follower_count":
                    dados_conta["follower_count_30d"] = total_val
        else:
            logger.warning(f"Não foi possível obter insights de follower_count da conta: {res.text}")
    except Exception as e:
        logger.error(f"Erro ao buscar insights de follower_count da conta: {e}")

    return dados_conta

def salvar_metricas_conta_firebase(dados_conta):
    """Salva os dados de insights da conta no Firebase Firestore."""
    db = get_db()
    if db is None:
        return

    try:
        doc_ref = db.collection("metricas_conta_instagram").document("consolidados")
        doc_ref.set(dados_conta, merge=True)
        logger.info("🔥 Insights consolidados da conta salvos no Firebase!")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar insights de conta no Firebase: {e}")

def rodar_coleta():
    logger.info("📊 Iniciando coleta de métricas...")
    from core.analytics.db import get_db
    db = get_db()
    
    historico = []
    if db:
        try:
            docs = db.collection("historico_posts").stream()
            historico = [doc.to_dict() for doc in docs]
            logger.info(f"📚 Carregados {len(historico)} posts do histórico (Firebase).")
        except Exception as e:
            logger.error(f"Erro ao ler historico_posts: {e}")

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

        if agora - post_dt > timedelta(days=30):
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

            # --- CORREÇÃO: Calcula e grava o growth_score individual do post ---
            # Isso alimenta o Motor de Hipóteses com dados reais por post
            gs_conversao   = (follows / prof_visits) if prof_visits > 0 else 0
            gs_curiosidade = (prof_visits / views) if views > 0 else 0
            gs_retencao    = (avg_watch / 1000 / duracao) if (avg_watch > 0 and duracao > 0) else 0
            gs_share       = (shares / views) if views > 0 else 0
            gs_save        = (saves / views) if views > 0 else 0
            novas_metricas["growth_score"] = round(
                0.35 * gs_conversao
                + 0.20 * gs_curiosidade
                + 0.20 * gs_retencao
                + 0.15 * gs_share
                + 0.10 * gs_save,
                4
            )
            # ------------------------------------------------------------------

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

    # --- Coleta e salvamento das métricas de conta ---
    try:
        logger.info("📥 Iniciando coleta de insights globais da conta do Instagram...")
        dados_conta = buscar_insights_conta_api()
        if dados_conta:
            # --- CORREÇÃO: Fallback de seguidores ---
            # A API da Meta pode retornar 0 para contas menores por limitação de privacidade.
            # Nesse caso, somamos os seguidores trazidos individualmente por cada post.
            if dados_conta.get("follower_count_30d", 0) == 0:
                follows_somados = sum(
                    metricas_salvas["posts"].get(pid, {}).get("metricas", {}).get("follows", 0)
                    for pid in metricas_salvas.get("posts", {})
                )
                if follows_somados > 0:
                    dados_conta["follower_count_30d"] = follows_somados
                    logger.info(f"📊 follower_count_30d preenchido via fallback (soma de posts): {follows_somados}")
            # -----------------------------------------
            salvar_metricas_conta_firebase(dados_conta)
            metricas_salvas["conta"] = dados_conta
    except Exception as e:
        logger.error(f"Erro ao coletar/salvar métricas de conta: {e}")

    salvar_metricas_local(metricas_salvas)
    logger.success(f"Coleta finalizada. {posts_processados} posts atualizados.")
    return metricas_salvas

if __name__ == "__main__":
    rodar_coleta()

