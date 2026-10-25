import os
import google_auth_oauthlib.flow

# Escopos necessários para postar vídeos e ler relatórios do Analytics
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

def autenticar():
    print("Iniciando fluxo de autenticação do YouTube...")
    
    if not os.path.exists("client_secrets.json"):
        print("❌ Arquivo 'client_secrets.json' não encontrado na raiz do projeto.")
        print("Por favor, baixe o arquivo JSON das credenciais do Google Cloud Console,")
        print("coloque-o nesta pasta e renomeie-o para 'client_secrets.json'.")
        return

    try:
        # Cria o fluxo de autenticação a partir do arquivo
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            "client_secrets.json", SCOPES
        )
        
        # Abre o navegador para o usuário fazer login
        credentials = flow.run_local_server(port=0)
        
        # Salva o token de acesso no arquivo token_youtube.json
        with open("token_youtube.json", "w") as token_file:
            token_file.write(credentials.to_json())
            
        print("\n✅ Autenticação concluída com sucesso!")
        print("O arquivo 'token_youtube.json' foi criado. Você já pode postar vídeos e coletar métricas.")
        
    except Exception as e:
        print(f"\n❌ Erro durante a autenticação: {e}")

if __name__ == "__main__":
    autenticar()
