"""
Módulo de Geração de Voz Neural / Narração por IA (core/audio/tts.py)

Mecanismo em Cascata Inteligente de 3 Níveis:
  1. ElevenLabs Conta 1 (Primária)  — chave/voz ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID
  2. ElevenLabs Conta 2 (Backup)    — chave/voz ELEVENLABS_API_KEY_2 / ELEVENLABS_VOICE_ID_2
  3. Microsoft Edge TTS (Gratuito e Ilimitado) — pt-BR-AntonioNeural
"""

import os
import uuid
import asyncio
import requests
from loguru import logger

from core.config.settings import (
    ELEVENLABS_API_KEY,  ELEVENLABS_VOICE_ID,
    ELEVENLABS_API_KEY_2, ELEVENLABS_VOICE_ID_2,
)

# ---------------------------------------------------------------------------
# Auxiliares internos
# ---------------------------------------------------------------------------

def _chamar_elevenlabs(api_key: str, voice_id: str, texto: str, caminho_saida: str) -> str | None:
    """Faz a requisição HTTP ao ElevenLabs e salva o .mp3. Retorna o caminho ou None."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    payload = {
        "text": texto,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.65,
            "similarity_boost": 0.75,
            "style": 0.30,
            "use_speaker_boost": True,
        },
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=35)

        if response.status_code == 200:
            os.makedirs(os.path.dirname(caminho_saida) or ".", exist_ok=True)
            with open(caminho_saida, "wb") as f:
                f.write(response.content)
            if os.path.getsize(caminho_saida) > 0:
                return caminho_saida
            logger.warning("⚠️ ElevenLabs retornou arquivo de áudio vazio.")
            return None

        # Cota esgotada: código 429 ou mensagem de quota
        if response.status_code in (429, 401) or "quota" in response.text.lower():
            logger.warning(
                f"⚠️ ElevenLabs cota/limite atingido (HTTP {response.status_code}). "
                "Passando para o próximo nível..."
            )
        else:
            logger.warning(
                f"⚠️ ElevenLabs HTTP {response.status_code}: {response.text[:120]}"
            )
        return None

    except Exception as e:
        logger.error(f"❌ Exceção ao chamar ElevenLabs: {e}")
        return None


async def _edge_tts_async(texto: str, caminho: str, voz: str = "pt-BR-AntonioNeural"):
    import edge_tts
    communicate = edge_tts.Communicate(texto, voz, rate="-10%")
    await communicate.save(caminho)


def _gerar_edge_tts(texto: str, caminho_saida: str, voz: str = "pt-BR-AntonioNeural") -> str | None:
    """Gera narração usando Microsoft Edge TTS (gratuito e sem limite de uso)."""
    try:
        try:
            asyncio.run(_edge_tts_async(texto, caminho_saida, voz=voz))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_edge_tts_async(texto, caminho_saida, voz=voz))

        if os.path.exists(caminho_saida) and os.path.getsize(caminho_saida) > 0:
            return caminho_saida
    except Exception as e:
        logger.warning(
            f"⚠️ Edge-TTS falhou (verifique se 'edge-tts' está instalado: pip install edge-tts): {e}"
        )
    return None


# ---------------------------------------------------------------------------
# Função pública principal
# ---------------------------------------------------------------------------

def gerar_audio_narracao(texto, voice_id: str | None = None, caminho_saida: str | None = None) -> str | None:
    """
    Gera narração em cascata:
      Nível 1 → ElevenLabs Conta 1
      Nível 2 → ElevenLabs Conta 2
      Nível 3 → Edge-TTS Microsoft (gratuito e ilimitado)

    Parâmetros:
      texto        : str ou list[str] com o texto a narrar.
      voice_id     : sobrescreve o voice_id padrão da conta 1 (opcional).
      caminho_saida: caminho do .mp3 de saída (opcional; gerado automaticamente).

    Retorna o caminho do arquivo de áudio gerado, ou None se tudo falhar.
    """
    # Normaliza texto
    if isinstance(texto, list):
        texto_limpo = " ".join(str(x) for x in texto if x).strip()
    else:
        texto_limpo = str(texto).replace("\n", " ").strip()

    if not texto_limpo:
        logger.warning("⚠️ Texto vazio para narração. Pulando.")
        return None

    os.makedirs("midia_temp", exist_ok=True)
    uid = uuid.uuid4().hex[:8]

    # ── Nível 1: ElevenLabs Conta 1 ────────────────────────────────────────
    if ELEVENLABS_API_KEY:
        vid1 = voice_id or ELEVENLABS_VOICE_ID
        saida1 = caminho_saida or f"midia_temp/narracao_el1_{uid}.mp3"
        logger.info(f"🎙️ [Nível 1] ElevenLabs Conta 1 — Voice ID: {vid1}")
        resultado = _chamar_elevenlabs(ELEVENLABS_API_KEY, vid1, texto_limpo, saida1)
        if resultado:
            logger.success("✅ Narração gerada com sucesso via ElevenLabs Conta 1.")
            return resultado
        logger.info("🔄 Conta 1 falhou. Ativando Conta 2...")
    else:
        logger.warning("⚠️ ELEVENLABS_API_KEY não configurada. Pulando Conta 1.")

    # ── Nível 2: ElevenLabs Conta 2 ────────────────────────────────────────
    if ELEVENLABS_API_KEY_2:
        vid2 = ELEVENLABS_VOICE_ID_2
        saida2 = f"midia_temp/narracao_el2_{uid}.mp3"
        logger.info(f"🎙️ [Nível 2] ElevenLabs Conta 2 (Backup) — Voice ID: {vid2}")
        resultado = _chamar_elevenlabs(ELEVENLABS_API_KEY_2, vid2, texto_limpo, saida2)
        if resultado:
            logger.success("✅ Narração gerada com sucesso via ElevenLabs Conta 2.")
            return resultado
        logger.info("🔄 Conta 2 também falhou. Ativando fallback gratuito (Edge-TTS)...")
    else:
        logger.warning("⚠️ ELEVENLABS_API_KEY_2 não configurada. Pulando Conta 2.")

    # ── Nível 3: Microsoft Edge TTS (gratuito e ilimitado) ──────────────────
    saida3 = f"midia_temp/narracao_edge_{uid}.mp3"
    logger.info("🎙️ [Nível 3] Microsoft Edge TTS — pt-BR-AntonioNeural (gratuito)")
    resultado = _gerar_edge_tts(texto_limpo, saida3)
    if resultado:
        logger.success("✅ Narração gerada via Edge-TTS (fallback gratuito).")
        return resultado

def gerar_audio_narracao_sincronizada(slides, voice_id: str | None = None):
    """
    Gera narração slide a slide, mede a duração exata do áudio de cada slide
    e retorna o áudio final concatenado + a lista com a duração exata de cada slide.
    
    Retorna: (caminho_audio_completo, lista_duracoes_slides)
    """
    if not slides:
        return None, []

    # Garante que slides é uma lista de strings
    if isinstance(slides, str):
        slides = [slides]

    os.makedirs("midia_temp", exist_ok=True)
    uid = uuid.uuid4().hex[:8]
    
    caminhos_audios_slides = []
    duracoes_slides = []

    try:
        from moviepy.editor import AudioFileClip, concatenate_audioclips
    except ImportError:
        logger.error("❌ Moviepy não disponível para sincronizar áudio por slide.")
        return gerar_audio_narracao(slides, voice_id=voice_id), []

    clips_audio = []
    pausa_inicial = 1.0  # 1s de silêncio antes da voz começar no slide
    pausa_final = 1.0    # 1s de silêncio após a voz terminar no slide
    tempo_acumulado = 0.0

    for idx, slide_texto in enumerate(slides):
        texto_limpo = str(slide_texto).replace("\n", " ").strip()
        if not texto_limpo:
            dur_vazio = round(pausa_inicial + 2.0 + pausa_final, 2)
            duracoes_slides.append(dur_vazio)
            tempo_acumulado += dur_vazio
            continue

        caminho_slide_mp3 = f"midia_temp/slide_{uid}_{idx}.mp3"
        audio_slide = gerar_audio_narracao(texto_limpo, voice_id=voice_id, caminho_saida=caminho_slide_mp3)

        if audio_slide and os.path.exists(audio_slide):
            try:
                aclip = AudioFileClip(audio_slide)
                dur_orig = aclip.duration
                # Corta 0.10s da cauda para eliminar resíduo de suspiro/respiração do TTS
                dur_limpa = max(0.1, dur_orig - 0.10) if dur_orig > 0.4 else dur_orig
                aclip = aclip.subclip(0, dur_limpa)

                # Aplica fade-out suave de 0.15s no final da fala
                if hasattr(aclip, "audio_fadeout"):
                    aclip = aclip.audio_fadeout(0.15)
                else:
                    try:
                        import moviepy.audio.fx.all as afx
                        aclip = afx.audio_fadeout(aclip, 0.15)
                    except Exception:
                        pass

                dur = aclip.duration
                # Posiciona o áudio 1s após o início do slide (margem inicial)
                aclip = aclip.set_start(tempo_acumulado + pausa_inicial)
                clips_audio.append(aclip)

                dur_total_slide = round(pausa_inicial + dur + pausa_final, 2)
                duracoes_slides.append(dur_total_slide)
                tempo_acumulado += dur_total_slide
                caminhos_audios_slides.append(audio_slide)
            except Exception as e_clip:
                logger.warning(f"⚠️ Erro ao medir áudio do slide {idx}: {e_clip}")
                dur_fallback = round(pausa_inicial + 2.0 + pausa_final, 2)
                duracoes_slides.append(dur_fallback)
                tempo_acumulado += dur_fallback
        else:
            dur_fallback = round(pausa_inicial + 2.0 + pausa_final, 2)
            duracoes_slides.append(dur_fallback)
            tempo_acumulado += dur_fallback

    if clips_audio:
        try:
            from moviepy.editor import CompositeAudioClip
            audio_final = CompositeAudioClip(clips_audio)
            # Necessário no MoviePy 1.x: CompositeAudioClip não define fps automaticamente
            audio_final.fps = 44100
            caminho_final = f"midia_temp/narracao_sincronizada_{uid}.mp3"
            audio_final.write_audiofile(caminho_final, logger=None, fps=44100)
            
            # Fecha clips temporários
            for c in clips_audio:
                try: c.close()
                except: pass

            # Limpa MP3s intermediários de slides
            for c_mp3 in caminhos_audios_slides:
                try: os.remove(c_mp3)
                except: pass

            logger.success(f"🎙️ Narração sincronizada gerada! {len(duracoes_slides)} slides mapeados com precisão 1:1.")
            return caminho_final, duracoes_slides
        except Exception as e_concat:
            logger.error(f"❌ Erro ao concatenar áudios dos slides: {e_concat}")

    return None, duracoes_slides

