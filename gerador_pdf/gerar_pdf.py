#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
O Fio de Ouro - Gerador de PDF via Terminal (Versão Ultra-Polida)
Produzido com Zelo, Fé e Propósito.
Aparência e cores 100% fiéis à versão Web!
"""

import os
import sys
import subprocess
import urllib.request

# --- Auto-instalação da biblioteca ReportLab ---
try:
    import reportlab
except ImportError:
    print("\033[93m[+] Biblioteca 'reportlab' não encontrada. Tentando instalar automaticamente...\033[0m")
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Configuração de Cores e Transparência Estilo Web ---

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

# --- Download e Registro Dinâmico de Fontes Premium (Inter & Space Grotesk) ---

def load_fonts():
    """
    Tenta baixar as fontes originais do Google Fonts para manter a mesma
    identidade tipográfica da Web. Caso falhe, retorna fontes nativas como fallback.
    """
    font_dir = os.path.join(os.path.expanduser("~"), ".fio_de_ouro_fonts")
    try:
        os.makedirs(font_dir, exist_ok=True)
    except Exception:
        font_dir = os.path.join(os.getcwd(), ".fonts")
        os.makedirs(font_dir, exist_ok=True)
    
    fonts_to_download = {
        "Inter-Regular": "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter-Regular.ttf",
        "Inter-Bold": "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter-Bold.ttf",
        "Inter-Italic": "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter-Italic.ttf",
        "SpaceGrotesk-Bold": "https://github.com/google/fonts/raw/main/ofl/spacegrotesk/static/SpaceGrotesk-Bold.ttf"
    }
    
    registered = {}
    
    for name, url in fonts_to_download.items():
        dest = os.path.join(font_dir, f"{name}.ttf")
        if not os.path.exists(dest):
            try:
                # Baixa com timeout curto para não travar em conexões instáveis
                urllib.request.urlretrieve(url, dest)
            except Exception:
                pass
                
        if os.path.exists(dest):
            try:
                pdfmetrics.registerFont(TTFont(name, dest))
                registered[name] = True
            except Exception:
                pass
                
    # Retorna o mapeamento com fallback elegante para Helvetica
    font_map = {
        "sans": "Inter-Regular" if "Inter-Regular" in registered else "Helvetica",
        "sans-bold": "Inter-Bold" if "Inter-Bold" in registered else "Helvetica-Bold",
        "sans-italic": "Inter-Italic" if "Inter-Italic" in registered else "Helvetica-Oblique",
        "display-bold": "SpaceGrotesk-Bold" if "SpaceGrotesk-Bold" in registered else "Helvetica-Bold"
    }
    return font_map

# Carrega o mapa de fontes globalmente
font_map = load_fonts()

# --- Funções de Desenho e Helpers de Layout ---

def draw_page_gradient(canvas, color1, color2):
    """Aplica um gradiente vertical completo de fundo de página de forma homogênea."""
    canvas.saveState()
    canvas.linearGradient(0, 841.89, 0, 0, [get_color(color1), get_color(color2)])
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
    """Insere padrões geométricos elegantes e sutis simulando os ícones da interface Web."""
    canvas.saveState()
    canvas.setStrokeColor(Color(1, 1, 1, 0.08))
    canvas.setFillColor(Color(1, 1, 1, 0.04))
    canvas.setLineWidth(1.5)
    
    if card_type == "nevoa":  # Usuários/Família
        cx1, cy1 = x + width - 35, y + 45
        cx2, cy2 = x + width - 55, y + 38
        canvas.circle(cx1, cy1, 16, stroke=1, fill=1)
        canvas.circle(cx2, cy2, 12, stroke=1, fill=1)
        
    elif card_type == "solucao":  # Ícone de Coração / União
        cx, cy = x + width - 55, y + height / 2
        path = canvas.beginPath()
        path.moveTo(cx, cy - 15)
        path.curveTo(cx - 15, cy + 10, cx - 30, cy - 5, cx, cy - 35)
        path.curveTo(cx + 30, cy - 5, cx + 15, cy + 10, cx, cy - 15)
        canvas.drawPath(path, stroke=1, fill=1)
        
    elif card_type == "proposito":  # Escudo de Proteção
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

def draw_chapter_header(canvas, subtitle, title, subtitle_color="#bfdbfe"):
    """Desenha o cabeçalho padronizado e refinado dos capítulos."""
    canvas.saveState()
    # Subtítulo (ex: CAPÍTULO 1)
    canvas.setFont(font_map["sans-bold"], 10)
    canvas.setFillColor(get_color(subtitle_color))
    # Espaçamento de caracteres emulado via desenho
    canvas.drawCentredString(297.63, 785, subtitle.upper())
    
    # Título Principal do Capítulo
    canvas.setFont(font_map["display-bold"], 26)
    canvas.setFillColor(get_color("#ffffff"))
    canvas.drawCentredString(297.63, 750, title)
    canvas.restoreState()

def draw_page_number(canvas, page_num, total_paginas=7):
    """Insere o número de página com opacidade e elegância."""
    canvas.saveState()
    canvas.setFont(font_map["sans"], 9)
    canvas.setFillColor(Color(1, 1, 1, 0.4))
    canvas.drawCentredString(297.63, 35, f"Página {page_num} de {total_paginas}")
    canvas.restoreState()

def draw_text_in_rect(canvas, title, paragraphs, x, y, width, height, title_font_size=16, body_font_size=10, has_highlight=False, has_italic_box=False):
    """Formata e desenha com precisão cirúrgica blocos de textos e caixas destacadas dentro dos Bento Cards."""
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
    
    # Custom rendering for Card 1 (A Névoa) with the highlight box at the bottom
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
        # Italic box fica fixa no rodapé do card
        box_padding = 8
        box_x = x + 12
        box_h = 55
        box_y = y + 15
        box_w = width - 24
        # Limite superior disponível para titulo + parágrafo = acima da box + gap
        area_topo_bottom = box_y + box_h + 8  # bottom da area de texto
        
        # Title
        title_p = Paragraph(title, title_style)
        w, h = title_p.wrap(width - 24, height)
        title_p.drawOn(canvas, x + 12, y + height - 15 - h)
        
        # Parágrafo 1 — limita altura disponível para não colidir com a box
        available_h = (y + height - 15 - h - 10) - area_topo_bottom
        p1_p = Paragraph(paragraphs[0], body_style)
        w1, h1 = p1_p.wrap(width - 24, max(available_h, 20))
        draw_y1 = y + height - 15 - h - 10 - h1
        # Garante que o parágrafo não ultrapasse o topo da italic box
        if draw_y1 < area_topo_bottom:
            draw_y1 = area_topo_bottom
        p1_p.drawOn(canvas, x + 12, draw_y1)
        
        # Italic box fixa no rodapé
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
        # General layout for Card 2 & 3 — com limite inferior para evitar overflow
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
            # Se o parágrafo não cabe, não desenha
            if current_y - h_p < bottom_limit:
                break
            p.drawOn(canvas, x + 12, current_y - h_p)
            current_y -= (h_p + 8)
            
    canvas.restoreState()

def draw_page_1_content(canvas, doc):
    """Gera o layout visual completo da Página 1 (Bento Grid com Proporções Perfeitas)."""
    conteudo = getattr(doc, "conteudo", None)
    
    titulo = "O Fio de Ouro."
    subtitulo = "Um Resgate Familiar."
    cards = []
    
    if conteudo:
        titulo = conteudo.get("titulo_pdf", titulo)
        subtitulo = conteudo.get("subtitulo_pdf", subtitulo)
        cards = conteudo.get("capa_cards", [])
        
    # 1. Título e subtítulo com Paragraph para suportar quebra de linha automática
    canvas.saveState()
    page_width = 595.27
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
    
    # Posiciona o bloco título+subtítulo no TOPO da página, com margem de 54pt
    top_margin = 54
    page_height = 841.89
    # O topo do título começa em (page_height - top_margin), o drawOn recebe o y do canto inferior
    titulo_bottom = page_height - top_margin - th
    subtitulo_bottom = titulo_bottom - sh - 8
    
    titulo_p.drawOn(canvas, margin_h, titulo_bottom)
    subtitulo_p.drawOn(canvas, margin_h, subtitulo_bottom)
    canvas.restoreState()
    
    # 2. Configurações de Dimensão do Bento Grid (A4: 595.27 x 841.89)
    left_margin = 40
    gap = 16
    col_w = 161.09
    double_col_w = col_w * 2 + gap # 338.18
    grid_height = 380
    row_h = 182.0
    grid_y = 176.0
    
    # --- Card 1: A Névoa ---
    c1_x = left_margin
    c1_y = grid_y
    c1_title = cards[0]["titulo"] if len(cards) > 0 else "A Névoa"
    c1_paragraphs = [cards[0]["texto"]] if len(cards) > 0 else [
        "Sob o mesmo teto, mas a quilômetros de distância. A rotina exaustiva, as telas sempre acesas e as preocupações têm roubado o diálogo e o afeto.",
        "Você sente que está perdendo os melhores anos da sua família para a correria implacável? O distanciamento invisível transforma lares em abrigos de passagem."
    ]
    if len(c1_paragraphs) == 1 and "Você sente" not in c1_paragraphs[0]:
        partes = c1_paragraphs[0].split(". ")
        if len(partes) > 1:
            c1_paragraphs = [partes[0] + ".", ". ".join(partes[1:])]
    # Texto fixo de abertura do card — nunca muda
    TEXTO_ABERTURA_NEVOA = "A voz interna te sabota toda vez que você tenta mudar."
    # A pergunta da caixinha de destaque é SEMPRE FIXA — nunca muda, independente da IA
    PERGUNTA_NEVOA_FIXA = "Você sente que está perdendo os melhores anos do convívio?"
    ai_texto = c1_paragraphs[0] if len(c1_paragraphs) >= 1 else ""
    # Une: frase fixa + texto da IA explicando o porquê + pergunta fixa na highlight box
    c1_paragraphs = [TEXTO_ABERTURA_NEVOA + " " + ai_texto, PERGUNTA_NEVOA_FIXA]
    
    draw_gradient_round_rect(canvas, c1_x, c1_y, col_w, grid_height, 18, 18, "#22d3ee", "#3b82f6", border_color="rgba(255,255,255,0.15)")
    draw_card_decorations(canvas, "nevoa", c1_x, c1_y, col_w, grid_height)
    draw_text_in_rect(canvas, c1_title, c1_paragraphs, c1_x, c1_y, col_w, grid_height, title_font_size=18, body_font_size=10, has_highlight=True)
    
    # --- Card 2: A Solução ---
    c2_x = left_margin + col_w + gap
    c2_y = grid_y + row_h + gap
    c2_title = cards[1]["titulo"] if len(cards) > 1 else "A Solução"
    c2_paragraphs = [cards[1]["texto"]] if len(cards) > 1 else [
        "A verdadeira solução não está em focar apenas em mais provisão material. A resposta exige uma atitude corajosa, simples e profunda: tempo de qualidade e intencionalidade.",
        "É preciso resgatar a presença ativa e tecer novamente os fios que mantêm o amor inabalável."
    ]
    draw_gradient_round_rect(canvas, c2_x, c2_y, double_col_w, row_h, 18, 18, "#c084fc", "#f472b6", border_color="rgba(255,255,255,0.15)")
    draw_card_decorations(canvas, "solucao", c2_x, c2_y, double_col_w, row_h)
    draw_text_in_rect(canvas, c2_title, c2_paragraphs, c2_x, c2_y, double_col_w, row_h, title_font_size=18, body_font_size=10)
    
    # --- Card 3: O Propósito ---
    c3_x = c2_x
    c3_y = grid_y
    c3_title = cards[2]["titulo"] if len(cards) > 2 else "O Propósito"
    c3_paragraphs = [cards[2]["texto"]] if len(cards) > 2 else [
        "Onde antes reinava o silêncio, a paz verdadeira se instaura, forjada no fogo das provações e guiada pela união."
    ]
    draw_gradient_round_rect(canvas, c3_x, c3_y, col_w, row_h, 18, 18, "#818cf8", "#a855f7", border_color="rgba(255,255,255,0.15)")
    draw_card_decorations(canvas, "proposito", c3_x, c3_y, col_w, row_h)
    draw_text_in_rect(canvas, c3_title, c3_paragraphs, c3_x, c3_y, col_w, row_h, title_font_size=16, body_font_size=10)
    
    # --- Card 4: A Verdade ---
    c4_x = c3_x + col_w + gap
    c4_y = grid_y
    c4_title = cards[3]["titulo"] if len(cards) > 3 else "A Verdade"
    c4_paragraphs = [cards[3]["texto"]] if len(cards) > 3 else [
        "O amor exige presença no campo de batalha da rotina.",
        "\"Onde colocamos nosso tempo, ali ancoramos nosso coração.\""
    ]
    if len(c4_paragraphs) == 1:
        c4_paragraphs.append('"Onde colocamos nosso tempo, ali ancoramos nosso coração."')
    draw_gradient_round_rect(canvas, c4_x, c4_y, col_w, row_h, 18, 18, "#3b82f6", "#4f46e5", border_color="rgba(255,255,255,0.15)")
    draw_text_in_rect(canvas, c4_title, c4_paragraphs, c4_x, c4_y, col_w, row_h, title_font_size=16, body_font_size=10, has_italic_box=True)

# --- Callback Master de Planos de Fundo (Gradients Exatos da Web) ---

def draw_all_page_backgrounds(canvas, doc):
    """Executado dinamicamente para renderizar os fundos, cabeçalhos e rodapés de cada página."""
    page_num = canvas.getPageNumber()
    conteudo = getattr(doc, "conteudo", None)
    capitulos = conteudo.get("capitulos", []) if conteudo else []
    num_capitulos = len(capitulos) if len(capitulos) > 0 else 5
    
    total_paginas = num_capitulos + 3  # Capa (1) + Capítulos (N) + Citação/Fechamento (1) + Plano (1)
    
    if page_num == 1:
        # Página 1: Cyan-Blue Gradient (#22d3ee -> #3b82f6)
        draw_page_gradient(canvas, "#22d3ee", "#3b82f6")
        draw_page_1_content(canvas, doc)
        draw_page_number(canvas, 1, total_paginas)
        
    elif 2 <= page_num <= num_capitulos + 1:
        # Páginas de Capítulos
        idx_cap = page_num - 2
        
        # Mapeia as cores de gradiente de capítulos
        grad_cores = [
            ("#3b82f6", "#a855f7"),  # Blue-Purple
            ("#a855f7", "#d946ef"),  # Purple-Fuchsia
            ("#d946ef", "#6366f1"),  # Fuchsia-Indigo
            ("#6366f1", "#2563eb"),  # Indigo-Blue
        ]
        sub_cores = ["#bfdbfe", "#f5d0fe", "#f5d0fe", "#c7d2fe"]
        
        cor1, cor2 = grad_cores[idx_cap % len(grad_cores)]
        sub_color = sub_cores[idx_cap % len(sub_cores)]
        
        cap_num = idx_cap + 1
        cap_title = capitulos[idx_cap].get("titulo", f"Capítulo {cap_num}") if idx_cap < len(capitulos) else f"Título do Capítulo {cap_num}"
        
        # Fallback estático caso conteudo seja None
        if not conteudo:
            titulos_estaticos = [
                "A Névoa do Cotidiano",
                "O Espelho Partido",
                "O Fio de Ouro",
                "Tecendo Novamente",
                "O Novo Manto"
            ]
            if idx_cap < len(titulos_estaticos):
                cap_title = titulos_estaticos[idx_cap]
        
        draw_page_gradient(canvas, cor1, cor2)
        draw_chapter_header(canvas, f"Capítulo {cap_num}", cap_title, subtitle_color=sub_color)
        draw_page_number(canvas, page_num, total_paginas)
        
    elif page_num == num_capitulos + 2:
        # Página de citação / fechamento
        draw_page_gradient(canvas, "#0f172a", "#172554")
        draw_chapter_header(canvas, "A Verdade Inabalável", "", subtitle_color="#bfdbfe")
        draw_page_number(canvas, page_num, total_paginas)
        
    elif page_num == num_capitulos + 3:
        # Página do Plano de Ação
        draw_page_gradient(canvas, "#6366f1", "#2563eb")
        # Sem cabeçalho
        draw_page_number(canvas, page_num, total_paginas)

# --- Construção Principal do Story do Documento ---

def gerar_pdf(filename="O_Fio_de_Ouro_Restauracao.pdf", conteudo=None):
    # Margens do Documento
    doc = SimpleDocTemplate(
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
        
    # Estilos de Texto do Fluxo (Aumentados para preencher elegantemente as páginas, como na Web)
    chapter_body_style = ParagraphStyle(
        name="ChapterBody",
        fontName=font_map["sans"],
        fontSize=14,
        leading=23,
        textColor=get_color("#f5f3ff"), # text-purple-50
        alignment=TA_JUSTIFY,
        spaceAfter=24
    )
    
    chapter_italic_style = ParagraphStyle(
        name="ChapterItalic",
        fontName=font_map["sans-italic"],
        fontSize=14,
        leading=23,
        textColor=get_color("#ddd6fe"), # text-purple-100
        alignment=TA_JUSTIFY,
        spaceAfter=24
    )
    
    # Estilo específico para a Página 5 (Capítulo 4) para comportar todos os parágrafos com elegância e sem transbordar
    page5_body_style = ParagraphStyle(
        name="Page5Body",
        parent=chapter_body_style,
        fontSize=12.5,
        leading=19,
        spaceAfter=14
    )
    
    # Bento Quote Box (Estilização Idêntica ao Web App)
    quote_title_style = ParagraphStyle(
        name="QuoteTitle",
        fontName=font_map["sans-bold"],
        fontSize=13,
        leading=16,
        textColor=get_color("#ffffff"),
        alignment=TA_CENTER,
        spaceAfter=6
    )
    quote_text_style = ParagraphStyle(
        name="QuoteText",
        fontName=font_map["sans-italic"],
        fontSize=10,
        leading=14,
        textColor=get_color("#bfdbfe"), # text-blue-100
        alignment=TA_CENTER,
        spaceAfter=10
    )
    bible_verse_style = ParagraphStyle(
        name="BibleVerse",
        fontName=font_map["sans-bold"],
        fontSize=10,
        leading=13,
        textColor=get_color("#38bdf8"), # text-blue-300 / sky-400
        alignment=TA_CENTER
    )
    
    story = []
    
    # ==================== PÁGINA 1 ====================
    # Desenhada de forma estática no canvas. Apenas avançamos o fluxo.
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    if conteudo:
        # --- MODO DINÂMICO (GEMINI IA) ---
        capitulos = conteudo.get("capitulos", [])
        
        # ==================== PÁGINAS DE CAPÍTULOS ====================
        for i, cap in enumerate(capitulos):
            story.append(Spacer(1, 140)) # Abre espaço exato abaixo do cabeçalho fixo do capítulo
            
            paragrafos = cap.get("paragrafos", [])
            use_small_style = len(paragrafos) >= 4 or sum(len(p) for p in paragrafos) > 600
            style_padrao = page5_body_style if use_small_style else chapter_body_style
            
            # Estilo itálico dinâmico
            style_italico = ParagraphStyle(
                name=f"Italic_{i}",
                parent=style_padrao,
                fontName=font_map["sans-italic"],
                textColor=get_color("#ddd6fe")
            )
            
            for p_idx, paragrafo in enumerate(paragrafos):
                is_italic = (p_idx == 1) # O segundo parágrafo costuma ser o pensamento em itálico
                story.append(Paragraph(paragrafo, style_italico if is_italic else style_padrao))
                
            story.append(PageBreak())
            
        # ==================== PÁGINA DE CITAÇÃO & FECHAMENTO ====================
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
            
        # --- Bento Quote Box (Citação de Destaque) ---
        citacao_texto = conteudo.get("citacao_destaque", "A restauração genuína começa no coração.")
        
        card_content = [
            [Paragraph("A Verdade Inabalável", quote_title_style)],
            [Paragraph(f'"{citacao_texto}"', quote_text_style)],
            [Paragraph('"Se o Senhor não edificar a casa, em vão trabalham os que a edificam."<br/><font color="#ffffff" size="9"><b>— Salmos 127:1</b></font>', bible_verse_style)]
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
        
        # ==================== PÁGINA DO PLANO DE AÇÃO ====================
        story.append(Spacer(1, 20)) # Pequena margem superior
        
        plano = conteudo.get("plano_acao", {})
        plano_titulo = plano.get("titulo_secao", "Plano de Ação Diário")
        plano_subtitulo = plano.get("subtitulo", "Aplique estes princípios na rotina para fortalecer os laços.")
        
        plan_title_style = ParagraphStyle(
            name="PlanTitle",
            fontName=font_map["display-bold"],
            fontSize=24,
            leading=28,
            textColor=get_color("#ffffff"),
            leftIndent=58,
            spaceAfter=4
        )
        plan_subtitle_style = ParagraphStyle(
            name="PlanSubtitle",
            fontName=font_map["sans"],
            fontSize=11,
            leading=15,
            textColor=get_color("#c7d2fe"), # text-purple-200
            leftIndent=58,
            spaceAfter=25
        )
        
        story.append(Paragraph(plano_titulo, plan_title_style))
        story.append(Paragraph(plano_subtitulo, plan_subtitle_style))
        
        # Estilos específicos para a tabela estilizada do plano de ação
        item_title_style = ParagraphStyle(
            name="ItemTitle",
            fontName=font_map["sans-bold"],
            fontSize=12,
            leading=15,
            textColor=get_color("#ffffff"),
            spaceAfter=3
        )
        item_desc_style = ParagraphStyle(
            name="ItemDesc",
            fontName=font_map["sans"],
            fontSize=9.5,
            leading=14,
            textColor=get_color("#e0e7ff"), # text-purple-100
            alignment=TA_JUSTIFY
        )
        
        passos = plano.get("passos", [])
        
        badge_cores = [
            ("#3b82f6", "rgba(59, 130, 246, 0.2)"),   # Passo 1
            ("#a855f7", "rgba(168, 85, 247, 0.2)"),   # Passo 2
            ("#d946ef", "rgba(217, 70, 239, 0.2)"),   # Passo 3
            ("#6366f1", "rgba(99, 102, 241, 0.2)")    # Passo 4
        ]
        
        plan_rows = []
        for p_idx, passo in enumerate(passos):
            num = str(passo.get("numero", p_idx + 1))
            title = passo.get("titulo", f"Passo {num}")
            desc = passo.get("descricao", "")
            
            text_color, bg_color = badge_cores[p_idx % len(badge_cores)]
            
            badge_style = ParagraphStyle(
                name=f"Badge_{num}",
                fontName=font_map["sans-bold"],
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
                fontName=font_map["sans-bold"],
                fontSize=14,
                leading=18,
                textColor=get_color("#3b82f6"),
                backColor=get_color("rgba(59, 130, 246, 0.2)"),
                borderPadding=8,
                alignment=TA_CENTER
            )
            plan_rows.append([Paragraph("1", badge_style_fallback), [Paragraph("Ação Inicial", item_title_style), Paragraph("Comece a agir hoje.", item_desc_style)]])
            
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
        
        # Assinatura de Rodapé do Plano de Ação
        footer_style = ParagraphStyle(
            name="PlanFooter",
            fontName=font_map["sans-bold"],
            fontSize=10,
            leading=12,
            textColor=get_color("#c7d2fe"),
            alignment=TA_CENTER,
            spaceBefore=15
        )
        story.append(Paragraph("PRODUZIDO COM ZELO, FÉ E PROPÓSITO.", footer_style))
        
    else:
        # --- MODO ESTÁTICO (FALLBACK ORIGINAL) ---
        # ==================== PÁGINA 2 (Capítulo 1) ====================
        story.append(Spacer(1, 140))
        story.append(Paragraph(
            "Arthur olhou para o relógio: 23:45. A luz azulada do monitor era a única coisa iluminando o escritório. No andar de baixo, a casa estava em absoluto silêncio. Um silêncio que costumava significar paz, mas que agora parecia um abismo intransponível.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "Ele fechou o notebook, esfregando os olhos cansados. Caminhando pelo corredor, passou pelo quarto de Lucas. O adolescente estava isolado com seus fones de ouvido, perdido em um mundo virtual vibrante, completamente alheio a quem passava pela porta. No quarto principal, Helena já dormia, um livro caído sobre o peito, a respiração compassada marcando o fim de mais um dia exaustivo.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "— Quando nos tornamos apenas colegas de quarto dividindo boletos? — pensou Arthur, cobrindo a esposa com sutileza e zelo, ajeitando o cobertor sobre seus ombros.",
            chapter_italic_style
        ))
        story.append(Paragraph(
            "Eles tinham a casa que sempre sonharam, a estabilidade pela qual tanto lutaram, mas a sensação era de que haviam perdido a si mesmos no processo de conquistar o mundo lá fora.",
            chapter_body_style
        ))
        story.append(PageBreak())
        
        # ==================== PÁGINA 3 (Capítulo 2) ====================
        story.append(Spacer(1, 140))
        story.append(Paragraph(
            "Na manhã seguinte, a cozinha parecia uma estação de trem. \"Bons dias\" apressados e mecânicos, café engolido de pé e olhos grudados em telas luminosas de smartphones. Era o caos organizado da família moderna.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "— Helena — Arthur chamou suavemente, segurando sua caneca de café com as duas mãos, interrompendo o fluxo automático da rotina. — Você se lembra da última vez que realmente conversamos? Não sobre as contas da casa, ou as notas do Lucas, mas... sobre nós?",
            chapter_body_style
        ))
        story.append(Paragraph(
            "Helena parou, a torrada a meio caminho da boca. Ela olhou para Arthur. Realmente olhou para ele, prestando atenção em seus olhos, pela primeira vez em semanas. Os ombros dela cederam levemente sob o peso invisível que carregava.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "— Sinto que estamos no mesmo barco, Arthur, mas remando em direções opostas com toda a nossa força — ela admitiu, a voz ligeiramente trêmula. — Nós estamos provendo tudo o que é material para eles. Tudo, exceto nós mesmos.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "Era a verdade dolorosa sendo exposta sob a luz do sol da manhã. O espelho da família \"perfeita\", tão bem polido para quem via de fora pelas redes sociais, estava rachado por dentro, pedindo socorro.",
            chapter_body_style
        ))
        story.append(PageBreak())
        
        # ==================== PÁGINA 4 (Capítulo 3) ====================
        story.append(Spacer(1, 140))
        story.append(Paragraph(
            "Naquela mesma noite, em vez de se trancar no home office logo após o jantar, Arthur sentou-se no sofá da sala. Ele chamou Helena, segurando um livro antigo, de capa de couro levemente gasta pelas décadas.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "— Encontrei isso hoje nas minhas coisas de infância — disse ele, passando os dedos sobre a capa. — Era do meu avô. Ele costumava me dizer que uma família é como uma grande tapeçaria. Se você usar apenas fios comuns e rotineiros — trabalho, busca por dinheiro, obrigações — o tecido eventualmente cede e rasga sob a pressão da vida.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "Ele abriu na primeira página, onde havia uma dedicatória escrita à mão. — Mas ele dizia que, se você tecer um \"Fio de Ouro\" por entre eles... a fé, a devoção a Deus, o perdão e a comunhão verdadeira... esse fio dourado fortalece a trama e mantém tudo unido, tornando o tecido inquebrável.",
            chapter_body_style
        ))
        story.append(Paragraph(
            "Helena tocou a capa desgastada, os olhos marejados refletindo a luz fraca do abajur. — Temos usado fios muito frágeis e baratos, não é?",
            chapter_body_style
        ))
        story.append(Paragraph(
            "— Sim. Nós deixamos o Arquiteto e o Seu material de fora da nossa construção — respondeu Arthur, segurando firme a mão dela. — Mas ainda há tempo de corrigir a rota. Nós podemos começar a tecer novamente. Hoje.",
            chapter_body_style
        ))
        story.append(PageBreak())
        
        # ==================== PÁGINA 5 (Capítulo 4) ====================
        story.append(Spacer(1, 110))
        story.append(Paragraph(
            "A mudança de rota não aconteceu como mágica em um passe de ilusionismo; ela foi intensamente intencional. E exigiu coragem para confrontar o desconforto.",
            page5_body_style
        ))
        story.append(Paragraph(
            "— Pessoal, reunião de família na sala. Agora mesmo. — Arthur anunciou em uma sexta-feira à noite, logo após chegar do trabalho, caminhando até o corredor e desconectando o roteador de internet da tomada.",
            page5_body_style
        ))
        story.append(Paragraph(
            "Lucas apareceu segundos depois, resmungando alto, seguido pela pequena Sofia, que arrastava sua boneca favorita de pano.",
            page5_body_style
        ))
        story.append(Paragraph(
            "— O que aconteceu? A internet caiu de vez no bairro? — Lucas cruzou os braços, frustrado com a interrupção de seu jogo.",
            page5_body_style
        ))
        story.append(Paragraph(
            "— Não, filho — Helena sorriu com doçura, sentando-se no tapete ao lado de Arthur. — Nós só estamos nos reconectando a uma rede muito melhor e infinitamente mais importante.",
            page5_body_style
        ))
        story.append(Paragraph(
            "Eles conversaram. No começo, o silêncio sem as telas como escudo foi constrangedor, quase palpável. Mas então, a represa se rompeu. Compartilharam seus medos diários, sonhos engavetados e um longo e necessário pedido de desculpas. Arthur pediu perdão por sua ausência física e mental. Helena pediu perdão por sua impaciência contínua, fruto do esgotamento.",
            page5_body_style
        ))
        story.append(Paragraph(
            "— Eu sentia falta de vocês assim... perto — Lucas murmurou, olhando para o chão, deixando sua grossa armadura de adolescente cair por um momento revelador.",
            page5_body_style
        ))
        story.append(Paragraph(
            "Eles deram as mãos em roda. Fizeram uma oração simples, um pouco desajeitada pelo tempo sem prática, mas profundamente honesta. Ali, naquela sala de estar, o Fio de Ouro estava finalmente passando pelo buraco estreito da agulha.",
            page5_body_style
        ))
        story.append(PageBreak())
        
        # ==================== PÁGINA 6 (Capítulo 5 & Caixa de Destaque) ====================
        story.append(Spacer(1, 100))
        
        p5_style = ParagraphStyle(
            name="Cap5Style",
            parent=chapter_body_style,
            fontSize=11,
            leading=16,
            spaceAfter=10
        )
        
        story.append(Paragraph(
            "Meses depois daquela primeira noite sem internet, a casa respirava de outra forma. Não havia se tornado um ambiente imune a falhas — ainda havia discussões ocasionais pelo controle remoto e manhãs pontuadas pelo caos dos horários escolares — mas o silêncio ensurdecedor e gelado havia desaparecido para sempre.",
            p5_style
        ))
        story.append(Paragraph(
            "Ele foi substituído por risadas espontâneas no corredor, jantares onde todos os celulares descansavam obrigatoriamente em uma pequena cesta de vime na cozinha, e um senso absoluto e profundo de pertencimento.",
            p5_style
        ))
        story.append(Paragraph(
            "Arthur e Helena aprenderam, na prática exaustiva do dia a dia, que a família não é um belo troféu de porcelana que se conquista e se coloca na estante da sala para impressionar as visitas e juntar poeira. A família é um jardim vivo que requer cuidado intencional, cultivo diário, rega paciente e um zelo contínuo para arrancar as ervas daninhas da indiferença.",
            p5_style
        ))
        story.append(Paragraph(
            "Encostado no batente da porta, Arthur observava Helena correndo atrás das crianças pelo quintal, sob a luz dourada reconfortante do fim de tarde. Seu peito transbordava de uma gratidão que o dinheiro de seu trabalho jamais poderia comprar.",
            p5_style
        ))
        
        story.append(Spacer(1, 10))
        
        card_content = [
            [Paragraph("A Verdade Inabalável", quote_title_style)],
            [Paragraph('"A restauração genuína de um lar começa no exato momento em que reconhecemos que nossas próprias forças são insuficientes. Quando o orgulho humano cede o seu lugar à humildade, e a distração da tela cede lugar ao foco no olhar do outro, Deus constrói fortalezas impenetráveis onde antes havia apenas ruínas."', quote_text_style)],
            [Paragraph('"Se o Senhor não edificar a casa, em vão trabalham os que a edificam."<br/><font color="#ffffff" size="9"><b>— Salmos 127:1</b></font>', bible_verse_style)]
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
        
        # ==================== PÁGINA 7 (Plano de Ação Diário) ====================
        story.append(Spacer(1, 20))
        
        plan_title_style = ParagraphStyle(
            name="PlanTitle",
            fontName=font_map["display-bold"],
            fontSize=24,
            leading=28,
            textColor=get_color("#ffffff"),
            leftIndent=58,
            spaceAfter=4
        )
        plan_subtitle_style = ParagraphStyle(
            name="PlanSubtitle",
            fontName=font_map["sans"],
            fontSize=11,
            leading=15,
            textColor=get_color("#c7d2fe"),
            leftIndent=58,
            spaceAfter=25
        )
        
        story.append(Paragraph("Plano de Ação Diário", plan_title_style))
        story.append(Paragraph("Aplique estes princípios na rotina para fortalecer os laços e proteger seu lar.", plan_subtitle_style))
        
        item_title_style = ParagraphStyle(
            name="ItemTitle",
            fontName=font_map["sans-bold"],
            fontSize=12,
            leading=15,
            textColor=get_color("#ffffff"),
            spaceAfter=3
        )
        item_desc_style = ParagraphStyle(
            name="ItemDesc",
            fontName=font_map["sans"],
            fontSize=9.5,
            leading=14,
            textColor=get_color("#e0e7ff"),
            alignment=TA_JUSTIFY
        )
        
        items_data = [
            ("1", "#3b82f6", "rgba(59, 130, 246, 0.2)", "Alinhamento (A Oração)", "Dedique 10 minutos hoje à noite para orarem juntos, de mãos dadas. Agradeçam e entreguem as preocupações e os desafios ao Criador."),
            ("2", "#a855f7", "rgba(168, 85, 247, 0.2)", "A Mesa da Comunhão", "Faça pelo menos uma refeição diária com todos da casa. Regra inegociável: distrações digitais e telas devem permanecer desligadas."),
            ("3", "#d946ef", "rgba(217, 70, 239, 0.2)", "Manual de Sabedoria", "Leia um capítulo do livro de Provérbios neste final de semana com sua família, e discutam a aplicação prática para a semana."),
            ("4", "#6366f1", "rgba(99, 102, 241, 0.2)", "O Protocolo do Perdão", "Nunca permita que o sol se ponha ou vá dormir guardando ressentimentos. Tenha a coragem de pedir perdão hoje por alguma ofensa.")
        ]
        
        plan_rows = []
        for num, text_color, bg_color, title, desc in items_data:
            badge_style = ParagraphStyle(
                name=f"Badge_{num}",
                fontName=font_map["sans-bold"],
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
            fontName=font_map["sans-bold"],
            fontSize=10,
            leading=12,
            textColor=get_color("#c7d2fe"),
            alignment=TA_CENTER,
            spaceBefore=15
        )
        story.append(Paragraph("PRODUZIDO COM ZELO, FÉ E PROPÓSITO.", footer_style))
        
    # --- Custom target badge drawn on background canvas for page 7 ---
    def draw_p7_badge(canvas):
        draw_gradient_round_rect(canvas, 54, 735, 42, 42, 10, 10, "#60a5fa", "#6366f1")
        canvas.saveState()
        canvas.setStrokeColor(get_color("#ffffff"))
        canvas.setLineWidth(1.5)
        cx, cy = 54 + 21, 735 + 21
        canvas.circle(cx, cy, 8, stroke=1, fill=0)
        canvas.circle(cx, cy, 3, stroke=1, fill=0)
        canvas.restoreState()

    def draw_p7_extras(canvas, doc):
        draw_all_page_backgrounds(canvas, doc)
        conteudo_p7 = getattr(doc, "conteudo", None)
        capitulos_p7 = conteudo_p7.get("capitulos", []) if conteudo_p7 else []
        num_capitulos_p7 = len(capitulos_p7) if len(capitulos_p7) > 0 else 5
        
        if canvas.getPageNumber() == num_capitulos_p7 + 3:
            draw_p7_badge(canvas)

    # --- Compilação final com callbacks integrados ---
    doc.build(
        story, 
        onFirstPage=draw_all_page_backgrounds, 
        onLaterPages=draw_p7_extras
    )

if __name__ == "__main__":
    print("\033[96m====================================================\033[0m")
    print("\033[1;92m   O Fio de Ouro - Gerador de PDF via Terminal\033[0m")
    print("\033[96m====================================================\033[0m")
    
    nome_arquivo = "O_Fio_de_Ouro_Restauracao.pdf"
    
    print(f"\033[94m[*] Iniciando a geração do PDF: '{nome_arquivo}'...\033[0m")
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
