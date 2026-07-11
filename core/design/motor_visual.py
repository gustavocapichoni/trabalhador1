import os
import requests
import textwrap
import random
import uuid
from io import BytesIO
from PIL import Image, ImageDraw

from .efeitos import aplicar_mesh_gradient, draw_text_with_shadow, desenhar_elementos_premium
from .templates import carregar_fontes, obter_fonte_do_dia, CORES
from core.config.state import verificar_midia_recente, registrar_midia_usada

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def buscar_imagem_fundo(tipo, tema_escolhido, TEMAS_MAPEADOS, prompt_imagem=None):
    """
    Busca de imagem em Cascata (Fase 2):
    Nível 1: Pollinations AI (Originalidade 100%)
    Nível 2: Unsplash API (Fotos Reais)
    Nível 3: Biblioteca Local (Modo Offline)
    Nível 4: Fundo Sólido Escuro (Emergência Catastrófica)
    """
    if tipo == "carousel":
        W, H = 2160, 1080
        orientation = "landscape"
    elif tipo in ["story", "story_manha", "story_tarde", "reels", "reels_noite", "reels_conquistador", "pexels_story", "pexels_story_noite", "test", "reels_leads"]:
        W, H = 1080, 1920
        orientation = "portrait"
    else:
        W, H = 1080, 1080
        orientation = "squarish"

    query_termo = "premium,inspiring,cinematic,aesthetic"
    if tema_escolhido and tema_escolhido in TEMAS_MAPEADOS:
        query_termo = TEMAS_MAPEADOS[tema_escolhido].get("query_unsplash", query_termo)

    # Se o Gemini gerou um prompt específico, usamos ele! Se não, usamos o fallback do tema.
    termo_final_ia = prompt_imagem if prompt_imagem else query_termo

    # --- NÍVEL 1: INTELIGÊNCIA ARTIFICIAL (Pollinations) ---
    try:
        print(f"🧠 [NÍVEL 1] Tentando gerar imagem exclusiva via IA (Pollinations): '{termo_final_ia}'")
        # Substitui vírgulas por espaços para o prompt da IA fluir melhor
        ai_prompt = termo_final_ia.replace(",", " ")
        # Seed aleatório garante imagem diferente a cada chamada
        seed_aleatorio = random.randint(1, 999999)
        url_pollinations = f"https://image.pollinations.ai/prompt/{ai_prompt}?width={W}&height={H}&nologo=true&seed={seed_aleatorio}"
        
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

    # --- NÍVEL 2: BANCO DE IMAGENS REAL (Unsplash) ---
    print(f"📸 [NÍVEL 2] Buscando foto real no Unsplash: '{termo_final_ia}'")
    try:
        if UNSPLASH_ACCESS_KEY:
            # Usa a primeira metade do prompt_imagem (ou o termo todo se for curto) para a API do Unsplash não bugar com strings longas
            unsplash_query = termo_final_ia.split(",")[0][:40] 
            url_unsplash = f"https://api.unsplash.com/photos/random?query={unsplash_query}&orientation={orientation}&client_id={UNSPLASH_ACCESS_KEY}"
        else:
            print("⚠️ UNSPLASH_ACCESS_KEY ausente. Tentando Nível 3 (Biblioteca Local)...")
            url_unsplash = None
        
        tentativas = 0
        img_valida_url = None
        
        while tentativas < 3 and url_unsplash:
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
    except Exception as e:
        print(f"⚠️ Erro geral no nível 2 (Unsplash): {e}")

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
    
    prompt_imagem = dados.get("prompt_imagem")
    img, W, H = buscar_imagem_fundo(tipo, tema_escolhido, TEMAS_MAPEADOS, prompt_imagem=prompt_imagem)
    
    # Aplica Gradient Inteligente em vez de overlay preto sólido
    img = aplicar_mesh_gradient(img)
    
    if tipo == "carousel":
        return _gerar_carrossel(img, W, H, dados)
    elif tipo in ["reels", "reels_noite", "reels_conquistador"]:
        return _gerar_reels(img, W, H, dados)
    else:
        return _gerar_estatico(img, W, H, tipo, dados, tema_escolhido, TEMAS_MAPEADOS)

def _gerar_carrossel(img, W_full, H, dados):
    caminhos_arquivos = []
    slides_conteudo = [dados["titulo"]] + dados["slides"] + ["CTA"]
    
    # Tamanho de cada slide
    slide_W, slide_H = 1080, 1080
    num_slides = len(slides_conteudo)
    
    # Calcula o deslocamento do fundo (panning) para criar o efeito panorâmico contínuo
    step = (W_full - slide_W) / (num_slides - 1) if num_slides > 1 else 0
    
    # Usa a fonte do dia da semana (sistema de identidade visual diária)
    estilo_sorteado = obter_fonte_do_dia()
    print(f"🎨 Usando fonte do dia no Carrossel: {estilo_sorteado}")
    
    # Fontes maiores para garantir legibilidade no carrossel 1080x1080
    font_capa, font_slides, font_marca = carregar_fontes(tamanho_display=86, tamanho_body=72, tamanho_detalhe=26, estilo=estilo_sorteado)
    font_sub = carregar_fontes(tamanho_display=30, tamanho_body=30, tamanho_detalhe=30, estilo=estilo_sorteado)[0]
    
    for idx, texto in enumerate(slides_conteudo):
        x_offset = int(idx * step)
        
        # Recorta a porção do fundo exata para este slide (Rampa de Deslizamento)
        slide_bg = img.crop((x_offset, 0, x_offset + slide_W, slide_H))
        
        slide_img = slide_bg.convert("RGB")
        draw = ImageDraw.Draw(slide_img)
        
def desenhar_marca_dagua_ouro(draw, posicao, texto, fonte):
    """Desenha a assinatura da marca com efeito glow dourado imitando o logo original."""
    x, y = posicao
    # Efeito de brilho dourado translúcido por trás (glow)
    cor_brilho = (235, 160, 40, 50)
    for ox in [-2, -1, 0, 1, 2]:
        for oy in [-2, -1, 0, 1, 2]:
            if ox != 0 or oy != 0:
                draw.text((x + ox, y + oy), texto, font=fonte, fill=cor_brilho, anchor="ms")
                
    # Sombra preta para dar leitura e contraste
    draw.text((x + 2, y + 2), texto, font=fonte, fill=(0, 0, 0, 220), anchor="ms")
    
    # Texto principal em Dourado Ouro Metálico
    cor_ouro = (250, 185, 55)
    draw.text((x, y), texto, font=fonte, fill=cor_ouro, anchor="ms")

def _gerar_carrossel(img, W_full, H, dados):
    caminhos_arquivos = []
    slides_conteudo = [dados["titulo"]] + dados["slides"] + ["CTA"]
    
    # Tamanho de cada slide
    slide_W, slide_H = 1080, 1080
    num_slides = len(slides_conteudo)
    
    # Calcula o deslocamento do fundo (panning) para criar o efeito panorâmico contínuo
    step = (W_full - slide_W) / (num_slides - 1) if num_slides > 1 else 0
    
    # Usa a fonte do dia da semana (sistema de identidade visual diária)
    estilo_sorteado = obter_fonte_do_dia()
    print(f"🎨 Usando fonte do dia no Carrossel: {estilo_sorteado}")
    
    # Fontes maiores para garantir legibilidade no carrossel 1080x1080
    font_capa, font_slides, font_marca = carregar_fontes(tamanho_display=86, tamanho_body=72, tamanho_detalhe=26, estilo=estilo_sorteado)
    font_sub = carregar_fontes(tamanho_display=30, tamanho_body=30, tamanho_detalhe=30, estilo=estilo_sorteado)[0]
    
    for idx, texto in enumerate(slides_conteudo):
        x_offset = int(idx * step)
        
        # Recorta a porção do fundo exata para este slide (Rampa de Deslizamento)
        slide_bg = img.crop((x_offset, 0, x_offset + slide_W, slide_H))
        
        slide_img = slide_bg.convert("RGB")
        draw = ImageDraw.Draw(slide_img)
        
        # Elementos de Agência Premium
        desenhar_elementos_premium(draw, slide_W, slide_H)
        
        # Marca d'água com a fonte do logo em Dourado Ouro e Caixa Alta (tamanho reduzido em 40%)
        font_marca_serif, _, _ = carregar_fontes(50, 72, 26, estilo="Playfair")
        desenhar_marca_dagua_ouro(draw, (slide_W/2, slide_H - 80), "GUSTAVO_8K_", font_marca_serif)
        
        if idx == 0:  # Capa (Playfair Display)
            # FIX: width menor = menos chars por linha = texto maior e mais legível
            linhas = textwrap.wrap(texto, width=15)
            y_inicial = (slide_H - (len(linhas) * 105)) / 2 - 40
            for i, linha in enumerate(linhas):
                draw_text_with_shadow(draw, (slide_W/2, y_inicial + i * 105), linha, font_capa, fill=CORES["texto_principal"], anchor="ms")
            draw_text_with_shadow(draw, (slide_W/2, slide_H - 175), "Arrasta para o lado  ▶", font_sub, fill=CORES["destaque"], anchor="ms")
            
        elif texto == "CTA":  # Slide Final
            draw.line([(slide_W*0.15, slide_H*0.35), (slide_W*0.85, slide_H*0.35)], fill=CORES["destaque"], width=2)
            linhas_cta = ["Gostou deste conteúdo?", "", "Salva para não perder", "e segue a página para mais!"]
            y_inicial = slide_H * 0.38
            for i, linha in enumerate(linhas_cta):
                draw_text_with_shadow(draw, (slide_W/2, y_inicial + i * 78), linha, font_slides, fill=CORES["texto_principal"], anchor="ms")
                
        else:  # Slides internos (Inter/Montserrat)
            linhas = textwrap.wrap(texto, width=20)
            y_inicial = (slide_H - (len(linhas) * 90)) / 2
            for i, linha in enumerate(linhas):
                draw_text_with_shadow(draw, (slide_W/2, y_inicial + i * 90), linha, font_slides, fill=CORES["texto_principal"], anchor="ms")
            
        caminho = f"carousel_{uuid.uuid4().hex}_{idx}.jpg"
        slide_img.save(caminho, "JPEG", quality=95)
        caminhos_arquivos.append(caminho)
        
    return caminhos_arquivos

def _gerar_reels(img, W, H, dados):
    caminhos = []
    frases = dados.get("slides", [dados.get("frase", "...")])
    
    estilo_sorteado = obter_fonte_do_dia()
    print(f"🎨 Usando fonte do dia no Reels: {estilo_sorteado}")
    font_display, font_body, font_marca = carregar_fontes(86, 22, 24, estilo=estilo_sorteado)
    
    for idx, frase in enumerate(frases):
        slide = img.copy().convert("RGB")
        draw = ImageDraw.Draw(slide)
        
        # Elementos de Agência Premium
        desenhar_elementos_premium(draw, W, H)
        
        # Assinatura com a fonte do logo em Dourado Ouro e Caixa Alta
        font_marca_serif, _, _ = carregar_fontes(86, 22, 24, estilo="Playfair")
        desenhar_marca_dagua_ouro(draw, (W/2, H - 150), "GUSTAVO_8K_", font_marca_serif)
        draw_text_with_shadow(draw, (W/2, H - 220), f"{idx+1} / {len(frases)}", font_body, fill=CORES["texto_secundario"], anchor="ms")
        
        linhas = textwrap.wrap(frase, width=22)
        y_inicial = (H - (len(linhas) * 70)) / 2
        for i, linha in enumerate(linhas):
            draw_text_with_shadow(draw, (W/2, y_inicial + i * 70), linha, font_display, fill=CORES["texto_principal"], anchor="ms")
            
        caminho = f"reels_slide_{uuid.uuid4().hex}_{idx}.jpg"
        slide.save(caminho, "JPEG", quality=95)
        caminhos.append(caminho)
    return caminhos

def _gerar_estatico(img, W, H, tipo, dados, tema_escolhido=None, TEMAS_MAPEADOS=None):
    layout_style = random.choice(["classic", "bottom", "quote"])
    print(f"🎨 Usando estilo de layout: {layout_style.upper()}")
    
    # Usa a fonte do dia independente do layout
    estilo_fonte = obter_fonte_do_dia()
        
    font_display, _, font_marca = carregar_fontes(48, 24, 24, estilo=estilo_fonte)
    
    frases = dados.get("frase", dados.get("slides", [""]))
    if isinstance(frases, str):
        frases = [frases]
        
    caminhos = []
    
    for idx, frase in enumerate(frases):
        # FIX: Para Stories com múltiplos slides, busca imagem diferente por slide
        tipo_story = tipo in ["story_manha", "story_tarde"]
        if tipo_story and idx > 0 and tema_escolhido and TEMAS_MAPEADOS:
            prompt_secundario = dados.get("prompt_imagem")
            nova_img, _, _ = buscar_imagem_fundo(tipo, tema_escolhido, TEMAS_MAPEADOS, prompt_imagem=prompt_secundario)
            nova_img = aplicar_mesh_gradient(nova_img)
            slide = nova_img.convert("RGB")
        else:
            slide = img.copy().convert("RGB")
        draw = ImageDraw.Draw(slide)
        
        # Elementos de Agência Premium
        desenhar_elementos_premium(draw, W, H)
        
        # Assinatura com a fonte serifada do logo em Dourado Ouro e Caixa Alta
        font_marca_serif, _, _ = carregar_fontes(48, 24, 24, estilo="Playfair")
        y_watermark = H - 150 if tipo in ["story", "story_manha", "story_tarde", "test"] else H - 80
        desenhar_marca_dagua_ouro(draw, (W/2, y_watermark), "GUSTAVO_8K_", font_marca_serif)
        
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
            
        _uid = uuid.uuid4().hex
        caminho_imagem = f"story_pronto_{_uid}_{idx}.jpg" if tipo in ["story", "story_manha", "story_tarde", "test"] else f"post_pronto_{_uid}_{idx}.jpg"
        slide.save(caminho_imagem, "JPEG", quality=95)
        caminhos.append(caminho_imagem)
        
    if len(caminhos) == 1:
        return caminhos[0]
    return caminhos
