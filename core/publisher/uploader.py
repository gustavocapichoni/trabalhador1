import requests
import time
import os

def upload_temporario(caminho_arquivo):
    print(f"📤 Enviando {caminho_arquivo} para tmpfiles.org...")
    try:
        with open(caminho_arquivo, 'rb') as f:
            response = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=120)
            
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                url_visualizador = data["data"]["url"]
                # Converte em link de download direto
                url_download_direto = url_visualizador.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
                print(f"🔗 Link direto de acesso gerado: {url_download_direto}")
                return url_download_direto
            else:
                raise Exception(f"Falha na API tmpfiles: {data}")
        else:
            raise Exception(f"Código HTTP inválido: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao enviar arquivo para o servidor temporário: {e}")
        raise e

