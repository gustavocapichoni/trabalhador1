import os
import requests
import textwrap
import random
from io import BytesIO
from PIL import Image, ImageDraw

from .efeitos import aplicar_mesh_gradient, draw_text_with_shadow
from .templates import carregar_fontes, CORES
from core.config.state import verificar_midia_recente, registrar_midia_usada

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def buscar_imagem_fundo(tipo, tema_escolhido, TEMAS_MAPEADOS):
    """
    Busca de imagem em Cascata (Fase 2):
    Nível 1: Pollinations AI (Originalidade 100%)
    Nível 2: Unsplash API (Fotos Reais)
    Nível 3: Biblioteca Local (Modo Offline)
    Nível 4: Fundo Sólido Escuro (Emergência Catastrófica)
    """
    if tipo in ["story", "story_manha", "story_tarde", "reels", "reels_noite", "reels_conquistador", "pexels_story", "pexels_story_noite", "test"]:
        W, H = 1080, 1920
        orientation = "portrait"
    else:
        W, H = 1080, 1080
        orientation = "squarish"

    query_termo = "dark,dramatic,cinematic,abstract"
    if tema_escolhido and tema_escolhido in TEMAS_MAPEADOS:
        query_termo = TEMAS_MAPEADOS[tema_escolhido].get("query_unsplash", query_termo)

    # --- NÍVEL 1: INTELIGÊNCIA ARTIFICIAL (Pollinations) ---
    try:
        print(f"🧠 [NÍVEL 1] Tentando gerar imagem exclusiva via IA (Pollinations): '{query_termo}'")
        # Substitui vírgulas por espaços para o prompt da IA fluir melhor
        ai_prompt = query_termo.replace(",", " ")
        url_pollinations = f"https://image.pollinations.ai/prompt/{ai_prompt}?width={W}&height={H}&nologo=true"
        
        # Timeout de 20s porque IA pode demorar um pouquinho para "pensar"
        response_ia = requests.get(url_pollinations, timeout=20)
        
        if response_ia.status_code == 200:
            print("✅ Imagem gerada por IA com sucesso!")
            img = Image.open(BytesIO(response_ia.content)).convert("RGBA")
            return img.resize((W, H), Image.Resampling.LANCZOS), W, H
        else:
            print(f"⚠️ IA (Pollinations) falhou com status {response_ia.status_code}. Tentando Nível 2...")
    except Exception as e:
        print(f"⚠️ Erro na geração de IA: {e}. Tentando Nível 2 (Unsplash)...")

    # --- NÍVEL 2: BANCO DE FOTOS REAIS (Unsplash) ---
    if not UNSPLASH_ACCESS_KEY:
        print("⚠️ UNSPLASH_ACCESS_KEY ausente. Tentando Nível 3 (Biblioteca Local)...")
    else:
        print(f"📸 [NÍVEL 2] Buscando foto real no Unsplash: '{query_termo}'")
        url_unsplash = f"https://api.unsplash.com/photos/random?query={query_termo}&orientation={orientation}&client_id={UNSPLASH_ACCESS_KEY}"
        
        tentativas = 0
        img_valida_url = None
        
        while tentativas < 3:
            try:
                response = requests.get(url_unsplash, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    img_url = data['urls']['regular']
                    img_id = data.get('id', img_url)
                    
                    if verificar_midia_recente(img_id):
                        print(f"🔄 Imagem já usada recentemente ({img_id}). Tentando outra...")
                        tentativas += 1
                        continue
                        
                    img_valida_url = img_url
                    registrar_midia_usada(img_id)
                    break
                else:
                    print(f"⚠️ Unsplash retornou status {response.status_code}. Tentando Nível 3...")
                    break
            except Exception as e:
                print(f"⚠️ Erro ao acessar Unsplash: {e}. Tentando Nível 3...")
                break
                
        if img_valida_url:
            try:
                img_response = requests.get(img_valida_url, timeout=15)
                img = Image.open(BytesIO(img_response.content)).convert("RGBA")
                print("✅ Foto do Unsplash carregada com sucesso e é inédita!")
                return img.resize((W, H), Image.Resampling.LANCZOS), W, H
            except Exception as e:
                print(f"⚠️ Erro ao baixar imagem validada do Unsplash: {e}")

    # --- FALLBACK: Biblioteca Local de Emergência ---
    tema_pasta = tema_escolhido if tema_escolhido else "geral"
    pasta_tema = os.path.join("biblioteca_local", "imagens", tema_pasta)
    pasta_geral = os.path.join("biblioteca_local", "imagens")

    for pasta in [pasta_tema, pasta_geral]:
        if os.path.exists(pasta):
            extensoes = [".jpg", ".jpeg", ".png", ".webp"]
            arquivos = [f for f in os.listdir(pasta) if any(f.lower().endswith(e) for e in extensoes)]
            if arquivos:
                escolhido = os.path.join(pasta, random.choice(arquivos))
                print(f"📂 [EMERGÊNCIA] Usando imagem local: {escolhido}")
                try:
                    img = Image.open(escolhido).convert("RGBA")
                    return img.resize((W, H), Image.Resampling.LANCZOS), W, H
                except Exception as e2:
                    print(f"⚠️ Erro ao carregar imagem local: {e2}")

    print("⚠️ Sem imagens locais disponíveis. Usando fundo escuro sólido.")
    return Image.new('RGBA', (W, H), color=(20, 20, 20, 255)), W, H

def criar_arte(tipo, dados, tema_escolhido, TEMAS_MAPEADOS):
    print(f"🎨 Desenhando arte ({tipo.upper()}) com Design Premium...")
    
    img, W, H = buscar_imagem_fundo(tipo, tema_escolhido, TEMAS_MAPEADOS)
    
    # Aplica Gradient Inteligente em vez de overlay preto sólido
    img = aplicar_mesh_gradient(img)
    
    if tipo == "carousel":
        return _gerar_carrossel(img, W, H, dados)
    elif tipo in ["reels", "reels_noite", "reels_conquistador"]:
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
    layout_style = random.choice(["classic", "bottom", "quote"])
    print(f"🎨 Usando estilo de layout: {layout_style.upper()}")
    
    if layout_style == "classic":
        estilo_fonte = "Montserrat"
    elif layout_style == "bottom":
        estilo_fonte = "Oswald"
    else:
        estilo_fonte = "Playfair"
        
    font_display, _, font_marca = carregar_fontes(48, 24, 24, estilo=estilo_fonte)
    
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
            font_display_bot, _, _ = carregar_fontes(42, 24, 24, estilo=estilo_fonte)
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
