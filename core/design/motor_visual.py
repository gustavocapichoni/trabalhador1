import os
import requests
import textwrap
import random
from io import BytesIO
from PIL import Image, ImageDraw

from .efeitos import aplicar_mesh_gradient, draw_text_with_shadow
from .templates import carregar_fontes, CORES

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def buscar_imagem_fundo(tipo, tema_escolhido, TEMAS_MAPEADOS):
    """Busca imagem no Unsplash ou retorna fundo escuro."""
    if tipo in ["story", "story_manha", "story_tarde", "reels", "reels_noite", "pexels_story", "pexels_story_noite", "test"]:
        W, H = 1080, 1920
        orientation = "portrait"
    else:
        W, H = 1080, 1080
        orientation = "squarish"

    if not UNSPLASH_ACCESS_KEY:
        print("⚠️ UNSPLASH_ACCESS_KEY ausente. Usando fundo escuro sólido.")
        return Image.new('RGBA', (W, H), color=(20, 20, 20, 255)), W, H

    query_termo = "nature,dark,landscape,abstract"
    if tema_escolhido and tema_escolhido in TEMAS_MAPEADOS:
        query_termo = TEMAS_MAPEADOS[tema_escolhido].get("query_unsplash", query_termo)
        
    url_unsplash = f"https://api.unsplash.com/photos/random?query={query_termo}&orientation={orientation}&client_id={UNSPLASH_ACCESS_KEY}"
    try:
        response = requests.get(url_unsplash, timeout=15)
        if response.status_code == 200:
            img_url = response.json()['urls']['regular']
            img_response = requests.get(img_url, timeout=15)
            img = Image.open(BytesIO(img_response.content)).convert("RGBA")
            return img.resize((W, H), Image.Resampling.LANCZOS), W, H
    except Exception as e:
        print(f"⚠️ Erro ao acessar Unsplash: {e}. Usando fallback.")
        
    return Image.new('RGBA', (W, H), color=(20, 20, 20, 255)), W, H

def criar_arte(tipo, dados, tema_escolhido, TEMAS_MAPEADOS):
    print(f"🎨 Desenhando arte ({tipo.upper()}) com Design Premium...")
    
    img, W, H = buscar_imagem_fundo(tipo, tema_escolhido, TEMAS_MAPEADOS)
    
    # Aplica Gradient Inteligente em vez de overlay preto sólido
    img = aplicar_mesh_gradient(img)
    
    if tipo == "carousel":
        return _gerar_carrossel(img, W, H, dados)
    elif tipo == "reels":
        return _gerar_reels(img, W, H, dados)
    else:
        return _gerar_estatico(img, W, H, tipo, dados)

def _gerar_carrossel(img, W, H, dados):
    caminhos_arquivos = []
    slides_conteudo = [dados["titulo"]] + dados["slides"] + ["CTA"]
    
    font_capa, font_slides, font_marca = carregar_fontes(tamanho_display=62, tamanho_body=46, tamanho_detalhe=22)
    font_sub = carregar_fontes(tamanho_display=30, tamanho_body=30, tamanho_detalhe=30)[0]
    
    for idx, texto in enumerate(slides_conteudo):
        slide_img = img.copy().convert("RGB")
        draw = ImageDraw.Draw(slide_img)
        
        # Marca d'água
        draw_text_with_shadow(draw, (W/2, H - 80), "⚜ @gustavo_8k_ ⚜", font_marca, fill=CORES["destaque"], anchor="ms")
        
        if idx == 0:  # Capa (Playfair Display)
            linhas = textwrap.wrap(texto, width=20)
            y_inicial = (H - (len(linhas) * 75)) / 2 - 40
            for i, linha in enumerate(linhas):
                draw_text_with_shadow(draw, (W/2, y_inicial + i * 75), linha, font_capa, fill=CORES["texto_principal"], anchor="ms")
            draw_text_with_shadow(draw, (W/2, H - 175), "Arrasta para o lado  ▶", font_sub, fill=CORES["destaque"], anchor="ms")
            
        elif texto == "CTA":  # Slide Final
            draw.line([(W*0.15, H*0.35), (W*0.85, H*0.35)], fill=CORES["destaque"], width=2)
            linhas_cta = ["Gostou deste conteúdo?", "", "Salva para não perder", "e segue a página para mais!", "", "✦ @gustavo_8k_ ✦"]
            y_inicial = H * 0.38
            for i, linha in enumerate(linhas_cta):
                cor = CORES["destaque"] if "@" in linha else CORES["texto_principal"]
                draw_text_with_shadow(draw, (W/2, y_inicial + i * 58), linha, font_slides, fill=cor, anchor="ms")
            draw.line([(W*0.15, H*0.72), (W*0.85, H*0.72)], fill=CORES["destaque"], width=2)
                
        else:  # Slides de conteúdo (Montserrat)
            linhas = textwrap.wrap(texto, width=24)
            y_inicial = (H - (len(linhas) * 62)) / 2
            for i, linha in enumerate(linhas):
                draw_text_with_shadow(draw, (W/2, y_inicial + i * 62), linha, font_slides, fill=CORES["texto_principal"], anchor="ms")
                
        caminho = f"carousel_{idx}.jpg"
        slide_img.save(caminho, "JPEG", quality=95)
        caminhos_arquivos.append(caminho)
        
    return caminhos_arquivos

def _gerar_reels(img, W, H, dados):
    caminhos = []
    frases = dados.get("slides", [dados.get("frase", "...")])
    font_display, font_body, font_marca = carregar_fontes(52, 22, 24)
    
    for idx, frase in enumerate(frases):
        slide = img.copy().convert("RGB")
        draw = ImageDraw.Draw(slide)
        
        draw_text_with_shadow(draw, (W/2, H - 150), "— @gustavo_8k_ —", font_marca, fill=CORES["texto_secundario"], anchor="ms")
        draw_text_with_shadow(draw, (W/2, H - 220), f"{idx+1} / {len(frases)}", font_body, fill=CORES["texto_secundario"], anchor="ms")
        
        linhas = textwrap.wrap(frase, width=22)
        y_inicial = (H - (len(linhas) * 70)) / 2
        for i, linha in enumerate(linhas):
            draw_text_with_shadow(draw, (W/2, y_inicial + i * 70), linha, font_display, fill=CORES["texto_principal"], anchor="ms")
            
        caminho = f"reels_slide_{idx}.jpg"
        slide.save(caminho, "JPEG", quality=95)
        caminhos.append(caminho)
    return caminhos

def _gerar_estatico(img, W, H, tipo, dados):
    font_display, _, font_marca = carregar_fontes(48, 24, 24)
    layout_style = random.choice(["classic", "bottom", "quote"])
    print(f"🎨 Usando estilo de layout: {layout_style.upper()}")
    
    frases = dados.get("frase", dados.get("slides", [""]))
    if isinstance(frases, str):
        frases = [frases]
        
    caminhos = []
    
    for idx, frase in enumerate(frases):
        slide = img.copy().convert("RGB")
        draw = ImageDraw.Draw(slide)
        
        y_watermark = H - 150 if tipo in ["story", "story_manha", "story_tarde", "test"] else H - 80
        draw_text_with_shadow(draw, (W/2, y_watermark), "@gustavo_8k_", font_marca, fill=CORES["texto_secundario"], anchor="ms")
        
        linhas = textwrap.wrap(frase, width=24)
        
        if layout_style == "bottom":
            font_display_bot, _, _ = carregar_fontes(42, 24, 24)
            y_inicial = H - (len(linhas) * 55) - 250
            for i, linha in enumerate(linhas):
                draw_text_with_shadow(draw, (W/2, y_inicial + i * 55), linha, font_display_bot, fill=CORES["texto_principal"], anchor="ms")
                
        elif layout_style == "quote":
            y_inicial = (H - (len(linhas) * 60)) / 2 - 100
            for i, linha in enumerate(linhas):
                draw_text_with_shadow(draw, (100, y_inicial + i * 60), linha, font_display, fill=CORES["texto_principal"], anchor="ls")
            draw.line([(70, y_inicial - 50), (70, y_inicial + len(linhas)*60)], fill=CORES["destaque"], width=8)
            
        else:
            y_inicial = (H - (len(linhas) * 60)) / 2
            for i, linha in enumerate(linhas):
                draw_text_with_shadow(draw, (W/2, y_inicial + i * 60), linha, font_display, fill=CORES["texto_principal"], anchor="ms")
            
        caminho_imagem = f"story_pronto_{idx}.jpg" if tipo in ["story", "story_manha", "story_tarde", "test"] else f"post_pronto_{idx}.jpg"
        slide.save(caminho_imagem, "JPEG", quality=95)
        caminhos.append(caminho_imagem)
        
    if len(caminhos) == 1:
        return caminhos[0]
    return caminhos
