import os
import urllib.request
from PIL import ImageFont
from datetime import datetime, timezone

# URLs alternativas por fonte (tenta cada uma em ordem até conseguir)
_FONTES_URLS = {
    "Oswald": [
        "https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/static/Oswald-Bold.ttf",
    ],
    "Inter": [
        "https://raw.githubusercontent.com/rsms/inter/master/docs/font/Inter-Bold.ttf",
        "https://fonts.gstatic.com/s/inter/v13/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa1ZL7W0Q5nw.woff2",
    ],
    "Playfair": [
        "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/static/PlayfairDisplay-Bold.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
    ],
    "Montserrat": [
        "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Bold.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/static/Montserrat-Bold.ttf",
    ],
    # --- Novas fontes modernas ---
    "BebasNeue": [
        "https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf",
    ],
    "Raleway": [
        "https://raw.githubusercontent.com/google/fonts/main/ofl/raleway/Raleway%5Bwght%5D.ttf",
    ],
    "Exo2": [
        "https://raw.githubusercontent.com/google/fonts/main/ofl/exo2/Exo2%5Bwght%5D.ttf",
    ],
    "Righteous": [
        "https://raw.githubusercontent.com/google/fonts/main/ofl/righteous/Righteous-Regular.ttf",
    ],
}

# ==========================================
# FONTE POR DIA DA SEMANA (0=Segunda ... 6=Domingo)
# ==========================================
FONTE_POR_DIA = {
    0: "BebasNeue",   # Segunda — Cinematográfico, impactante
    1: "Oswald",      # Terça   — Forte, compacto e agressivo
    2: "Raleway",     # Quarta  — Elegante e sofisticado
    3: "Exo2",        # Quinta  — Futurista, tecnológico
    4: "Montserrat",  # Sexta   — Versátil e premium
    5: "Playfair",    # Sábado  — Editorial de luxo
    6: "Righteous",   # Domingo — Vibrante e humano
}

def obter_fonte_do_dia():
    """Retorna o nome da fonte programada para o dia de hoje."""
    dia = datetime.now(timezone.utc).weekday()
    fonte = FONTE_POR_DIA.get(dia, "Montserrat")
    print(f"[FONTE] Fonte do dia ({['Seg','Ter','Qua','Qui','Sex','Sab','Dom'][dia]}): {fonte}")
    return fonte

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

def carregar_fontes(tamanho_display, tamanho_body, tamanho_detalhe, estilo=None):
    """Retorna os objetos ImageFont com os tamanhos corretos.
    Se estilo=None, usa automaticamente a fonte do dia da semana."""
    if estilo is None:
        estilo = obter_fonte_do_dia()

    caminhos = garantir_fontes()
    f_principal = caminhos.get(estilo) or caminhos.get("Montserrat") or "arial.ttf"
    f_body = caminhos.get("Montserrat") or caminhos.get("Inter") or "arial.ttf"
    
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

# Paleta Oficial de Branding da Marca — Roxo Neon + Azul Elétrico
CORES = {
    "texto_principal":   (255, 255, 255),    # Branco Neve
    "texto_secundario":  (200, 200, 220),    # Cinza Claro Azulado
    "destaque":          (224, 86, 253),     # Roxo Neon Vibrante (bordas, linhas, marca)
    "fundo_tint_inicio": (8, 40, 100),       # Azul Elétrico Escuro / Índigo (início no topo)
    "fundo_tint_fim":    (25, 5, 45),        # Roxo Escuro / Quase Preto (fim na base)
    "sombra":            (0, 0, 0, 200)      # Preto difuso para legibilidade
}
