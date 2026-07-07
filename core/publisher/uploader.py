import requests
import time
import os

def upload_temporario(caminho_arquivo):
    print(f"📤 Enviando {caminho_arquivo} para catbox.moe...")
    try:
        with open(caminho_arquivo, 'rb') as f:
            response = requests.post("https://catbox.moe/user/api.php", data={'reqtype': 'fileupload'}, files={"fileToUpload": f}, timeout=120)
            
        if response.status_code == 200:
            url_download_direto = response.text.strip()
            if url_download_direto.startswith("https://"):
                print(f"🔗 Link direto de acesso gerado: {url_download_direto}")
                # Aguarda o servidor disponibilizar o arquivo antes do Instagram tentar acessá-lo
                print("⏳ Aguardando 10s para o arquivo ficar disponível no servidor...")
                time.sleep(10)
                return url_download_direto
            else:
                raise Exception(f"Falha na API catbox.moe (resposta inesperada): {url_download_direto}")
        else:
            raise Exception(f"Código HTTP inválido: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao enviar arquivo para o servidor temporário: {e}")
        raise e

