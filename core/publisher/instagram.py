import requests
import time
import os
from loguru import logger

from core.config.settings import IG_ACCESS_TOKEN, IG_ACCOUNT_ID
from core.publisher.uploader import upload_temporario

# ============================================================
# MAPA DE ERROS CONHECIDOS
# Cada código tem uma ação definida: retry, skip ou fatal
# ============================================================
ERROS_CONHECIDOS = {
    2207027: {"acao": "retry", "espera": 20, "msg": "Mídia não pronta. Aguardando processamento do Instagram..."},
    9007:    {"acao": "skip",  "espera": 0,  "msg": "Story expirado. Pulando silenciosamente."},
    190:     {"acao": "fatal", "espera": 0,  "msg": "Token do Instagram INVÁLIDO ou EXPIRADO! Ação urgente necessária."},
}

def _publicar_com_retry(url_publish, payload_publish, descricao="mídia", max_tentativas=5):
    """Tenta publicar no Instagram com retry inteligente baseado no tipo de erro."""
    for tentativa in range(1, max_tentativas + 1):
        res = requests.post(url_publish, data=payload_publish, timeout=30)
        res_json = res.json()

        if 'id' in res_json:
            return res_json

        erro = res_json.get('error', {})
        codigo = erro.get('code')
        subcod  = erro.get('error_subcode')

        # Verifica no mapa de erros conhecidos (sub-código tem prioridade)
        config_erro = ERROS_CONHECIDOS.get(subcod) or ERROS_CONHECIDOS.get(codigo)

        if config_erro:
            acao = config_erro["acao"]
            logger.warning(f"⚠️ [{descricao}] Tentativa {tentativa}/{max_tentativas} — {config_erro['msg']}")

            if acao == "skip":
                return None  # sinaliza para ignorar sem falha crítica

            if acao == "fatal":
                raise Exception(f"🚨 ERRO FATAL: {config_erro['msg']} Resposta: {res_json}")

            if acao == "retry":
                if tentativa < max_tentativas:
                    espera = config_erro["espera"] * tentativa  # backoff crescente
                    logger.info(f"⏳ Aguardando {espera}s antes da próxima tentativa...")
                    time.sleep(espera)
                    continue

        # Erro desconhecido — backoff exponencial padrão
        logger.warning(f"⚠️ [{descricao}] Tentativa {tentativa}/{max_tentativas} — Erro desconhecido: {res_json}")
        if tentativa < max_tentativas:
            espera = 5 * (2 ** (tentativa - 1))  # 5s, 10s, 20s, 40s...
            logger.info(f"⏳ Aguardando {espera}s (backoff exponencial)...")
            time.sleep(espera)

    raise Exception(f"❌ Falha ao publicar {descricao} após {max_tentativas} tentativas. Última resposta: {res_json}")


def aguardar_processamento_container(container_id, max_tentativas=15, intervalo=8):
    """Aguarda o Instagram processar um container de mídia antes de publicar."""
    url = f"https://graph.facebook.com/v19.0/{container_id}"
    params = {'fields': 'status_code', 'access_token': IG_ACCESS_TOKEN}

    for tentativa in range(1, max_tentativas + 1):
        try:
            res = requests.get(url, params=params, timeout=15)
            status = res.json().get('status_code', '')
            if status == 'FINISHED':
                logger.info(f"✅ Container {container_id} pronto!")
                return True
            elif status == 'ERROR':
                raise Exception(f"Container {container_id} falhou com status ERROR.")
            else:
                logger.info(f"⏳ Container {container_id} — status: {status} (tentativa {tentativa}/{max_tentativas})")
                time.sleep(intervalo)
        except Exception as e:
            logger.warning(f"⚠️ Erro ao consultar status do container: {e}")
            time.sleep(intervalo)

    raise Exception(f"Container {container_id} não ficou pronto após {max_tentativas} tentativas.")


def postar_no_instagram(tipo, midia, legenda, dry_run=False):
    logger.info(f"🚀 Iniciando postagem no Instagram ({tipo.upper()})...")

    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID:
        logger.warning("⚠️ IG_ACCESS_TOKEN ou IG_ACCOUNT_ID ausente no .env. Postagem pulada.")
        return "ID_TESTE_LOCAL"

    # -------------------------------------------------------
    # 1. Story único / Teste
    # -------------------------------------------------------
    if tipo in ["story", "test"]:
        if dry_run:
            logger.info(f"[DRY-RUN] Enviaria imagem {midia} e criaria o container.")
            return "DRY_RUN_ID"

        url_publica = upload_temporario(midia)
        url_container = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
        payload = {'image_url': url_publica, 'access_token': IG_ACCESS_TOKEN}
        if tipo == "test" and legenda:
            payload['caption'] = legenda
        if tipo in ["story", "test"]:
            payload['media_type'] = 'STORIES'

        res_container = requests.post(url_container, data=payload, timeout=25)
        res_container_json = res_container.json()

        if 'id' not in res_container_json:
            raise Exception(f"Falha ao criar container. Resposta: {res_container_json}")

        creation_id = res_container_json['id']
        logger.info(f"✅ Container de mídia criado! ID: {creation_id}")
        time.sleep(10)

        url_publish = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish"
        payload_publish = {'creation_id': creation_id, 'access_token': IG_ACCESS_TOKEN}
        res_publish_json = _publicar_com_retry(url_publish, payload_publish, descricao="Story")

        if res_publish_json is None:
            logger.info("⏭️ Story pulado por ser expirado.")
            return None

        logger.success(f"🎉 PUBLICADO COM SUCESSO! ID: {res_publish_json['id']}")
        return res_publish_json['id']

    # -------------------------------------------------------
    # 1.5. Stories Sequenciais (manhã ou tarde)
    # -------------------------------------------------------
    elif tipo in ["story_manha", "story_tarde"]:
        if dry_run:
            midias = midia if isinstance(midia, list) else [midia]
            logger.info(f"[DRY-RUN] Enviaria {len(midias)} story(s) em sequência.")
            return "DRY_RUN_SEQ_STORY_ID"

        midias = midia if isinstance(midia, list) else [midia]
        ultimo_id = None

        for idx, caminho_story in enumerate(midias):
            logger.info(f"📤 Publicando story {idx+1}/{len(midias)}...")
            url_publica = upload_temporario(caminho_story)

            url_container = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
            payload = {'media_type': 'STORIES', 'access_token': IG_ACCESS_TOKEN}
            if caminho_story.lower().endswith('.mp4'):
                payload['video_url'] = url_publica
            else:
                payload['image_url'] = url_publica

            res_container = requests.post(url_container, data=payload, timeout=25)
            res_container_json = res_container.json()

            if 'id' not in res_container_json:
                raise Exception(f"Falha ao criar container do story {idx+1}. Resposta: {res_container_json}")

            creation_id = res_container_json['id']
            logger.info(f"✅ Container story {idx+1} criado! ID: {creation_id}. Aguardando processamento...")

            # Aguarda o Instagram processar o vídeo antes de publicar
            if caminho_story.lower().endswith('.mp4'):
                aguardar_processamento_container(creation_id, max_tentativas=15, intervalo=8)
            else:
                time.sleep(10)

            url_publish = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish"
            payload_publish = {'creation_id': creation_id, 'access_token': IG_ACCESS_TOKEN}
            res_publish_json = _publicar_com_retry(url_publish, payload_publish, descricao=f"Story {idx+1}")

            if res_publish_json is None:
                logger.info(f"⏭️ Story {idx+1} pulado (expirado).")
                continue

            ultimo_id = res_publish_json['id']
            logger.success(f"✅ Story {idx+1}/{len(midias)} publicado! ID: {ultimo_id}")

            if idx < len(midias) - 1:
                logger.info("⏳ Aguardando 15s antes do próximo story...")
                time.sleep(15)

        logger.success(f"🎉 SEQUÊNCIA DE STORIES PUBLICADA COM SUCESSO!")
        return ultimo_id

    # -------------------------------------------------------
    # 2. Carrossel
    # -------------------------------------------------------
    elif tipo == "carousel":
        if dry_run:
            logger.info(f"[DRY-RUN] Criaria containers filhos para {len(midia)} imagens.")
            return "DRY_RUN_CAROUSEL_ID"

        child_ids = []
        for idx, caminho_slide in enumerate(midia):
            logger.info(f"📸 Carregando slide {idx+1}/{len(midia)}...")
            url_publica = upload_temporario(caminho_slide)

            url_container = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
            payload = {'image_url': url_publica, 'is_carousel_item': 'true', 'access_token': IG_ACCESS_TOKEN}
            res_container = requests.post(url_container, data=payload, timeout=25)
            res_container_json = res_container.json()

            if 'id' not in res_container_json:
                raise Exception(f"Falha ao criar slide filho {idx}. Resposta: {res_container_json}")

            child_ids.append(res_container_json['id'])
            logger.info(f"✅ Slide filho {idx+1} criado. ID: {res_container_json['id']}")

        for cid in child_ids:
            aguardar_processamento_container(cid)

        logger.info("🎠 Criando container pai para o Carrossel...")
        children_str = ",".join(child_ids)
        url_parent = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
        payload_parent = {
            'media_type': 'CAROUSEL', 'children': children_str,
            'caption': legenda, 'access_token': IG_ACCESS_TOKEN
        }
        res_parent = requests.post(url_parent, data=payload_parent, timeout=25)
        res_parent_json = res_parent.json()

        if 'id' not in res_parent_json:
            raise Exception(f"Falha ao criar pai do carrossel. Resposta: {res_parent_json}")

        parent_id = res_parent_json['id']
        aguardar_processamento_container(parent_id)

        url_publish = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish"
        payload_publish = {'creation_id': parent_id, 'access_token': IG_ACCESS_TOKEN}
        res_publish_json = _publicar_com_retry(url_publish, payload_publish, descricao="Carrossel")

        logger.success(f"🎉 CARROSSEL PUBLICADO! ID: {res_publish_json['id']}")
        return res_publish_json['id']

    # -------------------------------------------------------
    # 3. Reels / Pexels Stories (vídeo)
    # -------------------------------------------------------
    elif tipo in ["reels", "pexels_story", "reels_noite", "pexels_story_noite", "reels_conquistador", "reels_leads"]:
        if dry_run:
            logger.info(f"[DRY-RUN] Enviaria vídeo Reels {midia} e publicaria.")
            return "DRY_RUN_REELS_ID"

        url_publica = upload_temporario(midia)

        logger.info("🎬 Criando contêiner de Reels...")
        url_container = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
        payload = {
            'media_type': 'REELS', 'video_url': url_publica,
            'caption': legenda, 'share_to_feed': 'true',
            'thumb_offset': '2000', 'access_token': IG_ACCESS_TOKEN
        }
        res_container = requests.post(url_container, data=payload, timeout=25)
        res_container_json = res_container.json()

        if 'id' not in res_container_json:
            raise Exception(f"Falha ao criar container Reels. Resposta: {res_container_json}")

        reels_id = res_container_json['id']
        logger.info(f"✅ Container Reels criado! ID: {reels_id}")
        aguardar_processamento_container(reels_id, max_tentativas=25)

        url_publish = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish"
        payload_publish = {'creation_id': reels_id, 'access_token': IG_ACCESS_TOKEN}
        res_publish_json = _publicar_com_retry(url_publish, payload_publish, descricao="Reels")

        published_id = res_publish_json['id']
        logger.success(f"🎉 REELS PUBLICADO! ID: {published_id}")
        


        return published_id
