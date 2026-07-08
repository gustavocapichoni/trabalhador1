import random

# ==========================================
# ESTILOS DE COPY (abordagem narrativa)
# ==========================================
ESTILOS_COPY = [
    "revelação científica ou histórica: comece citando um estudo, estatística ou fato histórico desconhecido (ex: 'Estudaram X por 11 anos e concluíram que...')",
    "quebra de expectativa/ilusão: aponte uma mentira que as pessoas contam a si mesmas (ex: 'O que você chama de prudência é na verdade...')",
    "diagnóstico cirúrgico: aponte o erro exato que o leitor está cometendo agora (ex: 'O erro que impede você de...')",
    "alerta de perigo/cuidado: chame a atenção de forma protetiva e misteriosa (ex: 'Leia isso com muito cuidado se você...')",
    "polarização direta: divida o público entre quem sabe algo e a massa ignorante (ex: 'A diferença entre quem joga o jogo real e quem fica na ilusão é...')",
]

# ==========================================
# GANCHOS NARRATIVOS (para abrir posts e vídeos)
# ==========================================
GANCHOS_NARRATIVOS = [
    # --- Segredo / Autoridade (Conexão direta com os métodos dos livros) ---
    "Existe um método não ensinado nas escolas que as pessoas do topo usam. E ele funciona assim:",
    "O que vou te mostrar agora foi retirado da rotina de pessoas que já chegaram onde você quer chegar. Preste atenção:",
    "Você está perdendo anos da sua vida tentando resolver isso do jeito difícil. Existe um atalho prático que ninguém fala:",
    "O segredo que as pessoas que têm resultados guardam a sete chaves não é sobre trabalhar mais. É sobre algo muito mais simples:",
    
    # --- Quebra Absoluta / Aversão à Perda ---
    "Nos próximos 30 segundos, eu vou te provar por que a sua estratégia atual está destruindo os seus resultados.",
    "Se você continuar fazendo isso, vai olhar para trás daqui a 5 anos e se arrepender profundamente.",
    "Pare o que está fazendo. Esse é o erro mais silencioso e destrutivo que você está cometendo todos os dias sem perceber:",
    "Leia isto com muito cuidado se você não aguenta mais ver outras pessoas avançando enquanto você sente que está parado no mesmo lugar:",
    
    # --- Polarização (Nós vs Eles) ---
    "Apenas 1% das pessoas vai ter coragem de ouvir a verdade dolorosa que estou prestes a dizer. A maioria vai pular esse vídeo:",
    "Enquanto a grande massa foca no que é bonito, quem tem resultados de verdade foca apenas neste único princípio:",
    "A verdade nua e crua que a indústria esconde de você para continuar vendendo ilusões:",
    "Tem maturidade suficiente para ler isto sem se ofender? O que você chama de 'esperar o momento certo' é apenas o seu medo de...",
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
# CTAS VARIADOS (chamadas para ação)
# ==========================================
CTAS_VARIAVEIS = [
    "Salve este post. A sua mente vai tentar esquecer essa verdade amanhã por puro instinto de defesa.",
    "Compartilhe com aquela pessoa que precisa parar de usar desculpas hoje mesmo.",
    "Qual slide bateu mais forte em você? Comente o número.",
    "Se você concorda, ótimo. Se discorda, me diga o porquê nos comentários.",
]

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
    # Filtra os estilos que NÃO estão no histórico recente
    opcoes = [e for e in ESTILOS_COPY if e not in historico_estilos]
    if not opcoes: # Se todos já foram usados, reseta
        opcoes = ESTILOS_COPY
    return random.choice(opcoes)

def sortear_gancho(historico_ganchos=None):
    if historico_ganchos is None: historico_ganchos = []
    opcoes = [g for g in GANCHOS_NARRATIVOS if g not in historico_ganchos]
    if not opcoes:
        opcoes = GANCHOS_NARRATIVOS
    return random.choice(opcoes)

def sortear_cta():
    return random.choice(CTAS_VARIAVEIS)
