"""
gerador.py — Script Principal do Gerador de PDF Semanal

Orquestra todo o processo:
1. Decisor: lê analytics + tendências e escolhe o tema/livro
2. Conteúdo: gera a narrativa completa via Gemini AI
3. Construtor: monta o PDF visual com fpdf2
4. Uploader: sobe para Firebase e registra no Firestore

Roda todo domingo de madrugada (via GitHub Actions ou cron externo).
"""
import os
import sys
import json
from datetime import datetime

# Garante encoding UTF-8 no terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ─── Paths ───
PASTA_GERADOR = os.path.dirname(os.path.abspath(__file__))
PASTA_SAIDA = os.path.join(PASTA_GERADOR, "output")
BOT_PATH = os.path.abspath(os.path.join(PASTA_GERADOR, ".."))
sys.path.insert(0, BOT_PATH)

from dotenv import load_dotenv
load_dotenv(os.path.join(BOT_PATH, ".env"))

# ─── Módulos do gerador ───
from decisor import montar_briefing_completo
from conteudo import gerar_conteudo_pdf
from gerar_pdf import gerar_pdf
from uploader import fazer_upload_pdf, registrar_campanha_no_firestore

DRY_RUN = "--dry-run" in sys.argv  # Passa --dry-run para testar sem subir para o Firebase


def main():
    print("\n" + "="*60)
    print("🚀 GERADOR DE PDF SEMANAL — INICIANDO")
    print(f"   Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    if DRY_RUN:
        print("   ⚠️  MODO DRY-RUN: Não vai subir para o Firebase!")
    print("="*60 + "\n")

    # ─── ETAPA 1: Decidir o tema e livro com base nos dados ───
    print("─── ETAPA 1: Análise de Dados ───")
    briefing = montar_briefing_completo()

    # ─── ETAPA 2: Gerar o conteúdo narrativo via IA ───
    print("\n─── ETAPA 2: Geração de Conteúdo ───")
    conteudo = gerar_conteudo_pdf(briefing)

    # Salva o JSON do conteúdo para debug
    caminho_json = os.path.join(PASTA_SAIDA, "ultimo_conteudo.json")
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=2)
    print(f"   💾 Conteúdo salvo em: {caminho_json}")

    # ─── ETAPA 3: Montar o PDF visual ───
    print("\n─── ETAPA 3: Construção Visual do PDF ───")
    semana_str = datetime.now().strftime("%Y-W%W")
    # Remove caracteres invalidos em nomes de arquivo no Windows
    titulo_limpo = conteudo['titulo_pdf'][:30]
    for char in [':', '/', '\\', '*', '?', '"', '<', '>', '|']:
        titulo_limpo = titulo_limpo.replace(char, '')
    titulo_limpo = titulo_limpo.strip().replace(' ', '_')
    nome_arquivo = f"pdf_{semana_str}_{titulo_limpo}.pdf"
    caminho_pdf = os.path.join(PASTA_SAIDA, nome_arquivo)
    gerar_pdf(caminho_pdf, conteudo=conteudo)

    if DRY_RUN:
        print("\n⚠️  DRY-RUN: Pulando upload para Firebase.")
        print(f"\n✅ PDF gerado localmente: {caminho_pdf}")
        print("   Abra o arquivo para verificar o resultado!")
        return

    # ─── ETAPA 4: Subir para Firebase e registrar campanha ───
    print("\n─── ETAPA 4: Upload para Firebase ───")
    url_pdf = fazer_upload_pdf(caminho_pdf, conteudo["titulo_pdf"])
    registrar_campanha_no_firestore(conteudo["titulo_pdf"], url_pdf, briefing)

    print("\n" + "="*60)
    print("🎉 PDF DA SEMANA GERADO COM SUCESSO!")
    print(f"   Título: {conteudo['titulo_pdf']}")
    print(f"   Tema:   {briefing['nome_display']}")
    print(f"   Livro:  {briefing['livro_base']}")
    print(f"   URL:    {url_pdf}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
