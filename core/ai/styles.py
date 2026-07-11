import random

# ==========================================
# ESTILOS DE COPY (abordagem narrativa / tons)
# ==========================================
ESTILOS_COPY = [
    "Tom agressivo e direto: acorde o leitor com uma verdade inconveniente, sem rodeios ou carinho (ex: 'Pare de mentir para você mesmo...')",
    "Tom acolhedor e poético: demonstre empatia e fale de alma para alma, criando um ambiente seguro (ex: 'Eu sei como a noite parece mais longa quando...')",
    "Tom filosófico e reflexivo: faça o leitor questionar a realidade profunda usando metáforas fortes (ex: 'Nós passamos a vida construindo gaiolas para...')",
    "Tom irônico e sarcástico: deboche suavemente da situação ridícula em que o leitor se colocou (ex: 'Parabéns, você conseguiu estragar tudo de novo. E agora?')",
    "Tom científico e analítico: explique as coisas como um neurologista ou psicólogo, usando fatos para destruir ilusões (ex: 'A dopamina que você busca no celular é a mesma que...')",
    "Tom misterioso e confidencial: fale como se estivesse revelando um segredo que ninguém mais sabe (ex: 'Feche a porta. O que vou te contar agora é apenas para...')",
    "Tom professoral e didático: ensine com autoridade e clareza, dividindo a verdade em passos lógicos (ex: 'Existem três regras imutáveis que você precisa entender.')",
    "Tom de urgência e alerta de perigo: chame a atenção de forma protetiva, instilando medo de perder tempo (ex: 'Você tem exatamente três meses antes de...')",
    "Tom cínico e realista cru: destrua expectativas de filmes da Disney e traga para a vida real dura (ex: 'O mundo não deve nada a você. Se quiser algo, levante e...')",
    "Tom motivacional intenso: seja o treinador gritando no ouvido antes da guerra, inflamando a coragem (ex: 'Você nasceu para coisas maiores. Não aceite menos que...')",
    "Tom de revelação científica ou histórica: comece citando um estudo, estatística ou fato histórico desconhecido (ex: 'Estudaram X por 11 anos e concluíram que...')",
    "Tom de polarização direta: divida o público entre quem sabe algo e a massa ignorante (ex: 'A diferença entre quem joga o jogo real e quem fica na ilusão é...')",
]

# ==========================================
# GANCHOS NARRATIVOS (para abrir posts e vídeos)
# ==========================================
GANCHOS_NARRATIVOS = [
    "Você provavelmente está fazendo isso sem perceber.",
    "Ninguém fala sobre isso, mas deveria.",
    "O maior erro é justamente esse.",
    "Existe um detalhe que muda tudo.",
    "Quase todo mundo acredita nisso... e está errado.",
    "Se você entender isso hoje, muita coisa vai fazer sentido.",
    "A maioria das pessoas só percebe isso quando já é tarde.",
    "O problema nunca foi o que você imaginava.",
    "Poucas pessoas conhecem isso, mas faz toda a diferença.",
    "Esse pequeno hábito pode transformar completamente seus resultados.",
    "Antes de continuar, você precisa saber disso.",
    "O que vou mostrar agora muda a forma como você enxerga isso.",
    "Você já parou para pensar por que isso sempre acontece?",
    "A resposta é muito diferente do que você imagina.",
    "Você não precisa fazer mais. Precisa fazer diferente.",
    "Será que tudo isso que você sente é amor ou só medo de ficar sozinho?",
    "Você está acordando exausto todos os dias por causa disso.",
    "2 atitudes silenciosas que destroem qualquer relação em meses."
]

# ==========================================
# GANCHOS CONQUISTADOR (Específicos para atração agressiva Topo de Funil)
# ==========================================
GANCHOS_CONQUISTADOR = [
    "Por que não te contaram isso antes?",
    "E se tudo o que você sabe sobre esse assunto estiver completamente errado?",
    "Você está fazendo isso de forma errada e eu posso provar.",
    "Por que fazer isso assim é infinitamente melhor do que o jeito tradicional.",
    "Como isso influencia a sua vida de uma forma que você nunca percebeu.",
    "Será que você está caindo nessa mesma armadilha sem notar?",
    "Então você acha que está no controle? Deixa eu te mostrar os bastidores."
]

def sortear_gancho_conquistador(historico=None):
    import random
    if historico is None: historico = []
    opcoes = [g for g in GANCHOS_CONQUISTADOR if g not in historico]
    if not opcoes:
        opcoes = GANCHOS_CONQUISTADOR
    return random.choice(opcoes)

# ==========================================
# REGRAS DE COPY (compartilhadas por todos os prompts)
# ==========================================
REGRAS_COPY_BASE = """
REGRAS ABSOLUTAS DE COPY (violá-las é inaceitável):

❌ PROIBIDO — NUNCA use estas frases de autoajuda vazia:
- "Acredite em você", "Você é capaz", "Nunca desista", "Foco e determinação"
- "Seja a melhor versão de si mesmo", "Saia da zona de conforto"
- "O sucesso é para quem corre atrás", "A vida é uma jornada"
- "Faça acontecer", "Você tem o poder", "Hoje é o dia"
- NUNCA use tom professoral, arrogante ou com palavras difíceis. Fale de igual para igual.
- NUNCA cite autores, livros, filmes, séries, marcas ou personagens pelo nome (exceto figuras públicas icônicas como Elon Musk em contextos específicos de curiosidade).

✅ OBRIGATÓRIO — o tom agressivo e atraente:
- O primeiro slide deve ser um gancho forte, curto e cortante. Ele DEVE quebrar o padrão e parar o scroll.
- Use linguagem direta, falada e visceral (coloquial do Brasil).
- Crie contradição imediata: o leitor deve querer discordar nos primeiros 3 segundos, mas concordar ao ler a explicação.
- Use sentenças curtas e parágrafos de uma linha. Textos longos matam a retenção.
- Direcionamento prático: no final de posts de valor, mostre um passo prático curto para resolver a dor.
- Tom: direto, instigante, misterioso e pragmático. Como alguém que enxerga o sistema por trás do comportamento.

🧠 PROCESSOS DE PERSUASÃO:
- INTERRUPÇÃO DE ESTADO: Mude o estado mental do usuário com um fato inesperado ou estudo chocante no início.
- EFEITO ZEIGARNIK: Abra um ciclo de curiosidade no slide 1 e só feche no final.
- DOPAMINA: Entregue um 'segredo' ou atalho prático que o leitor sinta que valeria dinheiro.
- IDENTIDADE: Trate quem lê até o fim como alguém acima da média (ex: 'Quem chega até aqui já entendeu o que a massa ignora').
"""

def sortear_estilo(historico_estilos=None):
    if historico_estilos is None: historico_estilos = []
    opcoes = [e for e in ESTILOS_COPY if e not in historico_estilos]
    if not opcoes:
        opcoes = ESTILOS_COPY
    return random.choice(opcoes)

def sortear_gancho(historico_ganchos=None):
    if historico_ganchos is None: historico_ganchos = []
    opcoes = [g for g in GANCHOS_NARRATIVOS if g not in historico_ganchos]
    if not opcoes:
        opcoes = GANCHOS_NARRATIVOS
    return random.choice(opcoes)
