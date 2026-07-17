import os
import time
import json
from loguru import logger
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

def obter_servico_youtube():
    """Carrega as credenciais e retorna o serviço da API do YouTube."""
    if not os.path.exists("token_youtube.json"):
        logger.error("❌ Arquivo 'token_youtube.json' não encontrado. Rode autenticar_youtube.py primeiro.")
        return None
        
    try:
        credentials = Credentials.from_authorized_user_file("token_youtube.json", SCOPES)
        # O build cria o serviço da API
        youtube = build("youtube", "v3", credentials=credentials)
        return youtube
    except Exception as e:
        logger.error(f"❌ Erro ao criar serviço do YouTube: {e}")
        return None

def postar_no_youtube(caminho_video, titulo, descricao, tags=None, privacidade="unlisted"):
    """
    Faz o upload do vídeo para o YouTube Shorts.
    """
    youtube = obter_servico_youtube()
    if not youtube:
        return None
        
    if tags is None:
        tags = ["shorts", "marketing", "digital", "bot"]
    else:
        # Garante que 'shorts' sempre esteja nas tags
        tags = [t.strip().replace("#", "") for t in tags]
        if "shorts" not in [t.lower() for t in tags]:
            tags.append("shorts")
            
    # Para ser considerado Shorts, o ideal é ter #shorts no título ou descrição
    if "#shorts" not in titulo.lower() and "#shorts" not in descricao.lower():
        descricao += "\n\n#shorts"

    body = {
        "snippet": {
            "title": titulo[:100],  # Limite do YouTube é 100 caracteres
            "description": descricao,
            "tags": tags,
            "categoryId": "27"  # 27 = Educação (pode alterar se quiser)
        },
        "status": {
            "privacyStatus": privacidade,  # public, private, unlisted
            "selfDeclaredMadeForKids": False
        }
    }
    
    logger.info(f"📤 Iniciando upload para o YouTube Shorts: {titulo[:30]}... ({privacidade})")
    
    try:
        media = MediaFileUpload(caminho_video, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"⏳ Upload YouTube: {int(status.progress() * 100)}%")
                
        video_id = response.get("id")
        logger.success(f"✅ Upload concluído! YouTube Video ID: {video_id}")
        return video_id
        
    except HttpError as e:
        logger.error(f"❌ Erro HTTP da API do YouTube: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao fazer upload para o YouTube: {e}")
        return None
