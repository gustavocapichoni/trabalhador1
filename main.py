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

def registrar_postagem(tipo, tema, post_id, estilo, frase_visual="", legenda="", gancho_categoria="", tipo_cta="", duracao_video=0, subtema="", objetivo="", categoria_imagem="", categoria_musica="", tom_emocional="", estrutura_narrativa="", complexidade=""):
    from core.config.state import carregar_estado, salvar_estado
    from datetime import datetime, timezone
    if not post_id or post_id.startswith("DRY_RUN"):
        return
        
    estado = carregar_estado()
    if "historico" not in estado:
        estado["historico"] = []
        
    novo_post = {
        "post_id": post_id,
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
    estado["historico"].append(novo_post)
    salvar_estado(estado)

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
                    midia = gerar_pexels_story(
                        conteudo.get("pexels_query", "nature calm"),
                        conteudo.get("slides", []),
                        caminho_saida=_saida,
                        tema=tema_escolhido,
                        is_conquistador=(args.type == "reels_conquistador"),
                        is_reels_leads=(args.type == "reels_leads")
                    )
                except Exception as e:
                    print(f"⚠️ [DRY-RUN] Erro ao gerar vídeo do Pexels Story: {e}")
                    midia = _saida
            else:
                midia = gerar_pexels_story(
                    conteudo.get("pexels_query", "nature calm"),
                    conteudo.get("slides", []),
                    caminho_saida=_saida,
                    tema=tema_escolhido,
                    is_conquistador=(args.type == "reels_conquistador"),
                    is_reels_leads=(args.type == "reels_leads")
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
                        fonte_size=fonte_size
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
                    fonte_size=fonte_size
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
        
        if post_id:
            gancho_cat = conteudo.get("_gancho_categoria", "")
            tipo_cta_val = conteudo.get("_tipo_cta", "")
            dur_video = conteudo.get("_duracao_video", 0)
            subtema_val = conteudo.get("_subtema", "")
            tom_val = conteudo.get("_tom_emocional", "")
            objetivo_val = conteudo.get("objetivo", "")
            cat_imagem_val = conteudo.get("categoria_imagem", "")
            cat_musica_val = conteudo.get("categoria_musica", "")
            est_narrativa_val = conteudo.get("estrutura_narrativa", "")
            complexidade_val = conteudo.get("complexidade", "")
            
            registrar_postagem(
                args.type, tema_escolhido, post_id, estilo_escolhido,
                frase_visual=frase_visual, legenda=legenda,
                gancho_categoria=gancho_cat, tipo_cta=tipo_cta_val, duracao_video=dur_video,
                subtema=subtema_val, objetivo=objetivo_val, categoria_imagem=cat_imagem_val,
                categoria_musica=cat_musica_val, tom_emocional=tom_val,
                estrutura_narrativa=est_narrativa_val, complexidade=complexidade_val
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
