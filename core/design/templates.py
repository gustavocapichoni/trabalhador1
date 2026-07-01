import os
import urllib.request
from PIL import ImageFont

def garantir_fontes():
    """Usa as fontes locais que já estão na pasta."""
    if not os.path.exists("fontes"):
        os.makedirs("fontes")
        
    f_display = "fontes/MontserratBold.ttf"
    f_body = "fontes/MontserratBold.ttf"
            
    # Fallback caso alguém delete a pasta no futuro
    if not os.path.exists(f_display): f_display = "fontes/fonte.ttf"
    if not os.path.exists(f_body): f_body = "fontes/fonte.ttf"
    
    return f_display, f_body

def carregar_fontes(tamanho_display, tamanho_body, tamanho_detalhe):
    """Retorna os objetos ImageFont com os tamanhos corretos."""
    f_display_path, f_body_path = garantir_fontes()
    
    try:
        font_display = ImageFont.truetype(f_display_path, tamanho_display)
    except:
        font_display = ImageFont.load_default()
        
    try:
        font_body = ImageFont.truetype(f_body_path, tamanho_body)
    except:
        font_body = ImageFont.load_default()
        
    try:
        font_detalhe = ImageFont.truetype(f_body_path, tamanho_detalhe)
    except:
        font_detalhe = ImageFont.load_default()
        
    return font_display, font_body, font_detalhe

# Cores Premium
CORES = {
    "texto_principal": (255, 255, 255),    # Branco
    "texto_secundario": (220, 220, 220),   # Prata claro
    "destaque": (212, 175, 55),            # Dourado
    "sombra": (0, 0, 0, 180)               # Preto difuso
}
