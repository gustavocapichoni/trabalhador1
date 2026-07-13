import os
import random
import requests
import textwrap
import numpy as np
import uuid
from PIL import Image, ImageDraw, ImageFont
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS
    
from loguru import logger
from core.design.templates import obter_fonte_do_dia
from core.config.state import verificar_midia_recente, registrar_midia_usada

def _carregar_fonte(tamanho=50, estilo=None):
    """Tenta carregar a fonte do projeto. Se falhar, usa a padrão do sistema."""
    if estilo is None:
        estilo = obter_fonte_do_dia()
    
    # Garante que o nome da fonte tenha a extensão .ttf
    if not estilo.endswith(".ttf"):
        estilo += ".ttf"
        
    caminhos = [
        f"fontes/{estilo}",
        "fontes/MontserratBold.ttf", # Fallback 1
        "fontes/Montserrat-Bold.ttf", # Fallback 2
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

def _adicionar_texto_frame(frame_array, texto, fonte, chars_to_show=None, fade_alpha=1.0, deslocamento_y=0):
    """Desenha texto centralizado com sombra/fundo em um frame (numpy array)."""
    img = Image.fromarray(frame_array)
    w, h = img.size

    # Criamos uma camada de texto transparente
    txt_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

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
    
    # Apenas calculamos by0 para posicionar o texto
    by0 = (h - total_h) // 2

    y = by0 + padding_v + deslocamento_y
    chars_drawn = 0
    for linha, alt, lw in zip(linhas, alturas, larguras):
        x = (w - lw) // 2
        
        if chars_to_show is not None:
            if chars_drawn >= chars_to_show:
                break
            
            linha_len = len(linha)
            if chars_drawn + linha_len > chars_to_show:
                linha_render = text_render = linha[:chars_to_show - chars_drawn]
            else:
                linha_render = text_render = linha
            chars_drawn += linha_len + 1 # +1 for space between words
        else:
            linha_render = text_render = linha
            
        # Efeito de contorno (stroke) mais estilo premium em vez de apenas sombra
        draw.text((x + 3, y + 3), linha_render, font=fonte, fill=(0, 0, 0, int(150 * fade_alpha))) # Sombra suave
        draw.text((x, y), linha_render, font=fonte, fill=(255, 255, 255, int(255 * fade_alpha)), stroke_width=2, stroke_fill=(0, 0, 0, int(255 * fade_alpha))) # Contorno forte
        y += alt + espaco_entre

    # Mescla a camada do texto com a imagem de fundo
    img = Image.alpha_composite(img.convert("RGBA"), txt_layer).convert("RGB")

    return np.array(img)


def _adicionar_texto_cta(frame_array, texto, fonte_cta, chars_to_show=None, fade_alpha=1.0, deslocamento_y=0):
    """Desenha o CTA final com visual dourado e destacado — maior impacto visual."""
    img = Image.fromarray(frame_array)
    w, h = img.size

    # Criamos a camada transparente para o CTA
    cta_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(cta_layer)

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

    bx0 = max((w - total_w) // 2, margem_px)
    by0 = (h - total_h) // 2 + deslocamento_y
    bx1 = min(bx0 + total_w, w - margem_px)
    by1 = by0 + total_h
    
    # Borda dourada + fundo escuro na camada do CTA com opacidade controlada
    draw.rounded_rectangle([bx0 - 4, by0 - 4, bx1 + 4, by1 + 4], radius=22, fill=(212, 175, 55, int(200 * fade_alpha)))
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=18, fill=(10, 10, 10, int(210 * fade_alpha)))

    # Texto em dourado vibrante com sombra
    y = by0 + padding_v
    chars_drawn = 0
    for linha, alt, lw in zip(linhas, alturas, larguras):
        x = (w - lw) // 2
        
        if chars_to_show is not None:
            if chars_drawn >= chars_to_show:
                break
            
            linha_len = len(linha)
            if chars_drawn + linha_len > chars_to_show:
                linha_render = linha[:chars_to_show - chars_drawn]
            else:
                linha_render = linha
            chars_drawn += linha_len + 1
        else:
            linha_render = linha
            
        # Sombra preta
        draw.text((x + 3, y + 3), linha_render, font=fonte_cta, fill=(0, 0, 0, int(255 * fade_alpha)))
        # Texto dourado
        draw.text((x, y), linha_render, font=fonte_cta, fill=(255, 215, 0, int(255 * fade_alpha)))
        y += alt + espaco_entre

    # Mescla escurecimento de fundo suave
    escurece = Image.new("RGBA", img.size, (0, 0, 0, int(120 * fade_alpha)))
    img = Image.alpha_composite(img.convert("RGBA"), escurece)
    
    # Mescla o CTA desenhado por cima
    img = Image.alpha_composite(img, cta_layer).convert("RGB")

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

def gerar_pexels_story(query, slides, caminho_saida="pexels_story.mp4", tema=None, is_conquistador=False, is_reels_leads=False):
    from core.config.settings import PEXELS_API_KEY, PIXABAY_API_KEY
    import urllib.parse
    logger.info(f"🎥 Buscando vídeo com query: '{query}'")

    temp_vids = []
    clip = None
    final_clip = None
    bg_audio = None
    query_encoded = urllib.parse.quote(query)
    
    # Define quantos vídeos baixar: 4 para reels_leads (vídeos longos) e 1 para posts normais
    num_videos_necessarios = 4 if is_reels_leads else 1

    # --- NÍVEL 1: API DO PIXABAY ---
    if PIXABAY_API_KEY and len(temp_vids) < num_videos_necessarios:
        try:
            logger.info("🔍 [NÍVEL 1] Tentando buscar vídeo no Pixabay...")
            url_pixabay = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query_encoded}&video_type=film"
            res_pixabay = requests.get(url_pixabay, timeout=15)
            
            if res_pixabay.status_code == 200:
                data = res_pixabay.json()
                hits_originais = data.get("hits", [])
                
                # Foca apenas em vídeos que possuem resolução puramente vertical (evita recortes)
                hits = []
                for h in hits_originais:
                    v_dict = h.get("videos", {})
                    for size in ["large", "medium", "small", "tiny"]:
                        if size in v_dict and v_dict[size].get("height", 0) > v_dict[size].get("width", 0):
                            hits.append(h)
                            break
                            
                if hits:
                    random.shuffle(hits)
                    for hit in hits:
                        if len(temp_vids) >= num_videos_necessarios:
                            break
                        vid_id = str(hit.get("id", ""))
                        if not verificar_midia_recente(vid_id):
                            videos_dict = hit.get("videos", {})
                            
                            # Tenta pegar versão vertical (tiny/small) ou grande
                            link_download = None
                            for size in ["large", "medium", "small", "tiny"]:
                                if size in videos_dict and videos_dict[size].get("url"):
                                    link_download = videos_dict[size]["url"]
                                    # Preferimos vídeos verticais (altura > largura)
                                    if videos_dict[size].get("height", 0) > videos_dict[size].get("width", 0):
                                        break
                            
                            if link_download:
                                logger.info(f"✅ Vídeo {len(temp_vids)+1} encontrado no Pixabay! Baixando...")
                                vid_resp = requests.get(link_download, timeout=30)
                                temp_vid = f"temp_video_{uuid.uuid4().hex}.mp4"
                                with open(temp_vid, "wb") as f:
                                    f.write(vid_resp.content)
                                temp_vids.append(temp_vid)
                                registrar_midia_usada(vid_id)
                else:
                    logger.warning("⚠️ Nenhum vídeo encontrado no Pixabay para essa query.")
            else:
                logger.warning(f"⚠️ Pixabay retornou status {res_pixabay.status_code}.")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao acessar Pixabay: {e}")

    # --- NÍVEL 2: API DO PEXELS ---
    if PEXELS_API_KEY and len(temp_vids) < num_videos_necessarios:
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
                    for v in videos:
                        if len(temp_vids) >= num_videos_necessarios:
                            break
                        vid_id = str(v.get("id", ""))
                        if not verificar_midia_recente(vid_id):
                            video_files = v.get("video_files", [])
                            
                            # Foca estritamente nos arquivos de vídeo verticais (altura > largura)
                            arquivos_verticais = [f for f in video_files if f.get("height", 0) > f.get("width", 0)]
                            
                            link = None
                            if arquivos_verticais:
                                # Pega a melhor resolução vertical disponível
                                arquivos_verticais.sort(key=lambda x: x.get("width", 0), reverse=True)
                                link = arquivos_verticais[0]["link"]

                            if link:
                                logger.info(f"✅ Vídeo {len(temp_vids)+1} encontrado no Pexels! Baixando...")
                                vid_resp = requests.get(link, timeout=30)
                                temp_vid = f"temp_video_{uuid.uuid4().hex}.mp4"
                                with open(temp_vid, "wb") as f:
                                    f.write(vid_resp.content)
                                temp_vids.append(temp_vid)
                                registrar_midia_usada(vid_id)
            else:
                logger.warning(f"⚠️ Pexels retornou status {response.status_code}.")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao acessar Pexels: {e}")

    # --- FALLBACK: Biblioteca Local de Emergência ---
    if not temp_vids:
        tema_pasta = tema if tema else "geral"
        pasta_tema = os.path.join("biblioteca_local", "videos", tema_pasta)
        pasta_geral = os.path.join("biblioteca_local", "videos")

        for pasta in [pasta_tema, pasta_geral]:
            if os.path.exists(pasta):
                arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(".mp4")]
                if arquivos:
                    random.shuffle(arquivos)
                    for arq in arquivos:
                        if len(temp_vids) >= num_videos_necessarios:
                            break
                        escolhido = os.path.join(pasta, arq)
                        logger.info(f"📂 [EMERGÊNCIA] Usando vídeo local: {escolhido}")
                        temp_vids.append(escolhido)
                    break

    if not temp_vids:
        raise Exception("❌ Nenhum vídeo disponível: Pexels falhou e biblioteca local está vazia.")

    logger.info("🎬 Processando vídeo com MoviePy + Pillow...")
    clip_candidatos = []
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, VideoClip, concatenate_videoclips
        
        # Carrega todos os clips baixados
        for fn in temp_vids:
            clip_candidatos.append(VideoFileClip(fn))
            
        if len(clip_candidatos) == 1:
            clip = clip_candidatos[0]
        else:
            logger.info(f"🔗 Concatendo {len(clip_candidatos)} vídeos diferentes para o reels_leads...")
            # Força que todos os vídeos tenham o mesmo tamanho/escala antes de juntar
            width_target = min(c.w for c in clip_candidatos)
            height_target = min(c.h for c in clip_candidatos)
            
            clips_redimensionados = []
            for c in clip_candidatos:
                if c.w != width_target or c.h != height_target:
                    clips_redimensionados.append(c.resize((width_target, height_target)))
                else:
                    clips_redimensionados.append(c)
                    
            clip = concatenate_videoclips(clips_redimensionados, method="compose")
        
        # Controle de duração
        if is_reels_leads:
            # Para o reels de venda (manual), precisamos de bastante tempo (até 3 mins)
            # Como a soma dos vídeos baixados pode ser menor que 3 min, fazemos um loop do conjunto costurado
            duracao_original = clip.duration
            if duracao_original < 180:
                import moviepy.video.fx.all as vfx
                loops = int(180 // duracao_original) + 1 
                clip = clip.fx(vfx.loop, n=loops)
            
            duracao = min(clip.duration, 180) # Max 3 minutos
            clip = clip.subclip(0, duracao)
        else:
            # Limita duração a 15 seg para stories e reels normais
            duracao = min(clip.duration, 15)
            clip = clip.subclip(0, duracao)
        
        # Usa a fonte do dia da semana (identidade visual unificada)
        estilo_do_dia = obter_fonte_do_dia()
        logger.info(f"✨ Fonte do dia para o vídeo: {estilo_do_dia}")
        
        # Resolução do vídeo original
        video_w, video_h = clip.size
        # Fator de escala baseado na largura padrão de 1080
        fator_escala = video_w / 1080.0
        
        # Tamanhos proporcionais e maiores (aumento de base 86->96 e 72->80)
        tamanho_normal = max(60, int(96 * fator_escala))
        tamanho_cta = max(50, int(80 * fator_escala))
        
        fonte_normal = _carregar_fonte(tamanho=tamanho_normal, estilo=estilo_do_dia)
        fonte_cta    = _carregar_fonte(tamanho=tamanho_cta, estilo=estilo_do_dia)

        if slides:
            logger.info("✍️ Adicionando textos via Pillow (sem ImageMagick)...")
            total_slides = len(slides)
            tempo_por_slide = duracao / total_slides
            idx_cta = total_slides - 1  # Última cena = CTA

            efeitos = ["none", "none", "cinematic_bars", "vignette_dark"]
            efeito_escolhido = random.choice(efeitos)
            if efeito_escolhido != "none":
                logger.info(f"✨ Aplicando efeito de vídeo: {efeito_escolhido.upper()}")

            # Sorteia uma das 4 animações para variar o estilo das postagens
            animacoes_disponiveis = ["typewriter", "fade", "reveal", "static"]
            animacao = random.choice(animacoes_disponiveis)
            logger.info(f"🎬 Animação de texto selecionada: {animacao.upper()}")

            def _desenhar_assinatura_rodape(frame_array, fator_escala=1.0):
                """Desenha a assinatura GUSTAVO_8K_ em dourado no rodapé do vídeo."""
                img = Image.fromarray(frame_array).convert("RGB")
                draw = ImageDraw.Draw(img)
                w, h = img.size
                tamanho_marca = max(22, int(36 * fator_escala))
                fonte_rodape = _carregar_fonte(tamanho_marca, "Montserrat")
                texto_marca = "GUSTAVO_8K_"
                bb = draw.textbbox((0, 0), texto_marca, font=fonte_rodape)
                tw = bb[2] - bb[0]
                x_marca = (w - tw) // 2
                y_marca = h - int(60 * fator_escala)
                # Efeito de brilho dourado (glow)
                cor_brilho = (235, 160, 40, 50)
                for ox in [-2, -1, 0, 1, 2]:
                    for oy in [-2, -1, 0, 1, 2]:
                        if ox != 0 or oy != 0:
                            draw.text((x_marca + ox, y_marca + oy), texto_marca, font=fonte_rodape, fill=cor_brilho)
                # Sombra e texto dourado
                draw.text((x_marca + 2, y_marca + 2), texto_marca, font=fonte_rodape, fill=(0, 0, 0, 200))
                draw.text((x_marca, y_marca), texto_marca, font=fonte_rodape, fill=(250, 185, 55))
                return np.array(img)

            def make_frame(t):
                idx = min(int(t / tempo_por_slide), total_slides - 1)
                t_slide = t - (idx * tempo_por_slide)
                texto_completo = slides[idx]
                
                # SLIDE 0 (CAPA/GANCHO) e ÚLTIMO SLIDE (CTA): sempre estáticos para garantir leitura
                if idx == 0 or (is_conquistador and idx == idx_cta):
                    chars_to_show = None
                    fade_alpha = 1.0
                    deslocamento_y = 0
                else:
                    # Inicializa variáveis padrão
                    chars_to_show = None
                    fade_alpha = 1.0
                    deslocamento_y = 0
                    
                    # Executa a lógica de cada animação
                    if animacao == "typewriter":
                        # Digitação mais suave e lenta: 20 caracteres por segundo
                        chars_to_show = max(1, int(t_slide * 20))
                    elif animacao == "fade":
                        # Esmaecimento suave nos primeiros 0.8 segundos
                        fade_alpha = min(1.0, t_slide / 0.8)
                    elif animacao == "reveal":
                        # Revelação suave (fade + subindo de baixo para cima nos primeiros 0.8 segundos)
                        progresso = min(1.0, t_slide / 0.8)
                        fade_alpha = progresso
                        deslocamento_y = int(20 * (1.0 - progresso) * fator_escala)
                    # "static" mantém fade_alpha=1.0, deslocamento_y=0 e chars_to_show=None
                
                frame = clip.get_frame(t)
                frame = _aplicar_efeito_cinematico(frame, efeito_escolhido)
                
                # Última cena = CTA em destaque dourado
                if is_conquistador and idx == idx_cta:
                    frame = _adicionar_texto_cta(
                        frame, texto_completo, fonte_cta, 
                        chars_to_show=chars_to_show, fade_alpha=fade_alpha, deslocamento_y=deslocamento_y
                    )
                else:
                    frame = _adicionar_texto_frame(
                        frame, texto_completo, fonte_normal, 
                        chars_to_show=chars_to_show, fade_alpha=fade_alpha, deslocamento_y=deslocamento_y
                    )
                
                # Assinatura GUSTAVO_8K_ sempre visível no rodapé
                frame = _desenhar_assinatura_rodape(frame, fator_escala)
                return frame

            final_clip = VideoClip(make_frame, duration=duracao)
            final_clip = final_clip.set_fps(clip.fps or 24)
        else:
            final_clip = clip

        # Adicionar áudio de fundo
        try:
            from core.media.reels import garantir_audio_reels
            import moviepy.audio.fx.all as afx
            audio_path = garantir_audio_reels()
            if audio_path:
                bg_audio = AudioFileClip(audio_path)
                # Loop no áudio se for menor que a duração do vídeo longo
                if bg_audio.duration < duracao:
                    bg_audio = afx.audio_loop(bg_audio, duration=duracao)
                    
                bg_audio = bg_audio.subclip(0, duracao)
                final_clip = final_clip.set_audio(bg_audio)
                logger.info("🎵 Áudio de fundo adicionado!")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao adicionar áudio de fundo: {e}")

        logger.info(f"⚙️ Exportando vídeo final para {caminho_saida}...")
        # Para reels_leads (até 3 min), limita o bitrate para ~3000kbps
        # Isso gera ~67MB para 3 minutos — bem abaixo do limite do catbox.moe (200MB).
        # Sem limitação, o ultrafast preset pode gerar 300-500MB e o upload falha com 412.
        write_kwargs = dict(
            fps=24, codec="libx264",
            audio_codec="aac", logger=None, threads=4, preset="ultrafast"
        )
        if is_reels_leads:
            write_kwargs["bitrate"] = "3000k"
            logger.info("📦 [reels_leads] Bitrate limitado a 3000kbps para manter o arquivo abaixo de 100MB.")
        final_clip.write_videofile(caminho_saida, **write_kwargs)
        return caminho_saida

    except Exception as e:
        logger.warning(f"⚠️ Erro ao processar o vídeo: {e}.")
        # Libera os arquivos
        try:
            if clip: clip.close()
            if final_clip: final_clip.close()
            if bg_audio: bg_audio.close()
            for c in clip_candidatos:
                try: c.close()
                except: pass
        except: pass
        raise e
    finally:
        # Limpeza final
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
        try:
            if bg_audio:
                bg_audio.close()
        except:
            pass
        # Fecha todos os sub-clipes individuais
        for c in clip_candidatos:
            try:
                c.close()
            except:
                pass
        # Apaga todos os arquivos baixados temporariamente
        for fn in temp_vids:
            if os.path.exists(fn):
                try:
                    os.remove(fn)
                except Exception as clean_err:
                    logger.debug(f"Não foi possível remover arquivo temporário {fn}: {clean_err}")
