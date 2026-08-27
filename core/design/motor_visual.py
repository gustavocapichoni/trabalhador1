import os
import requests
import textwrap
import random
import uuid
import urllib.parse
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from .efeitos import aplicar_mesh_gradient, draw_text_with_shadow, desenhar_elementos_premium
from .templates import carregar_fontes, obter_fonte_do_dia, CORES
from core.config.state import verificar_midia_recente, registrar_midia_usada

from core.config.settings import PEXELS_API_KEY, PIXABAY_API_KEY, UNSPLASH_ACCESS_KEY

def buscar_imagem_fundo(tipo, tema_escolhido, prompt_imagem=None):
    """
    Busca de imagem em Cascata:
    Nível 0: FLUX.1 via Hugging Face (IA Geradora - Prioridade Máxima)
    Nível 1: Unsplash API (Fotos Reais - Emergência)
    Nível 2: Pexels API (Fotos Reais - Emergência)
    Nível 3: Pixabay API (Fotos Reais - Emergência)
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

    query_termo = "cyberpunk,futuristic,city night,neon lights,dark gold"
    # ── Direção de Arte Fixa 'Ecos da Consciência' (80% Noturna, Luz Dourada/Âmbar, 35mm Film, Pessoas/Afetividade) ──
    UNSPLASH_FALLBACKS = {
        "espiritualidade": ["artistic portrait person thoughtful warm golden night light 35mm", "person looking night sky city lights warm amber glow cinematic bokeh", "contemplative person night ambient lighting 35mm film aesthetic"],
        "filosofia":       ["moody artistic portrait person looking rainy window night city 35mm", "thoughtful philosopher night city golden light deep shadows cinematic", "person meditating thoughts night cityscape warm neon glow 35mm"],
        "psicologia":      ["intimate artistic portrait couple talking night warm ambient shadows", "person deep thought night city lights moody portrait Kodak Portra", "artistic emotion human connection night warm golden lighting 35mm"],
        "financas":        ["modern artistic person walking night city golden neon reflections 35mm", "stylish couple night city lights warm amber glow cinematic portrait", "determined person night cityscape golden bokeh atmospheric 35mm"],
        "liberdade":       ["young artists celebrating freedom night city rooftop warm ambient glow", "person looking at night city skyline golden lights freedom mood 35mm", "free spirit person night city street lights cinematic atmospheric"],
        "conexoes":        ["warm genuine affectionate hug couple night intimate lighting 35mm", "friends laughing talking night city street warm golden light bokeh", "intimate human connection night moody artistic portrait Kodak Portra"],
        "superacao":       ["determined person walking night city lights rain intense cinematic 35mm", "strong resilient person night cityscape golden amber glow mood", "person overcoming adversity night city rain reflections 35mm film"],
        "proposito":       ["artistic portrait person contemplating under warm golden night lights", "thoughtful mentor night city lights deep shadows cinematic 35mm", "purposeful person looking horizon night city lights golden glow"],
    }
    QUERY_CORINGA = "artistic cinematic portrait night city lights warm golden lighting deep shadows 35mm Kodak Portra"
    
    tema_key = tema_escolhido if tema_escolhido else "superacao"
    queries_fallback = UNSPLASH_FALLBACKS.get(tema_key, [QUERY_CORINGA])
    
    # Injeta queries baseadas no sentimento do dia para posts padrão (não conquistador ou leads)
    from core.config.state import carregar_estado
    estado = carregar_estado()
    sentimento = estado.get("sentimento_do_dia")
    is_leads_ou_conquistador = (tipo in ["reels_conquistador", "reels_leads"])
    
    if sentimento and not is_leads_ou_conquistador:
        from core.ai.styles import SENTIMENTOS_CONFIG
        config_emocional = SENTIMENTOS_CONFIG.get(sentimento)
        if config_emocional and "busca_imagem" in config_emocional:
            queries_fallback = config_emocional["busca_imagem"]
            print(f"📸 [SINESTESIA] Usando queries de imagem do sentimento {sentimento.upper()}: {queries_fallback}")

    # Para buscas em APIs de fotos reais: começa pelos fallbacks temáticos coloridos (NÃO usa o prompt cinematográfico da IA)
    queries_a_tentar = queries_fallback + [QUERY_CORINGA]

    # --- NÍVEL -1: IMAGENS LOCAIS DA PASTA img_carrocel (Prioridade Máxima para Carrossel) ---
    if tipo == "carousel":
        pasta_carrocel = os.path.join("biblioteca_local", "img_carrocel")
        extensoes_validas = (".png", ".jpg", ".jpeg", ".webp")
        if os.path.isdir(pasta_carrocel):
            imagens_disponiveis = [
                f for f in os.listdir(pasta_carrocel)
                if os.path.splitext(f)[1].lower() in extensoes_validas
            ]
            if imagens_disponiveis:
                try:
                    from core.config.state import carregar_estado, salvar_estado
                    estado_local = carregar_estado()
                    ultima_usada = estado_local.get("ultima_img_carrocel", "")
                    opcoes = [f for f in imagens_disponiveis if f != ultima_usada]
                    if not opcoes:
                        opcoes = imagens_disponiveis  # Reinicia o rodízio se só tiver 1
                    img_escolhida = random.choice(opcoes)
                    estado_local["ultima_img_carrocel"] = img_escolhida
                    salvar_estado(estado_local)
                    caminho_local = os.path.join(pasta_carrocel, img_escolhida)
                    img = Image.open(caminho_local).convert("RGBA")
                    print(f"[NIVEL -1] Imagem local do carrossel carregada: {img_escolhida}")
                    return img.resize((W, H), Image.Resampling.LANCZOS), W, H
                except Exception as e_local:
                    print(f"[NIVEL -1] Erro ao carregar imagem local do carrossel: {e_local}. Continuando para FLUX...")

    # --- NÍVEL 0: FLUX.1 via Hugging Face (IA Geradora - Prioridade Máxima) ---
    # Apenas para os tipos de post que dependem de imagem como base do slideshow/arte
    _TIPOS_COM_FLUX = ["reels", "reels_noite", "story_manha", "carousel"]
    if tipo in _TIPOS_COM_FLUX:
        try:
            from core.media.flux_gerador import gerar_imagem_flux
            print(f"[NIVEL 0] Gerando imagem via FLUX.1 (IA) para o tipo '{tipo}'...")
            caminho_flux = gerar_imagem_flux(tipo=tipo, tema_escolhido=tema_escolhido)
            if caminho_flux and os.path.exists(caminho_flux):
                img = Image.open(caminho_flux).convert("RGBA")
                print(f"[NIVEL 0] Imagem FLUX carregada com sucesso: {caminho_flux}")
                return img.resize((W, H), Image.Resampling.LANCZOS), W, H
            else:
                print("[NIVEL 0] FLUX falhou em todos os tokens. Usando banco de imagens como emergencia...")
        except Exception as _e_flux:
            print(f"[NIVEL 0] Erro inesperado no FLUX: {_e_flux}. Continuando para Unsplash...")

    # --- NÍVEL 1: UNSPLASH (Fotos Reais) ---
    if UNSPLASH_ACCESS_KEY:
        print(f"📸 [NÍVEL 1] Buscando foto real no Unsplash (tema: {tema_key})...")
        img_valida_url = None
        img_id_valido = None
        
        TERMOS_PROIBIDOS_BUSCA = [
            "candle", "velas", "cross", "cruzes", "church", "religion", "skull", "occult",
            "meadow", "field", "grass", "green grass", "farm", "hay", "beach", "ocean daylight",
            "flower", "flowers", "garden", "nature daylight", "sunny", "sunlight", "daylight",
            "bright office", "white room", "landscape green", "trees daylight", "sun"
        ]
        for query_atual in queries_a_tentar:
            # Garante que nenhum termo indesejado entre na busca
            for t_proibido in TERMOS_PROIBIDOS_BUSCA:
                if t_proibido in query_atual.lower():
                    query_atual = query_atual.lower().replace(t_proibido, "").strip()

            url_unsplash = f"https://api.unsplash.com/photos/random?query={urllib.parse.quote(query_atual)}&orientation={orientation}&client_id={UNSPLASH_ACCESS_KEY}"
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
            page = random.randint(1, 10)
            query_encoded = urllib.parse.quote(query_atual)
            url_pexels = f"https://api.pexels.com/v1/search?query={query_encoded}&orientation={pex_orientation}&per_page=30&page={page}"
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

def criar_arte(tipo, dados, tema_escolhido):
    print(f"🎨 Desenhando arte ({tipo.upper()}) com Design Premium...")
    
    prompt_imagem = dados.get("prompt_imagem")
    img, W, H = buscar_imagem_fundo(tipo, tema_escolhido, prompt_imagem=prompt_imagem)
    
    # Aplica Gradient Inteligente em vez de overlay preto sólido
    img = aplicar_mesh_gradient(img)
    
    if tipo == "carousel":
        return _gerar_carrossel(img, W, H, dados)
    elif tipo in ["reels", "reels_noite", "reels_conquistador", "story_manha"]:
        return _gerar_reels(img, W, H, dados, tema_escolhido, tipo=tipo)
    else:
        return _gerar_estatico(img, W, H, tipo, dados, tema_escolhido)

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

def _gerar_slide_cta_carrossel(slide_img, texto_cta, estilo_sorteado):
    """Renderiza o slide final de CTA exclusivo do Carrossel (1080x1080)
    sem sobreposições entre eBook, texto e logo."""
    import re as _re
    import numpy as _np
    from core.media.pexels_story import _quebrar_texto_por_pixels, _desenhar_linha_sem_keyword, PALETA_PADRAO_MARCA, _sanitizar_texto_slide

    texto_cta = _sanitizar_texto_slide(texto_cta)
    slide_W, slide_H = 1080, 1080
    draw = ImageDraw.Draw(slide_img)

    # 1. Elementos de Agência Premium
    desenhar_elementos_premium(draw, slide_W, slide_H)

    # 2. Mockup 3D do Ebook no Topo
    ebook_path = os.path.join("biblioteca_local", "logo", "ebook.png")
    y_limite_topo = 60
    if os.path.exists(ebook_path):
        try:
            ebook_img = Image.open(ebook_path).convert("RGBA")
            target_w = 260
            aspect_ratio = ebook_img.height / ebook_img.width
            target_h = int(target_w * aspect_ratio)
            ebook_img = ebook_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            x_ebook = (slide_W - target_w) // 2
            y_ebook = 40
            slide_rgba = slide_img.convert("RGBA")
            slide_rgba.paste(ebook_img, (x_ebook, y_ebook), ebook_img)
            slide_img = slide_rgba.convert("RGB")
            draw = ImageDraw.Draw(slide_img)
            y_limite_topo = y_ebook + target_h + 20
        except Exception as e:
            print(f"⚠️ Erro ao inserir mockup do ebook no carrossel: {e}")

    # 3. Logo da marca no Rodapé
    logo_dir = os.path.join("biblioteca_local", "logo")
    path_logo = os.path.join(logo_dir, "foto_perfil.png")
    y_limite_base = slide_H - 80
    logo_aplicado = False
    if os.path.exists(path_logo):
        try:
            logo_img = Image.open(path_logo)
            largura_logo = 180
            aspect_ratio = logo_img.height / logo_img.width
            altura_logo = int(largura_logo * aspect_ratio)
            logo_redimensionado = logo_img.resize((largura_logo, altura_logo), Image.Resampling.LANCZOS).convert("RGBA")
            x_logo = (slide_W - largura_logo) // 2
            y_logo = slide_H - altura_logo - 35
            slide_rgba = slide_img.convert("RGBA")
            slide_rgba.paste(logo_redimensionado, (x_logo, y_logo), logo_redimensionado)
            slide_img = slide_rgba.convert("RGB")
            draw = ImageDraw.Draw(slide_img)
            y_limite_base = y_logo - 20
            logo_aplicado = True
        except Exception as e:
            print(f"⚠️ Erro ao aplicar logo no slide CTA do carrossel: {e}")

    if not logo_aplicado:
        font_marca_serif, _, _ = carregar_fontes(45, 72, 26, estilo="BebasNeue")
        desenhar_marca_dagua_ouro(draw, (slide_W/2, slide_H - 70), "GUSTAVO_8K_", font_marca_serif)
        y_limite_base = slide_H - 120

    # 4. Texto de CTA no espaço central livre entre eBook e Logo
    font_cta = carregar_fontes(tamanho_display=48, tamanho_body=48, tamanho_detalhe=24, estilo=estilo_sorteado)[0]
    
    # Detecta keyword de destaque (SABEDORIA prioritária)
    if "SABEDORIA" in texto_cta.upper():
        keyword_destaque = "SABEDORIA"
    else:
        match_keyword = _re.search(r"['\u2018\u2019\"]([^'\u2018\u2019\"]+)['\u2018\u2019\"]", texto_cta)
        keyword_destaque = match_keyword.group(1).upper().strip() if match_keyword else None
    
    tamanho_base = getattr(font_cta, 'size', 48)
    tamanho_kw = int(tamanho_base * 1.15)
    caminho_f = getattr(font_cta, 'path', None)
    try:
        font_kw = ImageFont.truetype(caminho_f, tamanho_kw) if caminho_f and os.path.exists(caminho_f) else font_cta
    except Exception:
        font_kw = font_cta

    margem_px = int(slide_W * 0.08)
    largura_max = slide_W - (margem_px * 2)
    linhas = _quebrar_texto_por_pixels(draw, texto_cta, font_cta, largura_max)

    alturas = []
    larguras = []
    for l in linhas:
        bb = draw.textbbox((0, 0), l, font=font_cta)
        alturas.append(bb[3] - bb[1])
        larguras.append(bb[2] - bb[0])

    espaco_entre = 12
    total_h = sum(alturas) + espaco_entre * (len(linhas) - 1) if linhas else 0

    # Ajuste dinâmico se ultrapassar o espaço disponível
    espaco_disponivel = y_limite_base - y_limite_topo
    if total_h > espaco_disponivel and len(linhas) > 0:
        font_cta = carregar_fontes(tamanho_display=40, tamanho_body=40, tamanho_detalhe=22, estilo=estilo_sorteado)[0]
        linhas = _quebrar_texto_por_pixels(draw, texto_cta, font_cta, largura_max)
        alturas = [draw.textbbox((0, 0), l, font=font_cta)[3] - draw.textbbox((0, 0), l, font=font_cta)[1] for l in linhas]
        larguras = [draw.textbbox((0, 0), l, font=font_cta)[2] - draw.textbbox((0, 0), l, font=font_cta)[0] for l in linhas]
        total_h = sum(alturas) + espaco_entre * (len(linhas) - 1)

    y_inicial = y_limite_topo + max(0, (espaco_disponivel - total_h) // 2)

    # Renderiza o texto com degradê da marca e keyword dourada
    shadow_layer = Image.new("RGBA", (slide_W, slide_H), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    txt_mask_layer = Image.new("RGBA", (slide_W, slide_H), (0, 0, 0, 0))
    mask_draw = ImageDraw.Draw(txt_mask_layer)

    y = y_inicial
    posicoes_linhas = []
    for linha, alt, lw in zip(linhas, alturas, larguras):
        x = (slide_W - lw) // 2
        _desenhar_linha_sem_keyword(shadow_draw, linha, x + 3, y + 3, font_cta, font_kw,
                                    keyword_destaque, 1.0, slide_W, cor_preenchimento=(0, 0, 0, 180))
        _desenhar_linha_sem_keyword(shadow_draw, linha, x, y, font_cta, font_kw,
                                    keyword_destaque, 1.0, slide_W, cor_preenchimento=(0, 0, 0, 0),
                                    stroke_w=2, stroke_c=(0, 0, 0, 255))
        _desenhar_linha_sem_keyword(mask_draw, linha, x, y, font_cta, font_kw,
                                    keyword_destaque, 1.0, slide_W)
        posicoes_linhas.append((linha, x, y, alt, lw))
        y += alt + espaco_entre

    # Gradiente metálico para o texto base
    color_top = _np.array(PALETA_PADRAO_MARCA[0])
    color_mid = _np.array(PALETA_PADRAO_MARCA[1])
    color_bot = _np.array(PALETA_PADRAO_MARCA[2])
    grad_arr = _np.zeros((slide_H, slide_W, 3), dtype=_np.uint8)
    for row in range(slide_H):
        if row < y_inicial:
            c = color_top
        elif row > y_inicial + max(1, total_h):
            c = color_bot
        else:
            ratio = (row - y_inicial) / max(1, float(total_h))
            c = color_top * (1 - ratio) + color_bot * ratio
        grad_arr[row, :, :] = c.astype(_np.uint8)
    grad_img = Image.fromarray(grad_arr, 'RGB')

    mask = txt_mask_layer.split()[3]
    final_txt_layer = Image.new("RGBA", (slide_W, slide_H), (0, 0, 0, 0))
    final_txt_layer.paste(grad_img, (0, 0), mask=mask)

    slide_img = Image.alpha_composite(slide_img.convert("RGBA"), shadow_layer)
    slide_img = Image.alpha_composite(slide_img, final_txt_layer).convert("RGB")

    # Renderiza a keyword destacada em Dourado
    if keyword_destaque:
        sabedoria_layer = Image.new("RGBA", (slide_W, slide_H), (0, 0, 0, 0))
        sabedoria_draw = ImageDraw.Draw(sabedoria_layer)
        espaco_w = sabedoria_draw.textbbox((0, 0), " ", font=font_cta)[2] - sabedoria_draw.textbbox((0, 0), " ", font=font_cta)[0]

        for (linha, x_linha, y_linha, alt_linha, lw_linha) in posicoes_linhas:
            linha_upper = linha.upper()
            if keyword_destaque not in linha_upper:
                continue
            palavras = linha.split(" ")
            larguras_palavras = []
            for p in palavras:
                p_clean = p.upper().replace("'", "").replace("\u2018", "").replace("\u2019", "").replace('"', '').replace(',', '').replace('.', '').replace('!', '').strip()
                f_usar = font_kw if p_clean == keyword_destaque else font_cta
                pw = sabedoria_draw.textbbox((0, 0), p, font=f_usar)[2] - sabedoria_draw.textbbox((0, 0), p, font=f_usar)[0]
                larguras_palavras.append((pw, f_usar, p_clean))

            largura_total_linha = sum(pw for pw, _, _ in larguras_palavras) + espaco_w * (len(palavras) - 1)
            cur_x = (slide_W - largura_total_linha) // 2

            for p, (pw, f_usar, p_clean) in zip(palavras, larguras_palavras):
                if p_clean == keyword_destaque:
                    cor_destaque_rgba = (250, 185, 55, 255)
                    bb_k = sabedoria_draw.textbbox((0, 0), p, font=f_usar)
                    alt_k = bb_k[3] - bb_k[1]
                    y_offset = (alt_linha - alt_k) // 2
                    sabedoria_draw.text((cur_x + 3, y_linha + y_offset + 3), p, font=f_usar, fill=(0, 0, 0, 180))
                    sabedoria_draw.text((cur_x, y_linha + y_offset), p, font=f_usar, fill=cor_destaque_rgba,
                                        stroke_width=3, stroke_fill=(0, 0, 0, 255))
                cur_x += pw + espaco_w

        slide_img = Image.alpha_composite(slide_img.convert("RGBA"), sabedoria_layer).convert("RGB")

    return slide_img

def _gerar_carrossel(img, W_full, H, dados):
    caminhos_arquivos = []
    slides_conteudo = [dados["titulo"]] + dados["slides"] + ["CTA"]
    
    # Tamanho de cada slide
    slide_W, slide_H = 1080, 1080
    num_slides = len(slides_conteudo)
    
    # Calcula o deslocamento do fundo (panning) para criar o efeito panorâmico contínuo
    step = (W_full - slide_W) / (num_slides - 1) if num_slides > 1 else 0
    
    # Usa a fonte oficial definida para o tipo de post
    estilo_sorteado = obter_fonte_do_dia(tipo="carousel")
    print(f"🎨 Usando fonte oficial no Carrossel: {estilo_sorteado}")
    

    # Fontes maiores para garantir legibilidade no carrossel 1080x1080
    font_capa, font_slides, _ = carregar_fontes(tamanho_display=86, tamanho_body=72, tamanho_detalhe=26, estilo=estilo_sorteado)
    font_sub = carregar_fontes(tamanho_display=30, tamanho_body=30, tamanho_detalhe=30, estilo=estilo_sorteado)[0]
    
    for idx, texto in enumerate(slides_conteudo):
        x_offset = int(idx * step)
        
        # Recorta a porção do fundo exata para este slide (Rampa de Deslizamento)
        slide_bg = img.crop((x_offset, 0, x_offset + slide_W, slide_H))
        
        if texto == "CTA":
            titulo_pdf_cta = "Material da Semana"
            try:
                caminho_pdf_cta = os.path.join("gerador_pdf", "output", "ultimo_conteudo.json")
                if os.path.exists(caminho_pdf_cta):
                    import json as _json_cta
                    with open(caminho_pdf_cta, "r", encoding="utf-8") as _f_cta:
                        _dados_cta = _json_cta.load(_f_cta)
                    titulo_pdf_cta = _dados_cta.get("titulo_pdf", "Material da Semana")
            except Exception:
                pass
            ctas_disponiveis = [
                f"Quer o guia completo sobre isso? Comenta SABEDORIA abaixo que te envio no Direct",
                f"Esse conteúdo tem um material completo. Comenta SABEDORIA e recebe o ebook '{titulo_pdf_cta}' no Direct.",
                f"Aprofunde esse conhecimento. Comenta SABEDORIA abaixo e receba o material da semana no Direct.",
                f"Quer aplicar isso na prática? Comenta SABEDORIA que te envio o guia completo agora",
                f"O ebook '{titulo_pdf_cta}' está gratuito. Comenta SABEDORIA e receba no Direct."
            ]
            linhas_cta = random.choice(ctas_disponiveis)
            slide_img = _gerar_slide_cta_carrossel(slide_bg.convert("RGB"), linhas_cta, estilo_sorteado)
        else:
            slide_img = slide_bg.convert("RGB")
            draw = ImageDraw.Draw(slide_img)
            
            # Elementos de Agência Premium
            desenhar_elementos_premium(draw, slide_W, slide_H)
            
            # Marca d'água / Logo no rodapé
            logo_aplicado = False
            logo_dir = os.path.join("biblioteca_local", "logo")
            path_logo = os.path.join(logo_dir, "foto_perfil.png")
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
                font_marca_serif, _, _ = carregar_fontes(50, 72, 26, estilo="BebasNeue")
                desenhar_marca_dagua_ouro(draw, (slide_W/2, slide_H - 80), "GUSTAVO_8K_", font_marca_serif)

            # Texto com degradê completo da marca via _adicionar_texto_degrade
            from core.media.pexels_story import PALETA_PADRAO_MARCA, _adicionar_texto_degrade
            import numpy as _np

            if idx == 0:  # Capa
                linhas = textwrap.wrap(texto, width=18)
                texto_unificado = "\n".join(linhas)
            else:  # Slides internos
                texto_unificado = texto

            if texto_unificado.strip():
                fonte_slide = font_capa if idx == 0 else font_slides
                frame_np = _np.array(slide_img)
                frame_np = _adicionar_texto_degrade(
                    frame_np, texto_unificado, fonte_slide, paleta=PALETA_PADRAO_MARCA
                )
                slide_img = Image.fromarray(frame_np)
                draw = ImageDraw.Draw(slide_img)
            
            if idx == 0:
                draw_text_with_shadow(draw, (slide_W/2, slide_H - 55), "Arrasta para o lado ->", font_sub, fill=CORES["destaque"], anchor="ms")
            
        caminho = f"carousel_{uuid.uuid4().hex}_{idx}.jpg"
        slide_img.save(caminho, "JPEG", quality=95)
        caminhos_arquivos.append(caminho)
        
    return caminhos_arquivos

def _gerar_reels(img, W, H, dados, tema_escolhido=None, tipo="reels"):
    """Gera os fundos dos slides do Reels (sem texto baked) e retorna as frases separadas para animação."""
    import random as _random
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

    # Injeta CTA apenas para reels_conquistador (reels manha/tarde/noite e story_manha sao sem CTAs)
    if tipo in ["reels_conquistador"]:
        ctas_seguir = [
            "Se você busca respostas que a maioria ignora, acompanhe o perfil.",
            "Quem chegou até aqui já está à frente. Siga para continuar crescendo.",
            "O conteúdo não para por aqui. Acompanhe para a próxima reflexão.",
            "Se esse assunto te move, este perfil foi feito para você. Siga.",
            "Cada dia uma verdade diferente. Siga para não perder nenhuma.",
        ]
        frases = list(frases) + [_random.choice(ctas_seguir)]
        print(f"📣 [CTA Visual] Slide de CTA injetado no final do {tipo.upper()}.")

    estilo_sorteado = obter_fonte_do_dia(tipo=tipo)
    print(f"🎨 Usando fonte oficial no Reels: {estilo_sorteado}")

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
        # story_manha, reels e reels_noite usam a MESMA imagem base para todos os slides (1 unica imagem por post)
        if idx > 0 and tema_escolhido and tipo not in ["story_manha", "reels", "reels_noite"]:
            # Busca uma nova imagem para o próximo slide (ex: carrossel)
            prompt_secundario = dados.get("prompt_imagem")
            nova_img, _, _ = buscar_imagem_fundo("reels", tema_escolhido, prompt_imagem=prompt_secundario)
            nova_img = aplicar_mesh_gradient(nova_img)
            slide = nova_img.convert("RGB")
        else:
            slide = img.copy().convert("RGB")
        draw = ImageDraw.Draw(slide)

        # Elementos de Agência Premium
        desenhar_elementos_premium(draw, W, H)

        # ── 1. [EMBLEMA REMOVIDO] Apenas marca d'água no rodapé é exibida ──
        logo_dir = os.path.join("biblioteca_local", "logo")

        # ── 2. MARCA D'ÁGUA NO RODAPÉ (ignora foto_perfil.png) ──
        logo_aplicado = False
        path_logo = os.path.join(logo_dir, "foto_perfil.png")
        if os.path.exists(path_logo):
            try:
                logo_img = Image.open(path_logo)
                largura_desejada = 200
                aspect_ratio = logo_img.height / logo_img.width
                altura_desejada = int(largura_desejada * aspect_ratio)
                logo_redimensionado = logo_img.resize((largura_desejada, altura_desejada), Image.Resampling.LANCZOS).convert("RGBA")

                x_pos = int((W - largura_desejada) / 2)
                y_pos = H - altura_desejada - 240

                slide_rgba = slide.convert("RGBA")
                slide_rgba.paste(logo_redimensionado, (x_pos, y_pos), logo_redimensionado)
                slide = slide_rgba.convert("RGB")
                draw = ImageDraw.Draw(slide)
                logo_aplicado = True  # Definido True logo após colar o logo para evitar duplicidade caso a escrita do número do slide falhe

                # Número do slide abaixo do logo
                try:
                    y_num_slide = y_pos + altura_desejada + 40
                    draw_text_with_shadow(draw, (W/2, y_num_slide), f"{idx+1} / {len(frases)}", font_body, fill=CORES["texto_secundario"], anchor="ms")
                except Exception as e_num:
                    print(f"⚠️ Erro ao desenhar número do slide no rodapé ({e_num})")
            except Exception as e:
                print(f"⚠️ Erro ao aplicar marca d'água no rodapé ({e}). Usando fallback de texto.")

        if not logo_aplicado:
            font_marca_serif, _, _ = carregar_fontes(86, 22, 24, estilo="BebasNeue")
            desenhar_marca_dagua_ouro(draw, (W/2, H - 200), "GUSTAVO_8K_", font_marca_serif)
            draw_text_with_shadow(draw, (W/2, H - 280), f"{idx+1} / {len(frases)}", font_body, fill=CORES["texto_secundario"], anchor="ms")

        # Salva o fundo SEM o texto de conteúdo (o texto será animado no reels.py)
        caminho = f"reels_slide_{uuid.uuid4().hex}_{idx}.jpg"
        slide.save(caminho, "JPEG", quality=95)
        caminhos_fundos.append(caminho)

    # Retorna tuple: (fundos sem texto, frases para animar, caminho fonte, tamanho fonte)
    return (caminhos_fundos, frases, caminho_fonte_valido, 86)

def _gerar_estatico(img, W, H, tipo, dados, tema_escolhido=None):
    layout_style = random.choice(["classic", "bottom", "quote"])
    print(f"🎨 Usando estilo de layout: {layout_style.upper()}")
    
    # Usa a fonte oficial definida para o tipo de post
    estilo_fonte = obter_fonte_do_dia(tipo=tipo)
        
    font_display, _, _ = carregar_fontes(48, 24, 24, estilo=estilo_fonte)
    
    frases = dados.get("frase", dados.get("slides", [""]))
    if isinstance(frases, str):
        frases = [frases]
        
    caminhos = []
    
    for idx, frase in enumerate(frases):
        # FIX: Para Stories com múltiplos slides, busca imagem diferente por slide
        tipo_story = tipo in ["story_manha", "story_tarde"]
        if tipo_story and idx > 0 and tema_escolhido:
            # Busca uma nova imagem para os próximos slides da sequência
            prompt_secundario = dados.get("prompt_imagem")
            nova_img, _, _ = buscar_imagem_fundo(tipo, tema_escolhido, prompt_imagem=prompt_secundario)
            nova_img = aplicar_mesh_gradient(nova_img)
            slide = nova_img.convert("RGB")
        else:
            slide = img.copy().convert("RGB")
        draw = ImageDraw.Draw(slide)
        
        # Elementos de Agência Premium
        desenhar_elementos_premium(draw, W, H)
        
        # ── 1. [EMBLEMA REMOVIDO] Apenas marca d'água no rodapé é exibida ──
        logo_dir = os.path.join("biblioteca_local", "logo")

        # ── 2. MARCA D'ÁGUA NO RODAPÉ (ignora foto_perfil.png) ──
        y_watermark = H - 150 if tipo in ["story", "story_manha", "story_tarde", "test"] else H - 80
        logo_aplicado = False
        path_logo = os.path.join(logo_dir, "foto_perfil.png")
        if os.path.exists(path_logo):
            try:
                logo_img = Image.open(path_logo)
                largura_desejada = 220
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
                print(f"⚠️ Erro ao aplicar marca d'água no rodapé (estático): {e}")

        if not logo_aplicado:
            font_marca_serif, _, _ = carregar_fontes(48, 24, 24, estilo="BebasNeue")
            desenhar_marca_dagua_ouro(draw, (W/2, y_watermark), "GUSTAVO_8K_", font_marca_serif)
        
        # ── Proteção de layout: limpa quebras e limita linhas ──
        # Remove \n que a IA pode gerar erroneamente (concatena num bloco único)
        frase_limpa = frase.replace("\n", " ").replace("\r", " ").strip()
        # Limita a 6 linhas máx por imagem para não vazar sobre o emblema/marca d'água
        MAX_LINHAS = 6
        linhas_raw = textwrap.wrap(frase_limpa, width=24)
        if len(linhas_raw) > MAX_LINHAS:
            linhas = linhas_raw[:MAX_LINHAS]
            # Adiciona reticências na última linha para indicar truncamento
            ultima = linhas[-1]
            if len(ultima) > 20:
                linhas[-1] = ultima[:20] + "..."
            else:
                linhas[-1] = ultima + "..."
            print(f"⚠️ [Layout] Texto truncado de {len(linhas_raw)} para {MAX_LINHAS} linhas.")
        else:
            linhas = linhas_raw

        # Margens seguras: topo livre (emblema removido), marca d'água ocupa rodapé
        Y_MIN_TEXTO = 150       # topo livre — texto pode subir mais
        Y_MAX_TEXTO = H - 280   # acima da marca d'água + folga

        # Texto com degradê completo via _adicionar_texto_degrade
        from core.media.pexels_story import PALETA_PADRAO_MARCA, _adicionar_texto_degrade
        import numpy as _np

        if linhas:
            frame_np = _np.array(slide)
            frame_np = _adicionar_texto_degrade(
                frame_np, frase_limpa, font_display, paleta=PALETA_PADRAO_MARCA
            )
            slide = Image.fromarray(frame_np)
            draw = ImageDraw.Draw(slide)
            
        _uid = uuid.uuid4().hex
        caminho_imagem = f"story_pronto_{_uid}_{idx}.jpg" if tipo in ["story", "story_manha", "story_tarde", "test"] else f"post_pronto_{_uid}_{idx}.jpg"
        slide.save(caminho_imagem, "JPEG", quality=95)
        caminhos.append(caminho_imagem)
        
    if len(caminhos) == 1:
        return caminhos[0]
    return caminhos
