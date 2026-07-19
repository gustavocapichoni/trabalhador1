# Efeitos Visuais Premium
from PIL import Image, ImageDraw

from .templates import CORES

def aplicar_mesh_gradient(img, cor_inicio=None, cor_fim=None, alpha_topo=15, alpha_base=40):
    """Aplica um degradê inteligente, escurecendo mais a parte inferior e central, usando a paleta da marca.
    
    Parâmetros opcionais permitem customizar a cor por tipo de post sem afetar os demais.
    """
    W, H = img.size
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    r_ini, g_ini, b_ini = cor_inicio if cor_inicio else CORES["fundo_tint_inicio"]
    r_fim, g_fim, b_fim = cor_fim if cor_fim else CORES["fundo_tint_fim"]
    
    # Degradê
    for y in range(H):
        # Interpolação linear da cor
        ratio = y / H
        r = int(r_ini + (r_fim - r_ini) * ratio)
        g = int(g_ini + (g_fim - g_ini) * ratio)
        b = int(b_ini + (b_fim - b_ini) * ratio)
        
        # Opacidade (Alpha) inteligente reduzida para dar mais transparência ao fundo
        if y < H * 0.3:
            alpha = alpha_topo  # Quase invisível no topo
        elif y < H * 0.7:
            progress = (y - H * 0.3) / (H * 0.4)
            alpha = int(alpha_topo + progress * (alpha_base - alpha_topo))
        else:
            alpha = alpha_base  # Sutil na base
            
        draw.line([(0, y), (W, y)], fill=(r, g, b, alpha))
        
    return Image.alpha_composite(img.convert('RGBA'), overlay)

def draw_text_with_shadow(draw, position, text, font, fill=(255, 255, 255), shadow_color=(0, 0, 0, 220), anchor="ms"):
    """Desenha texto com um contorno suave e sombra projetada forte para legibilidade máxima."""
    x, y = position
    offset = max(1, int(font.size * 0.03))
    
    # Contorno suave (Stroke em 8 direções)
    for dx in [-offset, 0, offset]:
        for dy in [-offset, 0, offset]:
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 140), anchor=anchor)
                
    # Sombra direcional forte
    draw.text((x + offset*2, y + offset*2), text, font=font, fill=shadow_color, anchor=anchor)
    
    # Texto principal
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

def desenhar_elementos_premium(draw, W, H, cor_moldura=None):
    """Adiciona molduras sutis e linhas separadoras para dar aspecto de design de agência.
    
    O parâmetro opcional cor_moldura permite customizar a cor da borda por tipo de post.
    """
    # Moldura sutil interna (margem de 40px)
    margem = 40
    if cor_moldura is None:
        cor_moldura = (*CORES["destaque"][:3], 80)  # Cor padrão (azul) com transparência
    
    # Desenha 4 linhas finas formando um quadro (top, bottom, left, right)
    draw.line([(margem, margem), (W - margem, margem)], fill=cor_moldura, width=1)
    draw.line([(margem, H - margem), (W - margem, H - margem)], fill=cor_moldura, width=1)
    draw.line([(margem, margem), (margem, H - margem)], fill=cor_moldura, width=1)
    draw.line([(W - margem, margem), (W - margem, H - margem)], fill=cor_moldura, width=1)

    

