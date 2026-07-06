import os
import urllib.request
from PIL import ImageFont

# URLs alternativas por fonte (tenta cada uma em ordem até conseguir)
_FONTES_URLS = {
    "Oswald": [
        "https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/static/Oswald-Bold.ttf",
    ],
    "Inter": [
        "https://fonts.gstatic.com/s/inter/v13/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa1ZL7W0Q5nw.woff2",
        "https://raw.githubusercontent.com/rsms/inter/master/docs/font/Inter-Bold.ttf"
    ],
    "Playfair": [
        "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/static/PlayfairDisplay-Bold.ttf",
    ],
    "Montserrat": [
        "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Bold.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/static/Montserrat-Bold.ttf",
    ],
}

def garantir_fontes():
    """Baixa e garante as fontes Premium na pasta, tentando múltiplas URLs."""
    if not os.path.exists("fontes"):
        os.makedirs("fontes")

    caminhos = {}
    for nome, urls in _FONTES_URLS.items():
        caminho = f"fontes/{nome}.ttf"
        if not os.path.exists(caminho):
            baixou = False
            for url in urls:
                try:
                    print(f"[FONTE] Baixando {nome}...")
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as resp, open(caminho, "wb") as out:
                        out.write(resp.read())
                    print(f"[FONTE] {nome} baixada com sucesso!")
                    baixou = True
                    break
                except Exception as e:
                    print(f"[FONTE] Falha na URL alternativa para {nome}: {e}")
            if not baixou:
                print(f"[FONTE] Nao foi possivel baixar {nome}. Usando fonte padrao.")
        caminhos[nome] = caminho if os.path.exists(caminho) else None

    return caminhos

def carregar_fontes(tamanho_display, tamanho_body, tamanho_detalhe, estilo="Montserrat"):
    """Retorna os objetos ImageFont com os tamanhos corretos, baseados no estilo escolhido."""
    caminhos = garantir_fontes()
    f_principal = caminhos.get(estilo) or caminhos.get("Montserrat") or "arial.ttf"
    f_body = caminhos.get("Inter") or caminhos.get("Montserrat") or "arial.ttf"
    
    try:
        font_display = ImageFont.truetype(f_principal, tamanho_display)
    except Exception:
        font_display = ImageFont.load_default()
        
    try:
        font_body = ImageFont.truetype(f_body, tamanho_body)
    except Exception:
        font_body = ImageFont.load_default()
        
    try:
        font_detalhe = ImageFont.truetype(f_body, tamanho_detalhe)
    except Exception:
        font_detalhe = ImageFont.load_default()
        
    return font_display, font_body, font_detalhe

# Cores Premium
CORES = {
    "texto_principal": (255, 255, 255),    # Branco
    "texto_secundario": (220, 220, 220),   # Prata claro
    "destaque": (212, 175, 55),            # Dourado
    "sombra": (0, 0, 0, 180)               # Preto difuso
}
