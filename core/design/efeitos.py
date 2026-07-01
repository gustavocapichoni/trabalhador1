# Efeitos Visuais Premium
from PIL import Image, ImageDraw, ImageFilter

def aplicar_mesh_gradient(img):
    """Aplica um degradê inteligente, escurecendo mais a parte inferior e central."""
    W, H = img.size
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Degradê
    for y in range(H):
        if y < H * 0.3:
            alpha = 40
        elif y < H * 0.7:
            progress = (y - H * 0.3) / (H * 0.4)
            alpha = int(40 + progress * 140)
        else:
            alpha = 180
            
        draw.line([(0, y), (W, y)], fill=(15, 15, 15, alpha))
        
    return Image.alpha_composite(img.convert('RGBA'), overlay)

def draw_text_with_shadow(draw, position, text, font, fill=(255, 255, 255), shadow_color=(0, 0, 0, 200), anchor="ms"):
    """Desenha texto com uma sombra projetada (Drop Shadow) para maior legibilidade."""
    x, y = position
    # Offset da sombra
    offset = max(2, int(font.size * 0.05))
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_color, anchor=anchor)
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)
