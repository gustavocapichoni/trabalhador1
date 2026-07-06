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

def enviar_email_notificacao(assunto, mensagem):
    if not SMTP_EMAIL or not SMTP_PASSWORD or not NOTIFY_EMAIL:
        print("⚠️ Configurações de e-mail SMTP incompletas. Pulando envio de e-mail.")
        return
    try:
        msg = MIMEText(mensagem, 'plain', 'utf-8')
        msg['Subject'] = Header(assunto, 'utf-8')
        msg['From'] = SMTP_EMAIL
        msg['To'] = NOTIFY_EMAIL

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15)
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, [NOTIFY_EMAIL], msg.as_string())
        server.quit()
        print("✅ E-mail enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

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
    if os.path.exists(ESTADO_FILE):
        try:
            with open(ESTADO_FILE, "r", encoding="utf-8") as f:
                estado = json.load(f)
                historico = estado.get("historico", [])
                
                # Filtra postagens dos últimos 7 dias
                limite_data = datetime.now(timezone.utc) - timedelta(days=7)
                for post in historico:
                    try:
                        # post['data'] está em formato "%Y-%m-%d %H:%M:%S"
                        post_dt = datetime.strptime(post.get("data"), "%Y-%m-%d %H:%M:%S")
                        # Converter datetime ingênuo para ciente de UTC (assumindo UTC do runner)
                        post_dt = post_dt.replace(tzinfo=timezone.utc)
                        if post_dt >= limite_data:
                            posts_recentes.append(post)
                    except Exception:
                        posts_recentes.append(post)
        except Exception as e:
            print(f"⚠️ Erro ao carregar histórico: {e}")
    return posts_recentes

def analisar_melhores_horarios():
    """Lê os dados de métricas locais e calcula os 3 horários com maior média de views."""
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
                horarios[hora] = {"total_views": 0, "count": 0}
                
            horarios[hora]["total_views"] += views
            horarios[hora]["count"] += 1
            
        ranking = []
        for h, stats in horarios.items():
            if stats["count"] > 0:
                media = stats["total_views"] / stats["count"]
                ranking.append({"hora": h, "media": media, "posts": stats["count"]})
                
        ranking.sort(key=lambda x: x["media"], reverse=True)
        return ranking[:6]
    except Exception as e:
        print(f"⚠️ Erro ao analisar horários: {e}")
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
        
    # --- Nova Seção: Horários de Ouro ---
    corpo.append("\n" + "="*40)
    corpo.append("⏰ TOP 6 MELHORES HORÁRIOS (Média de Views/Plays)")
    corpo.append("="*40)
    
    melhores_horarios = analisar_melhores_horarios()
    if melhores_horarios:
        for idx, item in enumerate(melhores_horarios, 1):
            hora_str = f"{item['hora']:02d}:00"
            corpo.append(f"🏆 #{idx} - {hora_str} | Média: {int(item['media'])} views ({item['posts']} posts analisados)")
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
