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

import shutil
import subprocess
from core.analytics.db import get_db

# Caminho para o repositório clonado localmente
REPOSITORIO_PDFS = os.path.join(os.path.dirname(__file__), "repositorio_pdfs")


def fazer_upload_pdf(caminho_local: str, titulo_pdf: str) -> str:
    """
    Copia o PDF para o repositório 'gustavo_8k' clonado localmente e faz o git push.
    Retorna a URL Raw do GitHub.
    """
    semana_str = datetime.now().strftime("%Y-W%W")
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_no_git = f"pdf_{timestamp_str}_{semana_str}.pdf"

    print(f"☁️  [Uploader] Copiando '{os.path.basename(caminho_local)}' para a pasta repositorio_pdfs...")
    
    # 1. Copia o PDF para o repositório clonado
    os.makedirs(REPOSITORIO_PDFS, exist_ok=True)
    caminho_destino = os.path.join(REPOSITORIO_PDFS, nome_no_git)
    shutil.copy2(caminho_local, caminho_destino)

    print(f"🐙 [Uploader] Subindo para o GitHub (gustavo_8k)...")
    
    try:
        # 2. Executa os comandos do git dentro da pasta repositorio_pdfs
        subprocess.run(["git", "config", "--local", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=REPOSITORIO_PDFS, check=True)
        subprocess.run(["git", "config", "--local", "user.name", "github-actions[bot]"], cwd=REPOSITORIO_PDFS, check=True)
        subprocess.run(["git", "add", "-f", nome_no_git], cwd=REPOSITORIO_PDFS, check=True)
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


def registrar_campanha_no_firestore(titulo: str, url_pdf: str, briefing: dict, landing_page: dict = None):
    """
    Salva os dados da campanha ativa no Firestore.
    A Landing Page vai ler esse documento para exibir o nome certo do PDF
    e entregar o link correto no e-mail.
    """
    db = get_db()
    if not db:
        print("⚠️ [Uploader] Firestore não disponível. Pulando registro de campanha no banco.")
        return None
    semana_str = datetime.now().strftime("%Y-W%W")

    campanha = {
        "titulo": titulo,
        "pdf_url": url_pdf,
        "tema": briefing.get("tema_chave", ""),
        "livro_base": briefing.get("livro_base", ""),
        "dor_central": briefing.get("dor_central", ""),
        "contexto_semana": briefing.get("contexto_semana", ""),
        "dados_performance_perfil": briefing.get("dados_performance_perfil", ""),
        "semana": semana_str,
        "criada_em": datetime.now(timezone.utc),
        "ativa": True,
        "landing_page": landing_page or {}
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

