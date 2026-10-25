#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
O Fio de Ouro - Gerador de PDF via Terminal (VersÃ£o Ultra-Polida)
Produzido com Zelo, FÃ© e PropÃ³sito.
AparÃªncia e cores 100% fiÃ©is Ã  versÃ£o Web!
"""

import os
import sys
import subprocess
import urllib.request

# --- Auto-instalaÃ§Ã£o da biblioteca ReportLab ---
try:
    import reportlab
except ImportError:
    print("\033[93m[+] Biblioteca 'reportlab' nÃ£o encontrada. Tentando instalar automaticamente...\033[0m")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
        import reportlab
        print("\033[92m[+] Biblioteca 'reportlab' instalada com sucesso!\033[0m\n")
    except Exception as e:
        print(f"\033[91m[-] Erro ao instalar 'reportlab': {e}\033[0m")
        print("\033[93mPor favor, instale manualmente usando o terminal: pip install reportlab\033[0m")
        sys.exit(1)

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import Color, HexColor
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, NextPageTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, KeepInFrame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- ConfiguraÃ§Ã£o de Cores e TransparÃªncia Estilo Web ---

def get_color(hex_or_rgba, alpha=None):
    """
    Retorna um objeto Color do ReportLab aceitando hex ou strings rgba.
    Garante suporte completo a opacidade (alpha).
    """
    if isinstance(hex_or_rgba, Color):
        return hex_or_rgba
    hex_or_rgba = hex_or_rgba.strip()
    if hex_or_rgba.startswith("rgba"):
        parts = hex_or_rgba.replace("rgba(", "").replace(")", "").split(",")
        r = float(parts[0].strip()) / 255.0
        g = float(parts[1].strip()) / 255.0
        b = float(parts[2].strip()) / 255.0
        a = float(parts[3].strip()) if len(parts) > 3 else 1.0
        return Color(r, g, b, a)
    elif hex_or_rgba.startswith("rgb"):
        parts = hex_or_rgba.replace("rgb(", "").replace(")", "").split(",")
        r = float(parts[0].strip()) / 255.0
        g = float(parts[1].strip()) / 255.0
        b = float(parts[2].strip()) / 255.0
        return Color(r, g, b, 1.0)
    else:
        c = HexColor(hex_or_rgba)
        if alpha is not None:
            return Color(c.red, c.green, c.blue, alpha)
        return c

# --- Download e Registro de Fontes: Sans (capa/bento) + Serif Editorial (capÃ­tulos) ---

def load_fonts():
    """
    Carrega DOIS conjuntos de fontes:
    1. font_map      â€” Inter + SpaceGrotesk (sans): para a CAPA e o BENTO (pÃ¡gina 2). Preservado.
    2. font_map_e    â€” Playfair Display + EB Garamond (serif editorial): para os CAPÃTULOS.
    """
    font_dir = os.path.join(os.path.expanduser("~"), ".fio_de_ouro_fonts")
    try:
        os.makedirs(font_dir, exist_ok=True)
    except Exception:
        font_dir = os.path.join(os.getcwd(), ".fonts")
        os.makedirs(font_dir, exist_ok=True)

    fonts_to_download = {
        # --- Sans (capa e bento) ---
        "Inter-Regular":    "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter-Regular.ttf",
        "Inter-Bold":       "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter-Bold.ttf",
        "Inter-Italic":     "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter-Italic.ttf",
        "SpaceGrotesk-Bold":"https://github.com/google/fonts/raw/main/ofl/spacegrotesk/static/SpaceGrotesk-Bold.ttf",
        # --- Serif editorial (capÃ­tulos) ---
        "PlayfairDisplay-Regular": "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Regular.ttf",
        "PlayfairDisplay-Bold":    "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Bold.ttf",
        "PlayfairDisplay-Italic":  "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Italic.ttf",
        "EBGaramond-Regular": "https://github.com/google/fonts/raw/main/ofl/ebgaramond/static/EBGaramond-Regular.ttf",
        "EBGaramond-Bold":    "https://github.com/google/fonts/raw/main/ofl/ebgaramond/static/EBGaramond-Bold.ttf",
        "EBGaramond-Italic":  "https://github.com/google/fonts/raw/main/ofl/ebgaramond/static/EBGaramond-Italic.ttf",
    }

    registered = {}
    for name, url in fonts_to_download.items():
        dest = os.path.join(font_dir, f"{name}.ttf")
        if not os.path.exists(dest):
            try:
                print(f"   â†“ Baixando fonte: {name}...")
                urllib.request.urlretrieve(url, dest)
            except Exception:
                pass
        if os.path.exists(dest):
            try:
                pdfmetrics.registerFont(TTFont(name, dest))
                registered[name] = True
            except Exception:
                pass

    # â”€â”€ Font Map 1: Sans â€” capa e bento (Inter / SpaceGrotesk) â”€â”€
    font_map_sans = {
        "sans":         "Inter-Regular"    if "Inter-Regular"    in registered else "Helvetica",
        "sans-bold":    "Inter-Bold"       if "Inter-Bold"       in registered else "Helvetica-Bold",
        "sans-italic":  "Inter-Italic"     if "Inter-Italic"     in registered else "Helvetica-Oblique",
        "display-bold": "SpaceGrotesk-Bold" if "SpaceGrotesk-Bold" in registered else "Helvetica-Bold",
        "display":      "SpaceGrotesk-Bold" if "SpaceGrotesk-Bold" in registered else "Helvetica-Bold",
        "display-italic": "Inter-Italic"   if "Inter-Italic"     in registered else "Helvetica-Oblique",
    }

    # â”€â”€ Font Map 2: Serif Editorial â€” capÃ­tulos (Playfair Display + EB Garamond) â”€â”€
    has_playfair = "PlayfairDisplay-Regular" in registered
    has_garamond = "EBGaramond-Regular" in registered
    font_map_edit = {
        "sans":          "EBGaramond-Regular"   if has_garamond  else "Times-Roman",
        "sans-bold":     "EBGaramond-Bold"      if has_garamond  else "Times-Bold",
        "sans-italic":   "EBGaramond-Italic"    if has_garamond  else "Times-Italic",
        "display-bold":  "PlayfairDisplay-Bold"    if has_playfair else "Times-Bold",
        "display":       "PlayfairDisplay-Regular" if has_playfair else "Times-Roman",
        "display-italic":"PlayfairDisplay-Italic"  if has_playfair else "Times-Italic",
    }

    return font_map_sans, font_map_edit

# Carrega ambos os mapas de fontes globalmente
# font_map    â†’ usado na capa e no bento (Inter/SpaceGrotesk â€” inalterado)
# font_map_e  â†’ usado nos capÃ­tulos (Playfair Display + EB Garamond â€” editorial)
font_map, font_map_e = load_fonts()


# --- FunÃ§Ãµes de Desenho e Helpers de Layout ---


def draw_image_cover(canvas, img_path, x, y, dest_w, dest_h, mask='auto'):
    """Desenha uma imagem como 'object-fit: cover': amplia e centraliza cortando as bordas
    para que o destino seja preenchido SEM distorÃ§Ã£o da imagem."""
    from PIL import Image as PILImage
    try:
        with PILImage.open(img_path) as pil_img:
            src_w, src_h = pil_img.size
    except Exception:
        src_w, src_h = 800, 500  # fallback seguro

    scale = max(dest_w / src_w, dest_h / src_h)
    scaled_w = src_w * scale
    scaled_h = src_h * scale

    # Calcula o offset de centralizaÃ§Ã£o (clipagem)
    offset_x = x - (scaled_w - dest_w) / 2
    offset_y = y - (scaled_h - dest_h) / 2

    canvas.saveState()
    # Cria uma mÃ¡scara de recorte para evitar que a imagem vaze para fora da Ã¡rea
    clip = canvas.beginPath()
    clip.rect(x, y, dest_w, dest_h)
    canvas.clipPath(clip, stroke=0, fill=0)
    canvas.drawImage(img_path, offset_x, offset_y, width=scaled_w, height=scaled_h,
                     preserveAspectRatio=False, mask=mask)
    canvas.restoreState()

def draw_page_gradient(canvas, color1=None, color2=None):
    canvas.saveState()
    canvas.linearGradient(0, 841.89, 0, 0, [get_color("#1A1818"), get_color("#1A1818")])
    canvas.restoreState()

def draw_gradient_round_rect(canvas, x, y, width, height, rx, ry, color1, color2, border_color=None):
    """Desenha um Bento Card arredondado e preenchido com gradiente linear na diagonal."""
    canvas.saveState()
    path = canvas.beginPath()
    path.roundRect(x, y, width, height, rx)
    canvas.clipPath(path, stroke=1 if border_color else 0, fill=0)
    canvas.linearGradient(x, y + height, x + width, y, [get_color(color1), get_color(color2)])
    canvas.restoreState()
    
    if border_color:
        canvas.saveState()
        canvas.setStrokeColor(get_color(border_color))
        canvas.setLineWidth(1)
        canvas.roundRect(x, y, width, height, rx, stroke=1, fill=0)
        canvas.restoreState()

def draw_card_decorations(canvas, card_type, x, y, width, height):
    """Insere padrÃµes geomÃ©tricos elegantes e sutis simulando os Ã­cones da interface Web."""
    canvas.saveState()
    canvas.setStrokeColor(Color(1, 1, 1, 0.08))
    canvas.setFillColor(Color(1, 1, 1, 0.04))
    canvas.setLineWidth(1.5)
    
    if card_type == "nevoa":  # UsuÃ¡rios/FamÃ­lia
        cx1, cy1 = x + width - 35, y + 45
        cx2, cy2 = x + width - 55, y + 38
        canvas.circle(cx1, cy1, 16, stroke=1, fill=1)
        canvas.circle(cx2, cy2, 12, stroke=1, fill=1)
        
    elif card_type == "solucao":  # Ãcone de CoraÃ§Ã£o / UniÃ£o
        cx, cy = x + width - 55, y + height / 2
        path = canvas.beginPath()
        path.moveTo(cx, cy - 15)
        path.curveTo(cx - 15, cy + 10, cx - 30, cy - 5, cx, cy - 35)
        path.curveTo(cx + 30, cy - 5, cx + 15, cy + 10, cx, cy - 15)
        canvas.drawPath(path, stroke=1, fill=1)
        
    elif card_type == "proposito":  # Escudo de ProteÃ§Ã£o
        cx, cy = x + width - 35, y + 35
        path = canvas.beginPath()
        path.moveTo(cx, cy + 18)
        path.lineTo(cx - 15, cy + 18)
        path.lineTo(cx - 15, cy + 2)
        path.lineTo(cx, cy - 13)
        path.lineTo(cx + 15, cy + 2)
        path.lineTo(cx + 15, cy + 18)
        path.close()
        canvas.drawPath(path, stroke=1, fill=1)
        
    canvas.restoreState()

def draw_thin_divider(canvas, y, x_start=None, x_end=None, color="#d4af37", alpha=0.5, thickness=0.7):
    """Desenha uma linha fina horizontal elegante â€” marca registrada do estilo editorial."""
    page_w = 595.27
    margin = 54
    if x_start is None:
        x_start = margin
    if x_end is None:
        x_end = page_w - margin
    canvas.saveState()
    c = get_color(color)
    canvas.setStrokeColor(Color(c.red, c.green, c.blue, alpha))
    canvas.setLineWidth(thickness)
    canvas.line(x_start, y, x_end, y)
    canvas.restoreState()

def draw_chapter_header(canvas, subtitle, title, subtitle_color="#d4af37"):
    """Cabeçalho editorial:
       label pequeno em tracking largo + linha fina + título grande em Playfair Display."""
    canvas.saveState()
    page_w = 595.27
    margin_h = 54
    text_w = page_w - 2 * margin_h
    
    # --- Label superior (ex: CAPÃ TULO 1) em tracking largo ---
    label_style = ParagraphStyle(
        name=f"chap_label_{hash(subtitle)}",
        fontName=font_map_e["sans-bold"],   # EB Garamond Bold
        fontSize=7.5,
        leading=11,
        textColor=get_color(subtitle_color),
        alignment=TA_CENTER,
        charSpace=4,
    )
    p_lbl = Paragraph(subtitle.upper(), label_style)
    lw, lh = p_lbl.wrap(text_w, 20)
    lbl_y = 800
    p_lbl.drawOn(canvas, margin_h, lbl_y)
    
    # --- Linha divisÃ³ria fina dourada ---
    divider_y = lbl_y - 6
    draw_thin_divider(canvas, divider_y, x_start=margin_h + 80, x_end=page_w - margin_h - 80,
                      color="#d4af37", alpha=0.6, thickness=0.6)
    
    # --- TÃ­tulo Principal â€” Playfair Display Bold ---
    font_size = 28
    if len(title) > 30:
        font_size = 24
    if len(title) > 45:
        font_size = 20

    cap_title_style = ParagraphStyle(
        name=f"chap_title_{hash(title)}",
        fontName=font_map_e["display-bold"],   # Playfair Display Bold
        fontSize=font_size,
        leading=font_size + 7,
        textColor=get_color("#ffffff"),
        alignment=TA_CENTER,
        spaceBefore=8,
    )
    
    if title:
        p_title = Paragraph(title, cap_title_style)
        tw, th = p_title.wrap(text_w, 150)
        p_title.drawOn(canvas, margin_h, divider_y - 12 - th)
    
    canvas.restoreState()

def draw_page_number(canvas, page_num, total_paginas=7):
    """Insere o nÃºmero de pÃ¡gina com opacidade e elegÃ¢ncia."""
    canvas.saveState()
    canvas.setFont(font_map_e["sans"], 8)   # EB Garamond para nÃºmero de pÃ¡gina
    canvas.setFillColor(Color(1, 1, 1, 0.35))
    canvas.setStrokeColor(Color(1, 1, 1, 0.15))
    canvas.setLineWidth(0.5)
    canvas.line(250, 48, 345, 48)
    canvas.drawCentredString(297.63, 34, f"{page_num} / {total_paginas}")
    canvas.restoreState()

def draw_text_in_rect(canvas, title, paragraphs, x, y, width, height, title_font_size=16, body_font_size=10, has_highlight=False, has_italic_box=False):
    """Formata e desenha com precisÃ£o cirÃºrgica blocos de textos e caixas destacadas dentro dos Bento Cards."""
    canvas.saveState()
    
    # Title style
    title_style = ParagraphStyle(
        name=f"title_{x}_{y}",
        fontName=font_map["sans-bold"],
        fontSize=title_font_size,
        leading=title_font_size + 3,
        textColor=get_color("#ffffff"),
        spaceAfter=10
    )
    
    # Body style
    body_style = ParagraphStyle(
        name=f"body_{x}_{y}",
        fontName=font_map["sans"],
        fontSize=body_font_size,
        leading=body_font_size + 3,
        textColor=get_color("#eff6ff"),
        spaceAfter=8
    )
    
    # Custom rendering for Card 1 (A NÃ©voa) with the highlight box at the bottom
    if has_highlight:
        # Title
        title_p = Paragraph(title, title_style)
        w, h = title_p.wrap(width - 24, height)
        title_p.drawOn(canvas, x + 12, y + height - 15 - h)
        
        # Paragraph 1
        p1_style = ParagraphStyle(
            name=f"p1_{x}_{y}",
            fontName=font_map["sans"],
            fontSize=body_font_size - 0.5,
            leading=body_font_size + 2.5,
            textColor=get_color("#eff6ff")
        )
        p1_p = Paragraph(paragraphs[0], p1_style)
        w1, h1 = p1_p.wrap(width - 24, height)
        p1_p.drawOn(canvas, x + 12, y + height - 15 - h - 10 - h1)
        
        # Highlight Box at the bottom
        box_padding = 10
        box_x = x + 12
        box_y = y + 15
        box_w = width - 24
        box_h = 105
        
        canvas.saveState()
        canvas.setFillColor(get_color("rgba(255,255,255,0.15)"))
        canvas.roundRect(box_x, box_y, box_w, box_h, 12, stroke=0, fill=1)
        canvas.restoreState()
        
        # Paragraph 2 (Highlight text inside the rounded rect)
        hl_style = ParagraphStyle(
            name=f"hl_{x}_{y}",
            fontName=font_map["sans-bold"],
            fontSize=body_font_size - 0.5,
            leading=body_font_size + 2,
            textColor=get_color("#ffffff")
        )
        p2_p = Paragraph(paragraphs[1], hl_style)
        w2, h2 = p2_p.wrap(box_w - 2 * box_padding, box_h - 2 * box_padding)
        # Center the text vertically inside the highlight box
        text_y = box_y + (box_h - h2) / 2
        p2_p.drawOn(canvas, box_x + box_padding, text_y)
        
    elif has_italic_box:
        # Italic box fica fixa no rodapÃ© do card (Card 4)
        box_padding = 8
        box_x = x + 12
        box_h = 55
        box_y = y + 15
        box_w = width - 24
        area_topo_bottom = box_y + box_h + 8  # Limite inferior do texto (topo da caixa itÃ¡lica)
        
        # 1. Desenha o TÃ­tulo no topo do card
        # Se o tÃ­tulo for longo (mais de 28 caracteres), ajusta a fonte para nÃ£o empurrar o texto
        effective_title_font_size = title_font_size
        if len(title) > 28:
            effective_title_font_size = title_font_size - 2
        if len(title) > 40:
            effective_title_font_size = title_font_size - 3.5

        card_title_style = ParagraphStyle(
            name=f"title_c4_{x}_{y}",
            fontName=font_map["sans-bold"],
            fontSize=effective_title_font_size,
            leading=effective_title_font_size + 3,
            textColor=get_color("#ffffff"),
            spaceAfter=6
        )
        
        title_p = Paragraph(title, card_title_style)
        w_title, h_title = title_p.wrap(width - 24, height)
        title_top_y = y + height - 15
        title_p.drawOn(canvas, x + 12, title_top_y - h_title)
        
        title_bottom_y = title_top_y - h_title
        
        # 2. ParÃ¡grafo 1 â€” posicionado estritamente ABAIXO do tÃ­tulo
        max_p_height = title_bottom_y - 6 - area_topo_bottom
        
        # Ajusta fonte do corpo se o espaÃ§o for muito apertado
        curr_body_font_size = body_font_size
        if max_p_height < 45:
            curr_body_font_size = body_font_size - 1.5

        c4_body_style = ParagraphStyle(
            name=f"body_c4_{x}_{y}",
            fontName=font_map["sans"],
            fontSize=curr_body_font_size,
            leading=curr_body_font_size + 2.5,
            textColor=get_color("#eff6ff")
        )
        
        p1_p = Paragraph(paragraphs[0], c4_body_style)
        w1, h1 = p1_p.wrap(width - 24, max(max_p_height, 20))
        
        # Desenha o texto logo abaixo do tÃ­tulo
        draw_y1 = title_bottom_y - 6 - h1
        # Se ultrapassar o topo da caixa itÃ¡lica, fixa no limite e previne subir sobre o tÃ­tulo
        if draw_y1 < area_topo_bottom:
            draw_y1 = area_topo_bottom
            
        p1_p.drawOn(canvas, x + 12, draw_y1)
        
        # 3. Caixa ItÃ¡lica fixa no rodapÃ©
        canvas.saveState()
        canvas.setFillColor(get_color("rgba(255,255,255,0.08)"))
        canvas.setStrokeColor(get_color("rgba(255,255,255,0.15)"))
        canvas.setLineWidth(1)
        canvas.roundRect(box_x, box_y, box_w, box_h, 10, stroke=1, fill=1)
        canvas.restoreState()
        
        box_text_style = ParagraphStyle(
            name=f"box_text_{x}_{y}",
            fontName=font_map["sans-italic"],
            fontSize=body_font_size - 1,
            leading=body_font_size + 1.5,
            textColor=get_color("#ffffff"),
            alignment=TA_CENTER
        )
        p2_p = Paragraph(paragraphs[1], box_text_style)
        w2, h2 = p2_p.wrap(box_w - 2 * box_padding, box_h - 2 * box_padding)
        text_y = box_y + (box_h - h2) / 2
        p2_p.drawOn(canvas, box_x + box_padding, text_y)
        
    else:
        # General layout for Card 2 & 3 â€” com limite inferior para evitar overflow
        bottom_limit = y + 14  # Nunca escreve abaixo da borda inferior do card
        current_y = y + height - 15
        
        title_p = Paragraph(title, title_style)
        w, h = title_p.wrap(width - 24, height)
        title_p.drawOn(canvas, x + 12, current_y - h)
        current_y -= (h + 10)
        
        for p_text in paragraphs:
            if current_y <= bottom_limit + 10:
                break  # Para de escrever se chegou no fundo do card
            available = current_y - bottom_limit
            p = Paragraph(p_text, body_style)
            w_p, h_p = p.wrap(width - 24, available)
            # Se o parÃ¡grafo nÃ£o cabe, nÃ£o desenha
            if current_y - h_p < bottom_limit:
                break
            p.drawOn(canvas, x + 12, current_y - h_p)
            current_y -= (h_p + 8)
            
    canvas.restoreState()

def draw_page_1_content(canvas, doc):
    """Gera o layout visual completo da PÃ¡gina 1 (Bento Grid com ProporÃ§Ãµes Perfeitas)."""
    conteudo = getattr(doc, "conteudo", None)
    
    titulo = "O Fio de Ouro."
    subtitulo = "Um Resgate Familiar."
    cards = []
    
    page_width = 595.27
    page_height = 841.89

    if conteudo:
        titulo = conteudo.get("titulo_pdf", titulo)
        subtitulo = conteudo.get("subtitulo_pdf", subtitulo)
        cards = conteudo.get("capa_cards", [])
        

    # 1. TÃ­tulo e subtÃ­tulo com Paragraph para suportar quebra de linha automÃ¡tica
    canvas.saveState()
    margin_h = 40
    text_width = page_width - 2 * margin_h
    
    font_size = 38
    if len(titulo) > 25:
        font_size = 32
    if len(titulo) > 35:
        font_size = 26
    if len(titulo) > 45:
        font_size = 22

    titulo_style = ParagraphStyle(
        name="cover_title",
        fontName=font_map["display-bold"],
        fontSize=font_size,
        leading=font_size + 6,
        textColor=get_color("#ffffff"),
        alignment=TA_CENTER
    )
    subtitulo_style = ParagraphStyle(
        name="cover_subtitle",
        fontName=font_map["sans-bold"],
        fontSize=18,
        leading=24,
        textColor=get_color("#dbeafe"),
        alignment=TA_CENTER
    )
    
    titulo_p = Paragraph(titulo, titulo_style)
    tw, th = titulo_p.wrap(text_width, 200)
    
    subtitulo_p = Paragraph(subtitulo, subtitulo_style)
    sw, sh = subtitulo_p.wrap(text_width, 100)
    
    # Posiciona o bloco tÃ­tulo+subtÃ­tulo no TOPO da pÃ¡gina
    top_margin = 54
    page_height = 841.89
    # O topo do tÃ­tulo comeÃ§a em (page_height - top_margin), o drawOn recebe o y do canto inferior
    titulo_bottom = page_height - top_margin - th
    subtitulo_bottom = titulo_bottom - sh - 8
    
    titulo_p.drawOn(canvas, margin_h, titulo_bottom)
    subtitulo_p.drawOn(canvas, margin_h, subtitulo_bottom)
    canvas.restoreState()
    
    # 2. ConfiguraÃ§Ãµes de DimensÃ£o do Bento Grid (A4: 595.27 x 841.89)
    left_margin = 40
    gap = 16
    col_w = 161.09
    double_col_w = col_w * 2 + gap # 338.18
    grid_height = 380
    row_h = 182.0
    grid_y = 176.0
    
    # --- Card 1: A Nevoa ---
    c1_x = left_margin
    c1_y = grid_y
    c1_title = cards[0]["titulo"] if len(cards) > 0 else "A Nevoa"
    if len(cards) > 0:
        c1_text = cards[0].get("texto", "")
        c1_pergunta = cards[0].get("pergunta_destaque", "Voce sente que esta perdendo os melhores anos do convivio?")
        c1_paragraphs = [c1_text, c1_pergunta]
    else:
        c1_paragraphs = [
            "Sob o mesmo teto, mas a quilometros de distancia. A rotina exaustiva, as telas sempre acesas e as preocupacoes tem roubado o dialogo e o afeto.",
            "Voce sente que esta perdendo os melhores anos da sua familia para a correria implacavel? O distanciamento invisivel transforma lares em abrigos de passagem."
        ]
    
    draw_gradient_round_rect(canvas, c1_x, c1_y, col_w, grid_height, 18, 18, "#1e3a5f", "#111111", border_color="rgba(255,255,255,0.15)")
    draw_card_decorations(canvas, "nevoa", c1_x, c1_y, col_w, grid_height)
    draw_text_in_rect(canvas, c1_title, c1_paragraphs, c1_x, c1_y, col_w, grid_height, title_font_size=18, body_font_size=10, has_highlight=True)
    
    # --- Card 2: A Solucao ---
    c2_x = left_margin + col_w + gap
    c2_y = grid_y + row_h + gap
    c2_title = cards[1]["titulo"] if len(cards) > 1 else "A Solucao"
    c2_paragraphs = [cards[1]["texto"]] if len(cards) > 1 else [
        "A verdadeira solucao nao esta em focar apenas em mais provisao material. A resposta exige uma atitude corajosa, simples e profunda: tempo de qualidade e intencionalidade.",
        "E preciso resgatar a presenca ativa e tecer novamente os fios que mantem o amor inabalavel."
    ]
    draw_gradient_round_rect(canvas, c2_x, c2_y, double_col_w, row_h, 18, 18, "#1e3a5f", "#111111", border_color="rgba(255,255,255,0.15)")
    draw_card_decorations(canvas, "solucao", c2_x, c2_y, double_col_w, row_h)
    draw_text_in_rect(canvas, c2_title, c2_paragraphs, c2_x, c2_y, double_col_w, row_h, title_font_size=18, body_font_size=10)
    
    # --- Card 3: O Proposito ---
    c3_x = c2_x
    c3_y = grid_y
    c3_title = cards[2]["titulo"] if len(cards) > 2 else "O Proposito"
    c3_paragraphs = [cards[2]["texto"]] if len(cards) > 2 else [
        "Onde antes reinava o silencio, a paz verdadeira se instaura, forjada no fogo das provacoes e guiada pela uniao."
    ]
    draw_gradient_round_rect(canvas, c3_x, c3_y, col_w, row_h, 18, 18, "#1e3a5f", "#111111", border_color="rgba(255,255,255,0.15)")
    draw_card_decorations(canvas, "proposito", c3_x, c3_y, col_w, row_h)
    draw_text_in_rect(canvas, c3_title, c3_paragraphs, c3_x, c3_y, col_w, row_h, title_font_size=16, body_font_size=10)
    
    # --- Card 4: A Verdade ---
    c4_x = c3_x + col_w + gap
    c4_y = grid_y
    c4_title = cards[3]["titulo"] if len(cards) > 3 else "A Verdade"
    if len(cards) > 3:
        c4_text = cards[3].get("texto", "")
        c4_citacao = cards[3].get("citacao_destaque", '"Onde colocamos nosso tempo, ali ancoramos nosso coracao."')
        c4_paragraphs = [c4_text, c4_citacao]
    else:
        c4_paragraphs = [
            "O amor exige presenca no campo de batalha da rotina.",
            "\"Onde colocamos nosso tempo, ali ancoramos nosso coracao.\""
        ]
    draw_gradient_round_rect(canvas, c4_x, c4_y, col_w, row_h, 18, 18, "#3b82f6", "#111111", border_color="rgba(255,255,255,0.15)")
    draw_text_in_rect(canvas, c4_title, c4_paragraphs, c4_x, c4_y, col_w, row_h, title_font_size=16, body_font_size=10, has_italic_box=True)

# --- Callback Master de Planos de Fundo (Gradients Exatos da Web) ---

def draw_cover_image_page(canvas, doc):
    """Renderiza a PÃ¡gina 1 exclusiva com moldura luxuosa tipo quadro, logo e subtÃ­tulo/tÃ­tulo dinÃ¢mico."""
    page_width = 595.27
    page_height = 841.89
    conteudo = getattr(doc, "conteudo", None) or {}

    # Caminho absoluto baseado na localizaÃ§Ã£o deste arquivo
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(base_dir, "biblioteca_local", "logo", "foto_perfil.png")

    # 1. Fundo preto absoluto elegante para a capa
    canvas.saveState()
    canvas.setFillColorRGB(0.10, 0.09, 0.09)
    canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    # 2. Desenha Moldura Dupla Dourada (Estilo Quadro de Luxo)
    m_out = 24
    canvas.setStrokeColor(get_color("#d97706"))
    canvas.setLineWidth(1.5)
    canvas.rect(m_out, m_out, page_width - 2 * m_out, page_height - 2 * m_out)

    m_in = 30
    canvas.setStrokeColor(get_color("#fbbf24"))
    canvas.setLineWidth(0.6)
    canvas.rect(m_in, m_in, page_width - 2 * m_in, page_height - 2 * m_in)

    # Cantos ornamentados nos 4 vÃ©rtices
    c_len = 12
    for x, y, dx, dy in [
        (m_in, m_in, 1, 1),
        (page_width - m_in, m_in, -1, 1),
        (m_in, page_height - m_in, 1, -1),
        (page_width - m_in, page_height - m_in, -1, -1)
    ]:
        canvas.setLineWidth(1.2)
        canvas.line(x, y, x + dx * c_len, y)
        canvas.line(x, y, x, y + dy * c_len)

    canvas.restoreState()

    # 3. Frase Inspiradora Refinada no Topo (acima da logo)
    frase_topo = conteudo.get("frase_topo_capa") or "SABEDORIA QUE TRANSFORMA DESTINOS"
    frase_topo = frase_topo.strip().upper()
    
    canvas.saveState()
    margin_h = 50
    text_width = page_width - 2 * margin_h

    topo_style = ParagraphStyle(
        name="cover_quote_top",
        fontName=font_map.get("display-bold", font_map["sans-bold"]),
        fontSize=12,
        leading=16,
        textColor=get_color("#fbbf24"),
        alignment=TA_CENTER
    )

    p_topo = Paragraph(f"✦ &nbsp; {frase_topo} &nbsp; ✦", topo_style)
    tw, th = p_topo.wrap(text_width, 60)
    p_topo.drawOn(canvas, margin_h, page_height - 115)
    canvas.restoreState()

    # 4. Emblema da Marca (foto_perfil.png) centralizado harmonicamente
    if os.path.exists(logo_path):
        try:
            canvas.saveState()
            logo_size = 350
            logo_x = (page_width - logo_size) / 2
            logo_y = (page_height - logo_size) / 2 + 15
            canvas.drawImage(logo_path, logo_x, logo_y, width=logo_size, height=logo_size, mask='auto', preserveAspectRatio=True)
            canvas.restoreState()
        except Exception as e_capa:
            print(f"⚠️  Aviso: Não foi possível renderizar a capa com foto_perfil.png: {e_capa}")
    else:
        print(f"⚠️  Aviso: foto_perfil.png não encontrada em: {logo_path}")

    # 5. Selo da Marca abaixo do Emblema
    canvas.saveState()
    tagline_style = ParagraphStyle(
        name="cover_tagline",
        fontName=font_map["sans-bold"],
        fontSize=11,
        leading=14,
        textColor=get_color("#d97706"),
        alignment=TA_CENTER
    )

    p_tagline = Paragraph("CODIGO DA SABEDORIA • EDICAO SEMANAL", tagline_style)
    gw, gh = p_tagline.wrap(text_width, 40)
    p_tagline.drawOn(canvas, margin_h, 110)

    canvas.restoreState()

# --- Templates Dinâmicos Substituindo numeração rígida de páginas ---
def get_total_pages(doc):
    c = getattr(doc, "conteudo", None)
    caps = c.get("capitulos", []) if c else []
    return len(caps) + 5 if len(caps) > 0 else 10

def draw_bg_capa(canvas, doc):
    draw_cover_image_page(canvas, doc)

def draw_bg_bento(canvas, doc):
    page_width, page_height = canvas._pagesize
    conteudo = getattr(doc, "conteudo", None) or {}
    img_path = conteudo.get("img_local_capa")
    
    # Desenha imagem de fundo na página 2 se existir, senão usa gradiente
    import os
    if img_path and os.path.exists(str(img_path)):
        try:
            draw_image_cover(canvas, img_path, 0, 0, page_width, page_height)
            
            # Máscara escura para contraste dos cards
            canvas.saveState()
            canvas.setFillColor(Color(0, 0, 0, alpha=0.68))
            canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
            canvas.restoreState()
        except Exception:
            draw_page_gradient(canvas, "#22d3ee", "#3b82f6")
    else:
        draw_page_gradient(canvas, "#22d3ee", "#3b82f6")
        
    draw_page_1_content(canvas, doc)
    draw_page_number(canvas, canvas.getPageNumber(), get_total_pages(doc))

def draw_bg_capitulo(canvas, doc, idx_cap):
    page_width, page_height = canvas._pagesize
    conteudo = getattr(doc, "conteudo", None)
    capitulos = conteudo.get("capitulos", []) if conteudo else []
    cap_num = idx_cap + 1
    cap_title = capitulos[idx_cap].get("titulo", f"Capítulo {cap_num}") if idx_cap < len(capitulos) else f"Título do Capítulo {cap_num}"
    img_path = capitulos[idx_cap].get("img_local") if idx_cap < len(capitulos) else None
    
    # IMPORTANTE: A lib os pode não estar importada no escopo se usarmos lambda, entao referenciamos direto
    import os
    has_image = img_path and os.path.exists(str(img_path))
    is_split = (idx_cap % 2 == 0)

    if has_image and is_split:
        SPLIT_X = 258
        canvas.saveState()
        canvas.setFillColor(Color(0.10, 0.09, 0.09))
        canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
        canvas.restoreState()
        try:
            draw_image_cover(canvas, img_path, 0, 0, SPLIT_X, page_height)
            canvas.saveState()
            canvas.setFillColor(Color(0, 0, 0, alpha=0.30))
            canvas.rect(0, 0, SPLIT_X, page_height, fill=1, stroke=0)
            canvas.restoreState()
        except Exception as _e:
            canvas.saveState()
            canvas.setFillColor(Color(0.10, 0.09, 0.09))
            canvas.rect(0, 0, SPLIT_X, page_height, fill=1, stroke=0)
            canvas.restoreState()
        
        canvas.saveState()
        canvas.setStrokeColor(get_color("#d4af37"))
        canvas.setLineWidth(0.8)
        canvas.line(SPLIT_X, 28, SPLIT_X, page_height - 28)
        canvas.restoreState()
        
        canvas.saveState()
        available_w = page_width - SPLIT_X - 30
        text_x = SPLIT_X + 16
        
        # Label editorial: tracking largo, dourado, caixa alta
        label_style = ParagraphStyle(
            name=f"SplitLbl_{cap_num}",
            fontName=font_map_e["sans-bold"],   # EB Garamond Bold
            fontSize=7.5,
            leading=10,
            textColor=get_color("#d4af37"),
            charSpace=3,
        )
        # TÃ­tulo em Playfair Display â€” grande e dramÃ¡tico
        fs_title = 22
        if len(cap_title) > 30: fs_title = 18
        if len(cap_title) > 45: fs_title = 15
        title_style = ParagraphStyle(
            name=f"SplitTtl_{cap_num}",
            fontName=font_map_e["display-bold"],   # Playfair Display Bold
            fontSize=fs_title,
            leading=fs_title + 6,
            textColor=get_color("#ffffff"),
        )
        
        lbl_y = page_height - 52
        p_lbl = Paragraph(f"CAPÃ TULO {cap_num}", label_style)
        lw, lh = p_lbl.wrap(available_w, 20)
        p_lbl.drawOn(canvas, text_x, lbl_y)
        
        # Linha divisÃ³ria fina dourada sob o label
        div_y = lbl_y - 6
        draw_thin_divider(canvas, div_y, x_start=text_x, x_end=text_x + available_w * 0.7,
                          color="#d4af37", alpha=0.55, thickness=0.6)
        
        p_ttl = Paragraph(cap_title, title_style)
        tw, th = p_ttl.wrap(available_w, 130)
        p_ttl.drawOn(canvas, text_x, div_y - 12 - th)
        canvas.restoreState()

    elif has_image and not is_split:
        try:
            draw_image_cover(canvas, img_path, 0, 0, page_width, page_height)
        except Exception:
            canvas.saveState()
            canvas.setFillColor(Color(0.10, 0.09, 0.09))
            canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
            canvas.restoreState()
        canvas.saveState()
        canvas.setFillColor(Color(0, 0, 0, alpha=0.68))
        canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
        canvas.restoreState()
        draw_chapter_header(canvas, f"CapÃ­tulo {cap_num}", cap_title, subtitle_color="#d4af37")
    else:
        canvas.saveState()
        canvas.setFillColor(Color(0.10, 0.09, 0.09))
        canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
        canvas.restoreState()
        draw_chapter_header(canvas, f"CapÃ­tulo {cap_num}", cap_title, subtitle_color="#d4af37")

    draw_page_number(canvas, canvas.getPageNumber(), get_total_pages(doc))

def draw_bg_fechamento(canvas, doc):
    draw_page_gradient(canvas, "#0f172a", "#172554")
    conteudo = getattr(doc, "conteudo", None)
    titulo_citacao = conteudo.get("titulo_citacao", "A Verdade InabalÃ¡vel") if conteudo else "A Verdade InabalÃ¡vel"
    draw_chapter_header(canvas, titulo_citacao, "", subtitle_color="#bfdbfe")
    draw_page_number(canvas, canvas.getPageNumber(), get_total_pages(doc))

def draw_bg_plano(canvas, doc):
    draw_page_gradient(canvas, "#6366f1", "#141414")
    draw_page_number(canvas, canvas.getPageNumber(), get_total_pages(doc))
    
    # Custom badge plano de acao
    draw_gradient_round_rect(canvas, 54, 735, 42, 42, 10, 10, "#60a5fa", "#6366f1")
    canvas.saveState()
    canvas.setStrokeColor(get_color("#ffffff"))
    canvas.setLineWidth(1.5)
    cx, cy = 54 + 21, 735 + 21
    canvas.circle(cx, cy, 8, stroke=1, fill=0)
    canvas.circle(cx, cy, 3, stroke=1, fill=0)
    canvas.restoreState()

def draw_bg_oferta(canvas, doc):
    """Pagina final exclusiva: CTA + cupom SABEDORIA30 + link clicavel."""
    page_width  = 595.27
    page_height = 841.89

    # 1. Fundo escuro elegante
    canvas.saveState()
    canvas.setFillColorRGB(0.10, 0.09, 0.09)
    canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    canvas.restoreState()

    # 2. Moldura dupla dourada (igual a capa)
    m_out = 24
    canvas.saveState()
    canvas.setStrokeColor(get_color("#d97706"))
    canvas.setLineWidth(1.5)
    canvas.rect(m_out, m_out, page_width - 2 * m_out, page_height - 2 * m_out)
    m_in = 30
    canvas.setStrokeColor(get_color("#fbbf24"))
    canvas.setLineWidth(0.6)
    canvas.rect(m_in, m_in, page_width - 2 * m_in, page_height - 2 * m_in)
    c_len = 12
    for cx_c, cy_c, dx, dy in [
        (m_in, m_in, 1, 1),
        (page_width - m_in, m_in, -1, 1),
        (m_in, page_height - m_in, 1, -1),
        (page_width - m_in, page_height - m_in, -1, -1)
    ]:
        canvas.setLineWidth(1.2)
        canvas.line(cx_c, cy_c, cx_c + dx * c_len, cy_c)
        canvas.line(cx_c, cy_c, cx_c, cy_c + dy * c_len)
    canvas.restoreState()

    margin = 46
    text_w = page_width - 2 * margin

    # 3. Label superior discreto e elegante
    label_style = ParagraphStyle(
        name="oferta_label",
        fontName=font_map_e["sans-bold"],
        fontSize=8,
        leading=11,
        textColor=get_color("#d4af37"),
        alignment=TA_CENTER,
        charSpace=2,
    )
    p_lbl = Paragraph("LEITORES DO CODIGO DA SABEDORIA", label_style)
    lw, lh = p_lbl.wrap(text_w, 20)
    lbl_y = page_height - 52
    p_lbl.drawOn(canvas, margin, lbl_y)

    div_y = lbl_y - 6
    draw_thin_divider(canvas, div_y, x_start=margin + 40, x_end=page_width - margin - 40,
                      color="#d4af37", alpha=0.5, thickness=0.6)

    # 4. Titulo e Subtitulo sutis
    titulo_style = ParagraphStyle(
        name="oferta_titulo",
        fontName=font_map_e["display-bold"],
        fontSize=24,
        leading=28,
        textColor=get_color("#ffffff"),
        alignment=TA_CENTER,
    )
    subtitulo_style = ParagraphStyle(
        name="oferta_subtitulo",
        fontName=font_map_e["sans-italic"],
        fontSize=10,
        leading=14,
        textColor=get_color("#d4af37"),
        alignment=TA_CENTER,
    )
    p_titulo = Paragraph("Codigo da Sabedoria", titulo_style)
    tw, th = p_titulo.wrap(text_w, 40)
    titulo_y = div_y - 10 - th
    p_titulo.drawOn(canvas, margin, titulo_y)

    p_sub = Paragraph("Uma descoberta nos bastidores para quem chegou ate o final", subtitulo_style)
    sw, sh = p_sub.wrap(text_w, 20)
    sub_y = titulo_y - 4 - sh
    p_sub.drawOn(canvas, margin, sub_y)

    # 5. Texto de Contexto Sutil
    intro_style = ParagraphStyle(
        name="oferta_intro",
        fontName=font_map_e["sans"],
        fontSize=8.5,
        leading=11.5,
        textColor=get_color("#d1d5db"),
        alignment=TA_CENTER,
    )
    intro_texto = (
        "Se voce chegou ate aqui, provavelmente procura mais do que apenas informacao. "
        "Existe um metodo que reune <b>estrategia + inteligencia artificial</b> criado para ajudar voce a pensar "
        "melhor em cada abordagem, mesmo que nunca tenha vendido nada pela internet. Nada teorico: tudo pratico, "
        "replicavel e guiado por um copiloto inteligente."
    )
    p_intro = Paragraph(intro_texto, intro_style)
    iw, ih = p_intro.wrap(text_w, 60)
    intro_y = sub_y - 8 - ih
    p_intro.drawOn(canvas, margin, intro_y)

    # 6. Card de Oportunidade / Beneficios
    benef_x = margin
    benef_h = 138
    benef_y = intro_y - 8 - benef_h
    benef_w = text_w

    canvas.saveState()
    canvas.setFillColor(get_color("rgba(255,255,255,0.03)"))
    canvas.setStrokeColor(get_color("rgba(212,175,55,0.25)"))
    canvas.setLineWidth(0.8)
    canvas.roundRect(benef_x, benef_y, benef_w, benef_h, 8, stroke=1, fill=1)
    canvas.restoreState()

    benef_head_style = ParagraphStyle(
        name="benef_head",
        fontName=font_map_e["sans-bold"],
        fontSize=9.5,
        leading=13,
        textColor=get_color("#fbbf24"),
    )
    benef_item_style = ParagraphStyle(
        name="benef_item",
        fontName=font_map_e["sans"],
        fontSize=8.5,
        leading=11.5,
        textColor=get_color("#e5e7eb"),
    )

    p_bh = Paragraph("O que voce encontra la dentro:", benef_head_style)
    bhw, bhh = p_bh.wrap(benef_w - 24, 20)
    cy_b = benef_y + benef_h - 10 - bhh
    p_bh.drawOn(canvas, benef_x + 12, cy_b)
    cy_b -= 6

    beneficios_lista = [
        "✦ <b>Metodo estruturado</b> testado em mais de 100.000 vendas reais.",
        "✦ <b>Copiloto de IA</b> para criacao, analise e validacao de abordagens.",
        "✦ <b>Scripts e estrategias praticas</b> para diferentes situacoes do dia a dia.",
        "✦ <b>Orientacao passo a passo</b> para testar e melhorar sua comunicacao.",
        "✦ <b>7 dias para conhecer</b> o metodo por dentro sem nenhum risco.",
    ]
    for b_text in beneficios_lista:
        pb_item = Paragraph(b_text, benef_item_style)
        bw_i, bh_i = pb_item.wrap(benef_w - 24, 20)
        cy_b -= bh_i
        pb_item.drawOn(canvas, benef_x + 12, cy_b)
        cy_b -= 3.5

    # 7. Card do Cupom Exclusivo
    cup_h = 92
    cup_y = benef_y - 8 - cup_h
    cup_x = margin
    cup_w = text_w

    draw_gradient_round_rect(canvas, cup_x, cup_y, cup_w, cup_h, 10, 10,
                             "#1a1200", "#2d1f00", border_color="#d4af37")
    canvas.saveState()
    canvas.setStrokeColor(get_color("#fbbf24"))
    canvas.setLineWidth(0.8)
    canvas.roundRect(cup_x + 2, cup_y + 2, cup_w - 4, cup_h - 4, 8, stroke=1, fill=0)
    canvas.restoreState()

    cupom_code_style = ParagraphStyle(
        name="cupom_code",
        fontName=font_map["display-bold"],
        fontSize=20,
        leading=24,
        textColor=get_color("#fbbf24"),
        alignment=TA_CENTER,
        charSpace=4,
    )
    p_code = Paragraph("SABEDORIA30", cupom_code_style)
    cw_c, ch_c = p_code.wrap(cup_w - 20, 30)
    code_y = cup_y + cup_h - 10 - ch_c
    p_code.drawOn(canvas, cup_x + 10, code_y)

    cupom_sub_style = ParagraphStyle(
        name="cupom_sub",
        fontName=font_map_e["sans"],
        fontSize=8.5,
        leading=11.5,
        textColor=get_color("#e8d5a0"),
        alignment=TA_CENTER,
    )
    desc_cupom = (
        "Este cupom concede <b>30% de desconto</b> — exclusivo para voce que baixa o "
        "<b>CODIGO DA SABEDORIA • EDICAO SEMANAL</b>. Uma condicao especial vinculada a esta edicao."
    )
    p_desc_cup = Paragraph(desc_cupom, cupom_sub_style)
    dw_c, dh_c = p_desc_cup.wrap(cup_w - 24, 45)
    p_desc_cup.drawOn(canvas, cup_x + 12, cup_y + 8)

    # 8. CTA Chamativo e Botao de Acao
    cta_chamada_style = ParagraphStyle(
        name="cta_chamada_top",
        fontName=font_map_e["sans-bold"],
        fontSize=9.5,
        leading=13,
        textColor=get_color("#fbbf24"),
        alignment=TA_CENTER,
        charSpace=1.5,
    )
    p_cta_top = Paragraph("✦ &nbsp; DESBLOQUEIE SEU ACESSO COM 30% OFF &nbsp; ✦", cta_chamada_style)
    cw_top, ch_top = p_cta_top.wrap(text_w, 20)
    cta_top_y = cup_y - 10 - ch_top
    p_cta_top.drawOn(canvas, margin, cta_top_y)

    btn_margin_h = 45
    btn_x = margin + btn_margin_h
    btn_w = text_w - 2 * btn_margin_h
    btn_h = 38
    btn_y = cta_top_y - 6 - btn_h

    draw_gradient_round_rect(canvas, btn_x, btn_y, btn_w, btn_h, 8, 8,
                             "#d97706", "#92400e", border_color="#fbbf24")

    btn_style = ParagraphStyle(
        name="btn_text",
        fontName=font_map["sans-bold"],
        fontSize=12,
        leading=15,
        textColor=get_color("#ffffff"),
        alignment=TA_CENTER,
    )
    p_btn = Paragraph("VER OPORTUNIDADE", btn_style)
    bw_btn, bh_btn = p_btn.wrap(btn_w - 20, btn_h)
    btn_text_y = btn_y + (btn_h - bh_btn) / 2
    p_btn.drawOn(canvas, btn_x + 10, btn_text_y)

    # Link clicavel no PDF
    canvas.linkURL(
        "https://codigodasabedoria.onrender.com",
        (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h),
        relative=0
    )

    # URL e Acesso Imediato
    url_style = ParagraphStyle(
        name="url_label",
        fontName=font_map_e["sans"],
        fontSize=8,
        leading=11,
        textColor=get_color("rgba(255,255,255,0.40)"),
        alignment=TA_CENTER,
    )
    p_url = Paragraph("Acesso imediato apos a confirmacao • <u>codigodasabedoria.onrender.com</u>", url_style)
    uw, uh = p_url.wrap(text_w, 15)
    p_url.drawOn(canvas, margin, btn_y - 4 - uh)

    # 9. Rodape
    selos_y = btn_y - 4 - uh - 12
    selos_style = ParagraphStyle(
        name="selos",
        fontName=font_map_e["sans"],
        fontSize=8,
        leading=11,
        textColor=get_color("rgba(255,255,255,0.45)"),
        alignment=TA_CENTER,
    )
    p_selos = Paragraph(
        "7 dias para experimentar &nbsp;•&nbsp; Garantia de reembolso &nbsp;•&nbsp; Pagamento 100% seguro",
        selos_style
    )
    sw2, sh2 = p_selos.wrap(text_w, 15)
    p_selos.drawOn(canvas, margin, selos_y - sh2)

# --- ConstruÃ§Ã£o Principal do Story do Documento ---

def gerar_pdf(filename="O_Fio_de_Ouro_Restauracao.pdf", conteudo=None):
    # Margens do Documento via BaseDocTemplate
    doc = BaseDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    if conteudo:
        doc.conteudo = conteudo
    else:
        doc.conteudo = None
        
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    
    templates = [
        PageTemplate(id='Capa', frames=frame, onPage=draw_bg_capa),
        PageTemplate(id='Bento', frames=frame, onPage=draw_bg_bento),
        PageTemplate(id='Fechamento', frames=frame, onPage=draw_bg_fechamento),
        PageTemplate(id='PlanoAcao', frames=frame, onPage=draw_bg_plano),
        PageTemplate(id='Oferta', frames=frame, onPage=draw_bg_oferta),
    ]
    
    caps = conteudo.get("capitulos", []) if conteudo else []
    for i in range(len(caps) if len(caps) > 0 else 5):
        # A magia de criar uma funÃ§Ã£o lambda que "prende" o valor de idx no momento
        templates.append(
            PageTemplate(id=f'Capitulo_{i}', frames=frame, onPage=lambda c, d, idx=i: draw_bg_capitulo(c, d, idx))
        )
        
    # O primeiro template da lista Ã© o template inicial do documento (Capa)
    doc.addPageTemplates(templates)
        
    # ── Estilos de Texto Editoriais ──
    # Corpo principal: EB Garamond, generoso, bem respirado
    chapter_body_style = ParagraphStyle(
        name="ChapterBody",
        fontName=font_map_e["sans"],          # EB Garamond Regular
        fontSize=14.5,
        leading=22,
        textColor=get_color("#e8e4e0"),
        alignment=TA_JUSTIFY,
        spaceAfter=16,
        firstLineIndent=0,
    )
    
    # ItÃ¡lico dourado â€” citaÃ§Ãµes e passagens de destaque
    chapter_italic_style = ParagraphStyle(
        name="ChapterItalic",
        fontName=font_map_e["sans-italic"],  # EB Garamond Italic
        fontSize=14.5,
        leading=22,
        textColor=get_color("#c9a84c"),
        alignment=TA_JUSTIFY,
        spaceAfter=16,
        leftIndent=12,
        rightIndent=12,
    )
    
    # Estilo para pÃ¡ginas densas (mais conteÃºdo)
    page5_body_style = ParagraphStyle(
        name="Page5Body",
        parent=chapter_body_style,
        fontSize=14,
        leading=22,
        spaceAfter=18
    )
    
    # â”€â”€ Caixa de CitaÃ§Ã£o â€” estilo literÃ¡rio elegante â”€â”€
    quote_title_style = ParagraphStyle(
        name="QuoteTitle",
        fontName=font_map_e["display-bold"],   # Playfair Display Bold
        fontSize=18,
        leading=24,
        textColor=get_color("#ffffff"),
        alignment=TA_CENTER,
        spaceAfter=10,
        charSpace=1,
    )
    quote_text_style = ParagraphStyle(
        name="QuoteText",
        fontName=font_map_e["display-italic"],  # Playfair Display Italic
        fontSize=15,
        leading=23,
        textColor=get_color("#d4c5a0"),
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    bible_verse_style = ParagraphStyle(
        name="BibleVerse",
        fontName=font_map_e["sans-bold"],       # EB Garamond Bold
        fontSize=11,
        leading=16,
        textColor=get_color("#c9a84c"),
        alignment=TA_CENTER,
        charSpace=0.5,
    )
    
    story = []

    # ==================== PÃ GINA 1: CAPA COM IMAGEM ====================
    # O template 'Capa' Ã© o primeiro da lista, entÃ£o jÃ¡ Ã© aplicado na pÃ¡gina 1
    story.append(NextPageTemplate('Bento'))
    story.append(PageBreak())

    # ==================== PÃ GINA 2: BENTO GRID ====================
    # O Bento jÃ¡ estÃ¡ ativo. Adicionamos um Spacer e preparamos o Capitulo_0
    # como o template da PRÃ“XIMA pÃ¡gina antes de quebrar.
    story.append(Spacer(1, 10))
    story.append(NextPageTemplate('Capitulo_0'))  
    story.append(PageBreak())

    if conteudo:
        # --- MODO DINÃ‚MICO (GEMINI IA) ---
        capitulos = conteudo.get("capitulos", [])
        
        # ==================== PÃ GINAS DE CAPÃ TULOS ====================
        SPLIT_X = 258          # deve ser igual ao valor no canvas
        DOC_LEFT_MARGIN = 54   # leftMargin do doc
        # leftIndent dentro do story para alinhar texto ao painel direito
        SPLIT_LEFT_INDENT = (SPLIT_X + 16) - DOC_LEFT_MARGIN  # â‰ˆ 220 pt

        for i, cap in enumerate(capitulos):
            # O template Capitulo_{i} jÃ¡ estÃ¡ ativo na pÃ¡gina atual!
            
            img_path = cap.get("img_local")
            has_image = img_path and os.path.exists(str(img_path))
            is_split = (i % 2 == 0)
            paragrafos = cap.get("paragrafos", [])

            if has_image and is_split:
                # Layout A: texto deslocado para o painel direito (split com imagem)
                story.append(Spacer(1, 95))
                split_body = ParagraphStyle(
                    name=f"SplitBody_{i}",
                    fontName=font_map_e["sans"],          # EB Garamond Regular
                    fontSize=12.5,
                    leading=18,
                    textColor=get_color("#e8e4e0"),
                    alignment=TA_JUSTIFY,
                    spaceAfter=12,
                    leftIndent=0,
                    rightIndent=0
                )
                split_italic = ParagraphStyle(
                    name=f"SplitItalic_{i}",
                    parent=split_body,
                    fontName=font_map_e["sans-italic"],   # EB Garamond Italic
                    textColor=get_color("#c9a84c"),
                    leftIndent=6,
                    rightIndent=6,
                )
                # Largura da coluna direita (do SPLIT_X ate a margem direita)
                col_dir_w = doc.width - SPLIT_LEFT_INDENT
                # Altura disponivel apos o Spacer(95) e o cabecalho do canvas (~100pt)
                alt_disponivel = doc.height - 95 - 100
                items_split = []
                for p_idx, paragrafo in enumerate(paragrafos):
                    items_split.append(Paragraph(paragrafo, split_italic if p_idx == 1 else split_body))
                # KeepInFrame: conteudo nunca vaza para a proxima pagina
                kif_split = KeepInFrame(col_dir_w, alt_disponivel, items_split, mode='truncate')
                # Empurra o bloco para a coluna direita usando uma tabela de 2 colunas
                tabela_split = Table(
                    [[Spacer(SPLIT_LEFT_INDENT, 1), kif_split]],
                    colWidths=[SPLIT_LEFT_INDENT, col_dir_w]
                )
                from reportlab.platypus import TableStyle as TS
                tabela_split.setStyle(TS([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(tabela_split)

            else:
                # Layout B (full bg) ou fallback: texto flui com muito espaco
                story.append(Spacer(1, 120))
                use_small = len(paragrafos) >= 4 or sum(len(p) for p in paragrafos) > 600
                s_base = page5_body_style if use_small else chapter_body_style
                s_italic = ParagraphStyle(
                    name=f"Italic_{i}",
                    parent=s_base,
                    fontName=font_map_e["sans-italic"],   # EB Garamond Italic
                    textColor=get_color("#c9a84c"),
                    leftIndent=12,
                    rightIndent=12,
                )
                # Altura disponivel apos Spacer(120) e cabecalho do canvas (~100pt)
                alt_full = doc.height - 120 - 100
                items_full = []
                for p_idx, paragrafo in enumerate(paragrafos):
                    items_full.append(Paragraph(paragrafo, s_italic if p_idx == 1 else s_base))
                # KeepInFrame: conteudo nunca vaza para a proxima pagina
                story.append(KeepInFrame(doc.width, alt_full, items_full, mode='truncate'))


            # Define o template para a PRÃ“XIMA pÃ¡gina antes de quebrar
            if i < len(capitulos) - 1:
                story.append(NextPageTemplate(f'Capitulo_{i+1}'))
            else:
                story.append(NextPageTemplate('Fechamento'))
                
            story.append(PageBreak())
            
        # ==================== PÃ GINA DE CITAÃ‡ÃƒO & FECHAMENTO ====================
        # O template 'Fechamento' jÃ¡ estÃ¡ ativo.
        story.append(Spacer(1, 100))
        
        fechamento_texto = conteudo.get("fechamento", "")
        if fechamento_texto:
            p_fechamento_style = ParagraphStyle(
                name="FechamentoStyle",
                parent=chapter_body_style,
                fontSize=11.5,
                leading=17,
                spaceAfter=12
            )
            story.append(Paragraph(fechamento_texto, p_fechamento_style))
            story.append(Spacer(1, 10))
            
        # --- Bento Quote Box (CitaÃ§Ã£o de Destaque) ---
        citacao_texto = conteudo.get("citacao_destaque", "A restauraÃ§Ã£o genuÃ­na comeÃ§a no coraÃ§Ã£o.")
        titulo_citacao = conteudo.get("titulo_citacao", "A Verdade InabalÃ¡vel")
        
        verso_base = conteudo.get("verso_base", "Se o Senhor nÃ£o edificar a casa, em vÃ£o trabalham os que a edificam.")
        ref_verso = conteudo.get("referencia_verso", "Salmos 127:1")
        
        card_content = [
            [Paragraph(titulo_citacao, quote_title_style)],
            [Paragraph(f'"{citacao_texto}"', quote_text_style)],
            [Paragraph(f'"{verso_base}"<br/><font color="#ffffff" size="9"><b>&mdash; {ref_verso}</b></font>', bible_verse_style)]
        ]
        
        reflection_table = Table(card_content, colWidths=[460])
        reflection_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), get_color("rgba(15, 23, 42, 0.4)")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
            ('BOX', (0, 0), (-1, -1), 1, get_color("rgba(255, 255, 255, 0.15)")),
        ]))
        
        story.append(reflection_table)
        story.append(PageBreak())
        
        # ==================== PÃGINA DO PLANO DE AÃ‡ÃƒO ====================
        story.append(Spacer(1, 20)) # Pequena margem superior
        
        # Inserir imagem do plano se houver
        if conteudo.get("plano_acao", {}).get("img_local") and os.path.exists(conteudo["plano_acao"]["img_local"]):
            try:
                story.append(Image(conteudo["plano_acao"]["img_local"], width=460, height=200))
                story.append(Spacer(1, 20))
            except:
                pass
        
        plano = conteudo.get("plano_acao", {})
        plano_titulo = plano.get("titulo_secao", "Plano de AÃ§Ã£o DiÃ¡rio")
        plano_subtitulo = plano.get("subtitulo", "Aplique estes princÃ­pios na rotina para fortalecer os laÃ§os.")
        
        plan_title_style = ParagraphStyle(
            name="PlanTitle",
            fontName=font_map_e["display-bold"],
            fontSize=24,
            leading=28,
            textColor=get_color("#ffffff"),
            leftIndent=58,
            spaceAfter=4
        )
        plan_subtitle_style = ParagraphStyle(
            name="PlanSubtitle",
            fontName=font_map_e["sans"],
            fontSize=11,
            leading=15,
            textColor=get_color("#d4af37"), # text-purple-200
            leftIndent=58,
            spaceAfter=25
        )
        
        story.append(Paragraph(plano_titulo, plan_title_style))
        story.append(Paragraph(plano_subtitulo, plan_subtitle_style))
        
        # Estilos especÃ­ficos para a tabela estilizada do plano de aÃ§Ã£o
        item_title_style = ParagraphStyle(
            name="ItemTitle",
            fontName=font_map_e["sans-bold"],
            fontSize=12,
            leading=15,
            textColor=get_color("#ffffff"),
            spaceAfter=3
        )
        item_desc_style = ParagraphStyle(
            name="ItemDesc",
            fontName=font_map_e["sans"],
            fontSize=9.5,
            leading=14,
            textColor=get_color("#a1a1aa"), # text-purple-100
            alignment=TA_JUSTIFY
        )
        
        passos = plano.get("passos", [])
        
        badge_cores = [
            ("#d4af37", "rgba(212, 175, 55, 0.1)"),   # Passo 1
            ("#e5e7eb", "rgba(255, 255, 255, 0.05)"),   # Passo 2
            ("#9ca3af", "rgba(255, 255, 255, 0.05)"),   # Passo 3
            ("#d1d5db", "rgba(255, 255, 255, 0.05)")    # Passo 4
        ]
        
        plan_rows = []
        for p_idx, passo in enumerate(passos):
            num = str(passo.get("numero", p_idx + 1))
            title = passo.get("titulo", f"Passo {num}")
            desc = passo.get("descricao", "")
            
            text_color, bg_color = badge_cores[p_idx % len(badge_cores)]
            
            badge_style = ParagraphStyle(
                name=f"Badge_{num}",
                fontName=font_map_e["sans-bold"],
                fontSize=14,
                leading=18,
                textColor=get_color(text_color),
                backColor=get_color(bg_color),
                borderColor=get_color(text_color, 0.3),
                borderWidth=1,
                borderPadding=8,
                alignment=TA_CENTER
            )
            
            cell_num = Paragraph(num, badge_style)
            cell_text = [
                Paragraph(title, item_title_style),
                Paragraph(desc, item_desc_style)
            ]
            plan_rows.append([cell_num, cell_text])
            
        if not plan_rows:
            # Fallback seguro
            badge_style_fallback = ParagraphStyle(
                name="Badge_Fallback",
                fontName=font_map_e["sans-bold"],
                fontSize=14,
                leading=18,
                textColor=get_color("#3b82f6"),
                backColor=get_color("rgba(212, 175, 55, 0.1)"),
                borderPadding=8,
                alignment=TA_CENTER
            )
            plan_rows.append([Paragraph("1", badge_style_fallback), [Paragraph("Acao Inicial", item_title_style), Paragraph("Comece a agir hoje.", item_desc_style)]])
            
        plan_table = Table(plan_rows, colWidths=[46, 420])
        plan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), get_color("rgba(255, 255, 255, 0.06)")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 1, get_color("rgba(255, 255, 255, 0.08)")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, get_color("rgba(255, 255, 255, 0.04)")),
        ]))
        
        story.append(plan_table)
        story.append(Spacer(1, 35))
        
        # Assinatura de Rodape do Plano de Acao
        footer_style = ParagraphStyle(
            name="PlanFooter",
            fontName=font_map_e["sans-bold"],
            fontSize=10,
            leading=12,
            textColor=get_color("#d4af37"),
            alignment=TA_CENTER,
            spaceBefore=15
        )
        rodape_texto = conteudo.get("rodape", "PRODUZIDO COM ZELO, FE E PROPOSITO.")
        story.append(Paragraph(rodape_texto.upper(), footer_style))
        
    else:
        # --- MODO ESTATICO (FALLBACK ORIGINAL) ---
        # ==================== PAGINA 2 (Capitulo 1) ====================
        story.append(Spacer(1, 140))
        story.append(Paragraph(
            "Arthur olhou para o relogio: 23:45. A luz azulada do monitor era a unica coisa iluminando o escritorio. No andar de baixo, a casa estava em absoluto silencio. Um silencio que costumava significar paz, mas que agora parecia um abismo intransponivel.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "Ele fechou o notebook, esfregando os olhos cansados. Caminhando pelo corredor, passou pelo quarto de Lucas. O adolescente estava isolado com seus fones de ouvido, perdido em um mundo virtual vibrante, completamente alheio a quem passava pela porta. No quarto principal, Helena ja dormia, um livro caido sobre o peito, a respiracao compassada marcando o fim de mais um dia exaustivo.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "- Quando nos tornamos apenas colegas de quarto dividindo boletos? - pensou Arthur, cobrindo a esposa com sutileza e zelo, ajeitando o cobertor sobre seus ombros.",
            chapter_italic_style
        ))
        story.append(Paragraph(
            "Eles tinham a casa que sempre sonharam, a estabilidade pela qual tanto lutaram, mas a sensacao era de que haviam perdido a si mesmos no processo de conquistar o mundo la fora.",
            chapter_body_style
        ))
        story.append(NextPageTemplate('Capitulo_1'))
        story.append(PageBreak())
        
        # ==================== PAGINA 3 (Capitulo 2) ====================
        story.append(Spacer(1, 140))
        story.append(Paragraph(
            "Na manha seguinte, a cozinha parecia uma estacao de trem. 'Bons dias' apressados e mecanicos, cafe engolido de pe e olhos grudados em telas luminosas de smartphones. Era o caos organizado da familia moderna.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "- Helena - Arthur chamou suavemente, segurando sua caneca de cafe com as duas maos, interrompendo o fluxo automatico da rotina. - Voce se lembra da ultima vez que realmente conversamos? Nao sobre as contas da casa, ou as notas do Lucas, mas... sobre nos?",
            chapter_body_style
        ))
        story.append(Paragraph(
            "Helena parou, a torrada a meio caminho da boca. Ela olhou para Arthur. Realmente olhou para ele, prestando atencao em seus olhos, pela primeira vez em semanas. Os ombros dela cederam levemente sob o peso invisivel que carregava.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "- Sinto que estamos no mesmo barco, Arthur, mas remando em direcoes opostas com toda a nossa forca - ela admitiu, a voz ligeiramente tremula. - Nos estamos provendo tudo o que e material para eles. Tudo, exceto nos mesmos.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "Era a verdade dolorosa sendo exposta sob a luz do sol da manha. O espelho da familia 'perfeita', tao bem polido para quem via de fora pelas redes sociais, estava rachado por dentro, pedindo socorro.",
            chapter_body_style
        ))
        story.append(NextPageTemplate('Capitulo_2'))
        story.append(PageBreak())
        
        # ==================== PAGINA 4 (Capitulo 3) ====================
        story.append(Spacer(1, 140))
        story.append(Paragraph(
            "Naquela mesma noite, em vez de se trancar no home office logo apos o jantar, Arthur sentou-se no sofa da sala. Ele chamou Helena, segurando um livro antigo, de capa de couro levemente gasta pelas decadas.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "- Encontrei isso hoje nas minhas coisas de infancia - disse ele, passando os dedos sobre a capa. - Era do meu avo. Ele costumava me dizer que uma familia e como uma grande tapecaria. Se voce usar apenas fios comuns e rotineiros - trabalho, busca por dinheiro, obrigacoes - o tecido eventualmente cede e rasga sob a pressao da vida.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "Ele abriu na primeira pagina, onde havia uma dedicatoria escrita a mao. - Mas ele dizia que, se voce tecer um 'Fio de Ouro' por entre eles... a fe, a devocao a Deus, o perdao e a comunhao verdadeira... esse fio dourado fortalece a trama e mantem tudo unido, tornando o tecido inquebravel.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "Helena tocou a capa desgastada, os olhos marejados refletindo a luz fraca do abajur. - Temos usado fios muito frageis e baratos, nao e?",
            chapter_body_style
        ))
        story.append(Paragraph(
            "- Sim. Nos deixamos o Arquiteto e o Seu material de fora da nossa construcao - respondeu Arthur, segurando firme a mao dela. - Mas ainda ha tempo de corrigir a rota. Nos podemos comecar a tecer novamente. Hoje.",
            chapter_body_style
        ))
        story.append(NextPageTemplate('Capitulo_3'))
        story.append(PageBreak())
        
        # ==================== PAGINA 5 (Capitulo 4) ====================
        story.append(Spacer(1, 110))
        story.append(Paragraph(
            "A mudanca de rota nao aconteceu como magica em um passe de ilusionismo; ela foi intensamente intencional. E exigiu coragem para confrontar o desconforto.",
            page5_body_style
        ))
        story.append(Paragraph(
            "- Pessoal, reuniao de familia na sala. Agora mesmo. - Arthur anunciou em uma sexta-feira a noite, logo apos chegar do trabalho, caminhando ate o corredor e desconectando o roteador de internet da tomada.",
            page5_body_style
        ))
        story.append(Paragraph(
            "Lucas apareceu segundos depois, resmungando alto, seguido pela pequena Sofia, que arrastava sua boneca favorita de pano.",
            page5_body_style
        ))
        story.append(Paragraph(
            "- O que aconteceu? A internet caiu de vez no bairro? - Lucas cruzou os bracos, frustrado com a interrupcao de seu jogo.",
            page5_body_style
        ))
        story.append(Paragraph(
            "- Nao, filho - Helena sorriu com docura, sentando-se no tapete ao lado de Arthur. - Nos so estamos nos reconectando a uma rede muito melhor e infinitamente mais importante.",
            page5_body_style
        ))
        story.append(Paragraph(
            "Eles conversaram. No comeco, o silencio sem as telas como escudo foi constrangedor, quase palpavel. Mas entao, a represa se rompeu. Compartilharam seus medos diarios, sonhos engavetados e um longo e necessario pedido de desculpas. Arthur pediu perdao por sua ausencia fisica e mental. Helena pediu perdao por sua impaciencia continua, fruto do esgotamento.",
            page5_body_style
        ))
        story.append(Paragraph(
            "- Eu sentia falta de voces assim... perto - Lucas murmurou, olhando para o chao, deixando sua grossa armadura de adolescente cair por um momento revelador.",
            page5_body_style
        ))
        story.append(Paragraph(
            "Eles deram as maos em roda. Fizeram uma oracao simples, um pouco desajeitada pelo tempo sem pratica, mas profundamente honesta. Ali, naquela sala de estar, o Fio de Ouro estava finalmente passando pelo buraco estreito da agulha.",
            page5_body_style
        ))
        story.append(NextPageTemplate('Fechamento'))
        story.append(PageBreak())
        
        # ==================== PAGINA 6 (Capitulo 5 & Caixa de Destaque) ====================
        story.append(Spacer(1, 100))
        
        p5_style = ParagraphStyle(
            name="Cap5Style",
            parent=chapter_body_style,
            fontSize=11,
            leading=16,
            spaceAfter=10
        )
        
        story.append(Paragraph(
            "Meses depois daquela primeira noite sem internet, a casa respirava de outra forma. Nao havia se tornado um ambiente imune a falhas - ainda havia discussoes ocasionais pelo controle remoto e manhas pontuadas pelo caos dos horarios escolares - mas o silencio ensurdecedor e gelado havia desaparecido para sempre.",
            p5_style
        ))
        story.append(Paragraph(
            "Ele foi substituido por risadas espontaneas no corredor, jantares onde todos os celulares descansavam obrigatoriamente em uma pequena cesta de vime na cozinha, e um senso absoluto e profundo de pertencimento.",
            p5_style
        ))
        story.append(Paragraph(
            "Arthur e Helena aprenderam, na pratica exaustiva do dia a dia, que a familia nao e um belo trofeu de porcelana que se conquista e se coloca na estante da sala para impressionar as visitas e juntar poeira. A familia e um jardim vivo que requer cuidado intencional, cultivo diario, rega paciente e um zelo continuo para arrancar as ervas daninhas da indiferenca.",
            p5_style
        ))
        story.append(Paragraph(
            "Encostado no batente da porta, Arthur observava Helena correndo atras das criancas pelo quintal, sob a luz dourada reconfortante do fim de tarde. Seu peito transbordava de uma gratidao que o dinheiro de seu trabalho jamais poderia comprar.",
            p5_style
        ))
        
        story.append(Spacer(1, 10))
        
        card_content = [
            [Paragraph("A Verdade Inabalavel", quote_title_style)],
            [Paragraph('"A restauracao genuina de um lar comeca no exato momento em que reconhecemos que nossas proprias forcas sao insuficientes. Quando o orgulho humano cede o seu lugar a humildade, e a distracao da tela cede lugar ao foco no olhar do outro, Deus constroi fortalezas impenetraveis onde antes havia apenas ruinas."', quote_text_style)],
            [Paragraph('"Se o Senhor nao edificar a casa, em vao trabalham os que a edificam."<br/><font color="#ffffff" size="9"><b>- Salmos 127:1</b></font>', bible_verse_style)]
        ]
        
        reflection_table = Table(card_content, colWidths=[460])
        reflection_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), get_color("rgba(15, 23, 42, 0.4)")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
            ('BOX', (0, 0), (-1, -1), 1, get_color("rgba(255, 255, 255, 0.15)")),
        ]))
        
        story.append(reflection_table)
        story.append(NextPageTemplate('PlanoAcao'))
        story.append(PageBreak())
        
        # ==================== PAGINA FINAL (Plano de Acao Diario) ====================
        story.append(Spacer(1, 20))
        
        plan_title_style = ParagraphStyle(
            name="PlanTitle",
            fontName=font_map_e["display-bold"],
            fontSize=24,
            leading=28,
            textColor=get_color("#ffffff"),
            leftIndent=58,
            spaceAfter=4
        )
        plan_subtitle_style = ParagraphStyle(
            name="PlanSubtitle",
            fontName=font_map_e["sans"],
            fontSize=11,
            leading=15,
            textColor=get_color("#d4af37"),
            leftIndent=58,
            spaceAfter=25
        )
        
        story.append(Paragraph("Plano de Acao Diario", plan_title_style))
        story.append(Paragraph("Aplique estes principios na rotina para fortalecer os lacos e proteger seu lar.", plan_subtitle_style))
        
        item_title_style = ParagraphStyle(
            name="ItemTitle",
            fontName=font_map_e["sans-bold"],
            fontSize=12,
            leading=15,
            textColor=get_color("#ffffff"),
            spaceAfter=3
        )
        item_desc_style = ParagraphStyle(
            name="ItemDesc",
            fontName=font_map_e["sans"],
            fontSize=9.5,
            leading=14,
            textColor=get_color("#a1a1aa"),
            alignment=TA_JUSTIFY
        )
        
        items_data = [
            ("1", "#3b82f6", "rgba(212, 175, 55, 0.1)", "Alinhamento (A Oracao)", "Dedique 10 minutos hoje a noite para orarem juntos, de maos dadas. Agradecam e entreguem as preocupacoes e os desafios ao Criador."),
            ("2", "#a855f7", "rgba(168, 85, 247, 0.2)", "A Mesa da Comunhao", "Faca pelo menos uma refeicao diaria com todos da casa. Regra inegociavel: distracoes digitais e telas devem permanecer desligadas."),
            ("3", "#d946ef", "rgba(217, 70, 239, 0.2)", "Manual de Sabedoria", "Leia um capitulo do livro de Proverbios neste final de semana com sua familia, e discutam a aplicacao pratica para a semana."),
            ("4", "#6366f1", "rgba(99, 102, 241, 0.2)", "O Protocolo do Perdao", "Nunca permita que o sol se ponha ou va dormir guardando ressentimentos. Tenha a coragem de pedir perdao hoje por alguma ofensa.")
        ]
        
        plan_rows = []
        for num, text_color, bg_color, title, desc in items_data:
            badge_style = ParagraphStyle(
                name=f"Badge_{num}",
                fontName=font_map_e["sans-bold"],
                fontSize=14,
                leading=18,
                textColor=get_color(text_color),
                backColor=get_color(bg_color),
                borderColor=get_color(text_color, 0.3),
                borderWidth=1,
                borderPadding=8,
                alignment=TA_CENTER
            )
            cell_num = Paragraph(num, badge_style)
            cell_text = [
                Paragraph(title, item_title_style),
                Paragraph(desc, item_desc_style)
            ]
            plan_rows.append([cell_num, cell_text])
            
        plan_table = Table(plan_rows, colWidths=[46, 420])
        plan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), get_color("rgba(255, 255, 255, 0.06)")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 1, get_color("rgba(255, 255, 255, 0.08)")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, get_color("rgba(255, 255, 255, 0.04)")),
        ]))
        
        story.append(plan_table)
        story.append(Spacer(1, 35))
        
        footer_style = ParagraphStyle(
            name="PlanFooter",
            fontName=font_map_e["sans-bold"],
            fontSize=10,
            leading=12,
            textColor=get_color("#d4af37"),
            alignment=TA_CENTER,
            spaceBefore=15
        )
        story.append(Paragraph("PRODUZIDO COM ZELO, FE E PROPOSITO.", footer_style))
        
    # ==================== PAGINA FINAL: OFERTA / CTA (sempre presente) ====================
    story.append(NextPageTemplate('Oferta'))
    story.append(PageBreak())
    story.append(Spacer(1, 1))

    # --- Compilacao final usando BaseDocTemplate (PageTemplates) ---
    doc.build(story)

if __name__ == "__main__":
    print("\033[96m====================================================\033[0m")
    print("\033[1;92m   O Fio de Ouro - Gerador de PDF via Terminal\033[0m")
    print("\033[96m====================================================\033[0m")
    
    nome_arquivo = "O_Fio_de_Ouro_Restauracao.pdf"
    
    print(f"\033[94m[*] Iniciando a geracao do PDF: '{nome_arquivo}'...\033[0m")
    try:
        gerar_pdf(nome_arquivo)
        print("\n\033[1;92m[OK] PDF gerado com absoluto sucesso!\033[0m")
        print(f"\033[95m[->] Arquivo salvo em: {os.path.abspath(nome_arquivo)}\033[0m")
        print("\033[96m====================================================\033[0m")
    except Exception as err:
        print(f"\n\033[91m[-] Ocorreu um erro ao gerar o PDF: {err}\033[0m")
        import traceback
        traceback.print_exc()
        sys.exit(1)
