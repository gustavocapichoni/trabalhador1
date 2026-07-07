import requests
import time
import os

def upload_temporario(caminho_arquivo):
    print(f"📤 Enviando {caminho_arquivo} para uguu.se...")
    try:
        with open(caminho_arquivo, 'rb') as f:
            response = requests.post("https://uguu.se/upload.php", files={"files[]": f}, timeout=120)
            
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("files"):
                url_download_direto = data["files"][0]["url"]
                print(f"🔗 Link direto de acesso gerado: {url_download_direto}")
                # Aguarda o servidor disponibilizar o arquivo antes do Instagram tentar acessá-lo
                print("⏳ Aguardando 10s para o arquivo ficar disponível no servidor...")
                time.sleep(10)
                return url_download_direto
            else:
                raise Exception(f"Falha na API uguu.se (resposta inesperada): {data}")
        else:
            raise Exception(f"Código HTTP inválido: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao enviar arquivo para o servidor temporário: {e}")
        raise e

