import requests
import time
import os

from core.config.settings import IG_ACCESS_TOKEN, IG_ACCOUNT_ID
from core.publisher.uploader import upload_temporario

def aguardar_processamento_container(container_id, max_tentativas=10, intervalo=5):
    """Aguarda o Instagram processar um container de mídia antes de publicar."""
    url = f"https://graph.facebook.com/v19.0/{container_id}"
    params = {
        'fields': 'status_code',
        'access_token': IG_ACCESS_TOKEN
    }
    for tentativa in range(1, max_tentativas + 1):
        try:
            res = requests.get(url, params=params, timeout=15)
            status = res.json().get('status_code', '')
            if status == 'FINISHED':
                print(f"✅ Container {container_id} pronto!")
                return True
            elif status == 'ERROR':
                raise Exception(f"Container {container_id} falhou com status ERROR.")
            else:
                print(f"⏳ Aguardando container {container_id} (tentativa {tentativa}/{max_tentativas}, status: {status})...")
                time.sleep(intervalo)
        except Exception as e:
            print(f"⚠️ Erro ao consultar status do container: {e}")
            time.sleep(intervalo)
    raise Exception(f"Container {container_id} não ficou pronto após {max_tentativas} tentativas.")

def postar_no_instagram(tipo, midia, legenda, dry_run=False):
    print(f"🚀 Iniciando postagem no Instagram ({tipo.upper()})...")
    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID:
        print("⚠️ IG_ACCESS_TOKEN ou IG_ACCOUNT_ID ausente no .env.")
        print("👉 A postagem real na API da Meta foi pulada.")
        return "ID_TESTE_LOCAL"
        
    # 1. Story único, Teste
    if tipo in ["story", "test"]:
        if dry_run:
            print(f"[DRY-RUN] Enviaria imagem {midia} e criaria o container.")
            return "DRY_RUN_ID"
            
        url_publica = upload_temporario(midia)
        
        url_container = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
        payload = {
            'image_url': url_publica,
            'access_token': IG_ACCESS_TOKEN
        }
        if tipo == "test" and legenda:
            payload['caption'] = legenda
        if tipo in ["story", "test"]:
            payload['media_type'] = 'STORIES'
            
        res_container = requests.post(url_container, data=payload, timeout=25)
        res_container_json = res_container.json()
        
        if 'id' not in res_container_json:
            raise Exception(f"Falha ao criar container. Resposta: {res_container_json}")
            
        creation_id = res_container_json['id']
        print(f"✅ Container de mídia criado! ID: {creation_id}")
        
        time.sleep(10)
        
        url_publish = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish"
        payload_publish = {
            'creation_id': creation_id,
            'access_token': IG_ACCESS_TOKEN
        }
        res_publish = requests.post(url_publish, data=payload_publish, timeout=25)
        res_publish_json = res_publish.json()
        
        if 'id' not in res_publish_json:
            raise Exception(f"Falha ao publicar a mídia. Resposta: {res_publish_json}")
            
        print(f"🎉 PUBLICADO COM SUCESSO! ID da publicação: {res_publish_json['id']}")
        return res_publish_json['id']
    
    # 1.5 Stories Sequenciais (manhã ou tarde)
    elif tipo in ["story_manha", "story_tarde"]:
        if dry_run:
            midias = midia if isinstance(midia, list) else [midia]
            print(f"[DRY-RUN] Enviaria {len(midias)} story(s) em sequência.")
            return "DRY_RUN_SEQ_STORY_ID"
        
        midias = midia if isinstance(midia, list) else [midia]
        ultimo_id = None
        for idx, caminho_story in enumerate(midias):
            print(f"📤 Publicando story {idx+1}/{len(midias)}...")
            url_publica = upload_temporario(caminho_story)
            
            url_container = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
            payload = {
                'image_url': url_publica,
                'media_type': 'STORIES',
                'access_token': IG_ACCESS_TOKEN
            }
            res_container = requests.post(url_container, data=payload, timeout=25)
            res_container_json = res_container.json()
            
            if 'id' not in res_container_json:
                raise Exception(f"Falha ao criar container do story {idx+1}. Resposta: {res_container_json}")
            
            creation_id = res_container_json['id']
            time.sleep(10)
            
            url_publish = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish"
            payload_publish = {
                'creation_id': creation_id,
                'access_token': IG_ACCESS_TOKEN
            }
            res_publish = requests.post(url_publish, data=payload_publish, timeout=25)
            res_publish_json = res_publish.json()
            
            if 'id' not in res_publish_json:
                raise Exception(f"Falha ao publicar story {idx+1}. Resposta: {res_publish_json}")
            
            ultimo_id = res_publish_json['id']
            print(f"✅ Story {idx+1}/{len(midias)} publicado! ID: {ultimo_id}")
            
            # Intervalo entre stories para garantir a ordem
            if idx < len(midias) - 1:
                print("⏳ Aguardando 15s antes do próximo story...")
                time.sleep(15)
        
        print(f"🎉 SEQUÊNCIA DE STORIES PUBLICADA COM SUCESSO!")
        return ultimo_id
        
    # 2. Carrossel
    elif tipo == "carousel":
        if dry_run:
            print(f"[DRY-RUN] Criaria containers filhos para {len(midia)} imagens e criaria carrossel.")
            return "DRY_RUN_CAROUSEL_ID"
            
        child_ids = []
        for idx, caminho_slide in enumerate(midia):
            print(f"Carregando imagem do slide {idx+1}/{len(midia)}...")
            url_publica = upload_temporario(caminho_slide)
            
            url_container = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
            payload = {
                'image_url': url_publica,
                'is_carousel_item': 'true',
                'access_token': IG_ACCESS_TOKEN
            }
            res_container = requests.post(url_container, data=payload, timeout=25)
            res_container_json = res_container.json()
            
            if 'id' not in res_container_json:
                raise Exception(f"Falha ao criar slide filho {idx}. Resposta: {res_container_json}")
                
            child_ids.append(res_container_json['id'])
            print(f"✅ Slide filho {idx} criado. ID: {res_container_json['id']}")
            
        # Polling dos filhos
        for cid in child_ids:
            aguardar_processamento_container(cid)
            
        # Cria container pai
        print("Criando container pai para o Carrossel...")
        children_str = ",".join(child_ids)
        url_parent = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
        payload_parent = {
            'media_type': 'CAROUSEL',
            'children': children_str,
            'caption': legenda,
            'access_token': IG_ACCESS_TOKEN
        }
        res_parent = requests.post(url_parent, data=payload_parent, timeout=25)
        res_parent_json = res_parent.json()
        
        if 'id' not in res_parent_json:
            raise Exception(f"Falha ao criar pai do carrossel. Resposta: {res_parent_json}")
            
        parent_id = res_parent_json['id']
        print(f"✅ Container pai criado! ID: {parent_id}")
        
        # Polling do pai
        aguardar_processamento_container(parent_id)
        
        # Publica
        url_publish = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish"
        payload_publish = {
            'creation_id': parent_id,
            'access_token': IG_ACCESS_TOKEN
        }
        res_publish = requests.post(url_publish, data=payload_publish, timeout=25)
        res_publish_json = res_publish.json()
        
        if 'id' not in res_publish_json:
            raise Exception(f"Falha ao publicar carrossel. Resposta: {res_publish_json}")
            
        print(f"🎉 CARROSSEL PUBLICADO COM SUCESSO! ID da publicação: {res_publish_json['id']}")
        return res_publish_json['id']
        
    # 3. Reels / Pexels Stories (vídeo)
    elif tipo in ["reels", "pexels_story"]:
        if dry_run:
            print(f"[DRY-RUN] Enviaria vídeo Reels {midia} e publicaria.")
            return "DRY_RUN_REELS_ID"
            
        url_publica = upload_temporario(midia)
        
        print("Criando contêiner de Reels...")
        url_container = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
        payload = {
            'media_type': 'REELS',
            'video_url': url_publica,
            'caption': legenda,
            'share_to_feed': 'true',
            'access_token': IG_ACCESS_TOKEN
        }
        res_container = requests.post(url_container, data=payload, timeout=25)
        res_container_json = res_container.json()
        
        if 'id' not in res_container_json:
            raise Exception(f"Falha ao criar container Reels. Resposta: {res_container_json}")
            
        reels_id = res_container_json['id']
        print(f"✅ Container Reels criado! ID: {reels_id}")
        
        # Polling
        aguardar_processamento_container(reels_id, max_tentativas=25)
        
        # Publica
        url_publish = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish"
        payload_publish = {
            'creation_id': reels_id,
            'access_token': IG_ACCESS_TOKEN
        }
        res_publish = requests.post(url_publish, data=payload_publish, timeout=25)
        res_publish_json = res_publish.json()
        
        if 'id' not in res_publish_json:
            raise Exception(f"Falha ao publicar Reels. Resposta: {res_publish_json}")
            
        print(f"🎉 REELS PUBLICADO COM SUCESSO! ID da publicação: {res_publish_json['id']}")
        return res_publish_json['id']

