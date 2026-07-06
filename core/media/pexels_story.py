import os
import random
import requests
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
from core.config.state import verificar_midia_recente, registrar_midia_usada

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

def _adicionar_texto_frame(frame_array, texto, fonte):
    """Desenha texto centralizado com sombra/fundo em um frame (numpy array)."""
    img = Image.fromarray(frame_array)
    draw = ImageDraw.Draw(img)
    w, h = img.size

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
    padding_h = 24
    padding_v = 20

    total_h = sum(alturas) + espaco_entre * (len(linhas) - 1) + padding_v * 2
    total_w = min(max(larguras) + padding_h * 2, w - margem_px * 2)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    bx0 = max((w - total_w) // 2, margem_px)
    by0 = (h - total_h) // 2
    bx1 = min(bx0 + total_w, w - margem_px)
    by1 = by0 + total_h
    overlay_draw.rounded_rectangle([bx0, by0, bx1, by1], radius=18, fill=(0, 0, 0, 160))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    y = by0 + padding_v
    for linha, alt, lw in zip(linhas, alturas, larguras):
        x = (w - lw) // 2
        draw.text((x + 2, y + 2), linha, font=fonte, fill=(0, 0, 0, 200))
        draw.text((x, y), linha, font=fonte, fill=(255, 255, 255))
        y += alt + espaco_entre

    return np.array(img)


def _adicionar_texto_cta(frame_array, texto, fonte_cta):
    """Desenha o CTA final com visual dourado e destacado — maior impacto visual."""
    img = Image.fromarray(frame_array)

    # Escurece levemente o fundo para o CTA se destacar mais
    escurece = Image.new("RGBA", img.size, (0, 0, 0, 120))
    img = Image.alpha_composite(img.convert("RGBA"), escurece).convert("RGB")

    draw = ImageDraw.Draw(img)
    w, h = img.size

    margem_px = int(w * 0.08)
    largura_max_texto = w - (margem_px * 2)

    linhas = _quebrar_texto_por_pixels(draw, texto, fonte_cta, largura_max_texto)
    if not linhas:
        return frame_array

    alturas = []
    larguras = []
    for l in linhas:
        bb = draw.textbbox((0, 0), l, font=fonte_cta)
        alturas.append(bb[3] - bb[1])
        larguras.append(bb[2] - bb[0])

    espaco_entre = 18
    padding_h = 36
    padding_v = 28

    total_h = sum(alturas) + espaco_entre * (len(linhas) - 1) + padding_v * 2
    total_w = min(max(larguras) + padding_h * 2, w - margem_px * 2)

    # Fundo dourado semitransparente para o CTA
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    bx0 = max((w - total_w) // 2, margem_px)
    by0 = (h - total_h) // 2
    bx1 = min(bx0 + total_w, w - margem_px)
    by1 = by0 + total_h
    # Borda dourada + fundo escuro
    overlay_draw.rounded_rectangle([bx0 - 4, by0 - 4, bx1 + 4, by1 + 4], radius=22, fill=(212, 175, 55, 200))
    overlay_draw.rounded_rectangle([bx0, by0, bx1, by1], radius=18, fill=(10, 10, 10, 210))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Texto em dourado vibrante com sombra
    y = by0 + padding_v
    for linha, alt, lw in zip(linhas, alturas, larguras):
        x = (w - lw) // 2
        # Sombra preta
        draw.text((x + 3, y + 3), linha, font=fonte_cta, fill=(0, 0, 0))
        # Texto dourado
        draw.text((x, y), linha, font=fonte_cta, fill=(255, 215, 0))
        y += alt + espaco_entre

    return np.array(img)

def _aplicar_efeito_cinematico(frame_array, efeito):
    """Aplica efeitos visuais no frame para variar o estilo."""
    if efeito == "none":
        return frame_array
        
    img = Image.fromarray(frame_array)
    w, h = img.size
    draw = ImageDraw.Draw(img)
    
    if efeito == "cinematic_bars":
        # Altura das tarjas (12% da altura)
        bar_h = int(h * 0.12)
        draw.rectangle([0, 0, w, bar_h], fill=(0, 0, 0))
        draw.rectangle([0, h - bar_h, w, h], fill=(0, 0, 0))
        
    elif efeito == "vignette_dark":
        # Escurece levemente a imagem inteira (moody)
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 80))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        
    return np.array(img)

def gerar_pexels_story(query, slides, caminho_saida="pexels_story.mp4", tema=None, is_conquistador=False):
    from core.config.settings import PEXELS_API_KEY, PIXABAY_API_KEY
    import urllib.parse
    logger.info(f"🎥 Buscando vídeo com query: '{query}'")

    temp_vid = None
    query_encoded = urllib.parse.quote(query)

    # --- NÍVEL 1: API DO PIXABAY ---
    if PIXABAY_API_KEY and not temp_vid:
        try:
            logger.info("🔍 [NÍVEL 1] Tentando buscar vídeo no Pixabay...")
            url_pixabay = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query_encoded}&video_type=film"
            res_pixabay = requests.get(url_pixabay, timeout=15)
            
            if res_pixabay.status_code == 200:
                data = res_pixabay.json()
                hits = data.get("hits", [])
                
                if hits:
                    random.shuffle(hits)
                    video_escolhido = None
                    for hit in hits:
                        vid_id = str(hit.get("id", ""))
                        if not verificar_midia_recente(vid_id):
                            video_escolhido = hit
                            registrar_midia_usada(vid_id)
                            break
                            
                    if not video_escolhido:
                        video_escolhido = random.choice(hits)
                        logger.info("🔄 Todos os vídeos do Pixabay já foram usados. Repetindo um aleatório.")

                    videos_dict = video_escolhido.get("videos", {})
                    
                    # Tenta pegar versão vertical (tiny/small) ou grande
                    link_download = None
                    for size in ["large", "medium", "small", "tiny"]:
                        if size in videos_dict and videos_dict[size].get("url"):
                            link_download = videos_dict[size]["url"]
                            # Preferimos vídeos verticais (altura > largura)
                            if videos_dict[size].get("height", 0) > videos_dict[size].get("width", 0):
                                break
                    
                    if link_download:
                        logger.info("✅ Vídeo encontrado no Pixabay! Baixando...")
                        vid_resp = requests.get(link_download, timeout=30)
                        temp_vid = "temp_video.mp4"
                        with open(temp_vid, "wb") as f:
                            f.write(vid_resp.content)
                else:
                    logger.warning("⚠️ Nenhum vídeo encontrado no Pixabay para essa query.")
            else:
                logger.warning(f"⚠️ Pixabay retornou status {res_pixabay.status_code}.")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao acessar Pixabay: {e}")

    # --- NÍVEL 2: API DO PEXELS ---
    if PEXELS_API_KEY and not temp_vid:
        try:
            logger.info("🔍 [NÍVEL 2] Tentando buscar vídeo no Pexels...")
            url_pexels = f"https://api.pexels.com/videos/search?query={query_encoded}&orientation=portrait&size=medium&per_page=15"
            headers = {"Authorization": PEXELS_API_KEY}
            response = requests.get(url_pexels, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if not data.get("videos"):
                    logger.warning("⚠️ Nenhum vídeo encontrado no Pexels, tentando query coringa 'cinematic'")
                    response = requests.get("https://api.pexels.com/videos/search?query=cinematic&orientation=portrait&per_page=15", headers=headers, timeout=15)
                    data = response.json()

                if data.get("videos"):
                    videos = data["videos"]
                    random.shuffle(videos)
                    video = None
                    for v in videos:
                        vid_id = str(v.get("id", ""))
                        if not verificar_midia_recente(vid_id):
                            video = v
                            registrar_midia_usada(vid_id)
                            break
                            
                    if not video:
                        video = random.choice(videos)
                        logger.info("🔄 Todos os vídeos do Pexels já foram usados. Repetindo um aleatório.")
                        
                    video_files = video.get("video_files", [])
                    link = None
                    for f in video_files:
                        if f.get("quality") == "hd" and f.get("width", 0) < f.get("height", 0):
                            link = f["link"]
                            break
                    if not link and len(video_files) > 0:
                        link = video_files[0]["link"]

                    if link:
                        logger.info("✅ Vídeo encontrado no Pexels! Baixando...")
                        vid_resp = requests.get(link, timeout=30)
                        temp_vid = "temp_video.mp4"
                        with open(temp_vid, "wb") as f:
                            f.write(vid_resp.content)
            else:
                logger.warning(f"⚠️ Pexels retornou status {response.status_code}.")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao acessar Pexels: {e}")

    # --- FALLBACK: Biblioteca Local de Emergência ---
    if not temp_vid:
        tema_pasta = tema if tema else "geral"
        pasta_tema = os.path.join("biblioteca_local", "videos", tema_pasta)
        pasta_geral = os.path.join("biblioteca_local", "videos")

        for pasta in [pasta_tema, pasta_geral]:
            if os.path.exists(pasta):
                arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(".mp4")]
                if arquivos:
                    escolhido = os.path.join(pasta, random.choice(arquivos))
                    logger.info(f"📂 [EMERGÊNCIA] Usando vídeo local: {escolhido}")
                    temp_vid = escolhido
                    break

    if not temp_vid:
        raise Exception("❌ Nenhum vídeo disponível: Pexels falhou e biblioteca local está vazia.")

    logger.info("🎬 Processando vídeo com MoviePy + Pillow...")
    clip = None
    final_clip = None
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, VideoClip
        clip = VideoFileClip(temp_vid)
        
        # Limita duração a 15 seg
        duracao = min(clip.duration, 15)
        clip = clip.subclip(0, duracao)
        
        # FIX: Fonte reduzida de 52 para 42px — evita que frases longas ocupem
        # a tela inteira. A quebra de linha já funciona por pixels, mas o
        # tamanho da fonte determinava o tamanho final de cada linha.
        fonte_normal = _carregar_fonte(tamanho=42)
        fonte_cta    = _carregar_fonte(tamanho=52)  # CTA um pouco maior que o texto normal

        if slides:
            logger.info("✍️ Adicionando textos via Pillow (sem ImageMagick)...")
            total_slides = len(slides)
            tempo_por_slide = duracao / total_slides
            idx_cta = total_slides - 1  # Última cena = CTA

            efeitos = ["none", "none", "cinematic_bars", "vignette_dark"]
            efeito_escolhido = random.choice(efeitos)
            if efeito_escolhido != "none":
                logger.info(f"✨ Aplicando efeito de vídeo: {efeito_escolhido.upper()}")

            def make_frame(t):
                idx = min(int(t / tempo_por_slide), total_slides - 1)
                frame = clip.get_frame(t)
                frame = _aplicar_efeito_cinematico(frame, efeito_escolhido)
                # Última cena = CTA em destaque dourado
                if is_conquistador and idx == idx_cta:
                    frame = _adicionar_texto_cta(frame, slides[idx], fonte_cta)
                else:
                    frame = _adicionar_texto_frame(frame, slides[idx], fonte_normal)
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
                logger.info("🎵 Áudio de fundo adicionado!")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao adicionar áudio de fundo: {e}")

        logger.info(f"⚙️ Exportando vídeo final para {caminho_saida}...")
        final_clip.write_videofile(
            caminho_saida, fps=24, codec="libx264",
            audio_codec="aac", logger=None, threads=4, preset="ultrafast"
        )
        return caminho_saida

    except Exception as e:
        logger.warning(f"⚠️ Erro ao processar o vídeo: {e}. Retornando vídeo original.")
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
