import os
import random
import requests
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def _carregar_fonte(tamanho=50):
    """Tenta carregar a fonte do projeto. Se falhar, usa a padrão do sistema."""
    caminhos = [
        "fontes/MontserratBold.ttf",
        "fontes/Montserrat-Bold.ttf",
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

def _adicionar_texto_frame(frame_array, texto, fonte):
    """Desenha texto centralizado com sombra/fundo em um frame (numpy array)."""
    img = Image.fromarray(frame_array)
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # Quebra o texto para caber na tela
    linhas = textwrap.wrap(texto, width=28)
    
    # Calcula altura total do bloco de texto
    alturas = [draw.textbbox((0, 0), l, font=fonte)[3] - draw.textbbox((0, 0), l, font=fonte)[1] for l in linhas]
    espaco_entre = 12
    total_h = sum(alturas) + espaco_entre * (len(linhas) - 1) + 40  # padding
    total_w = max([draw.textbbox((0, 0), l, font=fonte)[2] - draw.textbbox((0, 0), l, font=fonte)[0] for l in linhas] or [w]) + 60

    # Fundo semitransparente atrás do texto
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    bx0 = (w - total_w) // 2
    by0 = (h - total_h) // 2
    bx1 = bx0 + total_w
    by1 = by0 + total_h
    overlay_draw.rounded_rectangle([bx0, by0, bx1, by1], radius=18, fill=(0, 0, 0, 160))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Desenha cada linha centralizada
    y = by0 + 20
    for linha, alt in zip(linhas, alturas):
        bbox = draw.textbbox((0, 0), linha, font=fonte)
        lw = bbox[2] - bbox[0]
        x = (w - lw) // 2
        # Sombra
        draw.text((x + 2, y + 2), linha, font=fonte, fill=(0, 0, 0, 200))
        # Texto principal
        draw.text((x, y), linha, font=fonte, fill=(255, 255, 255))
        y += alt + espaco_entre

    return np.array(img)

def gerar_pexels_story(query, slides, caminho_saida="pexels_story.mp4"):
    from core.config.settings import PEXELS_API_KEY
    print(f"🎥 Buscando vídeo no Pexels com query: '{query}'")
    if not PEXELS_API_KEY:
        raise ValueError("PEXELS_API_KEY não configurada! Verifique seu .env")

    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&size=medium&per_page=15"
    headers = {"Authorization": PEXELS_API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Erro na API do Pexels: {response.text}")
        
    data = response.json()
    if not data.get("videos"):
        print("⚠️ Nenhum vídeo encontrado, tentando fallback para 'nature'")
        response = requests.get("https://api.pexels.com/videos/search?query=nature&orientation=portrait&per_page=15", headers=headers)
        data = response.json()

    if not data.get("videos"):
        raise Exception("Nenhum vídeo retornado pelo Pexels.")

    video = random.choice(data["videos"])
    video_files = video.get("video_files", [])
    
    # Pega a melhor resolução HD vertical (720x1280 ou similar)
    link = None
    for f in video_files:
        if f.get("quality") == "hd" and f.get("width", 0) < f.get("height", 0):
            link = f["link"]
            break
    
    if not link and len(video_files) > 0:
        link = video_files[0]["link"]

    print("⬇️ Baixando vídeo do Pexels...")
    vid_resp = requests.get(link)
    temp_vid = "temp_pexels.mp4"
    with open(temp_vid, "wb") as f:
        f.write(vid_resp.content)

    print("🎬 Processando vídeo com MoviePy + Pillow...")
    clip = None
    final_clip = None
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, VideoClip
        clip = VideoFileClip(temp_vid)
        
        # Limita duração a 15 seg
        duracao = min(clip.duration, 15)
        clip = clip.subclip(0, duracao)
        
        fonte = _carregar_fonte(tamanho=52)
        
        if slides:
            print("✍️ Adicionando textos via Pillow (sem ImageMagick)...")
            tempo_por_slide = duracao / len(slides)
            
            def make_frame(t):
                # Descobre qual slide mostrar baseado no tempo
                idx = min(int(t / tempo_por_slide), len(slides) - 1)
                frame = clip.get_frame(t)
                frame = _adicionar_texto_frame(frame, slides[idx], fonte)
                return frame
            
            final_clip = VideoClip(make_frame, duration=duracao)
            final_clip = final_clip.set_fps(clip.fps or 24)
        else:
            final_clip = clip

        # Adicionar áudio de fundo
        try:
            from core.media.reels import garantir_audio_reels
            audio_path = garantir_audio_reels()
            if audio_path:
                bg_audio = AudioFileClip(audio_path).subclip(0, duracao)
                final_clip = final_clip.set_audio(bg_audio)
                print("🎵 Áudio de fundo adicionado!")
        except Exception as e:
            print(f"⚠️ Erro ao adicionar áudio de fundo: {e}")

        print(f"⚙️ Exportando vídeo final para {caminho_saida}...")
        final_clip.write_videofile(
            caminho_saida, fps=24, codec="libx264",
            audio_codec="aac", logger=None, threads=4, preset="ultrafast"
        )
        return caminho_saida

    except Exception as e:
        print(f"⚠️ Erro ao processar o vídeo: {e}. Retornando vídeo original.")
        if os.path.exists(temp_vid):
            os.rename(temp_vid, caminho_saida)
            return caminho_saida
        raise e
    finally:
        # Garante que os handles são fechados SEMPRE, mesmo em caso de erro
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
        if os.path.exists(temp_vid):
            try:
                os.remove(temp_vid)
            except:
                pass
