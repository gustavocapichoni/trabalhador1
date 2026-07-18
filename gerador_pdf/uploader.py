"""
uploader.py — Upload para Firebase Storage e registro no Firestore

Faz o upload do PDF gerado para o Firebase Storage,
obtém o link público e salva a campanha no Firestore
para que a Landing Page leia automaticamente.
"""
import os
import sys
from datetime import datetime, timezone

BOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BOT_PATH)

from dotenv import load_dotenv
load_dotenv(os.path.join(BOT_PATH, ".env"))

import firebase_admin
from firebase_admin import credentials, firestore

import shutil
import subprocess

# Caminho para o repositório clonado localmente
REPOSITORIO_PDFS = os.path.join(os.path.dirname(__file__), "repositorio_pdfs")


def _inicializar_firebase():
    """Inicializa o Firebase Admin SDK para usar apenas o Firestore."""
    if not firebase_admin._apps:
        firebase_creds_str = os.getenv("FIREBASE_CREDENTIALS")
        
        if firebase_creds_str:
            # Se estiver rodando na nuvem (GitHub Actions)
            import json
            if firebase_creds_str.startswith("'") and firebase_creds_str.endswith("'"):
                firebase_creds_str = firebase_creds_str[1:-1]
            cred_dict = json.loads(firebase_creds_str)
            cred = credentials.Certificate(cred_dict)
            print("✅ [Uploader] Firebase Firestore inicializado via Secrets do GitHub.")
        else:
            # Se estiver rodando localmente
            chave_path = os.getenv("FIREBASE_KEY_PATH", os.path.join(BOT_PATH, "firebase-key.json"))
            cred = credentials.Certificate(chave_path)
            print("✅ [Uploader] Firebase Firestore inicializado via arquivo local.")
            
        firebase_admin.initialize_app(cred)


def fazer_upload_pdf(caminho_local: str, titulo_pdf: str) -> str:
    """
    Copia o PDF para o repositório 'gustavo_8k' clonado localmente e faz o git push.
    Retorna a URL Raw do GitHub.
    """
    semana_str = datetime.now().strftime("%Y-W%W")
    nome_no_git = f"pdf_semana_{semana_str}.pdf"

    print(f"☁️  [Uploader] Copiando '{os.path.basename(caminho_local)}' para a pasta repositorio_pdfs...")
    
    # 1. Copia o PDF para o repositório clonado
    caminho_destino = os.path.join(REPOSITORIO_PDFS, nome_no_git)
    shutil.copy2(caminho_local, caminho_destino)

    print(f"🐙 [Uploader] Subindo para o GitHub (gustavo_8k)...")
    
    try:
        # 2. Executa os comandos do git dentro da pasta repositorio_pdfs
        subprocess.run(["git", "config", "--local", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=REPOSITORIO_PDFS, check=True)
        subprocess.run(["git", "config", "--local", "user.name", "github-actions[bot]"], cwd=REPOSITORIO_PDFS, check=True)
        subprocess.run(["git", "add", nome_no_git], cwd=REPOSITORIO_PDFS, check=True)
        subprocess.run(["git", "commit", "-m", f"Adiciona PDF da semana {semana_str}: {titulo_pdf}"], cwd=REPOSITORIO_PDFS, check=True)
        # Tenta criar a branch main e dar push (importante se for repositório vazio)
        subprocess.run(["git", "branch", "-M", "main"], cwd=REPOSITORIO_PDFS, check=False)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=REPOSITORIO_PDFS, check=True)
        
        # 3. Pega o hash único do commit para quebrar o cache do jsDelivr
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORIO_PDFS).decode().strip()
        url_publica = f"https://cdn.jsdelivr.net/gh/gustavocapichoni/gustavo_8k@{commit_hash}/{nome_no_git}"
        print(f"✅ [Uploader] Upload para o GitHub concluído! URL: {url_publica}")
        return url_publica
        
    except subprocess.CalledProcessError as e:
        print(f"❌ [Uploader] Erro ao enviar para o GitHub: {e}")
        raise


def registrar_campanha_no_firestore(titulo: str, url_pdf: str, briefing: dict):
    """
    Salva os dados da campanha ativa no Firestore.
    A Landing Page vai ler esse documento para exibir o nome certo do PDF
    e entregar o link correto no e-mail.
    """
    _inicializar_firebase()

    db = firestore.client()
    semana_str = datetime.now().strftime("%Y-W%W")

    campanha = {
        "titulo": titulo,
        "pdf_url": url_pdf,
        "tema": briefing.get("tema_chave", ""),
        "livro_base": briefing.get("livro_base", ""),
        "semana": semana_str,
        "criada_em": datetime.now(timezone.utc),
        "ativa": True
    }

    # Salva com ID único auto-gerado para manter histórico completo de todas as execuções
    doc_ref = db.collection("campanhas").document()
    doc_ref.set(campanha)

    print(f"✅ [Uploader] Campanha registrada no Firestore: '{doc_ref.id}'")
    print(f"   Título: {titulo}")
    print(f"   URL: {url_pdf}")

    # Registra também no histórico de PDFs para anti-repetição de temas/títulos
    try:
        historico_pdf = {
            "titulo": titulo,
            "tema": briefing.get("tema_chave", ""),
            "livro_base": briefing.get("livro_base", ""),
            "semana": semana_str,
            "dor_principal": briefing.get("dor_alvo", ""),
            "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }
        db.collection("historico_pdfs").document(semana_str).set(historico_pdf)
        print(f"✅ [Uploader] PDF registrado em historico_pdfs (semana {semana_str}).")
    except Exception as e:
        print(f"⚠️ [Uploader] Erro ao registrar historico_pdfs: {e}")

    return doc_ref.id

