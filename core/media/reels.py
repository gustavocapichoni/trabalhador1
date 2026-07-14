import os
import glob
import random
import numpy as np
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS
from moviepy.editor import ImageClip, AudioFileClip
from loguru import logger

def garantir_audio_reels():
    from core.config.state import carregar_estado, salvar_estado
    try:
        pastas = [os.path.join("biblioteca_local", "musicas"), "musicas", "."]
        mp3_files = []
        for pasta in pastas:
            if os.path.exists(pasta):
                for f in os.listdir(pasta):
                    if f.lower().endswith(".mp3") and os.path.isfile(os.path.join(pasta, f)):
                        mp3_files.append(os.path.join(pasta, f))
        if mp3_files:
            estado = carregar_estado()
            fila_musicas = estado.get("fila_musicas", [])
            
            # Filtra a fila para remover arquivos que não existem mais
            fila_musicas = [f for f in fila_musicas if os.path.exists(f)]
            
            # Se a fila acabou ou está vazia, cria uma nova com todas as músicas embaralhadas
            if not fila_musicas:
                logger.info("🎶 Fila de músicas esgotada. Criando nova fila com todas as músicas...")
                nova_fila = mp3_files.copy()
                random.shuffle(nova_fila)
                fila_musicas = nova_fila
            
            # Pega a próxima música da fila (a primeira da lista)
            escolhido = fila_musicas.pop(0)
            logger.info(f"🎵 Próxima música da fila: '{os.path.basename(escolhido)}' | Restam {len(fila_musicas)} na fila.")
            
            # Salva a fila atualizada no estado
            estado["fila_musicas"] = fila_musicas
            # Remove campo antigo se existir para não confundir
            estado.pop("ultimas_musicas", None)
            salvar_estado(estado)
            
            return escolhido

    except Exception as e:
        logger.warning(f"⚠️ Erro ao listar arquivos de audio: {e}")
        
    audio_path = "background.mp3"
    if os.path.exists(audio_path):
        return audio_path
        
    logger.info("🎵 Nenhum arquivo MP3 encontrado. Tentando gerar silêncio temporário...")
    import subprocess
    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=mono",
            "-t", "10",
            "-q:a", "9",
            audio_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(audio_path):
            return audio_path
    except Exception as e:
        logger.warning(f"⚠️ Erro ao gerar silêncio temporário com ffmpeg: {e}")
        pass
    return None
def gerar_video_reels(caminhos_imagens, caminho_audio, caminho_saida="reels_pronto.mp4",
                      textos=None, fonte_path=None, fonte_size=86):
    logger.info("🎬 Montando slideshow 9:16 com música de fundo e animações de texto...")
    if 'ImageClip' not in globals() or 'AudioFileClip' not in globals():
        raise ImportError("A biblioteca 'moviepy' não está instalada! Execute 'pip install moviepy' para gerar Reels.")

    if isinstance(caminhos_imagens, str):
        caminhos_imagens = [caminhos_imagens]
    if textos is None:
        textos = []

    try:
        from moviepy import concatenate_videoclips, VideoClip
    except ImportError:
        from moviepy.editor import concatenate_videoclips, VideoClip  # type: ignore

    from PIL import Image as PILImage, ImageDraw as PILDraw, ImageFont as PILFont
    import textwrap as textwrap_mod

    audio_clip = None
    video_clip = None
    try:
        audio_clip = AudioFileClip(caminho_audio)
        duracao_por_slide = 3.0
        DURACAO_ULTIMO_SLIDE = 7.0  # Último slide (CTA) tem mais tempo para leitura
        n_slides = len(caminhos_imagens)

        # Dimensões da imagem (necessário antes de carregar o outro)
        try:
            with PILImage.open(caminhos_imagens[0]) as fi:
                W, H = fi.size
        except:
            W, H = 1080, 1920

        # --- Carrega o vídeo final (mudo) cedo para saber sua duração ---
        # A música dos slides deve continuar tocando por cima do vídeo final
        outro_clip = None
        outro_duracao = 0.0
        path_video_final = os.path.join("biblioteca_local", "logo", "video.mp4")
        if os.path.exists(path_video_final):
            try:
                try:
                    from moviepy.editor import VideoFileClip as _VFC
                except ImportError:
                    from moviepy import VideoFileClip as _VFC  # type: ignore
                outro_clip = _VFC(path_video_final)
                if outro_clip.w != W or outro_clip.h != H:
                    try:
                        outro_clip = outro_clip.resized((W, H))
                    except AttributeError:
                        outro_clip = outro_clip.resize((W, H))
                outro_duracao = outro_clip.duration
                logger.info(f"🎬 [Reels] Vídeo final carregado: {outro_duracao:.1f}s (mudo — música continua)")
            except Exception as _e_load:
                logger.warning(f"⚠️ Não foi possível carregar vídeo final: {_e_load}")
                outro_clip = None
                outro_duracao = 0.0

        # Duração do áudio = slides + vídeo final (música cobre tudo)
        duracao_slides = (n_slides - 1) * duracao_por_slide + DURACAO_ULTIMO_SLIDE
        duracao_total_audio = duracao_slides + outro_duracao

        if duracao_total_audio > audio_clip.duration:
            # Ajusta as durações para caber no áudio disponível
            ratio = audio_clip.duration / duracao_total_audio
            duracao_por_slide = duracao_por_slide * ratio
            DURACAO_ULTIMO_SLIDE = max(duracao_por_slide, DURACAO_ULTIMO_SLIDE * ratio)
            duracao_slides = (n_slides - 1) * duracao_por_slide + DURACAO_ULTIMO_SLIDE
            duracao_total_audio = audio_clip.duration

        try:
            audio_clip = audio_clip.subclipped(0, duracao_total_audio)
        except AttributeError:
            audio_clip = audio_clip.subclip(0, duracao_total_audio)

        from datetime import datetime, timezone
        import random as _random
        dia_semana = datetime.now(timezone.utc).weekday()
        dias_nomes     = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        texto_anims    = ["Máquina de Escrever", "Surgimento por Palavras", "Fade In Suave",
                          "Zoom-In Dinâmico", "Slide de Baixo", "Glitch/Vibração", "Karaokê Dourado"]
        imagem_anims   = ["Fade In", "Slide Direita", "Zoom In", "Slide Baixo",
                          "Slide Esquerda", "Zoom Out", "Slide Topo"]

        logger.info(f"🎭 [Reels] {dias_nomes[dia_semana]}: Imagem={imagem_anims[dia_semana]} | Texto={texto_anims[dia_semana]}")

        FPS = 24

        # --- Carrega fonte ---
        fonte_texto = None
        if fonte_path and os.path.exists(fonte_path):
            try:
                fonte_texto = PILFont.truetype(fonte_path, fonte_size)
            except:
                pass
        if fonte_texto is None:
            for fp in ["fontes/BebasNeue.ttf", "fontes/MontserratBold.ttf", "arial.ttf"]:
                if os.path.exists(fp):
                    try:
                        fonte_texto = PILFont.truetype(fp, fonte_size)
                        break
                    except:
                        pass
        if fonte_texto is None:
            fonte_texto = PILFont.load_default()

        # --- Função: desenha o texto animado sobre um frame numpy ---
        def desenhar_texto_animado(frame_np, texto, t, duracao, dia, W, H, eh_primeiro_slide, eh_ultimo_slide=False):
            """Renderiza o texto com a animação do dia sobre o frame numpy e retorna novo frame numpy."""
            if not texto:
                return frame_np

            img = PILImage.fromarray(frame_np).convert("RGBA")
            txt_layer = PILImage.new("RGBA", (W, H), (0, 0, 0, 0))
            draw = PILDraw.Draw(txt_layer)

            progresso = min(t / duracao, 1.0)

            # Quebra o texto em linhas que cabem na tela
            palavras = texto.split()
            linhas = textwrap_mod.wrap(texto, width=20)
            altura_linha = fonte_size + 14
            y_centro = (H - (len(linhas) * altura_linha)) / 2

            # Cor principal (branco) e sombra
            COR_PRINCIPAL = (255, 255, 255, 255)
            COR_SOMBRA    = (0, 0, 0, 200)
            COR_CINZA     = (180, 180, 180, 255)
            COR_OURO      = (250, 185, 55, 255)

            # --- Primeiro slide (capa/gancho) e último slide (CTA): texto 100% estático ---
            if eh_primeiro_slide or eh_ultimo_slide:
                for li, linha in enumerate(linhas):
                    y = y_centro + li * altura_linha
                    try:
                        lw = draw.textlength(linha, font=fonte_texto)
                    except:
                        lw = len(linha) * (fonte_size * 0.55)
                    x = (W - lw) / 2
                    draw.text((x + 2, y + 2), linha, font=fonte_texto, fill=COR_SOMBRA)
                    draw.text((x, y), linha, font=fonte_texto, fill=COR_PRINCIPAL)
            
            # --- Slides internos (idx > 0) têm a animação do dia ---
            elif dia == 0:  # Segunda: MÁQUINA DE ESCREVER (letra a letra)
                total_chars = sum(len(l) for l in linhas) + len(linhas)
                chars_visiveis = int(progresso * total_chars)
                chars_drawn = 0
                for li, linha in enumerate(linhas):
                    if chars_drawn >= chars_visiveis:
                        break
                    chars_restantes = chars_visiveis - chars_drawn
                    trecho = linha[:chars_restantes]
                    y = y_centro + li * altura_linha
                    try:
                        lw = draw.textlength(trecho, font=fonte_texto)
                    except:
                        lw = len(trecho) * (fonte_size * 0.55)
                    x = (W - lw) / 2
                    draw.text((x + 2, y + 2), trecho, font=fonte_texto, fill=COR_SOMBRA)
                    draw.text((x, y), trecho, font=fonte_texto, fill=COR_PRINCIPAL)
                    chars_drawn += len(linha) + 1

            elif dia == 1:  # Terça: SURGIMENTO POR PALAVRAS
                total_palavras = sum(len(l.split()) for l in linhas)
                palavras_visiveis = max(1, int(progresso * total_palavras))
                palavras_drawn = 0
                for li, linha in enumerate(linhas):
                    palavras_linha = linha.split()
                    palavras_ate_aqui = palavras_drawn + len(palavras_linha)
                    if palavras_drawn >= palavras_visiveis:
                        break
                    trecho_palavras = palavras_linha[:palavras_visiveis - palavras_drawn]
                    trecho = " ".join(trecho_palavras)
                    y = y_centro + li * altura_linha
                    try:
                        lw = draw.textlength(trecho, font=fonte_texto)
                    except:
                        lw = len(trecho) * (fonte_size * 0.55)
                    x = (W - lw) / 2
                    draw.text((x + 2, y + 2), trecho, font=fonte_texto, fill=COR_SOMBRA)
                    draw.text((x, y), trecho, font=fonte_texto, fill=COR_PRINCIPAL)
                    palavras_drawn = palavras_ate_aqui

            elif dia == 2:  # Quarta: FADE IN SUAVE DO TEXTO
                alpha = min(int(progresso * 2 * 255), 255)  # completa em 50% do slide
                cor_txt = (255, 255, 255, alpha)
                cor_shd = (0, 0, 0, int(alpha * 0.78))
                for li, linha in enumerate(linhas):
                    y = y_centro + li * altura_linha
                    try:
                        lw = draw.textlength(linha, font=fonte_texto)
                    except:
                        lw = len(linha) * (fonte_size * 0.55)
                    x = (W - lw) / 2
                    draw.text((x + 2, y + 2), linha, font=fonte_texto, fill=cor_shd)
                    draw.text((x, y), linha, font=fonte_texto, fill=cor_txt)

            elif dia == 3:  # Quinta: ZOOM-IN DINÂMICO (texto cresce de 50% a 100%)
                escala = 0.5 + 0.5 * min(progresso * 2, 1.0)
                tamanho_zoom = max(12, int(fonte_size * escala))
                try:
                    fonte_zoom = PILFont.truetype(fonte_path or "fontes/BebasNeue.ttf", tamanho_zoom)
                except:
                    fonte_zoom = fonte_texto
                for li, linha in enumerate(linhas):
                    y = y_centro + li * altura_linha
                    try:
                        lw = draw.textlength(linha, font=fonte_zoom)
                    except:
                        lw = len(linha) * (tamanho_zoom * 0.55)
                    x = (W - lw) / 2
                    draw.text((x + 2, y + 2), linha, font=fonte_zoom, fill=COR_SOMBRA)
                    draw.text((x, y), linha, font=fonte_zoom, fill=COR_PRINCIPAL)

            elif dia == 4:  # Sexta: ENTRADA DESLIZANTE DE BAIXO
                deslocamento = int(H * 0.3 * max(0, 1.0 - progresso * 3))
                for li, linha in enumerate(linhas):
                    y = y_centro + li * altura_linha + deslocamento
                    try:
                        lw = draw.textlength(linha, font=fonte_texto)
                    except:
                        lw = len(linha) * (fonte_size * 0.55)
                    x = (W - lw) / 2
                    draw.text((x + 2, y + 2), linha, font=fonte_texto, fill=COR_SOMBRA)
                    draw.text((x, y), linha, font=fonte_texto, fill=COR_PRINCIPAL)

            elif dia == 5:  # Sábado: GLITCH / VIBRAÇÃO (nos primeiros 0.6s e a cada 1s)
                vibra = (t < 0.6) or (0.95 < (t % 1.0) < 1.0)
                ox = _random.randint(-8, 8) if vibra else 0
                oy = _random.randint(-5, 5) if vibra else 0
                # Canal vermelho deslocado (efeito glitch de cor)
                cor_glitch = (255, 40, 40, 180) if vibra else COR_SOMBRA
                for li, linha in enumerate(linhas):
                    y = y_centro + li * altura_linha
                    try:
                        lw = draw.textlength(linha, font=fonte_texto)
                    except:
                        lw = len(linha) * (fonte_size * 0.55)
                    x = (W - lw) / 2
                    if vibra:
                        draw.text((x + ox + 4, y + oy + 4), linha, font=fonte_texto, fill=cor_glitch)
                    draw.text((x + 2, y + 2), linha, font=fonte_texto, fill=COR_SOMBRA)
                    draw.text((x + ox, y + oy), linha, font=fonte_texto, fill=COR_PRINCIPAL)

            elif dia == 6:  # Domingo: KARAOKÊ (palavras acendem de cinza para dourado)
                total_palavras = sum(len(l.split()) for l in linhas)
                palavras_acesas = int(progresso * total_palavras)
                contador_p = 0
                for li, linha in enumerate(linhas):
                    palavras_linha = linha.split()
                    try:
                        lw_total = draw.textlength(linha, font=fonte_texto)
                    except:
                        lw_total = len(linha) * (fonte_size * 0.55)
                    x_linha = (W - lw_total) / 2
                    y = y_centro + li * altura_linha
                    x_cursor = x_linha
                    for palavra in palavras_linha:
                        cor_p = COR_OURO if contador_p < palavras_acesas else COR_CINZA
                        draw.text((x_cursor + 2, y + 2), palavra, font=fonte_texto, fill=COR_SOMBRA)
                        draw.text((x_cursor, y), palavra, font=fonte_texto, fill=cor_p)
                        try:
                            pw = draw.textlength(palavra + " ", font=fonte_texto)
                        except:
                            pw = len(palavra + " ") * (fonte_size * 0.55)
                        x_cursor += pw
                        contador_p += 1

            # Compõe o texto sobre o frame
            img = PILImage.alpha_composite(img, txt_layer)
            return np.array(img.convert("RGB"))

        # --- Função: gera todos os frames de um slide (imagem + texto animado) ---
        def gerar_frames_slide(caminho_img, texto, duracao, dia, eh_primeiro_slide, W, H, fps, eh_ultimo_slide=False):  # noqa
            total_frames = int(duracao * fps)
            fade_frames  = int(0.5 * fps)

            img_pil = PILImage.open(caminho_img).convert("RGB").resize((W, H), PILImage.Resampling.LANCZOS)
            img_np  = np.array(img_pil)

            frames = []
            for f in range(total_frames):
                t = f / fps
                progresso = t / duracao
                frame = img_np.copy()

                # --- Transição de entrada da IMAGEM (slides 2+) ---
                if not eh_primeiro_slide and t < 0.5:
                    p = t / 0.5
                    if dia == 0:
                        frame = (frame * p).astype(np.uint8)
                    elif dia == 1:
                        offset_x = int(W * (1.0 - p))
                        canvas = np.zeros_like(frame)
                        dst_w = W - offset_x
                        if dst_w > 0:
                            canvas[:, :dst_w] = frame[:, offset_x:]
                        frame = canvas
                    elif dia == 2:
                        scale = 1.0 + 0.10 * progresso
                        new_w, new_h = int(W * scale), int(H * scale)
                        iz = PILImage.fromarray(frame).resize((new_w, new_h), PILImage.Resampling.LANCZOS)
                        cx, cy = (new_w - W) // 2, (new_h - H) // 2
                        frame = np.array(iz.crop((cx, cy, cx + W, cy + H)))
                    elif dia == 3:
                        offset_y = int(H * (1.0 - p))
                        canvas = np.zeros_like(frame)
                        dst_h = H - offset_y
                        if dst_h > 0:
                            canvas[:dst_h, :] = frame[offset_y:, :]
                        frame = canvas
                    elif dia == 4:
                        offset_x = int(W * (1.0 - p))
                        canvas = np.zeros_like(frame)
                        dst_w = W - offset_x
                        if dst_w > 0:
                            canvas[:, offset_x:] = frame[:, :dst_w]
                        frame = canvas
                    elif dia == 5:
                        scale = 1.10 - 0.10 * progresso
                        new_w, new_h = int(W * scale), int(H * scale)
                        iz = PILImage.fromarray(frame).resize((new_w, new_h), PILImage.Resampling.LANCZOS)
                        cx, cy = (new_w - W) // 2, (new_h - H) // 2
                        frame = np.array(iz.crop((cx, cy, cx + W, cy + H)))
                    elif dia == 6:
                        offset_y = int(H * (1.0 - p))
                        canvas = np.zeros_like(frame)
                        dst_h = H - offset_y
                        if dst_h > 0:
                            canvas[offset_y:, :] = frame[:dst_h, :]
                        frame = canvas

                # --- Animação de TEXTO sobre o frame ---
                if texto:
                    frame = desenhar_texto_animado(frame, texto, t, duracao, dia, W, H, eh_primeiro_slide, eh_ultimo_slide)

                # --- FadeOut no final do slide ---
                frames_restantes = total_frames - f
                if frames_restantes <= fade_frames and fade_frames > 0:
                    alpha = frames_restantes / fade_frames
                    frame = (frame * alpha).astype(np.uint8)

                frames.append(frame)

            return frames

        # --- Gera os clipes ---
        clips = []
        for idx, caminho in enumerate(caminhos_imagens):
            texto_slide = textos[idx] if idx < len(textos) else ""
            eh_ultimo = (idx == n_slides - 1)
            # Último slide (CTA) tem duração maior para garantir leitura completa
            dur_slide = DURACAO_ULTIMO_SLIDE if eh_ultimo else duracao_por_slide
            try:
                frames_lista = gerar_frames_slide(
                    caminho, texto_slide, dur_slide,
                    dia_semana, idx == 0, W, H, FPS, eh_ultimo
                )

                def make_frame_fn(fl=frames_lista, ds=dur_slide):
                    def frame_fn(t):
                        fi = min(int(t * FPS), len(fl) - 1)
                        return fl[fi]
                    return frame_fn

                clip = VideoClip(make_frame_fn(), duration=dur_slide)
            except Exception as e:
                logger.warning(f"⚠️ Falha no slide {idx} animado: {e}. Usando ImageClip.")
                try:
                    clip = ImageClip(caminho).with_duration(dur_slide)
                except:
                    clip = ImageClip(caminho).set_duration(dur_slide)

            clips.append(clip)

        # Concatena todos os slides (sem áudio ainda)
        video_clip = concatenate_videoclips(clips, method="compose")

        # Acopla o vídeo final (mudo) ANTES de aplicar o áudio
        # para que a música cubra tanto os slides quanto o vídeo final
        if outro_clip is not None:
            try:
                video_clip = concatenate_videoclips([video_clip, outro_clip], method="compose")
                logger.success("✅ Vídeo final (mudo) acoplado. Música continuará por cima.")
            except Exception as e_outro:
                logger.warning(f"⚠️ Erro ao acoplar o vídeo final: {e_outro}")

        # Aplica a música sobre o vídeo completo (slides + vídeo final)
        try:
            video_clip = video_clip.with_audio(audio_clip)
        except AttributeError:
            video_clip = video_clip.set_audio(audio_clip)

        logger.info(f"⚙️ Renderizando slideshow de {len(caminhos_imagens)} slides + vídeo final...")

        import glob as _glob
        for temp_file in _glob.glob("*TEMP_MPY*"):
            try:
                os.remove(temp_file)
            except:
                pass

        try:
            video_clip.write_videofile(caminho_saida, fps=FPS, codec="libx264", audio_codec="aac", logger=None)
        except TypeError:
            video_clip.write_videofile(caminho_saida, fps=FPS, codec="libx264", audio_codec="aac")

        logger.success(f"✅ Vídeo gerado com sucesso como {caminho_saida}")
        return caminho_saida
    except Exception as e:
        logger.error(f"❌ Erro ao converter imagem para vídeo com moviepy: {e}")
        raise e
    finally:
        # Garante liberação dos recursos mesmo em caso de erro (evita WinError 32)
        if video_clip is not None:
            try:
                video_clip.close()
            except Exception:
                pass
        if audio_clip is not None:
            try:
                audio_clip.close()
            except Exception:
                pass
        if outro_clip is not None:
            try:
                outro_clip.close()
            except Exception:
                pass


def gerar_video_story_individual(caminho_imagem, caminho_audio, caminho_saida="story_pronto.mp4", tempo_inicio=0.0):
    logger.info(f"🎬 Convertendo Story {caminho_imagem} em vídeo com música (inicio: {tempo_inicio}s)...")
    if 'ImageClip' not in globals() or 'AudioFileClip' not in globals():
        raise ImportError("A biblioteca 'moviepy' não está instalada! Execute 'pip install moviepy' para gerar Stories em vídeo.")

    audio_clip = None
    video_clip = None
    try:
        from moviepy.editor import afx
        
        audio_clip = AudioFileClip(caminho_audio)
        duracao_total = 10.0  # fixo em 10 segundos por slide
        
        # Faz um loop na música caso ela seja curta demais para o tempo_inicio + 10s
        if audio_clip.duration < tempo_inicio + duracao_total:
            audio_clip = afx.audio_loop(audio_clip, duration=tempo_inicio + duracao_total + 5)
        
        try:
            audio_clip = audio_clip.subclipped(tempo_inicio, tempo_inicio + duracao_total)
        except AttributeError:
            audio_clip = audio_clip.subclip(tempo_inicio, tempo_inicio + duracao_total)

        clip = ImageClip(caminho_imagem).set_duration(duracao_total)
        
        try:
            video_clip = clip.with_audio(audio_clip)
        except AttributeError:
            video_clip = clip.set_audio(audio_clip)

        logger.info(f"⚙️ Renderizando vídeo Story ({duracao_total:.1f}s)...")
        
        try:
            video_clip.write_videofile(
                caminho_saida,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None
            )
        except TypeError:
            video_clip.write_videofile(
                caminho_saida,
                fps=24,
                codec="libx264",
                audio_codec="aac"
            )
        logger.success(f"✅ Vídeo Story gerado com sucesso como {caminho_saida}")
        return caminho_saida
    except Exception as e:
        logger.error(f"❌ Erro ao converter story para vídeo: {e}")
        raise e
    finally:
        if video_clip is not None:
            try:
                video_clip.close()
            except Exception:
                pass
        if audio_clip is not None:
            try:
                audio_clip.close()
            except Exception:
                pass
