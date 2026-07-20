import argparse
import sys
import io
import time
import os
import uuid

# Forçar UTF-8 no Windows para suportar emojis no print
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.ai.gemini import gerar_conteudo_gemini
from core.ai.prompts import TEMAS_MAPEADOS
from core.design.motor_visual import criar_arte
from core.publisher.instagram import postar_no_instagram
from core.publisher.email_notifier import enviar_email_notificacao
from core.config.settings import POSTAR_NO_YOUTUBE
from core.publisher.youtube import postar_no_youtube

def registrar_postagem(tipo, tema, post_id, estilo, frase_visual="", legenda="", gancho_categoria="", tipo_cta="", duracao_video=0, subtema="", objetivo="", categoria_imagem="", categoria_musica="", tom_emocional="", estrutura_narrativa="", complexidade="", video_id_yt=""):
    from core.analytics.db import get_db
    from datetime import datetime, timezone
    
    if not post_id or post_id.startswith("DRY_RUN"):
        return
        
    db = get_db()
    if not db:
        print("⚠️ Firebase não conectado, postagem não registrada no histórico.")
        return
        
    novo_post = {
        "post_id": post_id,
        "video_id_yt": video_id_yt,
        "data": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "tipo": tipo,
        "tema": tema,
        "subtema": subtema,
        "objetivo": objetivo,
        "estilo_copy": estilo,
        "tom_emocional": tom_emocional,
        "estrutura_narrativa": estrutura_narrativa,
        "complexidade": complexidade,
        "categoria_imagem": categoria_imagem,
        "categoria_musica": categoria_musica,
        "frase_visual": frase_visual,
        "legenda": legenda,
        "gancho_categoria": gancho_categoria,
        "tipo_cta": tipo_cta,
        "duracao_video": duracao_video
    }
    
    try:
        db.collection("historico_posts").document(post_id).set(novo_post, merge=True)
        print(f"✅ Post {post_id} registrado com sucesso em historico_posts.")

        # Se for reels_leads, registra também na coleção dedicada para anti-repetição
        if tipo == "reels_leads":
            frase_gancho = ""
            if isinstance(frase_visual, list) and frase_visual:
                frase_gancho = frase_visual[0]
            elif isinstance(frase_visual, str):
                frase_gancho = frase_visual[:200]

            titulo_pdf = ""
            try:
                import json
                caminho_pdf_json = os.path.join("gerador_pdf", "output", "ultimo_conteudo.json")
                if os.path.exists(caminho_pdf_json):
                    with open(caminho_pdf_json, "r", encoding="utf-8") as f:
                        titulo_pdf = json.load(f).get("titulo_pdf", "")
            except Exception:
                pass

            doc_leads = {
                "post_id": post_id,
                "data": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "titulo_pdf": titulo_pdf,
                "gancho_fase1": frase_gancho,
                "legenda": legenda[:300],
                "estilo_copy": estilo,
            }
            db.collection("historico_reels_leads").document(post_id).set(doc_leads)
            print(f"✅ Reels_leads registrado em historico_reels_leads.")
    except Exception as e:
        print(f"❌ Erro ao salvar post no Firebase: {e}")

def main():
    parser = argparse.ArgumentParser(description="Bot de Instagram Automático 2.0")
    parser.add_argument("--type", type=str, required=True, 
                        choices=["story", "story_manha", "story_tarde", "carousel", "reels", "pexels_story", "reels_noite", "pexels_story_noite", "reels_conquistador", "reels_leads", "test"],
                        help="Tipo de postagem a gerar")
    parser.add_argument("--dry-run", action="store_true", help="Executa todo o processo sem postar no Instagram")
    
    args = parser.parse_args()
    
    print(f"🌅 --- Iniciando Bot de Postagem Automática ({args.type.upper()}) ---")
    
    if args.dry_run:
        print("🧪 [MODO DRY-RUN ATIVADO]")
        
    try:
        arquivos_gerados = []
        # Passo 0: Health Check
        if not args.dry_run:
            from core.utils.health import verificar_health
            verificar_health()
            
        # Passo 1: Solicita conteúdo ao Gemini
        conteudo, tema_escolhido, estilo_escolhido = gerar_conteudo_gemini(args.type)
        if args.type == "carousel":
            print(f"✨ Título do Carrossel: \"{conteudo.get('titulo')}\"")
        elif args.type in ["reels", "pexels_story", "reels_noite", "pexels_story_noite", "reels_conquistador", "reels_leads"]:
            slides = conteudo.get('slides', [])
            for i, s in enumerate(slides):
                print(f"✨ Slide {i+1}: \"{s}\"")
        else:
            print(f"✨ Frase Gerada: \"{conteudo.get('frase')}\"")
            
        # Passo 2: Cria a mídia (imagem, sequência ou vídeo)
        if args.type in ["pexels_story", "pexels_story_noite", "reels_conquistador", "reels_leads"]:
            from core.media.pexels_story import gerar_pexels_story
            req_id = uuid.uuid4().hex
            _saida = f"pexels_story_{req_id}.mp4"
            arquivos_gerados.append(_saida)
            if args.dry_run:
                try:
                    print("🧪 [DRY-RUN] Gerando vídeo local do Pexels Story para teste...")
                    pq = conteudo.get("pexels_queries") or conteudo.get("pexels_query", "nature calm")
                    if isinstance(pq, str):
                        pq = [pq]
                    midia = gerar_pexels_story(
                        pq,
                        conteudo.get("slides", []),
                        caminho_saida=_saida,
                        tema=tema_escolhido,
                        is_conquistador=(args.type == "reels_conquistador"),
                        is_reels_leads=(args.type == "reels_leads"),
                        is_noite=(args.type == "pexels_story_noite")
                    )
                except Exception as e:
                    print(f"⚠️ [DRY-RUN] Erro ao gerar vídeo do Pexels Story: {e}")
                    midia = _saida
            else:
                pq = conteudo.get("pexels_queries") or conteudo.get("pexels_query", "nature calm")
                if isinstance(pq, str):
                    pq = [pq]
                midia = gerar_pexels_story(
                    pq,
                    conteudo.get("slides", []),
                    caminho_saida=_saida,
                    tema=tema_escolhido,
                    is_conquistador=(args.type == "reels_conquistador"),
                    is_reels_leads=(args.type == "reels_leads"),
                    is_noite=(args.type == "pexels_story_noite")
                )
        else:
            midia = criar_arte(args.type, conteudo, tema_escolhido, TEMAS_MAPEADOS)
            if isinstance(midia, list): arquivos_gerados.extend(midia)
            elif isinstance(midia, str): arquivos_gerados.append(midia)
            elif isinstance(midia, tuple): arquivos_gerados.extend(midia[0])
        
        # Passo 3: Se for Reels (ou story_manha animado), gera o vídeo MP4
        if args.type in ["reels", "reels_noite", "story_manha"]:
            from core.media.reels import gerar_video_reels, garantir_audio_reels
            req_id = uuid.uuid4().hex
            nome_saida_reels = f"reels_pronto_{req_id}.mp4"
            arquivos_gerados.append(nome_saida_reels)

            # midia agora é um tuple (caminhos_fundos, frases, caminho_fonte, tamanho_fonte)
            if isinstance(midia, tuple):
                caminhos_fundos, frases_reels, fonte_path, fonte_size = midia
            else:
                caminhos_fundos, frases_reels, fonte_path, fonte_size = midia, [], None, 86

            if args.dry_run:
                try:
                    audio_path = garantir_audio_reels()
                    midia = gerar_video_reels(
                        caminhos_fundos, audio_path,
                        caminho_saida=nome_saida_reels,
                        textos=frases_reels,
                        fonte_path=fonte_path,
                        fonte_size=fonte_size,
                        incluir_video_final=(args.type != "story_manha")  # Story da manhã não inclui vídeo final
                    )
                except Exception as e:
                    print(f"⚠️ [DRY-RUN] Pulando geração real de vídeo do Reels: {e}")
                    midia = nome_saida_reels
            else:
                audio_path = garantir_audio_reels()
                midia = gerar_video_reels(
                    caminhos_fundos, audio_path,
                    caminho_saida=nome_saida_reels,
                    textos=frases_reels,
                    fonte_path=fonte_path,
                    fonte_size=fonte_size,
                    incluir_video_final=(args.type != "story_manha")  # Story da manhã não inclui vídeo final
                )
                
        # Passo 3.5: Se for Story (estático), converte obrigatoriamente JPGs para MP4s com música
        if args.type in ["story_tarde"]:
            from core.media.reels import gerar_video_story_individual, garantir_audio_reels
            print("🎵 Convertendo slides de Story para vídeo com música de fundo contínua...")
            midias_em_video = []
            req_id = uuid.uuid4().hex
            
            # 1. Sorteia UMA música que será tocada do início ao fim
            audio_path = None
            try:
                audio_path = garantir_audio_reels()
            except Exception as e:
                print(f"⚠️ Erro ao buscar áudio: {e}")
                
            for i, caminho_jpg in enumerate(midia):
                nome_saida = f"story_video_{i}_{req_id}.mp4"
                arquivos_gerados.append(nome_saida)
                if args.dry_run:
                    try:
                        if audio_path:
                            # 2. Faz a música continuar de onde parou (0s, 10s, 20s...)
                            gerar_video_story_individual(caminho_jpg, audio_path, caminho_saida=nome_saida, tempo_inicio=i*10.0)
                        midias_em_video.append(nome_saida)
                    except Exception as e:
                        print(f"⚠️ [DRY-RUN] Pulando geração de story em vídeo: {e}")
                        midias_em_video.append(caminho_jpg) # fallback
                else:
                    if audio_path:
                        novo_caminho = gerar_video_story_individual(caminho_jpg, audio_path, caminho_saida=nome_saida, tempo_inicio=i*10.0)
                        midias_em_video.append(novo_caminho)
                    else:
                        midias_em_video.append(caminho_jpg)
            midia = midias_em_video
            
        # Passo 4: Publicação no Instagram
        legenda = conteudo.get("legenda", "")
        
        # Extrair a frase visual para fins de log e relatório
        frase_visual = ""
        if args.type == "carousel":
            frase_visual = conteudo.get("titulo", "")
        elif args.type in ["reels", "pexels_story", "reels_noite", "pexels_story_noite", "reels_conquistador", "reels_leads"]:
            slides = conteudo.get('slides', [])
            frase_visual = " | ".join(slides) if isinstance(slides, list) else str(slides)
        else:
            frase_visual = conteudo.get("frase", "")
            if isinstance(frase_visual, list):
                frase_visual = " | ".join(frase_visual)

        post_id = postar_no_instagram(args.type, midia, legenda, dry_run=args.dry_run)
        
        yt_video_id = ""
        # Postagem opcional no YouTube Shorts para formatos de vídeo
        if POSTAR_NO_YOUTUBE and args.type in ["reels", "pexels_story", "reels_noite", "pexels_story_noite", "reels_conquistador", "reels_leads"] and isinstance(midia, str) and midia.endswith(".mp4"):
            try:
                # Carrega o áudio específico do YouTube
                from core.media.reels import trocar_audio_video, garantir_audio_reels
                caminho_yt_audio = garantir_audio_reels(pastas=[os.path.join("biblioteca_local", "musicas-youtube")])
                
                if caminho_yt_audio and os.path.exists(caminho_yt_audio):
                    # Cria um vídeo temporário substituindo o áudio
                    nome_saida_yt = midia.replace(".mp4", "_youtube.mp4")
                    trocar_audio_video(midia, caminho_yt_audio, nome_saida_yt)
                    arquivos_gerados.append(nome_saida_yt)  # Garante que será limpo depois
                    caminho_video_envio = nome_saida_yt
                else:
                    print("⚠️ Nenhuma música encontrada na pasta musicas-youtube. Enviando vídeo original.")
                    caminho_video_envio = midia

                titulo_yt = conteudo.get("titulo") or conteudo.get("frase") or tema_escolhido
                if isinstance(titulo_yt, list):
                    titulo_yt = titulo_yt[0] if titulo_yt else tema_escolhido
                
                # Executa o upload do vídeo com áudio trocado
                if not args.dry_run:
                    yt_video_id = postar_no_youtube(
                        caminho_video=caminho_video_envio,
                        titulo=titulo_yt,
                        descricao=legenda
                    )
                else:
                    musica_yt = os.path.basename(caminho_yt_audio) if caminho_yt_audio else "original"
                    print(f"⚠️ [DRY-RUN] Upload simulado para YouTube. Música: {musica_yt}")
            except Exception as e:
                print(f"⚠️ Erro ao postar no YouTube Shorts (continuando fluxo principal): {e}")
        
        if post_id:
            gancho_cat = conteudo.get("_gancho_categoria", "")
            tipo_cta_val = conteudo.get("_tipo_cta", "")
            dur_video = conteudo.get("_duracao_video", 0)
            
            # Se for formato de vídeo e a duração estiver zerada, mede a duração do arquivo físico
            if dur_video == 0 and isinstance(midia, str) and midia.endswith(".mp4") and os.path.exists(midia):
                try:
                    from moviepy.editor import VideoFileClip
                    with VideoFileClip(midia) as clip:
                        dur_video = int(clip.duration)
                except Exception as e:
                    print(f"⚠️ Erro ao obter a duração real do vídeo: {e}")

            subtema_val = conteudo.get("_subtema", "")
            tom_val = conteudo.get("_tom_emocional", "")
            objetivo_val = conteudo.get("objetivo", "")
            cat_imagem_val = conteudo.get("categoria_imagem", "")
            cat_musica_val = conteudo.get("categoria_musica", "")
            est_narrativa_val = conteudo.get("estrutura_narrativa", "")
            
            # Registra apenas uma vez, contendo o post_id do Insta e o video_id_yt
            complexidade_val = conteudo.get("complexidade", "")
            
            registrar_postagem(
                args.type, tema_escolhido, post_id, estilo_escolhido,
                frase_visual=frase_visual, legenda=legenda,
                gancho_categoria=gancho_cat, tipo_cta=tipo_cta_val, duracao_video=dur_video,
                subtema=subtema_val, objetivo=objetivo_val, categoria_imagem=cat_imagem_val,
                categoria_musica=cat_musica_val, tom_emocional=tom_val,
                estrutura_narrativa=est_narrativa_val, complexidade=complexidade_val,
                video_id_yt=yt_video_id
            )
        
        # Passo 5: Envia E-mail de Sucesso
        mensagens_sucesso = {
            "story": "Stories do dia publicado com sucesso para interagir com a audiência!",
            "story_manha": "Sequência de Stories da Manhã publicada com sucesso!",
            "story_tarde": "Dupla de Stories da Tarde publicada com sucesso!",
            "carousel": "Conteúdo aprofundado no ar! Seu Carrossel foi publicado com sucesso!",
            "reels": "Finalizando o dia: seu Reels em vídeo foi publicado com sucesso!",
            "pexels_story": "Video B-roll narrativo publicado com sucesso!",
            "reels_noite": "Reels noturno com arco narrativo publicado com sucesso!",
            "pexels_story_noite": "Pexels Story da noite publicado com sucesso!",
            "reels_conquistador": "Reels Conquistador no ar! Público em expansão às 22h!",
            "reels_leads": "Lead Magnet Reels publicado! O funil de vendas está ativo!",
            "test": "Ambiente de automação testado com sucesso!"
        }
        
        assunto_email = f"✅ Bot Instagram: Post de {args.type.upper()} Realizado!"
        corpo_email = f"{mensagens_sucesso.get(args.type, 'Postagem realizada!')}\n\n"
        if post_id:
            corpo_email += f"ID da Publicação: {post_id}\n"
            
        enviar_email_notificacao(assunto_email, corpo_email, dry_run=args.dry_run)
        
        # Passo 6: Limpeza de arquivos temporários
        if not args.dry_run:
            try:
                for f in set(arquivos_gerados):
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                        except:
                            pass
                print("🧹 Arquivos de mídia gerados nesta execução foram apagados (Lixo isolado).")
            except Exception as e:
                print(f"⚠️ Erro leve ao limpar arquivos temporários: {e}")

        print("🏁 --- Processo Finalizado com Sucesso ---")
        
    except Exception as e:
        erro_msg = f"❌ Falha crítica na execução do bot (tipo: {args.type.upper()}): {e}"
        print(erro_msg)
        enviar_email_notificacao(
            assunto=f"🚨 Falha Crítica no Bot do Instagram - {args.type.upper()}",
            mensagem=f"Ocorreu um erro durante a execução do bot automático.\n\nDetalhes do erro:\n{e}",
            dry_run=args.dry_run
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
