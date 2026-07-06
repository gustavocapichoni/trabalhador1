import os
import glob
import random
import moviepy.editor
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
from loguru import logger

def garantir_audio_reels():
    try:
        pastas = [os.path.join("biblioteca_local", "musicas"), "musicas", "."]
        mp3_files = []
        for pasta in pastas:
            if os.path.exists(pasta):
                for f in os.listdir(pasta):
                    if f.lower().endswith(".mp3") and os.path.isfile(os.path.join(pasta, f)):
                        mp3_files.append(os.path.join(pasta, f))
        if mp3_files:
            escolhido = random.choice(mp3_files)
            logger.info(f"🎵 Audio selecionado aleatoriamente para o vídeo: '{escolhido}'")
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
    except:
        pass
    return None
def gerar_video_reels(caminhos_imagens, caminho_audio, caminho_saida="reels_pronto.mp4"):
    logger.info("🎬 Montando slideshow 9:16 com música de fundo...")
    if 'ImageClip' not in globals() or 'AudioFileClip' not in globals():
        raise ImportError("A biblioteca 'moviepy' não está instalada! Execute 'pip install moviepy' para gerar Reels.")

    # Aceita tanto string (imagem única) quanto lista de imagens
    if isinstance(caminhos_imagens, str):
        caminhos_imagens = [caminhos_imagens]

    try:
        from moviepy import concatenate_videoclips
    except ImportError:
        from moviepy.editor import concatenate_videoclips  # type: ignore

    audio_clip = None
    video_clip = None
    try:
        audio_clip = AudioFileClip(caminho_audio)
        duracao_total = min(audio_clip.duration, 15)  # máximo 15 segundos
        duracao_por_slide = duracao_total / len(caminhos_imagens)

        # Corta o áudio na duração total
        try:
            audio_clip = audio_clip.subclipped(0, duracao_total)
        except AttributeError:
            audio_clip = audio_clip.subclip(0, duracao_total)

        # Cria um clipe para cada imagem do slideshow
        clips = []
        for caminho in caminhos_imagens:
            try:
                from moviepy.video.fx import FadeIn, FadeOut
                clip = ImageClip(caminho).with_duration(duracao_por_slide)
                clip = clip.with_effects([FadeIn(0.5), FadeOut(0.5)])
            except (AttributeError, ImportError):
                clip = ImageClip(caminho).set_duration(duracao_por_slide)
                try:
                    import moviepy.video.fx.all as vfx  # type: ignore
                    clip = clip.fx(vfx.fadein, 0.5).fx(vfx.fadeout, 0.5)
                except:
                    pass
            clips.append(clip)

        # Concatena todos os slides
        video_clip = concatenate_videoclips(clips, method="compose")

        # Adiciona o áudio
        try:
            video_clip = video_clip.with_audio(audio_clip)
        except AttributeError:
            video_clip = video_clip.set_audio(audio_clip)

        logger.info(f"⚙️ Renderizando slideshow de {len(caminhos_imagens)} slides ({duracao_total:.1f}s)...")

        # Remove arquivos temporários residuais do moviepy que possam bloquear a renderização
        import glob
        for temp_file in glob.glob("*TEMP_MPY*"):
            try:
                os.remove(temp_file)
                logger.info(f"🧹 Arquivo temporário residual removido: {temp_file}")
            except Exception:
                pass

        try:
            video_clip.write_videofile(
                caminho_saida,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None
            )
        except TypeError:
            # Fallback para versões antigas do moviepy sem suporte a logger=None
            video_clip.write_videofile(
                caminho_saida,
                fps=24,
                codec="libx264",
                audio_codec="aac"
            )
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

def gerar_video_story_individual(caminho_imagem, caminho_audio, caminho_saida="story_pronto.mp4"):
    logger.info(f"🎬 Convertendo Story {caminho_imagem} em vídeo com música...")
    if 'ImageClip' not in globals() or 'AudioFileClip' not in globals():
        raise ImportError("A biblioteca 'moviepy' não está instalada! Execute 'pip install moviepy' para gerar Stories em vídeo.")

    audio_clip = None
    video_clip = None
    try:
        audio_clip = AudioFileClip(caminho_audio)
        duracao_total = min(audio_clip.duration, 10)  # máximo 10 segundos por slide de story
        
        try:
            audio_clip = audio_clip.subclipped(0, duracao_total)
        except AttributeError:
            audio_clip = audio_clip.subclip(0, duracao_total)

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
