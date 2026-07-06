import argparse
import sys
import io
import time
import os

# Forçar UTF-8 no Windows para suportar emojis no print
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.ai.gemini import gerar_conteudo_gemini
from core.ai.prompts import TEMAS_MAPEADOS
from core.design.motor_visual import criar_arte
from core.publisher.instagram import postar_no_instagram
from core.publisher.email_notifier import enviar_email_notificacao

# Mock functions for verification and state that were in code.py
def verificar_expiracao_token():
    pass

def verificar_duplicidade_hoje(tipo):
    return False

def registrar_postagem(tipo, tema, post_id, estilo):
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
        "estilo_copy": estilo
    }
    estado["historico"].append(novo_post)
    salvar_estado(estado)

def main():
    parser = argparse.ArgumentParser(description="Bot de Instagram Automático 2.0")
    parser.add_argument("--type", type=str, required=True, 
                        choices=["story", "story_manha", "story_tarde", "carousel", "reels", "pexels_story", "reels_noite", "pexels_story_noite", "reels_conquistador", "test"],
                        help="Tipo de postagem a gerar")
    parser.add_argument("--dry-run", action="store_true", help="Executa todo o processo sem postar no Instagram")
    
    args = parser.parse_args()
    
    print(f"🌅 --- Iniciando Bot de Postagem Automática ({args.type.upper()}) ---")
    
    if args.dry_run:
        print("🧪 [MODO DRY-RUN ATIVADO]")
        
    try:
        # Passo 0: Health Check
        if not args.dry_run:
            from core.utils.health import verificar_health
            verificar_health()
            
        # Passo 1: Solicita conteúdo ao Gemini
        conteudo, tema_escolhido, estilo_escolhido = gerar_conteudo_gemini(args.type)
        if args.type == "carousel":
            print(f"✨ Título do Carrossel: \"{conteudo.get('titulo')}\"")
        elif args.type in ["reels", "pexels_story", "reels_noite", "pexels_story_noite", "reels_conquistador"]:
            slides = conteudo.get('slides', [])
            for i, s in enumerate(slides):
                print(f"✨ Slide {i+1}: \"{s}\"")
        else:
            print(f"✨ Frase Gerada: \"{conteudo.get('frase')}\"")
            
        # Passo 2: Cria a mídia (imagem, sequência ou vídeo)
        if args.type in ["pexels_story", "pexels_story_noite"]:
            from core.media.pexels_story import gerar_pexels_story
            ts = int(time.time())
            _saida = f"pexels_story_{ts}.mp4"
            if args.dry_run:
                print("[DRY-RUN] Pulando geracao real de Pexels Story.")
                midia = _saida
            else:
                midia = gerar_pexels_story(
                    conteudo.get("pexels_query", "nature calm"),
                    conteudo.get("slides", []),
                    caminho_saida=_saida
                )
        else:
            midia = criar_arte(args.type, conteudo, tema_escolhido, TEMAS_MAPEADOS)
        
        # Passo 3: Se for Reels, gera o vídeo MP4
        if args.type in ["reels", "reels_noite", "reels_conquistador"]:
            from core.media.reels import gerar_video_reels, garantir_audio_reels
            ts = int(time.time())
            nome_saida_reels = f"reels_pronto_{ts}.mp4"
            if args.dry_run:
                try:
                    audio_path = garantir_audio_reels()
                    midia = gerar_video_reels(midia, audio_path, caminho_saida=nome_saida_reels)
                except Exception as e:
                    print(f"⚠️ [DRY-RUN] Pulando geração real de vídeo do Reels: {e}")
                    midia = nome_saida_reels
            else:
                audio_path = garantir_audio_reels()
                midia = gerar_video_reels(midia, audio_path, caminho_saida=nome_saida_reels)
                
        # Passo 3.5: Se for Story, converte obrigatoriamente JPGs para MP4s com música
        if args.type in ["story_manha", "story_tarde"]:
            from core.media.reels import gerar_video_story_individual, garantir_audio_reels
            print("🎵 Convertendo slides de Story para vídeo com música de fundo...")
            midias_em_video = []
            ts = int(time.time())
            for i, caminho_jpg in enumerate(midia):
                nome_saida = f"story_video_{i}_{ts}.mp4"
                if args.dry_run:
                    try:
                        audio_path = garantir_audio_reels()
                        gerar_video_story_individual(caminho_jpg, audio_path, caminho_saida=nome_saida)
                        midias_em_video.append(nome_saida)
                    except Exception as e:
                        print(f"⚠️ [DRY-RUN] Pulando geração de story em vídeo: {e}")
                        midias_em_video.append(caminho_jpg) # fallback
                else:
                    audio_path = garantir_audio_reels()
                    novo_caminho = gerar_video_story_individual(caminho_jpg, audio_path, caminho_saida=nome_saida)
                    midias_em_video.append(novo_caminho)
            midia = midias_em_video
            
        # Passo 4: Publicação no Instagram
        legenda = conteudo.get("legenda", "")
        post_id = postar_no_instagram(args.type, midia, legenda, dry_run=args.dry_run)
        
        if post_id:
            registrar_postagem(args.type, tema_escolhido, post_id, estilo_escolhido)
        
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
                import glob
                arquivos_lixo = glob.glob("*.jpg") + glob.glob("reels_pronto_*.mp4") + glob.glob("pexels_story_*.mp4") + glob.glob("story_video_*.mp4")
                if isinstance(midia, str) and os.path.exists(midia):
                    if midia not in arquivos_lixo:
                        arquivos_lixo.append(midia)
                for f in arquivos_lixo:
                    if os.path.exists(f):
                        os.remove(f)
                print("🧹 Arquivos de mídia temporários apagados da raiz.")
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
