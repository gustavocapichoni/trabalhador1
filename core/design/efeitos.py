# Efeitos Visuais Premium
from PIL import Image, ImageDraw, ImageFilter

from .templates import CORES

def aplicar_mesh_gradient(img):
    """Aplica um degradê inteligente, escurecendo mais a parte inferior e central, usando a paleta da marca."""
    W, H = img.size
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    r, g, b = CORES["fundo_tint"]
    
    # Degradê
    for y in range(H):
        if y < H * 0.3:
            alpha = 60
        elif y < H * 0.7:
            progress = (y - H * 0.3) / (H * 0.4)
            alpha = int(60 + progress * 130)
        else:
            alpha = 190
            
        draw.line([(0, y), (W, y)], fill=(r, g, b, alpha))
        
    return Image.alpha_composite(img.convert('RGBA'), overlay)

def draw_text_with_shadow(draw, position, text, font, fill=(255, 255, 255), shadow_color=(0, 0, 0, 200), anchor="ms"):
    """Desenha texto com uma sombra projetada (Drop Shadow) para maior legibilidade."""
    x, y = position
    # Offset da sombra
    offset = max(2, int(font.size * 0.05))
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_color, anchor=anchor)
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

def desenhar_elementos_premium(draw, W, H):
    """Adiciona molduras sutis e linhas separadoras para dar aspecto de design de agência."""
    # Moldura sutil interna (margem de 40px)
    margem = 40
    cor_moldura = (*CORES["destaque"][:3], 80)  # Dourado com transparência
    
    # Desenha 4 linhas finas formando um quadro (top, bottom, left, right)
    draw.line([(margem, margem), (W - margem, margem)], fill=cor_moldura, width=1)
    draw.line([(margem, H - margem), (W - margem, H - margem)], fill=cor_moldura, width=1)
    draw.line([(margem, margem), (margem, H - margem)], fill=cor_moldura, width=1)
    draw.line([(W - margem, margem), (W - margem, H - margem)], fill=cor_moldura, width=1)
    
    # Linha separadora elegante (cross-hair style)
    # Fica próxima do centro/topo
    draw.line([(W/2 - 100, margem + 80), (W/2 + 100, margem + 80)], fill=cor_moldura, width=2)
