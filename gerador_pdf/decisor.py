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

def decidir_tema_da_semana():
    """
    Lê o recomendacoes.json e retorna o tema com melhor performance.
    Combina dados de analytics com um fator aleatório menor para variedade.
    """
    print("🧠 [Decisor] Lendo dados de performance do Analytics...")

    try:
        with open(RECOMENDACOES_PATH, "r", encoding="utf-8") as f:
            recomendacoes = json.load(f)

        distribuicao_temas = recomendacoes.get("distribuicoes", {}).get("temas", {})

        if not distribuicao_temas:
            print("⚠️ Sem dados suficientes no analytics. Escolhendo tema aleatório.")
            return _tema_aleatorio()

        # Roleta Viciada: temas com maior peso têm mais chance de ser escolhidos
        temas = list(distribuicao_temas.keys())
        pesos = list(distribuicao_temas.values())

        # Filtra apenas os temas que temos mapeados com livros
        temas_validos = [(t, p) for t, p in zip(temas, pesos) if t in LIVROS_POR_TEMA]

        if not temas_validos:
            print("⚠️ Temas do analytics não coincidem com a biblioteca. Usando fallback.")
            return _tema_aleatorio()

        temas_filtrados, pesos_filtrados = zip(*temas_validos)
        tema_escolhido = random.choices(temas_filtrados, weights=pesos_filtrados, k=1)[0]

        print(f"✅ [Decisor] Tema escolhido pelos dados: {tema_escolhido} "
              f"(peso: {distribuicao_temas.get(tema_escolhido, 0)*100:.1f}%)")

    except FileNotFoundError:
        print("⚠️ recomendacoes.json não encontrado. Usando tema aleatório.")
        tema_escolhido = _tema_aleatorio()
    except Exception as e:
        print(f"⚠️ Erro ao ler analytics: {e}. Usando tema aleatório.")
        tema_escolhido = _tema_aleatorio()

    return tema_escolhido


def _tema_aleatorio():
    return random.choice(list(LIVROS_POR_TEMA.keys()))


def montar_briefing_completo():
    """
    Monta o briefing completo para o gerador de conteúdo:
    - Tema vencedor do Analytics
    - Livro escolhido dentro do tema
    - Contexto de tendências da semana (Olhos da Rede)
    """
    historico = buscar_historico_pdfs_recentes(limite=3)
    livros_recentes = [h.get("livro_base") for h in historico if h.get("livro_base")]

    tema = decidir_tema_da_semana()
    dados_tema = LIVROS_POR_TEMA[tema]
    
    # Filtra os livros que não foram usados recentemente
    livros_disponiveis = [l for l in dados_tema["livros"] if l not in livros_recentes]
    if not livros_disponiveis:
        # Se todos já foram usados, reseta a lista
        livros_disponiveis = dados_tema["livros"]

    livro_escolhido = random.choice(livros_disponiveis)

    print(f"📚 [Decisor] Livro base escolhido (anti-repetição aplicada): '{livro_escolhido}'")

    # Tenta buscar contexto de tendências
    contexto_mundo = ""
    try:
        from core.ai.olhos_da_rede import gerar_contexto_mundo_real
        contexto_mundo = gerar_contexto_mundo_real(dias=7, tema_especifico=dados_tema["nome_display"])
        print("🌍 [Decisor] Contexto da semana capturado com sucesso.")
    except Exception as e:
        print(f"⚠️ Não foi possível buscar tendências: {e}")
        contexto_mundo = "Sem contexto externo disponível nesta semana."

    briefing = {
        "tema_chave": tema,
        "nome_display": dados_tema["nome_display"],
        "livro_base": livro_escolhido,
        "dor_central": dados_tema["dor_central"],
        "contexto_semana": contexto_mundo
    }

    print(f"\n📋 BRIEFING DA SEMANA:")
    print(f"   Tema:  {briefing['nome_display']}")
    print(f"   Livro: {briefing['livro_base']}")
    print(f"   Dor:   {briefing['dor_central']}")

    return briefing
