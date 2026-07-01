import os
import random
import requests
import textwrap

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

    print("🎬 Processando vídeo com MoviePy...")
    try:
        from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
        clip = VideoFileClip(temp_vid)
        
        # Limita duração a 15 seg
        duracao = min(clip.duration, 15)
        clip = clip.subclip(0, duracao)
        
        clips = [clip]
        
        if slides:
            print("✍️ Adicionando textos (slides)...")
            tempo_por_slide = duracao / len(slides)
            
            for i, slide in enumerate(slides):
                texto_quebrado = "\n".join(textwrap.wrap(slide, width=30))
                
                try:
                    txt_clip = TextClip(texto_quebrado, fontsize=50, color='white', bg_color='rgba(0,0,0,0.5)', 
                                        font='fontes/MontserratBold.ttf', align='center', method='caption', size=(900, None))
                except Exception as e:
                    # Fallback caso dê erro de fonte
                    txt_clip = TextClip(texto_quebrado, fontsize=50, color='white', bg_color='black')
                
                txt_clip = txt_clip.set_position('center').set_start(i * tempo_por_slide).set_duration(tempo_por_slide)
                clips.append(txt_clip)

        final_clip = CompositeVideoClip(clips)
        
        # Adicionar áudio de fundo usando a função já existente no projeto
        try:
            from core.media.reels import garantir_audio_reels
            audio_path = garantir_audio_reels()
            if audio_path:
                bg_audio = AudioFileClip(audio_path).subclip(0, duracao)
                # Mixar áudio
                final_clip = final_clip.set_audio(bg_audio)
        except Exception as e:
            print(f"⚠️ Erro ao adicionar áudio de fundo: {e}")

        print(f"⚙️ Exportando vídeo final para {caminho_saida}...")
        final_clip.write_videofile(caminho_saida, fps=24, codec="libx264", audio_codec="aac", 
                                   logger=None, threads=4, preset="ultrafast")
        
        # Limpar arquivo temp
        clip.close()
        final_clip.close()
        if os.path.exists(temp_vid):
            os.remove(temp_vid)
            
        return caminho_saida
    except Exception as e:
        print(f"⚠️ Erro ao processar o vídeo no MoviePy: {e}. Retornando vídeo original.")
        if os.path.exists(temp_vid):
            os.rename(temp_vid, caminho_saida)
            return caminho_saida
        raise e
