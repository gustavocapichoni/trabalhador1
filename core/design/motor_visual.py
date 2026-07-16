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

from core.config.settings import PEXELS_API_KEY, PIXABAY_API_KEY, UNSPLASH_ACCESS_KEY

def buscar_imagem_fundo(tipo, tema_escolhido, TEMAS_MAPEADOS, prompt_imagem=None):
    """
    Busca de imagem em Cascata (Fase 2):
    Nível 1: Unsplash API (Fotos Reais)
    Nível 2: Pexels API (Fotos Reais)
    Nível 3: Pixabay API (Fotos Reais)
    Nível 4: Pollinations AI (Geração por IA - Último caso online)
    Nível 5: Biblioteca Local (Modo Offline)
    Nível 6: Fundo Sólido Escuro (Emergência Catastrófica)
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


    # Palavras-chave simples e coloridas por tema — usadas EXCLUSIVAMENTE no Unsplash e Pexels
    UNSPLASH_FALLBACKS = {
        "espiritualidade": ["vast peaceful ocean sunrise", "mountains above clouds golden hour", "sun rays through forest trees", "peaceful golden nature light"],
        "filosofia":       ["ancient library warm light", "person reading sunlight", "sunset philosophy nature", "dramatic golden books"],
        "psicologia":      ["person thinking window sunlight", "colorful emotional portrait", "vibrant mind concept", "warm human connection"],
        "financas":        ["luxury city skyline sunset", "golden business executive", "vibrant wealth success", "colorful financial growth"],
        "liberdade":       ["colorful sunset open road", "person hiking mountain sunrise", "vibrant ocean freedom", "golden horizon adventure"],
        "conexoes":        ["couple sunset warm light", "friends laughing colorful", "warm hug golden hour", "vibrant family moment"],
        "superacao":       ["athlete sunrise training", "person climbing mountain golden", "colorful running determination", "vibrant victory winner"],
        "proposito":       ["colorful path forest sunlight", "inspiring sunrise horizon vibrant", "person journey golden light", "purpose light nature"],
    }
    QUERY_CORINGA = "vibrant colorful inspiring portrait golden light"
    
    tema_key = tema_escolhido if tema_escolhido else "superacao"
    queries_fallback = UNSPLASH_FALLBACKS.get(tema_key, [QUERY_CORINGA])
    
    # Para buscas em APIs de fotos reais: começa pelos fallbacks temáticos coloridos (NÃO usa o prompt cinematográfico da IA)
    queries_a_tentar = queries_fallback + [QUERY_CORINGA]

    # --- NÍVEL 1: UNSPLASH (Fotos Reais) ---
    if UNSPLASH_ACCESS_KEY:
        print(f"📸 [NÍVEL 1] Buscando foto real no Unsplash (tema: {tema_key})...")
        img_valida_url = None
        img_id_valido = None
        
        for query_atual in queries_a_tentar:
            url_unsplash = f"https://api.unsplash.com/photos/random?query={query_atual}&orientation={orientation}&client_id={UNSPLASH_ACCESS_KEY}"
            try:
                response = requests.get(url_unsplash, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    img_url = data['urls']['regular']
                    img_id = f"unsplash_{data.get('id', img_url)}"
                    
                    if verificar_midia_recente(img_id):
                        print(f"🔄 Imagem Unsplash {img_id} já usada recentemente. Tentando próxima query...")
                        continue
                        
                    img_valida_url = img_url
                    img_id_valido = img_id
                    break
                elif response.status_code == 401:
                    print("⚠️ Unsplash: Chave de API inválida (401). Pulando Unsplash...")
                    break
                elif response.status_code == 403:
                    print("⚠️ Unsplash: Limite de requisições excedido (403). Pulando Unsplash...")
                    break
            except Exception as e:
                print(f"⚠️ Erro ao acessar Unsplash para '{query_atual}': {e}")
                
        if img_valida_url:
            try:
                img_response = requests.get(img_valida_url, timeout=15)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content)).convert("RGBA")
                    registrar_midia_usada(img_id_valido)
                    print(f"✅ Foto do Unsplash carregada com sucesso e é inédita! ID: {img_id_valido}")
                    return img.resize((W, H), Image.Resampling.LANCZOS), W, H
            except Exception as e:
                print(f"⚠️ Erro ao baixar imagem do Unsplash: {e}")
    else:
        print("⚠️ UNSPLASH_ACCESS_KEY ausente. Pulando Nível 1...")

    # --- NÍVEL 2: PEXELS (Fotos Reais) ---
    if PEXELS_API_KEY:
        print(f"📸 [NÍVEL 2] Buscando foto real no Pexels (tema: {tema_key})...")
        pex_orientation = "square" if orientation == "squarish" else orientation
        headers = {"Authorization": PEXELS_API_KEY}
        img_valida_url = None
        img_id_valido = None
        
        for query_atual in queries_a_tentar:
            import urllib.parse
            query_encoded = urllib.parse.quote(query_atual)
            url_pexels = f"https://api.pexels.com/v1/search?query={query_encoded}&orientation={pex_orientation}&per_page=15"
            try:
                response = requests.get(url_pexels, headers=headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    photos = data.get("photos", [])
                    if photos:
                        random.shuffle(photos)
                        for photo in photos:
                            img_id = f"pexels_{photo['id']}"
                            if verificar_midia_recente(img_id):
                                print(f"🔄 Imagem Pexels {img_id} já usada recentemente. Tentando próxima...")
                                continue
                            
                            img_url = photo['src'].get('large2x') or photo['src'].get('large') or photo['src'].get('original')
                            if img_url:
                                img_valida_url = img_url
                                img_id_valido = img_id
                                break
                        if img_valida_url:
                            if query_atual != queries_a_tentar[0]:
                                print(f"✅ Pexels encontrou foto com query de fallback: '{query_atual}'")
                            break
                elif response.status_code == 401:
                    print("⚠️ Pexels: Chave de API inválida (401). Pulando Pexels...")
                    break
            except Exception as e:
                print(f"⚠️ Erro ao acessar Pexels para '{query_atual}': {e}")
                
        if img_valida_url:
            try:
                img_response = requests.get(img_valida_url, timeout=15)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content)).convert("RGBA")
                    registrar_midia_usada(img_id_valido)
                    print(f"✅ Foto do Pexels carregada com sucesso e é inédita! ID: {img_id_valido}")
                    return img.resize((W, H), Image.Resampling.LANCZOS), W, H
            except Exception as e:
                print(f"⚠️ Erro ao baixar imagem do Pexels: {e}")
    else:
        print("⚠️ PEXELS_API_KEY ausente. Pulando Nível 2...")

    # --- NÍVEL 3: PIXABAY (Fotos Reais) ---
    if PIXABAY_API_KEY:
        print(f"📸 [NÍVEL 3] Buscando foto real no Pixabay (tema: {tema_key})...")
        if orientation == "portrait":
            pixa_orientation = "vertical"
        elif orientation == "landscape":
            pixa_orientation = "horizontal"
        else:
            pixa_orientation = "all"
            
        img_valida_url = None
        img_id_valido = None
        
        for query_atual in queries_a_tentar:
            import urllib.parse
            query_encoded = urllib.parse.quote(query_atual)
            url_pixabay = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query_encoded}&image_type=photo&orientation={pixa_orientation}&per_page=15"
            try:
                response = requests.get(url_pixabay, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get("hits", [])
                    if hits:
                        random.shuffle(hits)
                        for hit in hits:
                            img_id = f"pixabay_{hit['id']}"
                            if verificar_midia_recente(img_id):
                                print(f"🔄 Imagem Pixabay {img_id} já usada recentemente. Tentando próxima...")
                                continue
                            
                            img_url = hit.get('largeImageURL') or hit.get('webformatURL')
                            if img_url:
                                img_valida_url = img_url
                                img_id_valido = img_id
                                break
                        if img_valida_url:
                            if query_atual != queries_a_tentar[0]:
                                print(f"✅ Pixabay encontrou foto com query de fallback: '{query_atual}'")
                            break
            except Exception as e:
                print(f"⚠️ Erro ao acessar Pixabay para '{query_atual}': {e}")
                
        if img_valida_url:
            try:
                img_response = requests.get(img_valida_url, timeout=15)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content)).convert("RGBA")
                    registrar_midia_usada(img_id_valido)
                    print(f"✅ Foto do Pixabay carregada com sucesso e é inédita! ID: {img_id_valido}")
                    return img.resize((W, H), Image.Resampling.LANCZOS), W, H
            except Exception as e:
                print(f"⚠️ Erro ao baixar imagem do Pixabay: {e}")
    else:
        print("⚠️ PIXABAY_API_KEY ausente. Pulando Nível 3...")

    # --- NÍVEL 4: INTELIGÊNCIA ARTIFICIAL (Pollinations - Último Caso Online) ---
    try:
        ai_prompt = prompt_imagem
        if not ai_prompt:
            from core.design.gerador_prompts import gerar_prompt_cinematografico
            ai_prompt = gerar_prompt_cinematografico(tema_key)

        print(f"🧠 [NÍVEL 4] Tentando gerar imagem exclusiva via IA (Pollinations) em último caso online: '{ai_prompt}'")
        seed_aleatorio = random.randint(1, 999999)
        import urllib.parse
        ai_prompt_encoded = urllib.parse.quote(ai_prompt)
        url_pollinations = f"https://image.pollinations.ai/prompt/{ai_prompt_encoded}?width={W}&height={H}&nologo=true&seed={seed_aleatorio}&model=flux-realism&enhance=false"
        
        response_ia = requests.get(url_pollinations, timeout=45)
        
        if response_ia.status_code == 200:
            print("✅ Imagem gerada por IA com sucesso!")
            img = Image.open(BytesIO(response_ia.content)).convert("RGBA")
            return img.resize((W, H), Image.Resampling.LANCZOS), W, H
        else:
            print(f"⚠️ IA (Pollinations) falhou com status {response_ia.status_code}. Tentando Nível 5...")
    except Exception as e:
        print(f"⚠️ Erro na geração de IA: {e}. Tentando Nível 5 (Local)...")

    # --- NÍVEL 5: Biblioteca Local de Emergência ---
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

    # --- NÍVEL 6: Fundo Escuro Sólido ---
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
    elif tipo in ["reels", "reels_noite", "reels_conquistador", "story_manha"]:
        return _gerar_reels(img, W, H, dados, tema_escolhido, TEMAS_MAPEADOS)
    else:
        return _gerar_estatico(img, W, H, tipo, dados, tema_escolhido, TEMAS_MAPEADOS)

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
    font_capa, font_slides, _ = carregar_fontes(tamanho_display=86, tamanho_body=72, tamanho_detalhe=26, estilo=estilo_sorteado)
    font_sub = carregar_fontes(tamanho_display=30, tamanho_body=30, tamanho_detalhe=30, estilo=estilo_sorteado)[0]
    
    for idx, texto in enumerate(slides_conteudo):
        x_offset = int(idx * step)
        
        # Recorta a porção do fundo exata para este slide (Rampa de Deslizamento)
        slide_bg = img.crop((x_offset, 0, x_offset + slide_W, slide_H))
        
        slide_img = slide_bg.convert("RGB")
        draw = ImageDraw.Draw(slide_img)
        
        # Elementos de Agência Premium
        desenhar_elementos_premium(draw, slide_W, slide_H)
        
        # Marca d'água / Logo no rodapé
        logo_aplicado = False
        logo_dir = os.path.join("biblioteca_local", "logo")
        path_logo = ""
        if os.path.exists(logo_dir):
            for f in os.listdir(logo_dir):
                if f.lower().endswith(".png"):
                    path_logo = os.path.join(logo_dir, f)
                    break
        if os.path.exists(path_logo):
            try:
                logo_img = Image.open(path_logo)
                largura_desejada = 250
                aspect_ratio = logo_img.height / logo_img.width
                altura_desejada = int(largura_desejada * aspect_ratio)
                logo_redimensionado = logo_img.resize((largura_desejada, altura_desejada), Image.Resampling.LANCZOS).convert("RGBA")

                x_pos = int((slide_W - largura_desejada) / 2)
                y_pos = int(slide_H - altura_desejada - 70)

                slide_rgba = slide_img.convert("RGBA")
                slide_rgba.paste(logo_redimensionado, (x_pos, y_pos), logo_redimensionado)
                slide_img = slide_rgba.convert("RGB")
                draw = ImageDraw.Draw(slide_img)
                logo_aplicado = True
            except Exception as e:
                print(f"⚠️ Erro ao aplicar logo no carrossel: {e}")

        if not logo_aplicado:
            font_marca_serif, _, _ = carregar_fontes(50, 72, 26, estilo="Playfair")
            desenhar_marca_dagua_ouro(draw, (slide_W/2, slide_H - 80), "GUSTAVO_8K_", font_marca_serif)
        
        if idx == 0:  # Capa (Playfair Display)
            # FIX: width menor = menos chars por linha = texto maior e mais legível
            linhas = textwrap.wrap(texto, width=18)
            y_inicial = (slide_H - (len(linhas) * 105)) / 2 - 40
            for i, linha in enumerate(linhas):
                draw_text_with_shadow(draw, (slide_W/2, y_inicial + i * 105), linha, font_capa, fill=CORES["texto_principal"], anchor="ms")
            draw_text_with_shadow(draw, (slide_W/2, slide_H - 55), "Arrasta para o lado ->", font_sub, fill=CORES["destaque"], anchor="ms")
            
        elif texto == "CTA":  # Slide Final
            ctas_disponiveis = [
                ["Gostou deste conteúdo?", "", "Salva para não perder", "e segue a página para mais!"],
                ["A mente precisa de", "constante evolução.", "", "Siga para não estagnar!"],
                ["O conhecimento inútil", "sem a prática.", "", "Salva esse post agora."],
                ["Se você leu até aqui,", "você já está na frente.", "", "Siga para continuar crescendo."],
                ["Não perca mais tempo", "com conteúdos vazios.", "", "Acompanhe nossa jornada!"]
            ]
            linhas_cta = random.choice(ctas_disponiveis)
            # Expande linhas longas para evitar corte nas bordas
            linhas_finais = []
            for linha in linhas_cta:
                if linha.strip():
                    partes = textwrap.wrap(linha, width=18)
                    linhas_finais.extend(partes if partes else [linha])
                else:
                    linhas_finais.append("")  # mantém linha vazia (espaçamento)
            y_inicial = slide_H * 0.25
            for i, linha in enumerate(linhas_finais):
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

def _gerar_reels(img, W, H, dados, tema_escolhido=None, TEMAS_MAPEADOS=None):
    """Gera os fundos dos slides do Reels (sem texto baked) e retorna as frases separadas para animação."""
    caminhos_fundos = []

    # Para story_manha: 'frase' é uma lista de strings (4-8 frases)
    # Para reels normais: 'slides' é uma lista de strings
    slides_raw = dados.get("slides")
    frase_raw  = dados.get("frase", "...")
    if slides_raw:
        frases = slides_raw if isinstance(slides_raw, list) else [slides_raw]
    elif isinstance(frase_raw, list):
        frases = frase_raw  # story_manha: já é uma lista de frases prontas
    else:
        frases = [frase_raw]  # story/post estático: string única

    estilo_sorteado = obter_fonte_do_dia()
    print(f"🎨 Usando fonte do dia no Reels: {estilo_sorteado}")

    # Determina o caminho e tamanho da fonte para passar ao motor de animação
    nome_fonte = estilo_sorteado if estilo_sorteado.endswith(".ttf") else estilo_sorteado + ".ttf"
    caminhos_fonte = [
        os.path.join("fontes", nome_fonte),
        os.path.join("fontes", "BebasNeue.ttf"),
        os.path.join("fontes", "MontserratBold.ttf"),
    ]
    caminho_fonte_valido = None
    for cf in caminhos_fonte:
        if os.path.exists(cf):
            caminho_fonte_valido = cf
            break

    font_display, font_body, _ = carregar_fontes(86, 22, 24, estilo=estilo_sorteado)

    for idx, frase in enumerate(frases):
        if idx > 0 and tema_escolhido and TEMAS_MAPEADOS:
            prompt_secundario = dados.get("prompt_imagem")
            nova_img, _, _ = buscar_imagem_fundo("reels", tema_escolhido, TEMAS_MAPEADOS, prompt_imagem=prompt_secundario)
            nova_img = aplicar_mesh_gradient(nova_img)
            slide = nova_img.convert("RGB")
        else:
            slide = img.copy().convert("RGB")
        draw = ImageDraw.Draw(slide)

        # Elementos de Agência Premium
        desenhar_elementos_premium(draw, W, H)

        # Logo da marca no rodapé (sem texto de conteúdo)
        logo_aplicado = False
        logo_dir = os.path.join("biblioteca_local", "logo")
        path_logo = ""
        if os.path.exists(logo_dir):
            for f in os.listdir(logo_dir):
                if f.lower().endswith(".png"):
                    path_logo = os.path.join(logo_dir, f)
                    break
        if os.path.exists(path_logo):
            try:
                logo_img = Image.open(path_logo)
                largura_desejada = 320
                aspect_ratio = logo_img.height / logo_img.width
                altura_desejada = int(largura_desejada * aspect_ratio)
                logo_redimensionado = logo_img.resize((largura_desejada, altura_desejada), Image.Resampling.LANCZOS).convert("RGBA")

                x_pos = int((W - largura_desejada) / 2)
                y_pos = H - altura_desejada - 240

                slide_rgba = slide.convert("RGBA")
                slide_rgba.paste(logo_redimensionado, (x_pos, y_pos), logo_redimensionado)
                slide = slide_rgba.convert("RGB")
                draw = ImageDraw.Draw(slide)

                # Número do slide abaixo do logo
                y_num_slide = y_pos + altura_desejada + 40
                draw_text_with_shadow(draw, (W/2, y_num_slide), f"{idx+1} / {len(frases)}", font_body, fill=CORES["texto_secundario"], anchor="ms")
                logo_aplicado = True
            except Exception as e:
                print(f"⚠️ Erro ao aplicar imagem de logo ({e}). Usando fallback de texto.")

        if not logo_aplicado:
            font_marca_serif, _, _ = carregar_fontes(86, 22, 24, estilo="Playfair")
            desenhar_marca_dagua_ouro(draw, (W/2, H - 200), "GUSTAVO_8K_", font_marca_serif)
            draw_text_with_shadow(draw, (W/2, H - 280), f"{idx+1} / {len(frases)}", font_body, fill=CORES["texto_secundario"], anchor="ms")

        # Salva o fundo SEM o texto de conteúdo (o texto será animado no reels.py)
        caminho = f"reels_slide_{uuid.uuid4().hex}_{idx}.jpg"
        slide.save(caminho, "JPEG", quality=95)
        caminhos_fundos.append(caminho)

    # Retorna tuple: (fundos sem texto, frases para animar, caminho fonte, tamanho fonte)
    return (caminhos_fundos, frases, caminho_fonte_valido, 86)

def _gerar_estatico(img, W, H, tipo, dados, tema_escolhido=None, TEMAS_MAPEADOS=None):
    layout_style = random.choice(["classic", "bottom", "quote"])
    print(f"🎨 Usando estilo de layout: {layout_style.upper()}")
    
    # Usa a fonte do dia independente do layout
    estilo_fonte = obter_fonte_do_dia()
        
    font_display, _, _ = carregar_fontes(48, 24, 24, estilo=estilo_fonte)
    
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
        
        # Assinatura / Logo no rodapé
        y_watermark = H - 150 if tipo in ["story", "story_manha", "story_tarde", "test"] else H - 80
        logo_aplicado = False
        logo_dir = os.path.join("biblioteca_local", "logo")
        path_logo = ""
        if os.path.exists(logo_dir):
            for f in os.listdir(logo_dir):
                if f.lower().endswith(".png"):
                    path_logo = os.path.join(logo_dir, f)
                    break
        if os.path.exists(path_logo):
            try:
                logo_img = Image.open(path_logo)
                largura_desejada = 400
                aspect_ratio = logo_img.height / logo_img.width
                altura_desejada = int(largura_desejada * aspect_ratio)
                logo_redimensionado = logo_img.resize((largura_desejada, altura_desejada), Image.Resampling.LANCZOS).convert("RGBA")

                x_pos = int((W - largura_desejada) / 2)
                y_pos = int(y_watermark - (altura_desejada / 2))

                slide_rgba = slide.convert("RGBA")
                slide_rgba.paste(logo_redimensionado, (x_pos, y_pos), logo_redimensionado)
                slide = slide_rgba.convert("RGB")
                draw = ImageDraw.Draw(slide)
                logo_aplicado = True
            except Exception as e:
                print(f"⚠️ Erro ao aplicar logo no post estático/story: {e}")

        if not logo_aplicado:
            font_marca_serif, _, _ = carregar_fontes(48, 24, 24, estilo="Playfair")
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
