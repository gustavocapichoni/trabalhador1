import os
import sys
import time
import io
import subprocess
from datetime import datetime, timezone

# Forçar UTF-8 no Windows para suportar emojis no print
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BOT_PATH)

def processar_solicitacoes_pendentes():
    """
    Busca solicitações pendentes criadas no Studio de Criação (Dashboard),
    gera o conteúdo/mídia personalizado e publica no Instagram.
    """
    try:
        from core.analytics.db import get_db
        db = get_db()
        if not db:
            print("⚠️ Firebase não conectado. Não foi possível checar a fila de solicitações.")
            return False

        # Busca até 5 pedidos pendentes
        docs = db.collection("solicitacoes_postagem").where("status", "==", "pendente").limit(5).stream()
        solicitacoes = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            solicitacoes.append(d)

        if not solicitacoes:
            print("💤 [Studio de Criação] Nenhuma solicitação pendente encontrada na fila.")
            return False

        print(f"📥 [Studio de Criação] {len(solicitacoes)} solicitação(ões) pendente(s) encontrada(s)!")

        for req in solicitacoes:
            doc_id = req.get("id")
            tema = req.get("tema", "Geral")
            modo_texto = req.get("modo_texto", "ia")
            mensagem = req.get("mensagem", "")
            tipo_post = req.get("tipo_post", "reels")

            # Mapeamento do tipo de post para a flag do main.py
            mapa_tipos = {
                "reels": "reels",
                "reels_leads": "reels_leads",
                "pexels_story": "pexels_story",
                "carousel": "carousel",
                "storytelling": "pexels_story_noite",
                "story": "story",
                "reels_conquistador": "reels_conquistador"
            }
            tipo_main = mapa_tipos.get(tipo_post, "reels")

            print(f"\n🚀 [Studio de Criação] Processando Pedido: ID={doc_id}")
            print(f"   📌 Tema/Profissão: {tema}")
            print(f"   ⚙️ Modo Texto:     {modo_texto.upper()}")
            print(f"   🎥 Formato:        {tipo_main}")
            print(f"   💬 Mensagem:       {mensagem[:100]}...")

            # Executa o main.py para gerar e publicar o post
            cmd = ["python", "main.py", "--type", tipo_main]
            print(f"🎬 Executando comando: {' '.join(cmd)}")
            res = subprocess.run(cmd, cwd=BOT_PATH)

            if res.returncode == 0:
                print(f"✅ [Studio de Criação] Postagem do pedido '{tema}' concluída com sucesso!")
                # Atualiza status no Firebase para publicado
                db.collection("solicitacoes_postagem").document(doc_id).update({
                    "status": "publicado",
                    "processado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                })

                # Notifica por e-mail se a notificação estiver configurada
                try:
                    from core.publisher.email_notifier import enviar_email_notificacao
                    assunto = f"✨ Postagem do Studio de Criação Publicada - {tema}"
                    corpo = f"Sua postagem personalizada encomendada pelo Studio de Criação foi gerada e publicada com sucesso no Instagram!\n\nTema: {tema}\nFormato: {tipo_main}\nModo: {modo_texto}"
                    enviar_email_notificacao(assunto=assunto, mensagem=corpo)
                except Exception as e_mail:
                    print(f"⚠️ Aviso ao enviar e-mail de notificação: {e_mail}")
            else:
                print(f"❌ [Studio de Criação] Falha ao processar a postagem para o pedido '{doc_id}'.")

        return True

    except Exception as e:
        print(f"❌ Erro ao processar solicitações de usuário: {e}")
        return False

if __name__ == "__main__":
    processar_solicitacoes_pendentes()
