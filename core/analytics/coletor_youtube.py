import os
import json
import time
from datetime import datetime, timezone, timedelta
from loguru import logger
from core.analytics.db import get_db
from core.config.state import carregar_estado
from core.publisher.youtube import obter_servico_youtube
from googleapiclient.errors import HttpError

METRICAS_FILE = "analytics/dados/metricas_youtube.json"

def carregar_metricas_local():
    if os.path.exists(METRICAS_FILE):
        try:
            with open(METRICAS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao ler {METRICAS_FILE}: {e}")
    return {"posts": {}}

def salvar_metricas_local(metricas):
    os.makedirs(os.path.dirname(METRICAS_FILE), exist_ok=True)
    with open(METRICAS_FILE, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=4, ensure_ascii=False)

def carregar_metricas():
    db = get_db()
    if db is not None:
        try:
            logger.info("📥 Baixando métricas do YouTube do Firebase Firestore...")
            docs = db.collection("metricas_posts_youtube").stream()
            posts = {}
            for doc in docs:
                data = doc.to_dict()
                video_id = doc.id
                posts[video_id] = {
                    "info_post": data.get("info_post", {}),
                    "metricas": data.get("metricas", {}),
                    "ultima_atualizacao": data.get("ultima_atualizacao", "")
                }
            metricas = {"posts": posts}
            salvar_metricas_local(metricas)
            return metricas
        except Exception as e:
            logger.error(f"❌ Erro ao sincronizar YouTube do Firebase: {e}")

    return carregar_metricas_local()

def salvar_metricas_firebase(video_id, info_post, metricas):
    db = get_db()
    if db is None:
        return

    try:
        doc_ref = db.collection("metricas_posts_youtube").document(video_id)
        doc_ref.set({
            "video_id": video_id,
            "info_post": info_post,
            "metricas": metricas,
            "ultima_atualizacao": datetime.now(timezone.utc).isoformat(),
        }, merge=True)
    except Exception as e:
        logger.error(f"❌ Erro ao salvar YouTube no Firebase: {e}")

def buscar_metricas_youtube_api(youtube, video_id, data_publicacao):
    """
    Coleta métricas da API de Dados (básicas) e da API de Analytics (avançadas).
    """
    metricas = {}
    
    # 1. Dados Básicos (YouTube Data API v3)
    try:
        req_data = youtube.videos().list(part="statistics", id=video_id)
        res_data = req_data.execute()
        
        if res_data.get("items"):
            stats = res_data["items"][0].get("statistics", {})
            metricas["views"] = int(stats.get("viewCount", 0))
            metricas["likes"] = int(stats.get("likeCount", 0))
            metricas["comments"] = int(stats.get("commentCount", 0))
        else:
            logger.warning(f"Vídeo {video_id} não encontrado na Data API.")
            return None
    except HttpError as e:
        logger.error(f"Erro na Data API para {video_id}: {e}")
        return None

    # 2. Métricas Avançadas (YouTube Analytics API)
    # Requer que data_publicacao seja string ISO YYYY-MM-DD
    data_inicio = "2000-01-01"
    try:
        post_dt = datetime.strptime(data_publicacao, "%Y-%m-%d %H:%M:%S")
        data_inicio = post_dt.strftime("%Y-%m-%d")
    except:
        pass
        
    data_fim = datetime.now().strftime("%Y-%m-%d")
    
    # IMPORTANTE: A API de analytics v2 não está no mesmo discovery service do v3.
    # Precisamos criar um novo client de analytics.
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    try:
        credentials = Credentials.from_authorized_user_file("token_youtube.json")
        youtube_analytics = build("youtubeAnalytics", "v2", credentials=credentials)
        
        req_analytics = youtube_analytics.reports().query(
            ids="channel==MINE",
            startDate=data_inicio,
            endDate=data_fim,
            metrics="estimatedMinutesWatched,averageViewDuration,subscribersGained,shares",
            dimensions="video",
            filters=f"video=={video_id}"
        )
        res_analytics = req_analytics.execute()
        
        rows = res_analytics.get("rows", [])
        if rows:
            row = rows[0]
            # Formato da row: [video_id, estimatedMinutesWatched, averageViewDuration, subscribersGained, shares]
            metricas["estimatedMinutesWatched"] = float(row[1])
            metricas["averageViewDuration"] = float(row[2]) # Segundos de retenção
            metricas["follows"] = int(row[3]) # Seguidores (inscritos)
            metricas["shares"] = int(row[4])
        else:
            # Analytics demora de 24 a 48h para processar.
            # Se não houver dados ainda, apenas usamos defaults de 0
            metricas["averageViewDuration"] = 0
            metricas["follows"] = 0
            metricas["shares"] = 0
            
    except Exception as e:
        logger.warning(f"Aviso: Dados de Analytics não disponíveis para {video_id} ainda (Pode levar 48h): {e}")
        metricas["averageViewDuration"] = 0
        metricas["follows"] = 0
        metricas["shares"] = 0
        
    return metricas

def rodar_coleta_youtube():
    logger.info("📊 Iniciando coleta de métricas do YOUTUBE...")
    estado = carregar_estado()
    historico = estado.get("historico_youtube", [])
    metricas_salvas = carregar_metricas()
    
    youtube = obter_servico_youtube()
    if not youtube:
        logger.error("Serviço do YouTube indisponível para analytics.")
        return

    agora = datetime.now(timezone.utc)
    posts_processados = 0

    for post in historico:
        video_id = post.get("video_id")
        data_str = post.get("data")

        if not video_id or video_id.startswith("DRY_RUN"):
            continue

        try:
            post_dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except:
            continue

        if agora - post_dt > timedelta(days=14):
            continue

        logger.info(f"📥 Coletando YouTube: vídeo {video_id}...")
        novas_metricas = buscar_metricas_youtube_api(youtube, video_id, data_str)

        if novas_metricas:
            # Calcula métricas extras padrão
            views = novas_metricas.get("views", 0)
            shares = novas_metricas.get("shares", 0)
            duracao = post.get("duracao_video", 0)
            avg_watch = novas_metricas.get("averageViewDuration", 0)

            novas_metricas["taxa_compartilhamento"] = round(shares / views, 4) if views > 0 else 0
            novas_metricas["retencao_media_pct"] = round(avg_watch / duracao, 4) if (avg_watch > 0 and duracao > 0) else 0

            # Salva
            if video_id not in metricas_salvas["posts"]:
                metricas_salvas["posts"][video_id] = {}
            metricas_salvas["posts"][video_id]["info_post"] = post
            metricas_salvas["posts"][video_id]["metricas"] = novas_metricas
            metricas_salvas["posts"][video_id]["ultima_atualizacao"] = agora.strftime("%Y-%m-%d %H:%M:%S")

            salvar_metricas_firebase(video_id, post, novas_metricas)
            posts_processados += 1

        time.sleep(1)

    salvar_metricas_local(metricas_salvas)
    logger.success(f"Coleta do YouTube finalizada. {posts_processados} vídeos atualizados.")
    return metricas_salvas

if __name__ == "__main__":
    rodar_coleta_youtube()
