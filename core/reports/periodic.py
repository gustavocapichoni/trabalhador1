import os
import sys
import json
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv

# Garante que importações da raiz do projeto funcionem
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

load_dotenv()

SMTP_EMAIL    = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
NOTIFY_EMAIL  = os.getenv("NOTIFY_EMAIL")
METRICAS_FILE = os.path.join(ROOT_DIR, "analytics", "dados", "metricas.json")

# Configuração de cada período
PERIODOS = {
    "mensal":     {"dias": 30,  "label": "MENSAL",     "emoji": "📅"},
    "trimestral": {"dias": 90,  "label": "TRIMESTRAL", "emoji": "📆"},
    "semestral":  {"dias": 180, "label": "SEMESTRAL",  "emoji": "🗓️"},
    "anual":      {"dias": 365, "label": "ANUAL",      "emoji": "📊"},
}


def enviar_email(assunto, mensagem):
    if not SMTP_EMAIL or not SMTP_PASSWORD or not NOTIFY_EMAIL:
        print("Configuracoes de e-mail SMTP incompletas. Pulando envio.")
        return
    try:
        msg = MIMEText(mensagem, 'plain', 'utf-8')
        msg['Subject'] = Header(assunto, 'utf-8')
        msg['From']    = SMTP_EMAIL
        msg['To']      = NOTIFY_EMAIL
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15)
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, [NOTIFY_EMAIL], msg.as_string())
        server.quit()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")


def carregar_metricas():
    # Sincroniza com o Firebase Firestore antes de carregar o arquivo local
    try:
        from core.analytics.coletor import carregar_metricas as sincronizar_firebase
        return sincronizar_firebase()
    except Exception as e:
        print(f"Erro ao sincronizar com Firebase: {e}. Usando arquivo local como fallback.")

    if not os.path.exists(METRICAS_FILE):
        print(f"Arquivo de metricas nao encontrado: {METRICAS_FILE}")
        return {}
    with open(METRICAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def filtrar_posts_por_periodo(posts: dict, dias: int) -> list:
    """Retorna apenas os posts dentro da janela de 'dias' dias."""
    limite = datetime.now(timezone.utc) - timedelta(days=dias)
    resultado = []
    for post_id, info in posts.items():
        data_str = info.get("info_post", {}).get("data", "")
        try:
            dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if dt >= limite:
            metricas = info.get("metricas", {})
            resultado.append({
                "post_id":      post_id,
                "data":         data_str,
                "tipo":         info.get("info_post", {}).get("tipo", "desconhecido"),
                "tema":         info.get("info_post", {}).get("tema", "desconhecido"),
                "estilo":       info.get("info_post", {}).get("estilo_copy", "padrao"),
                "frase_visual": info.get("info_post", {}).get("frase_visual", ""),
                "likes":        metricas.get("likes", 0),
                "comments":     metricas.get("comments", 0),
                "shares":       metricas.get("shares", 0),
                "saved":        metricas.get("saved", 0),
                "views":        metricas.get("views") or metricas.get("impressions") or metricas.get("plays") or 0,
                "caption":      metricas.get("caption", "") or info.get("info_post", {}).get("legenda", ""),
                "permalink":    metricas.get("permalink", ""),
            })
    return resultado


def calcular_estatisticas(posts: list) -> dict:
    """Calcula totais, médias e rankings dos posts."""
    if not posts:
        return {}

    total_views    = sum(p["views"]    for p in posts)
    total_likes    = sum(p["likes"]    for p in posts)
    total_comments = sum(p["comments"] for p in posts)
    total_shares   = sum(p["shares"]   for p in posts)
    total_saves    = sum(p["saved"]    for p in posts)
    n = len(posts)

    # Agrupamento por tipo
    por_tipo = {}
    for p in posts:
        t = p["tipo"].upper()
        if t not in por_tipo:
            por_tipo[t] = {"views": 0, "likes": 0, "count": 0}
        por_tipo[t]["views"] += p["views"]
        por_tipo[t]["likes"] += p["likes"]
        por_tipo[t]["count"] += 1

    # Agrupamento por tema
    por_tema = {}
    for p in posts:
        t = p["tema"].lower()
        if t not in por_tema:
            por_tema[t] = {"views": 0, "count": 0}
        por_tema[t]["views"] += p["views"]
        por_tema[t]["count"] += 1

    # Agrupamento por horário
    por_hora = {}
    for p in posts:
        try:
            hora = datetime.strptime(p["data"], "%Y-%m-%d %H:%M:%S").hour
        except Exception:
            continue
        if hora not in por_hora:
            por_hora[hora] = {"views": 0, "count": 0}
        por_hora[hora]["views"] += p["views"]
        por_hora[hora]["count"] += 1

    # Rankings
    top_views  = sorted(posts, key=lambda x: x["views"],  reverse=True)[:5]
    top_likes  = sorted(posts, key=lambda x: x["likes"],  reverse=True)[:5]
    top_shares = sorted(posts, key=lambda x: x["shares"], reverse=True)[:5]
    top_saves  = sorted(posts, key=lambda x: x["saved"],  reverse=True)[:5]

    melhor_tipo = max(por_tipo, key=lambda t: por_tipo[t]["views"] / max(por_tipo[t]["count"], 1)) if por_tipo else "N/A"
    melhor_tema = max(por_tema, key=lambda t: por_tema[t]["views"] / max(por_tema[t]["count"], 1)) if por_tema else "N/A"
    melhor_hora = max(por_hora, key=lambda h: por_hora[h]["views"] / max(por_hora[h]["count"], 1)) if por_hora else None

    return {
        "total_posts":     n,
        "total_views":     total_views,
        "total_likes":     total_likes,
        "total_comments":  total_comments,
        "total_shares":    total_shares,
        "total_saves":     total_saves,
        "media_views":     round(total_views    / n, 1),
        "media_likes":     round(total_likes    / n, 1),
        "media_comments":  round(total_comments / n, 1),
        "melhor_tipo":     melhor_tipo,
        "melhor_tema":     melhor_tema,
        "melhor_hora":     f"{melhor_hora:02d}:00" if melhor_hora is not None else "N/A",
        "top_views":       top_views,
        "top_likes":       top_likes,
        "top_shares":      top_shares,
        "top_saves":       top_saves,
        "por_tipo":        por_tipo,
        "por_tema":        por_tema,
    }


def montar_relatorio(tipo_periodo: str, stats: dict, total_posts_periodo: int) -> str:
    cfg = PERIODOS[tipo_periodo]
    label = cfg["label"]
    dias  = cfg["dias"]

    linhas = []
    linhas.append(f"RELATORIO {label} - BOT INSTAGRAM")
    linhas.append("=" * 45)
    linhas.append(f"Periodo analisado: ultimos {dias} dias")
    linhas.append(f"Data de geracao:   {datetime.now().strftime('%d/%m/%Y as %H:%M')}")
    linhas.append("=" * 45)

    if not stats:
        linhas.append(f"Nenhum post encontrado nos ultimos {dias} dias.")
        return "\n".join(linhas)

    # Resumo geral
    linhas.append("")
    linhas.append("RESUMO GERAL")
    linhas.append("-" * 30)
    linhas.append(f"  Total de posts publicados:  {stats['total_posts']}")
    linhas.append(f"  Total de visualizacoes:     {stats['total_views']:,}")
    linhas.append(f"  Total de curtidas:          {stats['total_likes']:,}")
    linhas.append(f"  Total de comentarios:       {stats['total_comments']:,}")
    linhas.append(f"  Total de compartilhamentos: {stats['total_shares']:,}")
    linhas.append(f"  Total de salvamentos:       {stats['total_saves']:,}")
    linhas.append("")
    linhas.append(f"  Media de views por post:    {stats['media_views']:,}")
    linhas.append(f"  Media de curtidas por post: {stats['media_likes']:,}")

    # Insights estrategicos
    linhas.append("")
    linhas.append("INSIGHTS ESTRATEGICOS DO PERIODO")
    linhas.append("-" * 30)
    linhas.append(f"  Formato campeo (mais views por post): {stats['melhor_tipo']}")
    linhas.append(f"  Tema campeo   (mais views por post):  {stats['melhor_tema']}")
    linhas.append(f"  Horario ouro  (mais views por post):  {stats['melhor_hora']}")

    # Desempenho por formato
    linhas.append("")
    linhas.append("DESEMPENHO POR FORMATO")
    linhas.append("-" * 30)
    for tipo, dados in sorted(stats["por_tipo"].items(), key=lambda x: x[1]["views"], reverse=True):
        media = round(dados["views"] / max(dados["count"], 1), 1)
        linhas.append(f"  {tipo:<20} | {dados['count']:>3} posts | {dados['views']:>8,} views totais | {media:>8,.1f} media")

    # Desempenho por tema
    linhas.append("")
    linhas.append("DESEMPENHO POR TEMA")
    linhas.append("-" * 30)
    for tema, dados in sorted(stats["por_tema"].items(), key=lambda x: x[1]["views"], reverse=True)[:10]:
        media = round(dados["views"] / max(dados["count"], 1), 1)
        linhas.append(f"  {tema:<25} | {dados['count']:>3} posts | {media:>8,.1f} media de views")

    # Top 5 posts por views
    linhas.append("")
    linhas.append("TOP 5 POSTS - MAIS VISUALIZADOS")
    linhas.append("-" * 30)
    for idx, p in enumerate(stats["top_views"], 1):
        caption = (p["caption"][:60] + "...") if p["caption"] else "Sem legenda"
        linhas.append(f"  #{idx} - {p['views']:,} views | {p['tipo'].upper()} | {p['tema']}")
        linhas.append(f"       Data:   {p['data']}")
        linhas.append(f"       Frase:  \"{p['frase_visual']}\"" if p["frase_visual"] else "       Frase:  Nao gravada")
        linhas.append(f"       Caption: \"{caption}\"")
        if p["permalink"]:
            linhas.append(f"       Link:   {p['permalink']}")

    # Top 5 posts por curtidas
    linhas.append("")
    linhas.append("TOP 5 POSTS - MAIS CURTIDOS")
    linhas.append("-" * 30)
    for idx, p in enumerate(stats["top_likes"], 1):
        linhas.append(f"  #{idx} - {p['likes']:,} curtidas | {p['tipo'].upper()} | {p['tema']} | {p['data']}")
        if p["permalink"]:
            linhas.append(f"       Link: {p['permalink']}")

    # Top 5 posts mais compartilhados
    linhas.append("")
    linhas.append("TOP 5 POSTS - MAIS COMPARTILHADOS")
    linhas.append("-" * 30)
    for idx, p in enumerate(stats["top_shares"], 1):
        linhas.append(f"  #{idx} - {p['shares']:,} shares | {p['tipo'].upper()} | {p['tema']} | {p['data']}")
        if p["permalink"]:
            linhas.append(f"       Link: {p['permalink']}")

    # Top 5 posts mais salvos
    linhas.append("")
    linhas.append("TOP 5 POSTS - MAIS SALVOS")
    linhas.append("-" * 30)
    for idx, p in enumerate(stats["top_saves"], 1):
        linhas.append(f"  #{idx} - {p['saved']:,} saves | {p['tipo'].upper()} | {p['tema']} | {p['data']}")
        if p["permalink"]:
            linhas.append(f"       Link: {p['permalink']}")

    linhas.append("")
    linhas.append("=" * 45)
    linhas.append("Bot automatico de postagens Instagram")
    linhas.append("Relatorio gerado automaticamente via GitHub Actions")

    return "\n".join(linhas)


def gerar_relatorio_periodico(tipo_periodo: str):
    """Ponto de entrada principal. Gera e envia o relatorio do periodo solicitado."""
    if tipo_periodo not in PERIODOS:
        print(f"Tipo de periodo invalido: {tipo_periodo}. Use: {list(PERIODOS.keys())}")
        sys.exit(1)

    cfg   = PERIODOS[tipo_periodo]
    label = cfg["label"]
    dias  = cfg["dias"]

    print(f"=== GERANDO RELATORIO {label} (ultimos {dias} dias) ===")

    dados    = carregar_metricas()
    posts    = filtrar_posts_por_periodo(dados.get("posts", {}), dias)
    stats    = calcular_estatisticas(posts)
    relatorio = montar_relatorio(tipo_periodo, stats, len(posts))

    print(relatorio)

    assunto = f"Relatorio {label} - Bot Instagram ({datetime.now().strftime('%d/%m/%Y')})"
    enviar_email(assunto, relatorio)

    print(f"=== RELATORIO {label} CONCLUIDO ===")


if __name__ == "__main__":
    tipo = sys.argv[1] if len(sys.argv) > 1 else None
    if not tipo:
        print("Uso: python periodic.py [mensal|trimestral|semestral|anual]")
        sys.exit(1)
    gerar_relatorio_periodico(tipo)
