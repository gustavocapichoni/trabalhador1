import os
import random
import requests
import textwrap
import numpy as np
import uuid
from PIL import Image, ImageDraw, ImageFont
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS
    
from loguru import logger
from core.design.templates import obter_fonte_do_dia
from core.config.state import verificar_midia_recente, registrar_midia_usada, carregar_estado, salvar_estado

def _carregar_fonte(tamanho=50, estilo=None):
    """Tenta carregar a fonte do projeto. Se falhar, usa a padrão do sistema."""
    if estilo is None:
        estilo = obter_fonte_do_dia()
    
    # Garante que o nome da fonte tenha a extensão .ttf
    if not estilo.endswith(".ttf"):
        estilo += ".ttf"
        
    caminhos = [
        f"fontes/{estilo}",
        "fontes/MontserratBold.ttf", # Fallback 1
        "fontes/Montserrat-Bold.ttf", # Fallback 2
    ]
    for c in caminhos:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, tamanho)
            except:
                pass
    try:
        return ImageFont.truetype("arial.ttf", tamanho)
    except:
        return ImageFont.load_default()

def _quebrar_texto_por_pixels(draw, texto, fonte, largura_max_px):
    """Quebra o texto em linhas que cabem dentro de largura_max_px."""
    palavras = texto.split()
    linhas = []
    linha_atual = ""

    for palavra in palavras:
        candidata = (linha_atual + " " + palavra).strip()
        bbox = draw.textbbox((0, 0), candidata, font=fonte)
        lw = bbox[2] - bbox[0]
        if lw <= largura_max_px:
            linha_atual = candidata
        else:
            if linha_atual:
                linhas.append(linha_atual)
            linha_atual = palavra
    if linha_atual:
        linhas.append(linha_atual)
    return linhas

def _adicionar_texto_frame(frame_array, texto, fonte, chars_to_show=None, fade_alpha=1.0, deslocamento_y=0):
    """Desenha texto centralizado com sombra/fundo em um frame. Destaca 'SABEDORIA' em Dourado."""
    if frame_array.dtype != np.uint8:
        frame_array = np.clip(frame_array, 0, 255).astype(np.uint8)
    img = Image.fromarray(frame_array)
    w, h = img.size

    txt_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    margem_px = int(w * 0.075)
    largura_max_texto = w - (margem_px * 2)

    linhas = _quebrar_texto_por_pixels(draw, texto, fonte, largura_max_texto)
    if not linhas:
        return frame_array

    alturas = []
    larguras = []
    for l in linhas:
        bb = draw.textbbox((0, 0), l, font=fonte)
        alturas.append(bb[3] - bb[1])
        larguras.append(bb[2] - bb[0])

    espaco_entre = 14
    padding_v = 20

    total_h = sum(alturas) + espaco_entre * (len(linhas) - 1) + padding_v * 2
    by0 = (h - total_h) // 2

    y = by0 + padding_v + deslocamento_y
    chars_drawn = 0
    for linha, alt, lw in zip(linhas, alturas, larguras):
        x = (w - lw) // 2
        
        if chars_to_show is not None:
            if chars_drawn >= chars_to_show:
                break
            linha_len = len(linha)
            if chars_drawn + linha_len > chars_to_show:
                linha_render = linha[:chars_to_show - chars_drawn]
            else:
                linha_render = linha
            chars_drawn += linha_len + 1
        else:
            linha_render = linha

        # Slides normais: texto sempre branco — destaque dourado só existe no slide do CTA
        draw.text((x + 3, y + 3), linha_render, font=fonte, fill=(0, 0, 0, int(150 * fade_alpha)))
        draw.text((x, y), linha_render, font=fonte, fill=(255, 255, 255, int(255 * fade_alpha)), stroke_width=2, stroke_fill=(0, 0, 0, int(255 * fade_alpha)))

        y += alt + espaco_entre

    img = Image.alpha_composite(img.convert("RGBA"), txt_layer).convert("RGB")

    return np.array(img)

# Paleta fixa da marca: Prata Metálico Sólido (#D8DCE3)
# Esta é a identidade visual permanente de todas as postagens do perfil.
PALETA_PADRAO_MARCA = ([216, 220, 227], [216, 220, 227], [216, 220, 227])

# Paleta do Reels Leads — Prata Metálico sólido (sem degradê colorido)
PALETAS_LEADS = [
    ([216, 220, 227], [216, 220, 227], [216, 220, 227]),   # Prata Metálico sólido
    ([216, 220, 227], [216, 220, 227], [216, 220, 227]),   # Prata Metálico sólido (alternado)
]

def obter_paleta_do_dia():
    """Retorna a paleta fixa da marca: Prata Metálico Sólido."""
    return PALETA_PADRAO_MARCA

def _adicionar_texto_degrade(frame_array, texto, fonte, chars_to_show=None, fade_alpha=1.0, deslocamento_y=0, paleta=None):
    if frame_array.dtype != np.uint8:
        frame_array = np.clip(frame_array, 0, 255).astype(np.uint8)
    img = Image.fromarray(frame_array)
    w, h = img.size
    
    # Camada inferior para sombra e contorno preto
    shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    
    # Camada superior puramente branca (será usada como máscara recortada)
    txt_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    margem_px = int(w * 0.075)
    largura_max_texto = w - (margem_px * 2)

    linhas = _quebrar_texto_por_pixels(draw, texto, fonte, largura_max_texto)
    if not linhas:
        return frame_array

    alturas = []
    larguras = []
    for l in linhas:
        bb = draw.textbbox((0, 0), l, font=fonte)
        alturas.append(bb[3] - bb[1])
        larguras.append(bb[2] - bb[0])

    espaco_entre = 14
    padding_v = 24
    padding_h = 36
    h_texto = sum(alturas) + espaco_entre * (len(linhas) - 1)
    total_h = h_texto + padding_v * 2
    by0 = (h - total_h) // 2

    y_inicial = by0 + padding_v + deslocamento_y
    
    # ── CARD VITRINE: Painel escuro semitransparente com cantos arredondados ──
    try:
        max_lw = max(larguras) if larguras else 0
        card_w = max_lw + (padding_h * 2)
        card_h = total_h
        card_x0 = (w - card_w) // 2
        card_y0 = (by0 + deslocamento_y)
        card_x1 = card_x0 + card_w
        card_y1 = card_y0 + card_h

        card_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card_layer)
        alpha_card = int(140 * fade_alpha)  # ~55% de opacidade para efeito vitrine vidro escuro
        cor_card = (12, 12, 18, alpha_card)  # Tom dark premium
        cor_borda = (235, 180, 50, int(60 * fade_alpha))  # Sutil borda dourada elegante
        card_draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=20, fill=cor_card, outline=cor_borda, width=1)
        img = Image.alpha_composite(img.convert("RGBA"), card_layer)
    except Exception as e_card:
        logger.debug(f"Erro ao desenhar card vitrine: {e_card}")

    y = y_inicial
    chars_drawn = 0
    for linha, alt, lw in zip(linhas, alturas, larguras):
        x = (w - lw) // 2
        
        if chars_to_show is not None:
            if chars_drawn >= chars_to_show:
                break
            linha_len = len(linha)
            if chars_drawn + linha_len > chars_to_show:
                linha_render = linha[:chars_to_show - chars_drawn]
            else:
                linha_render = linha
            chars_drawn += linha_len + 1
        else:
            linha_render = linha
            
        # Desenha sombra macia e contorno rígido preto
        shadow_draw.text((x + 3, y + 3), linha_render, font=fonte, fill=(0, 0, 0, int(150 * fade_alpha)))
        shadow_draw.text((x, y), linha_render, font=fonte, fill=(0, 0, 0, 0), stroke_width=2, stroke_fill=(0, 0, 0, int(255 * fade_alpha)))
        
        # Desenha o interior da letra puro para máscara alpha
        draw.text((x, y), linha_render, font=fonte, fill=(255, 255, 255, int(255 * fade_alpha)))
        y += alt + espaco_entre

    # Isola o recorte das letras
    mask = txt_layer.split()[3]
    
    # Cria a matriz do degradê com a paleta selecionada (ou padrão Roxo→Branco→Azul)
    gradient = np.zeros((h, w, 3), dtype=np.uint8)
    if paleta:
        color_top = np.array(paleta[0])
        color_mid = np.array(paleta[1])
        color_bot = np.array(paleta[2])
    else:
        color_top = np.array([176, 38, 255])
        color_mid = np.array([255, 255, 255])
        color_bot = np.array([0, 51, 255])
    
    y_min_texto = y_inicial
    y_max_texto = y_inicial + h_texto
    h_bloco = max(1, y_max_texto - y_min_texto)

    for i in range(h):
        if i < y_min_texto:
            color = color_top
        elif i > y_max_texto:
            color = color_bot
        else:
            ratio = (i - y_min_texto) / float(h_bloco)
            if ratio < 0.5:
                r = (ratio / 0.5)
                color = color_top * (1 - r) + color_mid * r
            else:
                r = ((ratio - 0.5) / 0.5)
                color = color_mid * (1 - r) + color_bot * r
        gradient[i, :, :] = color
        
    grad_img = Image.fromarray(gradient, 'RGB')
    final_txt_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    final_txt_layer.paste(grad_img, (0,0), mask=mask)
    
    # Empilha as 3 camadas: Fundo (vídeo) + Contorno (Preto) + Texto (Degradê)
    img = Image.alpha_composite(img.convert("RGBA"), shadow_layer)
    img = Image.alpha_composite(img, final_txt_layer).convert("RGB")

    return np.array(img)


def _desenhar_linha_sem_keyword(mask_draw, linha, x_linha, y_linha, fonte_cta, fonte_keyword, keyword_destaque, fade_alpha, w_img, cor_preenchimento=None, stroke_w=0, stroke_c=None):
    """Desenha a linha pulando (deixando transparente) a palavra-chave de destaque."""
    fill_cor = (255, 255, 255, int(255 * fade_alpha)) if cor_preenchimento is None else cor_preenchimento

    if not keyword_destaque or keyword_destaque not in linha.upper():
        mask_draw.text((x_linha, y_linha), linha, font=fonte_cta, fill=fill_cor,
                       stroke_width=stroke_w, stroke_fill=stroke_c)
        return

    palavras = linha.split(" ")
    espaco_w = mask_draw.textbbox((0, 0), " ", font=fonte_cta)[2] - mask_draw.textbbox((0, 0), " ", font=fonte_cta)[0]
    larguras_palavras = []
    
    for p in palavras:
        p_clean = p.upper().replace("'", "").replace("\u2018", "").replace("\u2019", "").replace('"', '').replace(',', '').replace('.', '').replace('!', '').strip()
        f_usar = fonte_keyword if p_clean == keyword_destaque else fonte_cta
        pw = mask_draw.textbbox((0, 0), p, font=f_usar)[2] - mask_draw.textbbox((0, 0), p, font=f_usar)[0]
        larguras_palavras.append((pw, f_usar, p_clean))

    largura_total_linha = sum(pw for pw, _, _ in larguras_palavras) + espaco_w * (len(palavras) - 1)
    cur_x = (w_img - largura_total_linha) // 2

    for p, (pw, f_usar, p_clean) in zip(palavras, larguras_palavras):
        if p_clean != keyword_destaque:
            mask_draw.text((cur_x, y_linha), p, font=f_usar, fill=fill_cor,
                           stroke_width=stroke_w, stroke_fill=stroke_c)
        cur_x += pw + espaco_w


def _adicionar_texto_cta(frame_array, texto, fonte_cta, chars_to_show=None, fade_alpha=1.0, deslocamento_y=0, paleta_override=None, cor_keyword=None):
    """Desenha o CTA final. Se paleta_override for fornecida (Reels Leads / Story Tarde), aplica degradê colorido nas letras.
    Caso contrário, usa o comportamento padrão: texto em branco com destaque na palavra-chave."""
    import re as _re
    if frame_array.dtype != np.uint8:
        frame_array = np.clip(frame_array, 0, 255).astype(np.uint8)
    img = Image.fromarray(frame_array)
    w, h = img.size

    # Cor da palavra-chave (padrão é Dourado, ou a cor informada via cor_keyword)
    if cor_keyword is None:
        cor_keyword_rgb = (255, 215, 0)
    else:
        cor_keyword_rgb = cor_keyword

    # Detecta a palavra-chave de destaque no texto.
    match_keyword = _re.search(r"['\u2018\u2019\"]([^'\u2018\u2019\"]+)['\u2018\u2019\"]", texto)
    if match_keyword:
        keyword_destaque = match_keyword.group(1).upper().strip()
    else:
        match_sem_aspas = _re.search(r'\bSABEDORIA\b', texto.upper())
        keyword_destaque = "SABEDORIA" if match_sem_aspas else None

    # Cria uma fonte maior para a palavra-chave (18% maior que a base do CTA)
    tamanho_cta_base = getattr(fonte_cta, 'size', None)
    fonte_keyword = None
    if keyword_destaque and tamanho_cta_base:
        tamanho_keyword = max(tamanho_cta_base, int(tamanho_cta_base * 1.18))
        try:
            caminho_fonte = getattr(fonte_cta, 'path', None)
            if caminho_fonte and os.path.exists(caminho_fonte):
                fonte_keyword = ImageFont.truetype(caminho_fonte, tamanho_keyword)
        except Exception:
            pass
    if fonte_keyword is None:
        fonte_keyword = fonte_cta

    txt_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    margem_px = int(w * 0.075)
    largura_max_texto = w - (margem_px * 2)

    partes = [p.strip() for p in texto.split("\n") if p.strip()]
    if len(partes) >= 2:
        texto_topo = partes[0]
        texto_baixo = partes[1]
    else:
        texto_topo = ""
        texto_baixo = texto

    linhas_topo = _quebrar_texto_por_pixels(draw, texto_topo, fonte_cta, largura_max_texto) if texto_topo else []
    linhas_baixo = _quebrar_texto_por_pixels(draw, texto_baixo, fonte_cta, largura_max_texto)

    alturas_topo = []
    larguras_topo = []
    for l in linhas_topo:
        bb = draw.textbbox((0, 0), l, font=fonte_cta)
        alturas_topo.append(bb[3] - bb[1])
        larguras_topo.append(bb[2] - bb[0])

    alturas_baixo = []
    larguras_baixo = []
    for l in linhas_baixo:
        bb = draw.textbbox((0, 0), l, font=fonte_cta)
        alturas_baixo.append(bb[3] - bb[1])
        larguras_baixo.append(bb[2] - bb[0])

    espaco_entre = 12
    divisor_espaco = 24
    padding_v = 30

    if linhas_topo:
        total_h = sum(alturas_topo) + espaco_entre * (len(linhas_topo) - 1) + divisor_espaco + sum(alturas_baixo) + espaco_entre * (len(linhas_baixo) - 1) + padding_v * 2
    else:
        total_h = sum(alturas_baixo) + espaco_entre * (len(linhas_baixo) - 1) + padding_v * 2

    by0 = (h - total_h) // 2
    y_inicial_bloco = by0 + padding_v + deslocamento_y

    # ── CARD VITRINE (CTA): Painel escuro semitransparente com cantos arredondados ──
    try:
        todas_larguras = larguras_topo + larguras_baixo
        max_lw = max(todas_larguras) if todas_larguras else 0
        padding_h = 36
        card_w = max_lw + (padding_h * 2)
        card_h = total_h
        card_x0 = (w - card_w) // 2
        card_y0 = (by0 + deslocamento_y)
        card_x1 = card_x0 + card_w
        card_y1 = card_y0 + card_h

        card_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card_layer)
        alpha_card = int(140 * fade_alpha)
        cor_card = (12, 12, 18, alpha_card)
        cor_borda = (235, 180, 50, int(60 * fade_alpha))
        card_draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=20, fill=cor_card, outline=cor_borda, width=1)
        img = Image.alpha_composite(img.convert("RGBA"), card_layer)
    except Exception as e_card:
        logger.debug(f"Erro ao desenhar card vitrine CTA: {e_card}")

    if paleta_override:
        shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        txt_mask_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        mask_draw = ImageDraw.Draw(txt_mask_layer)

        todas_linhas = list(zip(linhas_topo, alturas_topo, larguras_topo)) + \
                       list(zip(linhas_baixo, alturas_baixo, larguras_baixo))

        y_texto_min = y_inicial_bloco
        y_texto_max = y_inicial_bloco
        for linha, alt, lw in todas_linhas:
            y_texto_max += alt + espaco_entre
        if linhas_topo:
            y_texto_max += divisor_espaco - espaco_entre
        h_bloco_total = max(1, y_texto_max - y_texto_min)

        color_top = np.array(paleta_override[0])
        color_mid = np.array(paleta_override[1])
        color_bot = np.array(paleta_override[2])
        gradient_arr = np.zeros((h, w, 3), dtype=np.uint8)
        for row in range(h):
            if row < y_texto_min:
                c = color_top
            elif row > y_texto_max:
                c = color_bot
            else:
                ratio = (row - y_texto_min) / float(h_bloco_total)
                if ratio < 0.5:
                    r = ratio / 0.5
                    c = color_top * (1 - r) + color_mid * r
                else:
                    r = (ratio - 0.5) / 0.5
                    c = color_mid * (1 - r) + color_bot * r
            gradient_arr[row, :, :] = c.astype(np.uint8)
        grad_img = Image.fromarray(gradient_arr, 'RGB')

        posicoes_linhas_topo = []
        posicoes_linhas_baixo = []

        y = y_inicial_bloco
        if linhas_topo:
            for linha, alt, lw in zip(linhas_topo, alturas_topo, larguras_topo):
                x = (w - lw) // 2
                # Desenha sombra pulando a palavra-chave para nao criar texto fantasma por tras
                _desenhar_linha_sem_keyword(shadow_draw, linha, x + 3, y + 3, fonte_cta, fonte_keyword,
                                            keyword_destaque, fade_alpha, w, cor_preenchimento=(0, 0, 0, int(150 * fade_alpha)))
                _desenhar_linha_sem_keyword(shadow_draw, linha, x, y, fonte_cta, fonte_keyword,
                                            keyword_destaque, fade_alpha, w, cor_preenchimento=(0, 0, 0, 0),
                                            stroke_w=2, stroke_c=(0, 0, 0, int(255 * fade_alpha)))
                # Desenha a máscara do degradê pulando a palavra-chave
                _desenhar_linha_sem_keyword(mask_draw, linha, x, y, fonte_cta, fonte_keyword,
                                            keyword_destaque, fade_alpha, w)
                posicoes_linhas_topo.append((linha, x, y, alt, lw))
                y += alt + espaco_entre
            y += divisor_espaco - espaco_entre
        for linha, alt, lw in zip(linhas_baixo, alturas_baixo, larguras_baixo):
            x = (w - lw) // 2
            _desenhar_linha_sem_keyword(shadow_draw, linha, x + 3, y + 3, fonte_cta, fonte_keyword,
                                        keyword_destaque, fade_alpha, w, cor_preenchimento=(0, 0, 0, int(150 * fade_alpha)))
            _desenhar_linha_sem_keyword(shadow_draw, linha, x, y, fonte_cta, fonte_keyword,
                                        keyword_destaque, fade_alpha, w, cor_preenchimento=(0, 0, 0, 0),
                                        stroke_w=2, stroke_c=(0, 0, 0, int(255 * fade_alpha)))
            _desenhar_linha_sem_keyword(mask_draw, linha, x, y, fonte_cta, fonte_keyword,
                                        keyword_destaque, fade_alpha, w)
            posicoes_linhas_baixo.append((linha, x, y, alt, lw))
            y += alt + espaco_entre

        mask = txt_mask_layer.split()[3]
        final_txt_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        final_txt_layer.paste(grad_img, (0, 0), mask=mask)
        img = Image.alpha_composite(img.convert("RGBA"), shadow_layer)
        img = Image.alpha_composite(img, final_txt_layer).convert("RGB")

        if keyword_destaque:
            sabedoria_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            sabedoria_draw = ImageDraw.Draw(sabedoria_layer)
            espaco_w = sabedoria_draw.textbbox((0, 0), " ", font=fonte_cta)[2] - \
                       sabedoria_draw.textbbox((0, 0), " ", font=fonte_cta)[0]

            for (linha, x_linha, y_linha, alt_linha, lw_linha) in (posicoes_linhas_topo + posicoes_linhas_baixo):
                linha_upper = linha.upper()
                if keyword_destaque not in linha_upper:
                    continue
                palavras = linha.split(" ")
                larguras_palavras = []
                for p in palavras:
                    p_clean = p.upper().replace("'", "").replace("\u2018", "").replace("\u2019", "").replace('"', '').replace(',', '').replace('.', '').replace('!', '').strip()
                    f_usar = fonte_keyword if p_clean == keyword_destaque else fonte_cta
                    pw = sabedoria_draw.textbbox((0, 0), p, font=f_usar)[2] - sabedoria_draw.textbbox((0, 0), p, font=f_usar)[0]
                    larguras_palavras.append((pw, f_usar, p_clean))

                largura_total_linha = sum(pw for pw, _, _ in larguras_palavras) + espaco_w * (len(palavras) - 1)
                cur_x = (w - largura_total_linha) // 2

                for p, (pw, f_usar, p_clean) in zip(palavras, larguras_palavras):
                    if p_clean == keyword_destaque:
                        cor_destaque_rgba = (cor_keyword_rgb[0], cor_keyword_rgb[1], cor_keyword_rgb[2], int(255 * fade_alpha))
                        bb_k = sabedoria_draw.textbbox((0, 0), p, font=f_usar)
                        alt_k = bb_k[3] - bb_k[1]
                        y_offset = (alt_linha - alt_k) // 2
                        sabedoria_draw.text((cur_x + 3, y_linha + y_offset + 3), p, font=f_usar,
                                            fill=(0, 0, 0, int(150 * fade_alpha)))
                        sabedoria_draw.text((cur_x, y_linha + y_offset), p, font=f_usar, fill=cor_destaque_rgba,
                                            stroke_width=3, stroke_fill=(0, 0, 0, int(255 * fade_alpha)))
                    cur_x += pw + espaco_w

            img = Image.alpha_composite(img.convert("RGBA"), sabedoria_layer).convert("RGB")

        return np.array(img)

    # --- Modo Padrão (branco + destaque dourado na keyword) ---
    y = y_inicial_bloco
    if linhas_topo:
        for linha, alt, lw in zip(linhas_topo, alturas_topo, larguras_topo):
            x = (w - lw) // 2

            # Verifica se esta linha contém a palavra-chave de destaque
            linha_upper = linha.upper()
            contem_keyword = keyword_destaque and keyword_destaque in linha_upper

            if contem_keyword:
                # Renderiza palavra por palavra: destaca a keyword em Dourado + fonte maior
                palavras = linha.split(" ")
                espaco_w = draw.textbbox((0, 0), " ", font=fonte_cta)[2] - draw.textbbox((0, 0), " ", font=fonte_cta)[0]
                larguras_palavras = []
                for p in palavras:
                    p_clean = p.upper().replace("'", "").replace("\u2018", "").replace("\u2019", "").replace('"', '').replace(',', '').replace('.', '').replace('!', '').strip()
                    f_usar = fonte_keyword if p_clean == keyword_destaque else fonte_cta
                    pw = draw.textbbox((0, 0), p, font=f_usar)[2] - draw.textbbox((0, 0), p, font=f_usar)[0]
                    larguras_palavras.append((pw, f_usar, p_clean))

                largura_total_linha = sum(pw for pw, _, _ in larguras_palavras) + espaco_w * (len(palavras) - 1)
                cur_x = (w - largura_total_linha) // 2

                for p, (pw, f_usar, p_clean) in zip(palavras, larguras_palavras):
                    if p_clean == keyword_destaque:
                        cor_palavra = (255, 215, 0, int(255 * fade_alpha))
                        bb_k = draw.textbbox((0, 0), p, font=f_usar)
                        alt_k = bb_k[3] - bb_k[1]
                        y_offset = (alt - alt_k) // 2
                        draw.text((cur_x + 3, y + y_offset + 3), p, font=f_usar, fill=(0, 0, 0, int(150 * fade_alpha)))
                        draw.text((cur_x, y + y_offset), p, font=f_usar, fill=cor_palavra,
                                  stroke_width=3, stroke_fill=(0, 0, 0, int(255 * fade_alpha)))
                    else:
                        draw.text((cur_x + 3, y + 3), p, font=f_usar, fill=(0, 0, 0, int(150 * fade_alpha)))
                        draw.text((cur_x, y), p, font=f_usar, fill=(216, 220, 227, int(255 * fade_alpha)),
                                  stroke_width=2, stroke_fill=(0, 0, 0, int(255 * fade_alpha)))
                    cur_x += pw + espaco_w
            else:
                # Sombra suave + contorno preto com texto Prata Metálico
                draw.text((x + 3, y + 3), linha, font=fonte_cta, fill=(0, 0, 0, int(150 * fade_alpha)))
                draw.text((x, y), linha, font=fonte_cta, fill=(216, 220, 227, int(255 * fade_alpha)),
                          stroke_width=2, stroke_fill=(0, 0, 0, int(255 * fade_alpha)))
            y += alt + espaco_entre
        y += divisor_espaco - espaco_entre

    # 2. Renderiza as linhas de Baixo (Proposta de Valor) sempre em Prata Metálico
    #    Esta seção é descritiva e não deve ter destaque dourado (a keyword aqui é contextual, não o CTA)
    for linha, alt, lw in zip(linhas_baixo, alturas_baixo, larguras_baixo):
        x = (w - lw) // 2
        draw.text((x + 3, y + 3), linha, font=fonte_cta, fill=(0, 0, 0, int(150 * fade_alpha)))
        draw.text((x, y), linha, font=fonte_cta, fill=(216, 220, 227, int(255 * fade_alpha)),
                  stroke_width=2, stroke_fill=(0, 0, 0, int(255 * fade_alpha)))
        y += alt + espaco_entre


    # Sem escurecimento extra — o overlay da marca já cobre o vídeo inteiro
    img = Image.alpha_composite(img.convert("RGBA"), txt_layer).convert("RGB")

    return np.array(img)

def _aplicar_efeito_cinematico(frame_array, efeito):
    """Aplica filtro escuro noturno (Dark Overlay 45%) uniforme em todos os frames."""
    if frame_array.dtype != np.uint8:
        frame_array = np.clip(frame_array, 0, 255).astype(np.uint8)
        
    img = Image.fromarray(frame_array)
    w, h = img.size
    
    # Camada de escurecimento noturno uniforme (Dark Aesthetic constante)
    dark_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 115)) # 45% opacidade preta
    img = Image.alpha_composite(img.convert("RGBA"), dark_overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    if efeito == "cinematic_bars":
        bar_h = int(h * 0.12)
        draw.rectangle([0, 0, w, bar_h], fill=(0, 0, 0))
        draw.rectangle([0, h - bar_h, w, h], fill=(0, 0, 0))
        
    elif efeito == "warm_amber":
        amber_overlay = Image.new("RGBA", (w, h), (212, 175, 55, 25))
        img = Image.alpha_composite(img.convert("RGBA"), amber_overlay).convert("RGB")
        
    elif efeito == "dark_gold_neon":
        gold_overlay = Image.new("RGBA", (w, h), (180, 140, 30, 30))
        img = Image.alpha_composite(img.convert("RGBA"), gold_overlay).convert("RGB")
        
    return np.array(img)

def gerar_pexels_story(query, slides, caminho_saida="pexels_story.mp4", tema=None, is_conquistador=False, is_reels_leads=False, is_noite=False, is_story_tarde=False):
    from core.config.settings import PEXELS_API_KEY, PIXABAY_API_KEY
    import urllib.parse
    import random

    # --- Normaliza e enriquece queries com alternância temática profunda ---
    QUERIES_VIDEO_VARIADAS = [
        # Metrô / Transporte
        "subway passenger sitting night window cinematic",
        "london tube underground platform empty night",
        "subway escalator long perspective night moody",
        "metro train interior lonely passenger looking out",
        "subway window reflection night motion dark",

        # Multidão / Chuva / Faixa de Pedestres
        "london rain crowd street crosswalk night 35mm",
        "top down crosswalk pedestrians umbrellas night rain",
        "wet street reflections pedestrians walking night city",
        "london red bus rain night crosswalk motion",
        "crowded city intersection night rain street light",

        # Praças / Ruas Históricas (Paris/Londres)
        "paris plaza night couple bench ambient light",
        "london park bench night fog street lamp",
        "paris river seine bridge night lights reflection",
        "cobblestone street night alley walking warm lamp",
        "paris cafe terrace night rain solitude",

        # Vidro / Chuva / Bokeh
        "rain drops on window glass night city bokeh",
        "taxi window rain night city lights motion blur",
        "rainy window blurry lights dark aesthetic",
        "car window rain night street lights reflection",

        # Geral Urban Solitude
        "night urban solitude city street golden light 35mm",
        "person walking night city crowd moody",
    ]

    if isinstance(query, str):
        queries_lista = [query, random.choice(QUERIES_VIDEO_VARIADAS)]
    else:
        queries_lista = list(query) + [random.choice(QUERIES_VIDEO_VARIADAS)]

    # --- HIGIENIZAÇÃO E PADRONIZAÇÃO DE QUERIES (Filtro Estrito: Solidão Urbana Contemporânea Noturna) ---
    # Elimina vídeos claros, academias, natureza diurna, praias e escritórios iluminados.
    TERMOS_PROIBIDOS_VIDEO = [
        "study", "studying", "student", "library", "classroom", "school",
        "sunlight", "daylight", "meadow", "park", "bright office", "white room",
        "field", "grass", "green grass", "farm", "hay", "beach", "ocean daylight",
        "flower", "flowers", "garden", "nature daylight", "sunny", "landscape green",
        "trees daylight", "mountain sunrise", "bright day", "sun",
        "gym", "boxing", "workout", "training", "fitness", "ring", "boxing ring", "athlete daylight",
        "stadium", "soccer", "football", "crowd party", "drinking", "alcohol", "bar", "wine", "beer"
    ]
    queries_higienizadas = []
    for q in queries_lista:
        q_clean = q.lower()
        for term in TERMOS_PROIBIDOS_VIDEO:
            q_clean = q_clean.replace(term, "").strip()
        if len(q_clean) < 4:
            q_clean = random.choice(QUERIES_VIDEO_VARIADAS)
        if "night" not in q_clean:
            q_clean += " night urban solitude 35mm cinematic"
        queries_higienizadas.append(q_clean)
    queries_lista = queries_higienizadas

    logger.info(f"🎥 Buscando vídeos com {len(queries_lista)} quer{'y' if len(queries_lista)==1 else 'ies'} de Solidão Urbana Noturna: {queries_lista}")

    slides = list(slides)

    temp_vids = []
    clip = None
    final_clip = None
    bg_audio = None
    outro_clip = None


    # --- Rotação sequencial exclusiva do Conquistador (animação e plataforma) ---
    animacao_conquistador = None
    plataforma_principal_conquistador = None  # None = usa a cascata padrão (Pixabay -> Pexels)

    if is_conquistador:
        estado_conq = carregar_estado()
        animacoes_lista = ["typewriter", "fade", "reveal", "static"]
        idx_anim = estado_conq.get("index_animacao_conquistador", 0) % len(animacoes_lista)
        animacao_conquistador = animacoes_lista[idx_anim]
        estado_conq["index_animacao_conquistador"] = (idx_anim + 1) % len(animacoes_lista)

        idx_plat = estado_conq.get("index_plataforma_conquistador", 0) % 2
        plataforma_principal_conquistador = idx_plat  # 0=Pixabay primeiro, 1=Pexels primeiro
        estado_conq["index_plataforma_conquistador"] = (idx_plat + 1) % 2

        salvar_estado(estado_conq)
        logger.info(f"🎨 [CONQUISTADOR] Animação: {animacao_conquistador.upper()} | Plataforma: {'Pixabay' if idx_plat == 0 else 'Pexels'}")

    # --- Rotação de paletas exclusivas do Reels Leads ---
    paleta_reels_leads = None
    _path_cta_do_dia = None  # Inicializado aqui para ser acessível em toda a função
    if is_reels_leads:
        estado_leads = carregar_estado()
        idx_pal_leads = estado_leads.get("index_palette_leads", 0) % len(PALETAS_LEADS)
        paleta_reels_leads = PALETAS_LEADS[idx_pal_leads]
        estado_leads["index_palette_leads"] = (idx_pal_leads + 1) % len(PALETAS_LEADS)
        salvar_estado(estado_leads)
        nome_pal = "Visão Profética (Roxo/Azul)" if idx_pal_leads == 0 else "Paixão & Força (Rosa/Vermelho)"
        logger.info(f"🟣 [REELS_LEADS] Paleta exclusiva ativada: #{idx_pal_leads + 1} - {nome_pal}")

    # ─────────────────────────────────────────────────────────────────────────
    # ROLETA DIÁRIA DE CTA (exclusiva para reels_leads e story_tarde)
    # Funciona como uma roleta: cta00 → cta01 → cta02 → cta03 → cta00 ...
    # A roleta avança 1x por dia (data do sistema). O mesmo CTA do dia é
    # compartilhado entre reels_leads e story_tarde (postados uma vez por dia).
    # ─────────────────────────────────────────────────────────────────────────
    if is_reels_leads or is_story_tarde:
        import datetime
        _logo_dir_cta = os.path.join("biblioteca_local", "logo")
        _nomes_cta = [f"cta0{i}.png" for i in range(4)]  # cta00, cta01, cta02, cta03
        _ctas_disponiveis = [os.path.join(_logo_dir_cta, n) for n in _nomes_cta
                             if os.path.exists(os.path.join(_logo_dir_cta, n))]
        if _ctas_disponiveis:
            _estado_cta = carregar_estado()
            _hoje = datetime.date.today().isoformat()  # ex: "2026-08-10"
            _ultimo_dia_cta = _estado_cta.get("ultimo_dia_cta", "")
            _idx_cta_dia = _estado_cta.get("index_cta_dia", 0)
            # Avança a roleta apenas se for um novo dia
            if _ultimo_dia_cta != _hoje:
                if _ultimo_dia_cta != "":  # Não avança na primeira execução (sem dia anterior)
                    _idx_cta_dia = (_idx_cta_dia + 1) % len(_ctas_disponiveis)
                _estado_cta["index_cta_dia"] = _idx_cta_dia
                _estado_cta["ultimo_dia_cta"] = _hoje
                salvar_estado(_estado_cta)
            _path_cta_do_dia = _ctas_disponiveis[_idx_cta_dia % len(_ctas_disponiveis)]
            logger.info(f"🎯 [CTA DO DIA] Índice {_idx_cta_dia} → {os.path.basename(_path_cta_do_dia)} (dia: {_hoje})")
        else:
            logger.warning("⚠️ Nenhum arquivo cta0X.png encontrado em biblioteca_local/logo. Usando marca d'água padrão.")

    # Define quantos vídeos baixar de forma adaptativa:
    # Para reels_leads: 3 slides rápidos de ~4s a 5s cada = ~12s a 15s no máximo
    # Para story_tarde: preservado com 5s por slide
    # Para pexels_story (dia e noite): 1 único vídeo de fundo contínuo de ~12s a 14s (3 slides de ~4s)
    # Para reels_conquistador: 3 vídeos rápidos sincronizados de ~4s cada = ~12s a 14s no máximo
    if is_story_tarde:
        num_slides_estimado = len(slides) if slides else 5
        duracao_necessaria_reels = num_slides_estimado * 5
        duracao_minima_download = 30
        num_videos_necessarios = 1
        logger.info(f"📊 [STORY_TARDE] {num_slides_estimado} slides × 5s = {duracao_necessaria_reels}s | 1 vídeo único de {duracao_minima_download}s+")
    elif is_reels_leads:
        num_slides_estimado = len(slides) if slides else 4
        duracao_necessaria_reels = num_slides_estimado * 5.0  # 5s por slide (ex: 4 slides = 20s)
        duracao_minima_download = int(duracao_necessaria_reels)
        num_videos_necessarios = 1
        logger.info(f"📊 [REELS_LEADS] {num_slides_estimado} slides × 5s = {duracao_necessaria_reels:.1f}s necessários | 1 vídeo de fundo contínuo")
    elif (not is_noite) and (not is_conquistador):
        # pexels_story da Manhã: 1 único vídeo de fundo contínuo de ~12s a 14s (3 slides)
        num_slides_estimado = len(slides) if slides else 3
        duracao_necessaria_reels = min(14.0, num_slides_estimado * 4.0)  # ~12s a 14s
        num_videos_necessarios = 1
        logger.info(f"📊 [PEXELS_STORY MANHÃ] {num_slides_estimado} slides → ~{duracao_necessaria_reels:.1f}s necessários | 1 vídeo de fundo contínuo")
    elif is_noite and (not is_conquistador):
        # pexels_story_noite: 1 único vídeo de fundo contínuo de ~13s a 15s (3 slides)
        num_slides_estimado = len(slides) if slides else 3
        duracao_necessaria_reels = min(15.0, num_slides_estimado * 4.5)  # ~13.5s a 15s
        num_videos_necessarios = 1
        logger.info(f"📊 [PEXELS_STORY NOITE] {num_slides_estimado} slides → ~{duracao_necessaria_reels:.1f}s necessários | 1 vídeo de fundo contínuo")
    else:
        # Conquistador: 3 vídeos rápidos sincronizados de ~4s cada (12s a 14s total)
        num_slides_estimado = len(slides) if slides else 3
        duracao_necessaria_reels = min(14.0, num_slides_estimado * 4.0)
        num_videos_necessarios = num_slides_estimado
        logger.info(f"📊 [CONQUISTADOR] {num_slides_estimado} slides → ~{duracao_necessaria_reels:.1f}s necessários → baixando {num_videos_necessarios} vídeos (1 por slide)")

    # --- BUSCA DE VÍDEOS: ordem depende da rotação do Conquistador ---
    # plataforma_principal_conquistador: None=padrão(Pixabay→Pexels), 0=Pixabay→Pexels, 1=Pexels→Pixabay
    _usar_pixabay_primeiro = (plataforma_principal_conquistador != 1)

    def _buscar_pixabay(q_encoded):
        nonlocal temp_vids
        if not PIXABAY_API_KEY or len(temp_vids) >= num_videos_necessarios:
            return
        try:
            # Paginação aleatória: sorteia entre página 1, 2 ou 3 — triplica o pool de resultados
            page = random.randint(1, 3)
            logger.info(f"🔍 [Pixabay] '{urllib.parse.unquote(q_encoded)}' (pág. {page})...")
            url_pixabay = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={q_encoded}&video_type=film&page={page}&per_page=15"
            res_pixabay = requests.get(url_pixabay, timeout=15)
            if res_pixabay.status_code == 200:
                data = res_pixabay.json()
                hits_originais = data.get("hits", [])
                hits = []
                for h in hits_originais:
                    v_dict = h.get("videos", {})
                    for size in ["large", "medium", "small", "tiny"]:
                        if size in v_dict and v_dict[size].get("height", 0) > v_dict[size].get("width", 0):
                            hits.append(h)
                            break
                if hits:
                    random.shuffle(hits)
                    for hit in hits:
                        if len(temp_vids) >= num_videos_necessarios:
                            break
                        vid_id = str(hit.get("id", ""))
                        # Filtro de duração exclusivo para reels_leads/story_tarde: aceita apenas vídeos com 30s ou mais
                        if is_reels_leads or is_story_tarde:
                            duracao_hit = hit.get("duration", 0)
                            if duracao_hit < duracao_minima_download:
                                continue
                        if not verificar_midia_recente(vid_id):
                            videos_dict = hit.get("videos", {})
                            link_download = None
                            for size in ["large", "medium", "small", "tiny"]:
                                if size in videos_dict and videos_dict[size].get("url"):
                                    link_download = videos_dict[size]["url"]
                                    if videos_dict[size].get("height", 0) > videos_dict[size].get("width", 0):
                                        break
                            if link_download:
                                logger.info(f"✅ Vídeo {len(temp_vids)+1} encontrado no Pixabay! Baixando...")
                                vid_resp = requests.get(link_download, timeout=30)
                                temp_vid = f"temp_video_{uuid.uuid4().hex}.mp4"
                                with open(temp_vid, "wb") as fv:
                                    fv.write(vid_resp.content)
                                temp_vids.append(temp_vid)
                                registrar_midia_usada(vid_id)
                                
                                try:
                                    from core.utils.contexto import registrar_contexto
                                    registrar_contexto("plataforma_video", "Pixabay")
                                    registrar_contexto("query_video", urllib.parse.unquote(q_encoded))
                                except Exception as context_err:
                                    logger.debug(f"Erro ao registrar contexto Pixabay: {context_err}")
                else:
                    logger.warning("⚠️ Nenhum vídeo encontrado no Pixabay para essa query.")
            else:
                logger.warning(f"⚠️ Pixabay retornou status {res_pixabay.status_code}.")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao acessar Pixabay: {e}")

    def _buscar_pexels(q_encoded):
        nonlocal temp_vids
        if not PEXELS_API_KEY or len(temp_vids) >= num_videos_necessarios:
            return
        try:
            # Paginação aleatória expandida: sorteia entre página 1 a 10 e 30 vídeos por página — multiplica o pool por 10
            page = random.randint(1, 10)
            logger.info(f"🔍 [Pexels] '{urllib.parse.unquote(q_encoded)}' (pág. {page})...")
            url_pexels = f"https://api.pexels.com/videos/search?query={q_encoded}&orientation=portrait&size=medium&per_page=30&page={page}"
            headers = {"Authorization": PEXELS_API_KEY}
            response = requests.get(url_pexels, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if not data.get("videos"):
                    logger.warning("⚠️ Nenhum vídeo encontrado no Pexels para a página sorteada, tentando página 1...")
                    response = requests.get(f"https://api.pexels.com/videos/search?query={q_encoded}&orientation=portrait&per_page=30&page=1", headers=headers, timeout=15)
                    data = response.json()
                if data.get("videos"):
                    videos = data["videos"]
                    random.shuffle(videos)
                    for v in videos:
                        if len(temp_vids) >= num_videos_necessarios:
                            break
                        vid_id = str(v.get("id", ""))
                        # Filtro de duração exclusivo para reels_leads/story_tarde: aceita apenas vídeos com 30s ou mais
                        if is_reels_leads or is_story_tarde:
                            duracao_v = v.get("duration", 0)
                            if duracao_v < duracao_minima_download:
                                continue
                        if not verificar_midia_recente(vid_id):
                            video_files = v.get("video_files", [])
                            arquivos_verticais = [f for f in video_files if f.get("height", 0) > f.get("width", 0)]
                            link = None
                            if arquivos_verticais:
                                arquivos_verticais.sort(key=lambda x: x.get("width", 0), reverse=True)
                                link = arquivos_verticais[0]["link"]
                            if link:
                                logger.info(f"✅ Vídeo {len(temp_vids)+1} encontrado no Pexels! Baixando...")
                                vid_resp = requests.get(link, timeout=30)
                                temp_vid = f"temp_video_{uuid.uuid4().hex}.mp4"
                                with open(temp_vid, "wb") as fv:
                                    fv.write(vid_resp.content)
                                temp_vids.append(temp_vid)
                                registrar_midia_usada(vid_id)
                                
                                try:
                                    from core.utils.contexto import registrar_contexto
                                    registrar_contexto("plataforma_video", "Pexels")
                                    registrar_contexto("query_video", urllib.parse.unquote(q_encoded))
                                except Exception as context_err:
                                    logger.debug(f"Erro ao registrar contexto Pexels: {context_err}")
            else:
                logger.warning(f"⚠️ Pexels retornou status {response.status_code}.")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao acessar Pexels: {e}")

    # --- Loop pelas queries: cada query busca em ambas as APIs ---
    # Garante que vídeos de universos visuais distintos sejam baixados para o mesmo post
    for q in queries_lista:
        if len(temp_vids) >= num_videos_necessarios:
            break
        q_encoded = urllib.parse.quote(q)
        if _usar_pixabay_primeiro:
            _buscar_pixabay(q_encoded)
            if len(temp_vids) < num_videos_necessarios:
                _buscar_pexels(q_encoded)
        else:
            _buscar_pexels(q_encoded)
            if len(temp_vids) < num_videos_necessarios:
                _buscar_pixabay(q_encoded)



    # --- FALLBACK: Biblioteca Local de Emergência ---
    # Ativa se: não tiver NENHUM vídeo (emergência total) OU se tiver menos do que o necessário (complemento parcial)
    if len(temp_vids) < num_videos_necessarios:
        if temp_vids:
            logger.warning(f"⚠️ APIs retornaram apenas {len(temp_vids)}/{num_videos_necessarios} vídeos. Complementando com biblioteca local...")
        
        tema_pasta = tema if tema else "geral"
        pasta_tema = os.path.join("biblioteca_local", "videos", tema_pasta)
        pasta_geral = os.path.join("biblioteca_local", "videos")

        vids_ja_usados = set(os.path.abspath(v) for v in temp_vids)
        for pasta in [pasta_tema, pasta_geral]:
            if os.path.exists(pasta):
                arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(".mp4")]
                if arquivos:
                    random.shuffle(arquivos)
                    for arq in arquivos:
                        if len(temp_vids) >= num_videos_necessarios:
                            break
                        escolhido = os.path.join(pasta, arq)
                        # Evita duplicar vídeos que já estão na lista
                        if os.path.abspath(escolhido) not in vids_ja_usados:
                            logger.info(f"📂 [EMERGÊNCIA] Usando vídeo local: {escolhido}")
                            temp_vids.append(escolhido)
                            vids_ja_usados.add(os.path.abspath(escolhido))
                            
                            try:
                                from core.utils.contexto import registrar_contexto
                                registrar_contexto("plataforma_video", "Biblioteca Local")
                            except Exception as context_err:
                                logger.debug(f"Erro ao registrar contexto Local: {context_err}")
                    if len(temp_vids) >= num_videos_necessarios:
                        break

    if not temp_vids:
        raise Exception("❌ Nenhum vídeo disponível: Pexels falhou e biblioteca local está vazia.")

    logger.info("🎬 Processando vídeo com MoviePy + Pillow...")
    clip_candidatos = []
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, VideoClip, concatenate_videoclips
        
        # Carrega todos os clips baixados
        for fn in temp_vids:
            clip_candidatos.append(VideoFileClip(fn))
            
        if is_conquistador and slides:
            # ── SINCRONIZAÇÃO PERFEITA: cada vídeo dura exatamente o mesmo que seu slide de texto (Apenas Conquistador) ──
            total_s = len(slides)
            _dur_gancho = 5.0
            _tempo_slide = (duracao_necessaria_reels - _dur_gancho) / max(1, total_s - 1) if total_s > 1 else duracao_necessaria_reels
            _duracoes_por_slide = [_dur_gancho] + [_tempo_slide] * (total_s - 1)

            import moviepy.video.fx.all as _vfx_sync
            width_target  = min(c.w for c in clip_candidatos)
            height_target = min(c.h for c in clip_candidatos)

            clips_sincronizados = []
            for i in range(total_s):
                c = clip_candidatos[i % len(clip_candidatos)]  # cicla se a API retornar menos vídeos que slides
                dur_s = _duracoes_por_slide[i]
                # Faz loop no vídeo se ele for mais curto que a duração do slide
                if c.duration < dur_s:
                    c = c.fx(_vfx_sync.loop, duration=dur_s + 0.1)
                c_sub = c.subclip(0, dur_s)
                if c_sub.w != width_target or c_sub.h != height_target:
                    c_sub = c_sub.resize((width_target, height_target))
                clips_sincronizados.append(c_sub)

            if len(clips_sincronizados) > 1:
                clip = concatenate_videoclips(clips_sincronizados, method="compose")
            else:
                clip = clips_sincronizados[0]
            logger.info(f"✅ [SYNC] {len(clips_sincronizados)} segmentos sincronizados | gancho={_dur_gancho:.0f}s | slides={_tempo_slide:.1f}s cada")

        elif len(clip_candidatos) == 1:
            clip = clip_candidatos[0]
        else:
            logger.info(f"🔗 Concatendo {len(clip_candidatos)} vídeos diferentes com micro-cortes dinâmicos...")
            width_target = min(c.w for c in clip_candidatos)
            height_target = min(c.h for c in clip_candidatos)

            # Calcula a duração de corte por vídeo para cobrir toda a mensagem sem loops
            tempo_corte_por_video = max(5.0, duracao_necessaria_reels / len(clip_candidatos))

            clips_redimensionados = []
            for c in clip_candidatos:
                c_sub = c.subclip(0, min(c.duration, tempo_corte_por_video))
                if c_sub.w != width_target or c_sub.h != height_target:
                    clips_redimensionados.append(c_sub.resize((width_target, height_target)))
                else:
                    clips_redimensionados.append(c_sub)

            clip = concatenate_videoclips(clips_redimensionados, method="compose")
        
        # Controle de duração (agora usado para ambos: reels_leads e pexels_story)
        duracao_original = clip.duration
        logger.info(f"⏱️ Duração total dos vídeos baixados: {duracao_original:.1f}s | Necessário: {duracao_necessaria_reels:.0f}s")
        if duracao_original < duracao_necessaria_reels:
            # Só loopeia se ainda falta duração (último recurso)
            import moviepy.video.fx.all as vfx
            loops = int(duracao_necessaria_reels // duracao_original) + 1
            clip = clip.fx(vfx.loop, n=loops)
            logger.warning(f"⚠️ Vídeos baixados insuficientes ({duracao_original:.1f}s). Aplicando loop x{loops} como fallback.")
        
        duracao = min(clip.duration, duracao_necessaria_reels)
        clip = clip.subclip(0, duracao)
        
        # --- Carrega o vídeo final preparado pelo usuário se existir ---
        path_video_final = os.path.join("biblioteca_local", "logo", "video.mp4")
        if os.path.exists(path_video_final):
            try:
                logger.info(f"🎬 [Pexels Story] Carregando vídeo final de encerramento: {path_video_final}")
                outro_clip = VideoFileClip(path_video_final)
                w_target, h_target = clip.size
                if outro_clip.w != w_target or outro_clip.h != h_target:
                    try:
                        outro_clip = outro_clip.resized((w_target, h_target))
                    except AttributeError:
                        outro_clip = outro_clip.resize((w_target, h_target))
                outro_duracao = outro_clip.duration
                logger.info(f"🎬 Vídeo de encerramento carregado: {outro_duracao:.1f}s")
            except Exception as e_load_outro:
                logger.warning(f"⚠️ Não foi possível carregar vídeo final: {e_load_outro}")
                outro_clip = None
        
        # Padroniza a fonte BebasNeue.ttf em caixa alta para 100% dos vídeos da marca (garante legibilidade e identidade forte)
        estilo_do_dia = "BebasNeue.ttf"
        logger.info(f"✨ Fonte da marca padronizada: {estilo_do_dia}")
        
        # Resolução do vídeo original
        video_w, _ = clip.size
        # Fator de escala baseado na largura padrão de 1080
        fator_escala = video_w / 1080.0
        
        # Tamanhos proporcionais e maiores (aumento de base 86->96 e 72->80)
        tamanho_normal = max(60, int(96 * fator_escala))
        tamanho_cta = max(50, int(80 * fator_escala))
        
        fonte_normal = _carregar_fonte(tamanho=tamanho_normal, estilo=estilo_do_dia)
        fonte_cta    = _carregar_fonte(tamanho=tamanho_cta, estilo=estilo_do_dia)

        if slides:
            logger.info("✍️ Adicionando textos via Pillow (sem ImageMagick)...")
            total_slides = len(slides)
            idx_cta = total_slides - 1  # Última cena = CTA

            # Narração de voz removida do pexels_story_noite — usa apenas música de fundo
            caminho_narracao_story = None
            # Define o tempo de início exato de cada slide
            slide_start_times = [0.0] * (total_slides + 1)
            
            if is_story_tarde:
                tempo_por_slide = duracao / max(1, total_slides)
                t_atual = 0.0
                for i in range(total_slides):
                    slide_start_times[i] = t_atual
                    t_atual += tempo_por_slide
            elif is_reels_leads:
                # 3 slides divididos de forma equilibrada no vídeo de ~13-15s
                tempo_por_slide = duracao / max(1, total_slides)
                t_atual = 0.0
                for i in range(total_slides):
                    slide_start_times[i] = t_atual
                    t_atual += tempo_por_slide
            else:
                # Formatos padrão rápidos (Pexels Story Manhã, Noite, Conquistador): Gancho ágil de 3.5s
                duracao_gancho = min(3.5, duracao / max(1, total_slides))
                if total_slides > 1:
                    tempo_slide_normal = (duracao - duracao_gancho) / (total_slides - 1)
                else:
                    tempo_slide_normal = duracao
                    
                t_atual = 0.0
                for i in range(total_slides):
                    slide_start_times[i] = t_atual
                    if i == 0:
                        t_atual += duracao_gancho
                    else:
                        t_atual += tempo_slide_normal
            
            slide_start_times[total_slides] = duracao

            # Efeito visual de marca: GARANTE escurecimento e tom dark gold/amber para NUNCA ter vídeos claros estourados
            efeitos_marca = ["warm_amber", "dark_gold_neon", "vignette_dark"]
            efeito_escolhido = random.choice(efeitos_marca)
            logger.info(f"🟠 Filtro de marca exclusivo aplicado: {efeito_escolhido.upper()}")

            # Para o Conquistador: usa animação sequencial pré-definida; demais formatos: sorteio aleatório
            if is_conquistador and animacao_conquistador:
                animacao = animacao_conquistador
                logger.info(f"🎬 [CONQUISTADOR] Animação sequencial: {animacao.upper()}")
            else:
                animacoes_disponiveis = ["typewriter", "fade", "reveal", "static"]
                animacao = random.choice(animacoes_disponiveis)
                logger.info(f"🎬 Animação de texto selecionada: {animacao.upper()}")




            def _desenhar_elementos_marca(frame_array, fator_escala=1.0, is_cta=False, t_slide=0.0, idx_slide_atual=0):
                """
                Desenha a marca d'água permanente no rodapé do frame (foto_perfil.png).
                """
                img = Image.fromarray(frame_array).convert("RGBA")
                w, h = img.size
                logo_dir = os.path.join("biblioteca_local", "logo")

                # ── Helper: aplica logo com opacidade total ──────────────────
                def _colar_logo(path_img, largura_px, y_offset_px):
                    if not path_img or not os.path.exists(path_img):
                        return False
                    try:
                        logo_img = Image.open(path_img).convert("RGBA")
                        aspect = logo_img.height / logo_img.width
                        altura_px = int(largura_px * aspect)
                        logo_res = logo_img.resize((largura_px, altura_px), Image.Resampling.LANCZOS)
                        x_pos = int((w - largura_px) / 2)
                        y_pos = h - altura_px - y_offset_px
                        img.paste(logo_res, (x_pos, y_pos), logo_res)
                        return True
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao colar imagem '{path_img}': {e}")
                        return False

                # ── Marca d'água permanente (foto_perfil.png em todos os slides) ──
                path_logo_rodape = os.path.join(logo_dir, "foto_perfil.png")
                largura_marca = max(140, int(280 * fator_escala))
                y_offset_marca = int(55 * fator_escala)

                marca_aplicada = _colar_logo(path_logo_rodape, largura_marca, y_offset_marca)

                # Fallback textual se a imagem da marca não estiver disponível
                if not marca_aplicada:
                    draw = ImageDraw.Draw(img)
                    tamanho_marca = max(22, int(36 * fator_escala))
                    fonte_rodape = _carregar_fonte(tamanho_marca, "Montserrat")
                    texto_marca = "GUSTAVO_8K_"
                    bb = draw.textbbox((0, 0), texto_marca, font=fonte_rodape)
                    tw = bb[2] - bb[0]
                    x_marca = (w - tw) // 2
                    y_marca = h - int(60 * fator_escala)
                    cor_brilho = (235, 160, 40, 50)
                    cor_sombra = (0, 0, 0, 200)
                    cor_texto  = (250, 185, 55, 255)
                    for ox in [-2, -1, 0, 1, 2]:
                        for oy in [-2, -1, 0, 1, 2]:
                            if ox != 0 or oy != 0:
                                draw.text((x_marca + ox, y_marca + oy), texto_marca, font=fonte_rodape, fill=cor_brilho)
                    draw.text((x_marca + 2, y_marca + 2), texto_marca, font=fonte_rodape, fill=cor_sombra)
                    draw.text((x_marca, y_marca), texto_marca, font=fonte_rodape, fill=cor_texto)

                return np.array(img.convert("RGB"))

            def make_frame(t):
                # Busca dinamicamente qual slide corresponde ao tempo t exato
                idx = 0
                for i in range(total_slides):
                    if slide_start_times[i] <= t < slide_start_times[i + 1]:
                        idx = i
                        break
                else:
                    idx = total_slides - 1
                t_slide = t - slide_start_times[idx]
                duracao_do_slide = slide_start_times[idx + 1] - slide_start_times[idx]
                    
                texto_completo = slides[idx]
                
                # SLIDE 0 (CAPA/GANCHO) e ÚLTIMO SLIDE (CTA): sempre estáticos para garantir leitura
                if idx == 0 or idx == idx_cta:
                    chars_to_show = None
                    fade_alpha = 1.0
                    deslocamento_y = 0
                else:
                    # Inicializa variáveis padrão
                    chars_to_show = None
                    fade_alpha = 1.0
                    deslocamento_y = 0
                    
                    # Executa a lógica de cada animação
                    if animacao == "typewriter":
                        # Termina a digitação 1.5 segundos antes do fim do slide para tempo de leitura
                        tempo_ativo = max(1.0, duracao_do_slide - 1.5)
                        progresso = min(t_slide / tempo_ativo, 1.0)
                        chars_to_show = int(progresso * len(texto_completo))
                    elif animacao == "fade":
                        # Esmaecimento suave nos primeiros 0.8s com curva Ease-Out
                        prog_linear = min(1.0, t_slide / 0.8)
                        fade_alpha = 1.0 - (1.0 - prog_linear) ** 2
                    elif animacao == "reveal":
                        # Revelação suave (fade + subida fluida de baixo para cima nos primeiros 0.8s com Ease-Out)
                        prog_linear = min(1.0, t_slide / 0.8)
                        ease_out = 1.0 - (1.0 - prog_linear) ** 2
                        fade_alpha = ease_out
                        deslocamento_y = int(20 * (1.0 - ease_out) * fator_escala)
                    # "static" mantém fade_alpha=1.0, deslocamento_y=0 e chars_to_show=None
                
                frame = clip.get_frame(t)
                frame = _aplicar_efeito_cinematico(frame, efeito_escolhido)

                if idx == idx_cta and (is_reels_leads or is_story_tarde):
                    # Reels Leads & Story Tarde: Degradê colorido nas letras + SABEDORIA por cima
                    # Normaliza \\n literal → \n real
                    texto_cta_norm = texto_completo.replace("\\n", "\n")
                    paleta_cta = paleta_reels_leads if is_reels_leads else PALETA_PADRAO_MARCA
                    cor_kw = (0, 230, 118) if is_story_tarde else None  # Verde Esmeralda/Neon no Story Tarde, Dourado no Reels Leads
                    frame = _adicionar_texto_cta(
                        frame, texto_cta_norm, fonte_cta,
                        chars_to_show=chars_to_show, fade_alpha=fade_alpha, deslocamento_y=deslocamento_y,
                        paleta_override=paleta_cta, cor_keyword=cor_kw
                    )
                elif idx == idx_cta:
                    # Pexels Story e Conquistador: Mantém o degradê da marca até o último frame do vídeo
                    frame = _adicionar_texto_degrade(
                        frame, texto_completo, fonte_cta,
                        chars_to_show=chars_to_show, fade_alpha=fade_alpha,
                        deslocamento_y=deslocamento_y, paleta=PALETA_PADRAO_MARCA
                    )
                else:
                    # Slides de corpo do vídeo: Reels Leads usa sua paleta exclusiva alternada; demais usam a paleta da marca
                    paleta_aplicada = paleta_reels_leads if is_reels_leads else PALETA_PADRAO_MARCA
                    frame = _adicionar_texto_degrade(
                        frame, texto_completo, fonte_normal,
                        chars_to_show=chars_to_show, fade_alpha=fade_alpha,
                        deslocamento_y=deslocamento_y, paleta=paleta_aplicada
                    )
                
                # Desenha o Selo foto_perfil.png no topo, a Marca d'água no rodapé e o efeito de brilho no CTA
                frame = _desenhar_elementos_marca(frame, fator_escala, is_cta=(idx == idx_cta), t_slide=t_slide, idx_slide_atual=idx)
                # Garante que o frame retornado e sempre uint8 (evita erro 'Cannot handle this data type: <i8')
                if isinstance(frame, np.ndarray) and frame.dtype != np.uint8:
                    frame = np.clip(frame, 0, 255).astype(np.uint8)
                return frame

            final_clip = VideoClip(make_frame, duration=duracao)
            final_clip = final_clip.set_fps(clip.fps or 24)
        else:
            final_clip = clip

        # Acopla o clipe final preparado pelo usuário se existir
        if outro_clip is not None:
            try:
                final_clip = concatenate_videoclips([final_clip, outro_clip], method="compose")
                logger.info("✅ Vídeo de encerramento acoplado no pexels_story!")
            except Exception as e_outro_concat:
                logger.warning(f"⚠️ Erro ao acoplar o vídeo de encerramento: {e_outro_concat}")

        # Adicionar áudio de fundo
        try:
            from core.media.reels import garantir_audio_reels
            import moviepy.audio.fx.all as afx
            audio_path = garantir_audio_reels()
            if audio_path:
                bg_audio = AudioFileClip(audio_path)
                duracao_total_video = final_clip.duration
                # Loop no áudio se for menor que a duração total do vídeo
                if bg_audio.duration < duracao_total_video:
                    bg_audio = afx.audio_loop(bg_audio, duration=duracao_total_video)
                    
                bg_audio = bg_audio.subclip(0, duracao_total_video)

                # Sem narração: apenas música de fundo
                final_clip = final_clip.set_audio(bg_audio)
                logger.info("🎵 Áudio de fundo adicionado!")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao adicionar áudio de fundo: {e}")

        logger.info(f"⚙️ Exportando vídeo final para {caminho_saida}...")
        # Para reels_leads (até 3 min), limita o bitrate para ~3000kbps
        # Isso gera ~67MB para 3 minutos — bem abaixo do limite do catbox.moe (200MB).
        # Sem limitação, o ultrafast preset pode gerar 300-500MB e o upload falha com 412.
        write_kwargs = dict(
            fps=24, codec="libx264",
            audio_codec="aac", logger=None, threads=4, preset="ultrafast"
        )
        if is_reels_leads:
            write_kwargs["bitrate"] = "3000k"
            logger.info("📦 [reels_leads] Bitrate limitado a 3000kbps para manter o arquivo abaixo de 100MB.")
        final_clip.write_videofile(caminho_saida, **write_kwargs)
        return caminho_saida

    except Exception as e:
        logger.warning(f"⚠️ Erro ao processar o vídeo: {e}.")
        # Libera os arquivos
        try:
            if clip: clip.close()
            if final_clip: final_clip.close()
            if bg_audio: bg_audio.close()
            if outro_clip: outro_clip.close()
            for c in clip_candidatos:
                try: c.close()
                except: pass
        except: pass
        raise e
    finally:
        # Limpeza final
        try:
            if clip:
                clip.close()
        except:
            pass
        try:
            if final_clip:
                final_clip.close()
        except:
            pass
        try:
            if bg_audio:
                bg_audio.close()
        except:
            pass
        try:
            if outro_clip:
                outro_clip.close()
        except:
            pass
        try:
            if 'audio_narracao_clip' in locals() and audio_narracao_clip:
                audio_narracao_clip.close()
        except:
            pass
        # Fecha todos os sub-clipes individuais
        for c in clip_candidatos:
            try:
                c.close()
            except:
                pass
        # Apaga todos os arquivos baixados temporariamente
        for fn in temp_vids:
            if os.path.exists(fn):
                try:
                    os.remove(fn)
                except Exception as clean_err:
                    logger.debug(f"Não foi possível remover arquivo temporário {fn}: {clean_err}")
