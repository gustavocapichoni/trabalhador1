import os
import sys
import json
import time
import requests
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv

# Garante que importações da raiz do projeto funcionem
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

from core.config.state import carregar_estado
from core.publisher.email_notifier import enviar_email_notificacao

# Configura o terminal para aceitar UTF-8 (emojis) no Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Carrega as variáveis de ambiente do .env se existir
load_dotenv()

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")
ESTADO_FILE = "estado.json"



def obter_id_conta_instagram():
    """Tenta descobrir o ID da conta do Instagram se não estiver explicitamente configurado."""
    global IG_ACCOUNT_ID
    if IG_ACCOUNT_ID:
        return IG_ACCOUNT_ID
        
    if not IG_ACCESS_TOKEN:
        return None
        
    print("🔍 IG_ACCOUNT_ID ausente no ambiente. Tentando descobrir automaticamente...")
    try:
        url_pages = f"https://graph.facebook.com/v19.0/me/accounts?access_token={IG_ACCESS_TOKEN}"
        res = requests.get(url_pages, timeout=15)
        if res.status_code == 200:
            pages = res.json().get("data", [])
            for page in pages:
                page_id = page.get("id")
                url_ig = f"https://graph.facebook.com/v19.0/{page_id}?fields=instagram_business_account&access_token={IG_ACCESS_TOKEN}"
                res_ig = requests.get(url_ig, timeout=15)
                if res_ig.status_code == 200:
                    ig_data = res_ig.json()
                    ig_biz = ig_data.get("instagram_business_account", {})
                    ig_id = ig_biz.get("id")
                    if ig_id:
                        print(f"✅ Conta do Instagram encontrada: {ig_id}")
                        IG_ACCOUNT_ID = ig_id
                        return ig_id
        else:
            print(f"⚠️ Erro ao buscar páginas vinculadas: {res.text}")
    except Exception as e:
        print(f"⚠️ Erro ao descobrir conta do Instagram automaticamente: {e}")
    return None

def obter_metricas_instagram(ig_id):
    if not ig_id or not IG_ACCESS_TOKEN:
        return None
        
    print(f"📊 Buscando métricas para a conta {ig_id}...")
    try:
        url = f"https://graph.facebook.com/v19.0/{ig_id}?fields=followers_count,media_count,name,username&access_token={IG_ACCESS_TOKEN}"
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            return res.json()
        else:
            print(f"⚠️ Erro ao consultar métricas da Meta API: {res.text}")
    except Exception as e:
        print(f"⚠️ Erro de rede ao buscar métricas: {e}")
    return None

def carregar_historico_recente():
    posts_recentes = []
    from core.analytics.db import get_db
    db = get_db()
    if not db:
        return posts_recentes

    try:
        limite_data = datetime.now(timezone.utc) - timedelta(days=7)
        # Tenta pegar apenas da data para frente (string sorting)
        limite_str = limite_data.strftime("%Y-%m-%d %H:%M:%S")
        
        docs = db.collection("historico_posts").where("data", ">=", limite_str).stream()
        for doc in docs:
            posts_recentes.append(doc.to_dict())
            
    except Exception as e:
        print(f"⚠️ Erro ao consultar historico_posts: {e}")
            
    return posts_recentes

def analisar_melhores_horarios():
    """Lê os dados de métricas locais e calcula os 6 horários com maior média de views e detalha formatos, temas e abordagens campeãs."""
    metricas_file = "analytics/dados/metricas.json"
    if not os.path.exists(metricas_file):
        return None
        
    try:
        with open(metricas_file, "r", encoding="utf-8") as f:
            dados = json.load(f)
            
        posts = dados.get("posts", {})
        horarios = {}
        
        for post_id, info in posts.items():
            info_post = info.get("info_post", {})
            metricas = info.get("metricas", {})
            
            data_str = info_post.get("data")
            if not data_str:
                continue
                
            try:
                hora = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").hour
            except:
                continue
                
            views = metricas.get("views") or metricas.get("impressions") or metricas.get("plays") or 0
            
            if hora not in horarios:
                horarios[hora] = {
                    "total_views": 0, 
                    "count": 0,
                    "tipos": {},
                    "temas": {},
                    "estilos": {}
                }
                
            horarios[hora]["total_views"] += views
            horarios[hora]["count"] += 1
            
            tipo = info_post.get("tipo", "desconhecido").upper()
            tema = info_post.get("tema", "desconhecido").lower()
            estilo = info_post.get("estilo_copy", "padrão")
            if estilo and ":" in estilo:
                estilo = estilo.split(":")[0]
            
            horarios[hora]["tipos"][tipo] = horarios[hora]["tipos"].get(tipo, 0) + views
            horarios[hora]["temas"][tema] = horarios[hora]["temas"].get(tema, 0) + views
            horarios[hora]["estilos"][estilo] = horarios[hora]["estilos"].get(estilo, 0) + views
            
        ranking = []
        for h, stats in horarios.items():
            if stats["count"] > 0:
                media = stats["total_views"] / stats["count"]
                
                melhor_tipo = max(stats["tipos"], key=stats["tipos"].get) if stats["tipos"] else "N/A"
                melhor_tema = max(stats["temas"], key=stats["temas"].get) if stats["temas"] else "N/A"
                melhor_estilo = max(stats["estilos"], key=stats["estilos"].get) if stats["estilos"] else "N/A"
                
                ranking.append({
                    "hora": h, 
                    "media": media, 
                    "posts": stats["count"],
                    "melhor_tipo": melhor_tipo,
                    "melhor_tema": melhor_tema,
                    "melhor_estilo": melhor_estilo
                })
                
        ranking.sort(key=lambda x: x["media"], reverse=True)
        return ranking[:6]
    except Exception as e:
        print(f"⚠️ Erro ao analisar horários: {e}")
        return None

def obter_top_posts_semanais():
    metricas_file = "analytics/dados/metricas.json"
    if not os.path.exists(metricas_file):
        return None
        
    try:
        with open(metricas_file, "r", encoding="utf-8") as f:
            dados = json.load(f)
            
        posts = dados.get("posts", {})
        posts_semanais = []
        limite_data = datetime.now(timezone.utc) - timedelta(days=7)
        
        for post_id, info in posts.items():
            info_post = info.get("info_post", {})
            metricas = info.get("metricas", {})
            
            data_str = info_post.get("data")
            if not data_str:
                continue
                
            try:
                post_dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except:
                continue
                
            if post_dt >= limite_data:
                posts_semanais.append({
                    "post_id": post_id,
                    "data": data_str,
                    "tipo": info_post.get("tipo", "desconhecido"),
                    "tema": info_post.get("tema", "desconhecido"),
                    "estilo": info_post.get("estilo_copy", "padrão"),
                    "likes": metricas.get("likes", 0),
                    "comments": metricas.get("comments", 0),
                    "shares": metricas.get("shares", 0),
                    "saved": metricas.get("saved", 0),
                    "views": metricas.get("views") or metricas.get("impressions") or metricas.get("plays") or 0,
                    "caption": metricas.get("caption", "") or info_post.get("legenda", ""),
                    "frase_visual": info_post.get("frase_visual", ""),
                    "permalink": metricas.get("permalink", "")
                })
        
        top_views = sorted(posts_semanais, key=lambda x: x["views"], reverse=True)[:5]
        top_likes = sorted(posts_semanais, key=lambda x: x["likes"], reverse=True)[:5]
        top_shares = sorted(posts_semanais, key=lambda x: x["shares"], reverse=True)[:5]
        top_saves = sorted(posts_semanais, key=lambda x: x["saved"], reverse=True)[:5]
        
        return {
            "top_views": top_views,
            "top_likes": top_likes,
            "top_shares": top_shares,
            "top_saves": top_saves
        }
    except Exception as e:
        print(f"⚠️ Erro ao obter top posts semanais: {e}")
        return None

def gerar_e_enviar_relatorio():
    print("📋 Gerando relatório semanal do Bot Instagram...")
    ig_id = obter_id_conta_instagram()
    metrics = obter_metricas_instagram(ig_id)
    posts = carregar_historico_recente()
    
    # Monta a mensagem do relatório
    corpo = []
    corpo.append("📊 RELATÓRIO SEMANAL — BOT INSTAGRAM 📊")
    corpo.append("="*40)
    
    if metrics:
        corpo.append(f"Nome da Conta: {metrics.get('name')}")
        corpo.append(f"Username: @{metrics.get('username')}")
        corpo.append(f"Seguidores: {metrics.get('followers_count')}")
        corpo.append(f"Total de Publicações: {metrics.get('media_count')}")
    else:
        corpo.append("⚠️ Não foi possível obter métricas da Meta API para esta conta.")
        
    corpo.append("\n" + "="*40)
    corpo.append(f"📝 RESUMO DE ATIVIDADE (Últimos 7 dias)")
    corpo.append(f"Total de posts feitos pelo bot na semana: {len(posts)}")
    corpo.append("="*40)
    
    if posts:
        for idx, post in enumerate(posts, 1):
            corpo.append(f"{idx}. [{post.get('data')}] Tipo: {post.get('tipo').upper()} | Tema: {post.get('tema')}")
            if post.get("post_id"):
                corpo.append(f"   ID: {post.get('post_id')}")
    else:
        corpo.append("Nenhum post registrado nos últimos 7 dias no arquivo de estado.")
        
    # --- Nova Seção: Top Destaques da Semana ---
    corpo.append("\n" + "="*40)
    corpo.append("🏆 DESTAQUES DA SEMANA (TOP 5) 🏆")
    corpo.append("="*40)
    
    top_posts = obter_top_posts_semanais()
    if top_posts and any(top_posts.values()):
        # 1. Mais Visualizados
        corpo.append("\n🎬 REELS/POSTS MAIS VISUALIZADOS:")
        for idx, post in enumerate(top_posts["top_views"], 1):
            caption_resumida = post["caption"][:60].replace("\n", " ") + "..." if post["caption"] else "Sem legenda"
            frase_visual = f"\"{post['frase_visual']}\"" if post['frase_visual'] else "Não gravada"
            corpo.append(f"   #{idx} - {post['views']} views | Tema: {post['tema']} | Tipo: {post['tipo']}")
            corpo.append(f"       Frase Visual (Na tela): {frase_visual}")
            corpo.append(f"       Legenda (Texto do Post): \"{caption_resumida}\"")
            if post["permalink"]:
                corpo.append(f"       Ver no Instagram: {post['permalink']}")
                
        # 2. Mais Curtidos
        corpo.append("\n❤️ REELS/POSTS MAIS CURTIDOS:")
        for idx, post in enumerate(top_posts["top_likes"], 1):
            caption_resumida = post["caption"][:60].replace("\n", " ") + "..." if post["caption"] else "Sem legenda"
            frase_visual = f"\"{post['frase_visual']}\"" if post['frase_visual'] else "Não gravada"
            corpo.append(f"   #{idx} - {post['likes']} curtidas | Tema: {post['tema']} | Tipo: {post['tipo']}")
            corpo.append(f"       Frase Visual (Na tela): {frase_visual}")
            corpo.append(f"       Legenda (Texto do Post): \"{caption_resumida}\"")
            if post["permalink"]:
                corpo.append(f"       Ver no Instagram: {post['permalink']}")
                
        # 3. Mais Compartilhados
        corpo.append("\n✈️ REELS/POSTS MAIS COMPARTILHADOS:")
        for idx, post in enumerate(top_posts["top_shares"], 1):
            caption_resumida = post["caption"][:60].replace("\n", " ") + "..." if post["caption"] else "Sem legenda"
            frase_visual = f"\"{post['frase_visual']}\"" if post['frase_visual'] else "Não gravada"
            corpo.append(f"   #{idx} - {post['shares']} envios | Tema: {post['tema']} | Tipo: {post['tipo']}")
            corpo.append(f"       Frase Visual (Na tela): {frase_visual}")
            corpo.append(f"       Legenda (Texto do Post): \"{caption_resumida}\"")
            if post["permalink"]:
                corpo.append(f"       Ver no Instagram: {post['permalink']}")
                
        # 4. Mais Salvos
        corpo.append("\n📌 REELS/POSTS MAIS SALVOS (SAVES):")
        for idx, post in enumerate(top_posts["top_saves"], 1):
            caption_resumida = post["caption"][:60].replace("\n", " ") + "..." if post["caption"] else "Sem legenda"
            frase_visual = f"\"{post['frase_visual']}\"" if post['frase_visual'] else "Não gravada"
            corpo.append(f"   #{idx} - {post['saved']} salvamentos | Tema: {post['tema']} | Tipo: {post['tipo']}")
            corpo.append(f"       Frase Visual (Na tela): {frase_visual}")
            corpo.append(f"       Legenda (Texto do Post): \"{caption_resumida}\"")
            if post["permalink"]:
                corpo.append(f"       Ver no Instagram: {post['permalink']}")
    else:
        corpo.append("Ainda não há dados de métricas suficientes para listar os posts mais populares.")

    # --- Nova Seção: Horários de Ouro ---
    corpo.append("\n" + "="*40)
    corpo.append("⏰ TOP 6 MELHORES HORÁRIOS (Média de Views/Plays)")
    corpo.append("="*40)
    
    melhores_horarios = analisar_melhores_horarios()
    if melhores_horarios:
        for idx, item in enumerate(melhores_horarios, 1):
            hora_str = f"{item['hora']:02d}:00"
            corpo.append(
                f"🏆 #{idx} - {hora_str} | Média: {int(item['media'])} views ({item['posts']} posts)\n"
                f"       Melhor Formato: {item['melhor_tipo']} | Tema Vencedor: {item['melhor_tema']} | Abordagem: {item['melhor_estilo']}"
            )
        corpo.append("\n💡 Dica: Ajuste o agendamento no github actions (cron) para priorizar estes horários!")
    else:
        corpo.append("Ainda não há dados suficientes para determinar os melhores horários.")
        
    corpo.append("\n" + "="*40)
    corpo.append("Bot automático de postagens Instagram - Monitoramento Ativo")
    
    mensagem_final = "\n".join(corpo)
    print("\n--- Conteúdo do Relatório ---")
    print(mensagem_final)
    print("-----------------------------\n")
    
    enviar_email_notificacao(
        assunto="📊 Relatório Semanal de Atividade - Instagram Bot",
        mensagem=mensagem_final
    )

if __name__ == "__main__":
    if not IG_ACCESS_TOKEN:
        print("⚠️ IG_ACCESS_TOKEN não está configurado. Rodando relatório local apenas em modo log...")
    gerar_e_enviar_relatorio()
