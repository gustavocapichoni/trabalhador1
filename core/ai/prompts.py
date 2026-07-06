import random
from core.ai.styles import REGRAS_COPY_BASE, sortear_gancho

# ==========================================
# TEMAS E SUB-ÂNGULOS APROFUNDADOS
# ==========================================
TEMAS_MAPEADOS = {
    "espiritualidade": {
        "nome": "Espiritualidade e Fé",
        "inspira": "Evangelhos de Mateus e João, Provérbios de Salomão, Cantares, O Homem Mais Inteligente da História (gestão de emoções de Jesus)",
        "query_unsplash": "ancient temple golden hour,mystical ethereal light,sacred geometry bright,cinematic holy light ray,majestic stone ruins sunshine",
        "hashtags": ["#sabedoria", "#fe", "#proposito", "#espiritualidade", "#reflexao"],
        "sub_angulos": [
            "O silêncio absoluto que você evita é onde as respostas da sabedoria milenar estão guardadas",
            "Como o maior mestre da história não se abalava com o ódio, focando apenas na sua missão",
            "O paradoxo de exigir milagres divinos enquanto você foge da disciplina de fazer a sua parte",
            "A diferença entre religiosidade de fachada e a sabedoria brutal e prática dos provérbios antigos",
            "A hipocrisia de quem usa a fé como escudo para esconder um caráter corrompido nos bastidores",
            "Por que perdoar não é fraqueza, mas uma gestão de emoções avançada para não ser refém do passado"
        ]
    },
    "filosofia": {
        "nome": "Filosofia e Autoconhecimento",
        "inspira": "A Arte da Guerra (estratégia mental), O Vendedor de Sonhos (desconstrução do sistema), Estoicismo, PNL",
        "query_unsplash": "stoic marble statue bright,solitary chess piece golden hour,philosophical abstract light,shattered mirror reflection,cinematic thought clear sky",
        "hashtags": ["#autoconhecimento", "#filosofia", "#sabedoria", "#estoicismo", "#reflexao"],
        "sub_angulos": [
            "O sistema tenta te vender sonhos enlatados para que você nunca acorde para a sua verdadeira força",
            "Toda batalha é vencida ou perdida na sua própria mente muito antes do primeiro passo no mundo real",
            "A ilusão de ler dezenas de livros e não ter a coragem de aplicar uma única linha no caos da vida real",
            "Como o sistema educacional formatou a maioria para ter medo de pensar fora da caixa",
            "A verdadeira liberdade é não se importar com o tribunal do julgamento alheio enquanto constrói o seu império",
            "Por que tentar controlar o que está fora do seu alcance é a maneira mais rápida de destruir sua paz"
        ]
    },
    "psicologia": {
        "nome": "Psicologia e Comportamento Humano",
        "inspira": "Rápido e Devagar (Sistema 1 e 2), Blink, Armadilhas da Mente, Neurociência aplicada",
        "query_unsplash": "neon brain glowing,neural pathways bright,abstract mind maze light,psychological silhouette sunrise,premium dual face",
        "hashtags": ["#psicologia", "#decisao", "#mentalidade", "#comportamento", "#habito"],
        "sub_angulos": [
            "O seu cérebro prefere manter você preso no sofrimento conhecido do que arriscar a dor da mudança",
            "As armadilhas da sua mente: como você cria problemas imaginários para não focar no que precisa ser feito",
            "A farsa da 'falta de tempo': seu cérebro toma decisões em milissegundos para proteger seus vícios",
            "Por que o excesso de planejamento é apenas o seu medo paralisante fantasiado de inteligência analítica",
            "A síndrome do impostor: lá no fundo, você sabe que está entregando apenas uma fração do seu potencial",
            "Como a neurociência explica o seu vício por dopamina rápida enquanto a sua vida real fica estagnada"
        ]
    },
    "financas": {
        "nome": "Mentalidade Financeira e Riqueza",
        "inspira": "Pai Rico Pai Pobre (ativos vs passivos), Mais Esperto que o Diabo (alienação), PNL focada em negócios",
        "query_unsplash": "luxury wall street cinematic,monopoly board golden,luxury corporate skyscraper sun,premium gold vault,bright modern boardroom",
        "hashtags": ["#financas", "#riqueza", "#mentalidadefinanceira", "#sucesso", "#dinheiro"],
        "sub_angulos": [
            "O passivo financeiro de luxo que as pessoas compram apenas para impressionar quem elas nem gostam",
            "A alienação do sistema: o treinamento invisível para vender seu tempo valioso por uma segurança ilusória",
            "Ativos reais vs brinquedos caros: a diferença brutal entre focar em parecer livre",
            "O custo devastador de não arriscar criar um sistema de renda própria por puro medo do fracasso temporário",
            "A mentira de achar que ganhar mais dinheiro resolve a falta de inteligência emocional para poupar",
            "Como a mentalidade herdada de que 'o dinheiro é a raiz dos males' sabota suas chances de prosperar"
        ]
    },
    "liberdade": {
        "nome": "Liberdade, Sonhos e Coragem de Começar",
        "inspira": "O Vendedor de Sonhos (liberdade mental), O Poder da Ação, Mais Esperto que o Diabo (quebrar a hipnose)",
        "query_unsplash": "broken golden cage bright sky,cliff jump silhouette sunrise,lone wolf mountain top,epic mountain freedom bright,cinematic ocean waves sun",
        "hashtags": ["#liberdade", "#sonhos", "#jornada", "#perseveranca", "#foco"],
        "sub_angulos": [
            "A dor insuportável de olhar para trás daqui a 10 anos e ver que não teve a coragem de vender seus próprios sonhos",
            "A ilusão da segurança corporativa: o preço de vender sua energia vital para realizar a meta de outra pessoa",
            "O alienado nunca age: por que a grande massa desiste exatamente no ponto em que o jogo começaria a virar",
            "Tem poder quem age: não adianta ler todos os livros de sucesso se você treme perante o julgamento alheio",
            "O sacrifício silencioso que ninguém curte no Instagram e que define quem realmente vai ter liberdade de tempo",
            "Como saber se o seu cansaço é real ou é só a voz do medo te puxando de volta para a gaiola dourada"
        ]
    },
    "conexoes": {
        "nome": "Relacionamentos e Inteligência Emocional",
        "inspira": "Como Fazer Amigos e Influenciar Pessoas, A Arte da Persuasão, construção de família e relacionamentos fortes",
        "query_unsplash": "rain window cozy light,emotional connection,melancholic beautiful person,warm light embrace,city lights beautiful",
        "hashtags": ["#relacionamentos", "#conexao", "#empatia", "#inteligenciaemocional", "#amor"],
        "sub_angulos": [
            "O que você chama de amor incondicional é muitas vezes apenas um medo patológico e doentio de ficar sozinho",
            "Se você não consegue dizer 'não' aos outros, você está dizendo 'não' para a paz da sua própria família",
            "O maior segredo da persuasão não é falar bonito, é calar a boca e realmente ouvir o que o outro esconde",
            "Por que você tolera o desrespeito em silêncio achando que está sendo compreensivo, maduro e diplomático",
            "A diferença entre acolher alguém na sua vida e se tornar a lata de lixo dos problemas emocionais alheios",
            "O orgulho e a falta de diálogo direto destroem relações familiares de anos em um simples piscar de olhos"
        ]
    },
    "superacao": {
        "nome": "Superação e Autossabotagem",
        "inspira": "O Poder do Hábito (loop do hábito), O Poder da Ação, A Arte da Guerra (disciplina inclemente)",
        "query_unsplash": "storm path clearing sun,runner silhouette sunrise,gritty determination bright,mountain climb peak,intense morning light",
        "hashtags": ["#superacao", "#foco", "#resiliencia", "#coragem", "#determinacao"],
        "sub_angulos": [
            "O ciclo da derrota: um gatilho te estressa, você foge para um hábito destrutivo e depois se culpa",
            "O seu maior inimigo é a voz interna que sempre te convence a descansar um pouco mais quando ninguém vê",
            "A armadilha motivacional: o erro amador de esperar estar 'inspirado' em vez de usar a disciplina cega",
            "Escolha as suas batalhas: ser forte não é apanhar de tudo, é saber qual guerra vale a pena lutar até o fim",
            "O conforto é uma anestesia lenta que destrói o seu potencial um pouco todos os dias, sem causar dor imediata",
            "Se você focar apenas na meta e não mudar a sua identidade diária, a sua autossabotagem vai vencer de novo"
        ]
    },
    "proposito": {
        "nome": "Propósito e Legado",
        "inspira": "Eclesiastes, Provérbios de Salomão, Mais Esperto que o Diabo (propósito vs alienação), PNL (visão)",
        "query_unsplash": "epic forest sunlight ray,golden compass,lighthouse bright day,ancient tree roots glowing,vast sky stars bright",
        "hashtags": ["#proposito", "#legado", "#vida", "#intencao", "#evoluir"],
        "sub_angulos": [
            "A diferença colossal entre ter metas vazias para inflar o ego e construir um legado que proteja as próximas gerações",
            "Por que o sucesso material e os aplausos sem um propósito claro são a forma mais rápida de se sentir vazio",
            "Como saber se você está caminhando com intencionalidade ou apenas seguindo o rebanho hipnotizado para o abismo",
            "O preço silencioso de adiar a sua grande missão de vida ano após ano, até que não te reste mais saúde",
            "Quem você está se tornando no processo é infinitamente mais importante do que as conquistas temporárias",
            "O seu legado invisível: as decisões brutais que você toma hoje no escuro mudarão o rumo da sua família"
        ]
    }
}

# ==========================================
# TEMA POR DIA DA SEMANA
# ==========================================
TEMAS_POR_DIA = {
    0: "espiritualidade",  # Segunda
    1: "filosofia",        # Terça
    2: "psicologia",       # Quarta
    3: "financas",         # Quinta
    4: "liberdade",        # Sexta
    5: "conexoes",         # Sábado
    # Domingo = sorteio entre superacao e proposito
}

def montar_instrucoes_copy(detalhes_tema, contexto_analytics="", historico_angulos=None, historico_ganchos=None, is_conquistador=False):
    """Monta o bloco de instrução de copy injetado em todos os prompts, evitando repetições."""
    if historico_angulos is None: historico_angulos = []
    
    # Sorteia Ângulo (Roleta anti-repetição)
    opcoes_angulos = [a for a in detalhes_tema["sub_angulos"] if a not in historico_angulos]
    if not opcoes_angulos: # Reseta se todos já foram usados
        opcoes_angulos = detalhes_tema["sub_angulos"]
    sub_angulo = random.choice(opcoes_angulos)
    
    # Sorteia Gancho (passando histórico)
    from core.ai.styles import sortear_gancho_conquistador, sortear_gancho
    if is_conquistador:
        gancho = sortear_gancho_conquistador(historico_ganchos)
    else:
        gancho = sortear_gancho(historico_ganchos)

    instrucoes = f"""
    {REGRAS_COPY_BASE}
    
    Tema de inspiração (NÃO cite nomes, use apenas a essência): {detalhes_tema['inspira']}
    
    Ângulo específico para esta postagem: {sub_angulo}
    
    Gancho narrativo: {gancho}
    
    {contexto_analytics}
    """
    return instrucoes, sub_angulo, gancho
