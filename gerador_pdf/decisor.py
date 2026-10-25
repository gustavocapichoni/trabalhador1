"""
decisor.py — Inteligência de Decisão do PDF

Lê o recomendacoes.json (Analytics Interno) + tendências da semana (Olhos da Rede)
e decide qual tema e livro usar para o PDF desta semana.
"""
import json
import os
import sys
import random

# Raiz do repositório do bot (pasta pai do gerador_pdf)
BOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RECOMENDACOES_PATH = os.path.join(BOT_PATH, "analytics", "dados", "recomendacoes.json")

sys.path.insert(0, BOT_PATH)

def buscar_historico_pdfs_recentes(limite=4):
    """
    Busca os últimos PDFs gerados em 'historico_pdfs' no Firebase.
    Usado para evitar repetir os mesmos temas e livros recentes.
    """
    try:
        from core.analytics.db import get_db
        db = get_db()
        if not db:
            return []
        docs = db.collection("historico_pdfs").order_by("semana", direction="DESCENDING").limit(limite).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"⚠️ Erro ao buscar histórico de PDFs: {e}")
        return []

sys.path.insert(0, BOT_PATH)

# Mapeamento de temas para livros (espelhado do prompts.py do bot)
LIVROS_POR_TEMA = {
    "espiritualidade": {
        "nome_display": "Espiritualidade e Fé",
        "livros": ["Os Evangelhos", "Provérbios de Salomão", "O Homem Mais Inteligente da História"],
        "dor_central": "sentir que a vida perdeu o sentido e a conexão com algo maior"
    },
    "filosofia": {
        "nome_display": "Filosofia e Autoconhecimento",
        "livros": ["A Arte da Guerra", "O Vendedor de Sonhos"],
        "dor_central": "tentar agradar a todos enquanto se perde de si mesmo"
    },
    "psicologia": {
        "nome_display": "Psicologia e Comportamento Humano",
        "livros": ["Rápido e Devagar", "Blink", "Armadilhas da Mente"],
        "dor_central": "o cérebro que sabota e prefere o sofrimento conhecido à mudança"
    },
    "financas": {
        "nome_display": "Mentalidade Financeira",
        "livros": ["Pai Rico Pai Pobre", "Mais Esperto que o Diabo"],
        "dor_central": "trabalhar exausto sem nunca sentir que está chegando a algum lugar"
    },
    "liberdade": {
        "nome_display": "Liberdade e Coragem",
        "livros": ["O Vendedor de Sonhos", "O Poder da Ação", "Mais Esperto que o Diabo"],
        "dor_central": "adiar os próprios sonhos para construir a meta de outra pessoa"
    },
    "conexoes": {
        "nome_display": "Relacionamentos e IE",
        "livros": ["Como Fazer Amigos e Influenciar Pessoas", "A Arte da Persuasão"],
        "dor_central": "a solidão dentro de relacionamentos que já não se comunicam de verdade"
    },
    "superacao": {
        "nome_display": "Superação e Hábitos",
        "livros": ["O Poder do Hábito", "O Poder da Ação", "A Arte da Guerra"],
        "dor_central": "a voz interna que manda desistir toda vez que a mudança começa a doer"
    },
    "proposito": {
        "nome_display": "Propósito e Legado",
        "livros": ["Eclesiastes", "Provérbios de Salomão", "Mais Esperto que o Diabo"],
        "dor_central": "conquistar tudo materialmente mas sentir um vazio inexplicável por dentro"
    }
}

def decidir_tema_da_semana(temas_recentes=None):
    """
    Lê o recomendacoes.json e retorna o tema com melhor performance.
    Aplica rotação rígida para garantir que os 8 temas circulem e nunca repitam o tema recente.
    """
    print("🧠 [Decisor] Lendo dados de performance do Analytics para os 8 temas...")
    temas_recentes = temas_recentes or []

    try:
        with open(RECOMENDACOES_PATH, "r", encoding="utf-8") as f:
            recomendacoes = json.load(f)

        distribuicao_temas = recomendacoes.get("peso_final_temas", {})

        # Todos os 8 temas disponíveis no projeto
        todos_temas = list(LIVROS_POR_TEMA.keys())

        # Filtra temas não usados recentemente para manter inovação semanal
        temas_disponiveis = [t for t in todos_temas if t not in temas_recentes]
        if not temas_disponiveis:
            temas_disponiveis = todos_temas

        pesos = []
        for t in temas_disponiveis:
            peso = distribuicao_temas.get(t, 0.125) # Peso equilibrado padrão
            pesos.append(max(peso, 0.05))

        tema_escolhido = random.choices(temas_disponiveis, weights=pesos, k=1)[0]
        print(f"✅ [Decisor] Tema inovador escolhido: {tema_escolhido} (entre 8 temas possíveis)")

    except Exception as e:
        print(f"⚠️ Erro ao ler analytics: {e}. Usando rotação dos 8 temas.")
        todos_temas = list(LIVROS_POR_TEMA.keys())
        temas_disponiveis = [t for t in todos_temas if t not in temas_recentes] or todos_temas
        tema_escolhido = random.choice(temas_disponiveis)

    return tema_escolhido


def montar_briefing_completo():
    """
    Monta o briefing completo para o gerador de conteúdo:
    - Tema inovador (rotação entre os 8 temas sem repetição recente)
    - Livro base escolhido com anti-repetição
    - Contexto de tendências em tempo real (Olhos da Rede)
    - Dados de performance/interação do perfil (o que mais chamou atenção recentemente)
    """
    historico = buscar_historico_pdfs_recentes(limite=4)
    temas_recentes = [h.get("tema_chave") for h in historico if h.get("tema_chave")]
    livros_recentes = [h.get("livro_base") for h in historico if h.get("livro_base")]

    tema = decidir_tema_da_semana(temas_recentes=temas_recentes)
    dados_tema = LIVROS_POR_TEMA[tema]
    
    # Filtra os livros que não foram usados recentemente
    livros_disponiveis = [l for l in dados_tema["livros"] if l not in livros_recentes]
    if not livros_disponiveis:
        livros_disponiveis = dados_tema["livros"]

    livro_escolhido = random.choice(livros_disponiveis)

    print(f"📚 [Decisor] Livro base escolhido (anti-repetição aplicada): '{livro_escolhido}'")

    # Busca contexto de tendências nos Olhos da Rede
    contexto_mundo = ""
    try:
        from core.ai.olhos_da_rede import gerar_contexto_mundo_real
        contexto_mundo = gerar_contexto_mundo_real(dias=7, tema_especifico=dados_tema["nome_display"])
        print("🌍 [Decisor] Contexto da semana capturado com sucesso nos Olhos da Rede.")
    except Exception as e:
        print(f"⚠️ Não foi possível buscar tendências: {e}")
        contexto_mundo = "Sem contexto externo disponível nesta semana."

    # Extrai o que mais chamou atenção no perfil recentemente
    dados_performance_perfil = "Sem dados de performance recentes do perfil."
    try:
        if os.path.exists(RECOMENDACOES_PATH):
            with open(RECOMENDACOES_PATH, "r", encoding="utf-8") as f:
                recs = json.load(f)
            
            # Pega os ganchos com maior growth score
            ganchos = recs.get("ganchos_growth_score", {})
            ganchos_ordenados = sorted(ganchos.items(), key=lambda x: x[1], reverse=True)
            ganchos_str = "\n".join([f"  - {g[0]} (Score: {g[1]})" for g in ganchos_ordenados[:2]])
            
            # Pega os estilos/tons com melhor performance de retenção
            estilos = recs.get("peso_final_estilos", {})
            estilos_ordenados = sorted(estilos.items(), key=lambda x: x[1], reverse=True)
            estilos_str = "\n".join([f"  - {e[0][:120]}... (Peso: {e[1]})" for e in estilos_ordenados[:2]])
            
            dados_performance_perfil = (
                f"ESTILOS DE MAIOR RETENÇÃO NO PERFIL:\n{estilos_str}\n\n"
                f"GATILHOS DE MAIOR ENGAJAMENTO (GANCHOS):\n{ganchos_str}"
            )
    except Exception as e:
        print(f"⚠️ Erro ao extrair dados de performance para briefing do PDF: {e}")

    briefing = {
        "tema_chave": tema,
        "nome_display": dados_tema["nome_display"],
        "livro_base": livro_escolhido,
        "dor_central": dados_tema["dor_central"],
        "contexto_semana": contexto_mundo,
        "dados_performance_perfil": dados_performance_perfil
    }

    print(f"\n📋 BRIEFING DA SEMANA:")
    print(f"   Tema:  {briefing['nome_display']}")
    print(f"   Livro: {briefing['livro_base']}")
    print(f"   Dor:   {briefing['dor_central']}")

    return briefing
