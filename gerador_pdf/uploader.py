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
        chave_path = os.getenv("FIREBASE_KEY_PATH", os.path.join(BOT_PATH, "firebase-key.json"))
        cred = credentials.Certificate(chave_path)
        firebase_admin.initialize_app(cred)
        print("✅ [Uploader] Firebase Firestore inicializado com sucesso.")


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
        subprocess.run(["git", "add", nome_no_git], cwd=REPOSITORIO_PDFS, check=True)
        subprocess.run(["git", "commit", "-m", f"Adiciona PDF da semana {semana_str}: {titulo_pdf}"], cwd=REPOSITORIO_PDFS, check=True)
        # Tenta criar a branch main e dar push (importante se for repositório vazio)
        subprocess.run(["git", "branch", "-M", "main"], cwd=REPOSITORIO_PDFS, check=False)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=REPOSITORIO_PDFS, check=True)
        
        # 3. Monta a URL pública usando a CDN jsDelivr (Garante que o PDF abra na tela e não faça download forçado)
        url_publica = f"https://cdn.jsdelivr.net/gh/gustavocapichoni/gustavo_8k@main/{nome_no_git}"
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

    # Salva com ID único por semana (substitui se rodar duas vezes na mesma semana)
    doc_ref = db.collection("campanhas").document(f"semana_{semana_str}")
    doc_ref.set(campanha)

    print(f"✅ [Uploader] Campanha registrada no Firestore: 'semana_{semana_str}'")
    print(f"   Título: {titulo}")
    print(f"   URL: {url_pdf}")
    return doc_ref.id
