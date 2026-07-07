import requests
import time
import os

def upload_temporario(caminho_arquivo):
    print(f"📤 Enviando {caminho_arquivo} para catbox.moe (suporta até 200MB)...")
    try:
        with open(caminho_arquivo, 'rb') as f:
            # catbox.moe API requires reqtype=fileupload
            payload = {'reqtype': 'fileupload'}
            files = {'fileToUpload': f}
            response = requests.post("https://catbox.moe/user/api.php", data=payload, files=files, timeout=120)
            
        if response.status_code == 200:
            url_download_direto = response.text.strip()
            if url_download_direto.startswith("http"):
                print(f"🔗 Link direto de acesso gerado: {url_download_direto}")
                print("⏳ Aguardando 10s para o arquivo ficar disponível globalmente...")
                time.sleep(10)
                return url_download_direto
            else:
                raise Exception(f"Falha na API catbox.moe (resposta inesperada): {url_download_direto}")
        else:
            raise Exception(f"Código HTTP inválido: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao enviar arquivo para o servidor temporário: {e}")
        raise e

