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
import uuid
import urllib.parse
import requests
import time
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

    # ─── ETAPA 2.5: Busca de Imagens via Unsplash/Pexels/Pixabay + Conversão P&B ───
    print("\n─── ETAPA 2.5: Busca de Imagens (Unsplash → Pexels → Pixabay) ───")
    pasta_imagens = os.path.join(PASTA_SAIDA, "imagens_temp")
    os.makedirs(pasta_imagens, exist_ok=True)

    UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
    PEXELS_KEY   = os.getenv("PEXELS_API_KEY", "")
    PIXABAY_KEY  = os.getenv("PIXABAY_API_KEY", "")

    def extrair_query(prompt_texto):
        """Extrai palavras-chave simples do prompt da IA para busca nas APIs de fotos."""
        if not prompt_texto:
            return "cinematic dramatic portrait"
        import re
        texto = prompt_texto.lower()
        remover = {"cinematic", "moody", "photography", "of", "a", "an", "the",
                   "in", "with", "dark", "8k", "hiper", "realista", "cinematographic",
                   "highly", "detailed", "shadows", "and", "at", "looking", "out",
                   "being", "forged", "photo", "image", "shot", "view", "scene"}
        palavras = re.findall(r'\b[a-z]{3,}\b', texto)
        filtradas = [p for p in palavras if p not in remover][:5]
        return " ".join(filtradas) if filtradas else "dramatic portrait dark shadows"

    def converter_pb(caminho):
        """Converte a imagem para preto e branco usando Pillow."""
        try:
            from PIL import Image as PILImage, ImageOps
            with PILImage.open(caminho) as img:
                img_rgb = img.convert("RGB")
                img_pb = ImageOps.grayscale(img_rgb)
                img_pb_rgb = img_pb.convert("RGB")  # mantém formato JPEG compatível
                img_pb_rgb.save(caminho, quality=92)
            return True
        except Exception as e:
            print(f"      [!] Erro ao converter P&B: {e}")
            return False

    def _salvar_imagem(conteudo_bytes, prefix):
        """Salva bytes de imagem em disco e retorna o caminho."""
        nome = f"{prefix}_{uuid.uuid4().hex[:6]}.jpg"
        caminho = os.path.join(pasta_imagens, nome)
        with open(caminho, 'wb') as f:
            f.write(conteudo_bytes)
        return caminho

    def buscar_unsplash(query, prefix):
        if not UNSPLASH_KEY:
            return None
        try:
            url = (f"https://api.unsplash.com/photos/random"
                   f"?query={urllib.parse.quote(query)}&orientation=landscape&content_filter=high")
            headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                img_url = resp.json().get("urls", {}).get("regular", "")
                if img_url:
                    ir = requests.get(img_url, timeout=30)
                    if ir.status_code == 200 and len(ir.content) > 5000:
                        return _salvar_imagem(ir.content, prefix)
        except Exception as e:
            print(f"      [!] Unsplash erro: {e}")
        return None

    def buscar_pexels(query, prefix):
        if not PEXELS_KEY:
            return None
        try:
            url = (f"https://api.pexels.com/v1/search"
                   f"?query={urllib.parse.quote(query)}&per_page=5&orientation=landscape")
            headers = {"Authorization": PEXELS_KEY}
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                import random as _rnd
                fotos = resp.json().get("photos", [])
                if fotos:
                    img_url = _rnd.choice(fotos).get("src", {}).get("large", "")
                    if img_url:
                        ir = requests.get(img_url, timeout=30)
                        if ir.status_code == 200 and len(ir.content) > 5000:
                            return _salvar_imagem(ir.content, prefix)
        except Exception as e:
            print(f"      [!] Pexels erro: {e}")
        return None

    def buscar_pixabay(query, prefix):
        if not PIXABAY_KEY:
            return None
        try:
            url = (f"https://pixabay.com/api/"
                   f"?key={PIXABAY_KEY}&q={urllib.parse.quote(query)}"
                   f"&image_type=photo&orientation=horizontal&per_page=5&safesearch=true")
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                import random as _rnd
                hits = resp.json().get("hits", [])
                if hits:
                    img_url = _rnd.choice(hits).get("largeImageURL", "")
                    if img_url:
                        ir = requests.get(img_url, timeout=30)
                        if ir.status_code == 200 and len(ir.content) > 5000:
                            return _salvar_imagem(ir.content, prefix)
        except Exception as e:
            print(f"      [!] Pixabay erro: {e}")
        return None

    def buscar_foto_pb(prompt, prefix):
        """Busca foto em cascata (Unsplash → Pexels → Pixabay) e converte para P&B."""
        if not prompt:
            return None
        query = extrair_query(prompt)
        print(f"   Buscando imagem '{prefix}' (query: '{query}')...")
        time.sleep(0.5)  # pausa educada entre requisicoes

        caminho = buscar_unsplash(query, prefix)
        if not caminho:
            print(f"      [>] Unsplash sem resultado. Tentando Pexels...")
            caminho = buscar_pexels(query, prefix)
        if not caminho:
            print(f"      [>] Pexels sem resultado. Tentando Pixabay...")
            caminho = buscar_pixabay(query, prefix)

        if caminho:
            print(f"      [OK] Convertendo para preto e branco...")
            converter_pb(caminho)
            print(f"      [OK] {os.path.basename(caminho)}")
            return caminho

        print(f"      [SKIP] {prefix} sem imagem — usando fundo escuro.")
        return None

    if "prompt_imagem_capa" in conteudo:
        conteudo["img_local_capa"] = buscar_foto_pb(conteudo["prompt_imagem_capa"], "capa")
    
    if "capitulos" in conteudo:
        for idx, cap in enumerate(conteudo["capitulos"]):
            if "prompt_imagem" in cap:
                cap["img_local"] = buscar_foto_pb(cap["prompt_imagem"], f"capitulo_{idx+1}")
                
    if "plano_acao" in conteudo and "prompt_imagem" in conteudo["plano_acao"]:
        conteudo["plano_acao"]["img_local"] = buscar_foto_pb(conteudo["plano_acao"]["prompt_imagem"], "plano_acao")


    # Salva o JSON do conteúdo para debug
    caminho_json = os.path.join(PASTA_SAIDA, "ultimo_conteudo.json")
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=2)
    print(f"\n   💾 Conteúdo e dados salvos em: {caminho_json}")

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
    landing_page_data = conteudo.get("landing_page", {})
    registrar_campanha_no_firestore(conteudo["titulo_pdf"], url_pdf, briefing, landing_page_data)

    print("\n" + "="*60)
    print("🎉 PDF DA SEMANA GERADO COM SUCESSO!")
    print(f"   Título: {conteudo['titulo_pdf']}")
    print(f"   Tema:   {briefing['nome_display']}")
    print(f"   Livro:  {briefing['livro_base']}")
    print(f"   URL:    {url_pdf}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
