import os
import glob
import random
import numpy as np
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS
from moviepy.editor import ImageClip, AudioFileClip
from loguru import logger

def garantir_audio_reels(pastas=None):
    from core.config.state import carregar_estado, salvar_estado
    try:
        # Garante caminhos absolutos baseados na raiz do projeto
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        estado = carregar_estado()
        
        # Mapeamento do sentimento do dia para as subpastas (apenas se for a pasta padrão e houver sentimento ativo)
        usando_pastas_padrao = (pastas is None)
        sentimento = estado.get("sentimento_do_dia")

        if pastas is None:
            if sentimento:
                from core.ai.styles import SENTIMENTOS_CONFIG
                config_emocional = SENTIMENTOS_CONFIG.get(sentimento)
                if config_emocional and "pasta_audio" in config_emocional:
                    sub_pasta_sentimento = config_emocional["pasta_audio"]
                    caminho_emocional = os.path.join(root_dir, "biblioteca_local", "musicas", sub_pasta_sentimento)
                    # Verifica se o usuário criou a pasta física para aquele sentimento
                    if os.path.exists(caminho_emocional) and os.listdir(caminho_emocional):
                        pastas = [caminho_emocional]
                        logger.info(f"🎶 [SINESTESIA] Usando subpasta de áudio do sentimento {sentimento.upper()}: '{sub_pasta_sentimento}'")
            
            # Se não houver sentimento ou a pasta do sentimento não existir/estiver vazia, usa a padrão
            if pastas is None:
                pastas = [os.path.join(root_dir, "biblioteca_local", "musicas")]
        else:
            pastas = [os.path.join(root_dir, p) if not os.path.isabs(p) else p for p in pastas]
            
        mp3_map = {}
        pasta_principal = "padrao"
        for pasta in pastas:
            if os.path.exists(pasta):
                pasta_principal = os.path.basename(pasta)
                for f in os.listdir(pasta):
                    if f.lower().endswith(".mp3") and os.path.isfile(os.path.join(pasta, f)):
                        mp3_map[f] = os.path.join(pasta, f)
        
        if mp3_map:
            chave_estado = f"fila_musicas_{pasta_principal}"
            
            # Pega a fila gravada no estado (pode conter caminhos antigos ou apenas nomes de arquivos)
            fila_bruta = estado.get(chave_estado, [])
            if pasta_principal == "musicas" and "fila_musicas" in estado:
                fila_bruta = estado.pop("fila_musicas")

            # Extrai apenas o nome do arquivo para garantir compatibilidade entre ambientes (Windows/Linux)
            fila_nomes = [os.path.basename(f) for f in fila_bruta if isinstance(f, str)]
            # Mantém na fila apenas os nomes de arquivos que realmente existem na pasta física
            fila_nomes = [nome for nome in fila_nomes if nome in mp3_map]

            # Detecta músicas novas que estão na pasta mas não constam na fila salva
            nomes_novos = [nome for nome in mp3_map.keys() if nome not in fila_nomes]
            if nomes_novos:
                logger.info(f"🎶 [{pasta_principal}] Encontrada(s) {len(nomes_novos)} nova(s) música(s) na pasta! Adicionando à fila...")
                random.shuffle(nomes_novos)
                fila_nomes.extend(nomes_novos)

            # Se a fila ficou vazia (todas tocaram), recria a fila embaralhada com todas as músicas da pasta
            if not fila_nomes:
                logger.info(f"🎶 Fila '{chave_estado}' concluída. Reiniciando ciclo com {len(mp3_map)} músicas embaralhadas...")
                todos_nomes = list(mp3_map.keys())
                random.shuffle(todos_nomes)
                fila_nomes = todos_nomes

            # Pega o próximo nome de música da fila
            nome_escolhido = fila_nomes.pop(0)
            caminho_escolhido = mp3_map[nome_escolhido]
            logger.info(f"🎵 Próxima música ({pasta_principal}): '{nome_escolhido}' | Restam {len(fila_nomes)} no ciclo.")

            try:
                from core.utils.contexto import registrar_contexto
                registrar_contexto("musica_real", nome_escolhido)
            except Exception as context_err:
                logger.debug(f"Erro ao registrar contexto de música: {context_err}")

            # Salva a fila contendo apenas nomes de arquivos no estado
            estado[chave_estado] = fila_nomes
            salvar_estado(estado)

            return caminho_escolhido

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

def trocar_audio_video(caminho_video_orig, caminho_audio_novo, caminho_saida):
    """
    Substitui o áudio de um vídeo MP4 existente por um novo áudio MP3
    usando ffmpeg de forma ultra rápida (sem decodificar o vídeo).
    """
    import subprocess
    import imageio_ffmpeg
    logger.info(f"🔄 Trocando áudio do vídeo para a versão do YouTube...")
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [
        ffmpeg_exe, "-y",
        "-i", caminho_video_orig,       # Entrada 0: Vídeo original
        "-i", caminho_audio_novo,       # Entrada 1: Novo áudio
        "-map", "0:v:0",                # Mapeia o vídeo da entrada 0
        "-map", "1:a:0",                # Mapeia o áudio da entrada 1
        "-c:v", "copy",                 # Copia o vídeo (sem re-renderizar, ultra rápido!)
        "-c:a", "aac",                  # Codifica o áudio em AAC
        "-shortest",                    # Ajusta para o menor tempo entre vídeo e áudio
        caminho_saida
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return caminho_saida

def gerar_video_reels(caminhos_imagens, caminho_audio, caminho_saida="reels_pronto.mp4",
                      textos=None, fonte_path=None, fonte_size=86, incluir_video_final=True, tipo="reels"):
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
        if tipo in ["story_manha", "reels", "reels_noite"]:
            duracao_por_slide = 6.5    # Slides internos
            DURACAO_ULTIMO_SLIDE = 6.5  # CTA final
            DURACAO_GANCHO_COMUM = 5.0  # Primeiro slide (gancho)
        else:
            duracao_por_slide = 9.0
            DURACAO_ULTIMO_SLIDE = 11.0  # Último slide (CTA) tem mais tempo para leitura
            DURACAO_GANCHO_COMUM = 7.0  # Gancho do reels dura 7 segundos para leitura confortável
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
        if incluir_video_final and os.path.exists(path_video_final):
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
        is_reels_comum = (tipo in ["reels", "reels_noite"])
        is_simples = (tipo in ["story_manha", "reels", "reels_noite"])
        if is_simples and n_slides >= 2:
            duracao_slides = DURACAO_GANCHO_COMUM + (n_slides - 2) * duracao_por_slide + DURACAO_ULTIMO_SLIDE
        elif is_simples:
            duracao_slides = n_slides * DURACAO_GANCHO_COMUM
        elif is_reels_comum and n_slides >= 2:
            duracao_slides = DURACAO_GANCHO_COMUM + (n_slides - 2) * duracao_por_slide + DURACAO_ULTIMO_SLIDE
        else:
            duracao_slides = (n_slides - 1) * duracao_por_slide + DURACAO_ULTIMO_SLIDE
        duracao_total_audio = duracao_slides + outro_duracao

        if duracao_total_audio > audio_clip.duration:
            # Ajusta as durações para caber no áudio disponível
            ratio = audio_clip.duration / duracao_total_audio
            duracao_por_slide = duracao_por_slide * ratio
            DURACAO_ULTIMO_SLIDE = max(duracao_por_slide, DURACAO_ULTIMO_SLIDE * ratio)
            DURACAO_GANCHO_COMUM = DURACAO_GANCHO_COMUM * ratio
            if (is_simples or is_reels_comum) and n_slides >= 2:
                duracao_slides = DURACAO_GANCHO_COMUM + (n_slides - 2) * duracao_por_slide + DURACAO_ULTIMO_SLIDE
            else:
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
            """Renderiza o texto com animação do dia usando degradê completo da marca via _adicionar_texto_degrade."""
            from core.media.pexels_story import PALETA_PADRAO_MARCA, _adicionar_texto_degrade
            # Garante que texto é sempre string
            if isinstance(texto, list):
                texto = " ".join(str(x) for x in texto)
            texto = str(texto).strip()
            if not texto:
                return frame_np

            tempo_ativo = max(1.0, duracao - 1.5)
            progresso = min(t / tempo_ativo, 1.0)

            # Parâmetros de animação (compatíveis com _adicionar_texto_degrade)
            chars_to_show = None
            fade_alpha    = 1.0
            deslocamento_y = 0

            # Slides fixos (capa e CTA): sempre estáticos
            if eh_primeiro_slide or eh_ultimo_slide:
                pass  # mantém defaults acima

            # Slides internos: animação do dia da semana
            elif dia == 0:  # Segunda: Máquina de Escrever (letra a letra)
                chars_to_show = int(progresso * len(texto))

            elif dia == 1:  # Terça: Surgimento por Palavras (fade progressivo)
                fade_alpha = min(1.0, progresso * 2)

            elif dia == 2:  # Quarta: Fade In Suave
                fade_alpha = min(1.0, progresso * 2)

            elif dia == 3:  # Quinta: Zoom-In (sem chars control, usa fade)
                fade_alpha = min(1.0, progresso * 2)

            elif dia == 4:  # Sexta: Deslizamento de baixo
                deslocamento_y = int(H * 0.15 * max(0, 1.0 - progresso * 3))

            elif dia == 5:  # Sábado: Reveal (fade + subida)
                fade_alpha = min(1.0, t / 0.8)
                deslocamento_y = int(20 * (1.0 - min(1.0, t / 0.8)))

            elif dia == 6:  # Domingo: Typewriter também (padrão universal)
                chars_to_show = int(progresso * len(texto))

            return _adicionar_texto_degrade(
                frame_np, texto, fonte_texto,
                chars_to_show=chars_to_show,
                fade_alpha=fade_alpha,
                deslocamento_y=deslocamento_y,
                paleta=PALETA_PADRAO_MARCA
            )

        # --- Função: gera todos os frames de um slide (imagem + texto animado) ---
        def gerar_frames_slide(caminho_img, texto, duracao, dia, eh_primeiro_slide, W, H, fps, eh_ultimo_slide=False, animar_imagem=True):  # noqa
            total_frames = int(duracao * fps)
            fade_frames  = int(0.5 * fps)

            img_pil = PILImage.open(caminho_img).convert("RGB").resize((W, H), PILImage.Resampling.LANCZOS)
            img_np  = np.array(img_pil)

            # Pré-redimensiona para Zoom apenas se animação de imagem estiver ativa (dias 2 e 5)
            img_zoomed_np = None
            if animar_imagem and dia in [2, 5]:
                scale_max = 1.12
                w_zoom, h_zoom = int(W * scale_max), int(H * scale_max)
                img_zoomed_pil = img_pil.resize((w_zoom, h_zoom), PILImage.Resampling.LANCZOS)
                img_zoomed_np  = np.array(img_zoomed_pil)

            frames = []
            for f in range(total_frames):
                t = f / fps
                progresso = t / duracao
                frame = img_np.copy()

                # --- Transição de entrada da IMAGEM (slides 2+) com curva suave (Ease-Out) ---
                if animar_imagem and not eh_primeiro_slide and t < 0.5:
                    p_linear = t / 0.5
                    # Curva Ease-Out: movimento começa rápido e freia suavemente (sem tranco)
                    p = 1.0 - (1.0 - p_linear) ** 2

                    if dia == 0:
                        frame = (frame * p).astype(np.uint8)
                    elif dia == 1:
                        offset_x = int(W * (1.0 - p))
                        canvas = np.zeros_like(frame)
                        dst_w = W - offset_x
                        if dst_w > 0:
                            canvas[:, :dst_w] = frame[:, offset_x:]
                        frame = canvas
                    elif dia == 2 and img_zoomed_np is not None:
                        # Zoom In ultra rápido via fatiamento de matriz (0ms)
                        scale_curr = 1.0 + 0.12 * p
                        w_c, h_c = int(W * scale_curr), int(H * scale_curr)
                        cx, cy = (img_zoomed_np.shape[1] - w_c) // 2, (img_zoomed_np.shape[0] - h_c) // 2
                        frame = img_zoomed_np[cy:cy+h_c, cx:cx+w_c]
                        if frame.shape[0] != H or frame.shape[1] != W:
                            frame = np.array(PILImage.fromarray(frame).resize((W, H), PILImage.Resampling.BILINEAR))
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
                    elif dia == 5 and img_zoomed_np is not None:
                        # Zoom Out ultra rápido via fatiamento de matriz (0ms)
                        scale_curr = 1.12 - 0.12 * p
                        w_c, h_c = int(W * scale_curr), int(H * scale_curr)
                        cx, cy = (img_zoomed_np.shape[1] - w_c) // 2, (img_zoomed_np.shape[0] - h_c) // 2
                        frame = img_zoomed_np[cy:cy+h_c, cx:cx+w_c]
                        if frame.shape[0] != H or frame.shape[1] != W:
                            frame = np.array(PILImage.fromarray(frame).resize((W, H), PILImage.Resampling.BILINEAR))
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

                # --- FadeOut suave no final do slide ---
                frames_restantes = total_frames - f
                if frames_restantes <= fade_frames and fade_frames > 0:
                    alpha_linear = frames_restantes / fade_frames
                    alpha = alpha_linear ** 2  # curva suave de fechamento
                    frame = (frame * alpha).astype(np.uint8)

                frames.append(frame)

            return frames

        # Narração de voz removida do reels_noite — usa apenas música de fundo
        audio_narracao_clip = None
        duracoes_sincronizadas = []

        # --- Gera os clipes ---
        clips = []
        for idx, caminho in enumerate(caminhos_imagens):
            _raw_texto = textos[idx] if idx < len(textos) else ""
            # Garante que cada texto de slide é sempre string
            if isinstance(_raw_texto, list):
                texto_slide = " ".join(str(x) for x in _raw_texto)
            else:
                texto_slide = str(_raw_texto).strip()
            eh_ultimo = (idx == n_slides - 1)

            # Duração adaptável: se houver narração sincronizada, usa a duração exata da voz daquele slide!
            if duracoes_sincronizadas and idx < len(duracoes_sincronizadas):
                dur_slide = duracoes_sincronizadas[idx]
            elif eh_ultimo:
                dur_slide = DURACAO_ULTIMO_SLIDE
            elif idx == 0 and (is_simples or is_reels_comum):
                dur_slide = DURACAO_GANCHO_COMUM
            else:
                dur_slide = duracao_por_slide
            _animar_img = not is_simples
            try:
                frames_lista = gerar_frames_slide(
                    caminho, texto_slide, dur_slide,
                    dia_semana, idx == 0, W, H, FPS, eh_ultimo,
                    animar_imagem=_animar_img
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
            video_clip.write_videofile(caminho_saida, fps=FPS, codec="libx264", audio_codec="aac", logger=None, threads=4, preset="ultrafast")
        except TypeError:
            video_clip.write_videofile(caminho_saida, fps=FPS, codec="libx264", audio_codec="aac", threads=4, preset="ultrafast")

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
        if 'audio_narracao_clip' in locals() and audio_narracao_clip is not None:
            try:
                audio_narracao_clip.close()
            except Exception:
                pass

        # Limpa arquivos temporários de imagem de slides criados durante a geração
        if caminhos_imagens:
            for c_img in caminhos_imagens:
                if c_img and os.path.exists(c_img) and "reels_slide_" in os.path.basename(c_img):
                    try:
                        os.remove(c_img)
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
                logger=None,
                threads=4,
                preset="ultrafast"
            )
        except TypeError:
            video_clip.write_videofile(
                caminho_saida,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                threads=4,
                preset="ultrafast"
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
