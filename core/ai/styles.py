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
# GANCHOS ORGANIZADOS POR CATEGORIA
# Cada categoria define uma ESTRUTURA diferente para o Slide 1.
# O sistema usa sequência LINEAR — um gancho por postagem, em ordem,
# reiniciando do início ao chegar no último.
# ==========================================
GANCHOS_POR_CATEGORIA = {

    # ── Categorias Originais ──────────────────────────────────────────

    "pergunta_que_agride": [
        "Você já parou pra pensar por que isso sempre acontece com você?",
        "Por que a maioria das pessoas entrega o mínimo e espera o máximo?",
        "Qual é o preço real que você está pagando por esse hábito?",
        "Será que tudo isso que você sente é amor ou só medo de ficar sozinho?",
        "Você está construído para vencer ou só para sobreviver?",
        "Por que você trata qualquer um melhor do que trata a si mesmo?",
    ],
    "afirmacao_que_choca": [
        "Quase todo mundo acredita nisso... e está completamente errado.",
        "A maioria das pessoas só percebe isso quando já é tarde demais.",
        "O problema nunca foi o que você imaginava.",
        "O seu maior inimigo está dentro da sua própria cabeça.",
        "Disciplina sem direção é só sofrimento organizado.",
        "Tudo que você adia vira uma dívida emocional que vai cobrar juros.",
    ],
    "declaracao_segunda_pessoa": [
        "Você provavelmente está fazendo isso sem perceber.",
        "Você está acordando exausto todos os dias por causa disso.",
        "Você não precisa fazer mais. Precisa fazer diferente.",
        "Você tolera demais quem não te respeita nem um pouco.",
        "Você confunde lealdade com medo de decepcionar.",
        "Você sabe a resposta. Só tem medo de agir sobre ela.",
    ],
    "segredo_revelacao": [
        "Ninguém fala sobre isso, mas deveria.",
        "Existe um detalhe que muda tudo. Pouquíssimas pessoas conhecem.",
        "Antes de continuar, você precisa saber disso.",
        "O que vou mostrar agora muda a forma como você enxerga isso.",
        "2 atitudes silenciosas que destroem qualquer relação em meses.",
        "Há um padrão nos seus erros que você não foi treinado pra ver.",
    ],
    "dado_estatistica": [
        "Estudos mostram que a maioria abandona o seu sonho exatamente aqui.",
        "7 em cada 10 pessoas fazem isso e nunca chegam onde querem.",
        "Pesquisas revelam que esse único hábito muda completamente os resultados.",
        "Existe um padrão científico por trás do que você está sentindo agora.",
        "O seu cérebro faz isso automaticamente. E isso pode estar destruindo você.",
        "A neurociência já sabe por que você fica preso nesse ciclo.",
    ],

    # ── Novas Categorias ─────────────────────────────────────────────

    "desafio": [
        "Você tem 30 segundos para me provar que...",
        "Tente responder isso sem pensar por muito tempo...",
        "Me diga se você realmente acredita nisso...",
        "Você conseguiria explicar isso para uma criança?",
        "Aposto que você nunca parou para pensar nisso.",
        "Quero ver se você consegue responder essa pergunta.",
        "Faça um teste comigo agora.",
        "Você teria coragem de responder isso olhando no espelho?",
    ],
    "curiosidade": [
        "Uma coisa que ninguém te conta é...",
        "Existe um detalhe que muda tudo.",
        "Quase ninguém percebe isso.",
        "Existe uma pergunta que a maioria evita responder.",
        "Poucas pessoas entendem o verdadeiro motivo disso.",
        "Você provavelmente nunca ouviu isso dessa forma.",
        "Existe algo acontecendo e quase ninguém percebe.",
        "O problema nunca foi o que você imaginou.",
    ],
    "quebra_de_expectativa": [
        "Poder não é ter dinheiro. Poder é...",
        "O sucesso não começa quando você vence.",
        "O maior erro não é errar.",
        "A liberdade não é fazer tudo o que você quer.",
        "O medo não é seu maior inimigo.",
        "Inteligência não garante boas decisões.",
        "Nem tudo que faz sentido funciona.",
        "Nem toda verdade ajuda você.",
    ],
    "reflexao": [
        "Como você imaginou sua vida anos atrás?",
        "Quando foi a última vez que você mudou de ideia?",
        "O que você vê quando olha para este post?",
        "Quem você seria se não tivesse medo?",
        "O que realmente controla suas decisões?",
        "Qual foi a última escolha que mudou sua vida?",
        "Você vive ou apenas reage?",
        "Se ninguém estivesse olhando, você faria a mesma coisa?",
    ],
    "paradoxo": [
        "Quanto mais você tenta controlar tudo...",
        "Quanto mais você foge disso...",
        "Quanto mais respostas você encontra...",
        "Às vezes perder é exatamente o que faz você ganhar.",
        "O maior obstáculo pode ser justamente sua maior qualidade.",
        "Quanto mais ocupado você está, menos você avança.",
        "Quanto mais você busca aprovação, menos liberdade encontra.",
        "A resposta que você procura pode ser justamente a pergunta que evita fazer.",
    ],
    "identidade": [
        "Existem dois tipos de pessoas...",
        "Pessoas comuns fazem isso. Pessoas extraordinárias fazem aquilo.",
        "Quem pensa assim dificilmente cresce.",
        "Quem domina isso nunca mais vê a vida da mesma forma.",
        "A diferença entre quem consegue e quem desiste está aqui.",
        "Você pertence a qual grupo?",
        "O que separa os fortes dos fracos não é força.",
        "A maioria vive desse jeito. Poucos vivem assim.",
    ],
    "conflito": [
        "Eu discordo completamente dessa ideia...",
        "Todo mundo acredita nisso... e talvez esteja errado.",
        "Essa é uma opinião impopular.",
        "Você foi ensinado a acreditar nisso desde criança.",
        "Existe uma mentira que parece verdade.",
        "A pior decisão que você pode tomar é essa.",
        "O conselho mais famoso pode ser o mais perigoso.",
        "O que vou dizer agora incomoda muita gente.",
    ],
    "comparacao": [
        "Antes de perceber isso...",
        "Depois que entendi isso...",
        "Antes eu fazia assim. Hoje faço diferente.",
        "A diferença entre essas duas pessoas parece pequena, mas muda tudo.",
        "O mesmo problema pode ter duas respostas completamente diferentes.",
        "O que mudou não foi minha vida, foi minha forma de pensar.",
    ],
}

# ─────────────────────────────────────────────────────────────────────
# LISTA SEQUENCIAL MESTRA — todos os ganchos na ordem de cadastro.
# O bot cicla por esta lista: post 1 usa índice 0, post 2 usa índice 1,
# e quando chega ao último, reinicia do zero.
# ─────────────────────────────────────────────────────────────────────
LISTA_GANCHOS_SEQUENCIAL = [
    gancho for categoria in GANCHOS_POR_CATEGORIA.values() for gancho in categoria
]


# ==========================================
# GANCHOS CONQUISTADOR — ciclo sequencial próprio
# ==========================================
LISTA_GANCHOS_CONQUISTADOR = [
    "Por que não te contaram isso antes?",
    "E se tudo o que você sabe sobre esse assunto estiver completamente errado?",
    "Você está fazendo isso de forma errada e eu posso provar.",
    "Por que fazer isso assim é infinitamente melhor do que o jeito tradicional.",
    "Como isso influencia a sua vida de uma forma que você nunca percebeu.",
    "Será que você está caindo nessa mesma armadilha sem notar?",
    "Então você acha que está no controle? Deixa eu te mostrar os bastidores.",
]



# ─────────────────────────────────────────────────────────────────────
# FUNÇÕES DE CICLO SEQUENCIAL
# ─────────────────────────────────────────────────────────────────────

def proximo_gancho(indice_atual=0):
    """Retorna o próximo gancho da sequência linear, reiniciando após o último.

    Returns:
        gancho (str): Texto do gancho a ser usado.
        novo_indice (int): Próximo índice a ser salvo no estado.
        categoria_gancho (str): Categoria do gancho (usada para orientar a IA).
    """
    indice_atual = indice_atual % len(LISTA_GANCHOS_SEQUENCIAL)
    gancho = LISTA_GANCHOS_SEQUENCIAL[indice_atual]
    novo_indice = (indice_atual + 1) % len(LISTA_GANCHOS_SEQUENCIAL)

    # Identifica a categoria para orientar a IA sobre o formato correto
    categoria_gancho = "afirmacao_que_choca"  # fallback
    for cat, ganchos in GANCHOS_POR_CATEGORIA.items():
        if gancho in ganchos:
            categoria_gancho = cat
            break

    return gancho, novo_indice, categoria_gancho


def proximo_gancho_conquistador(indice_atual=0):
    """Retorna o próximo gancho conquistador na sequência linear.

    Returns:
        gancho (str): Texto do gancho conquistador.
        novo_indice (int): Próximo índice a ser salvo no estado.
    """
    indice_atual = indice_atual % len(LISTA_GANCHOS_CONQUISTADOR)
    gancho = LISTA_GANCHOS_CONQUISTADOR[indice_atual]
    novo_indice = (indice_atual + 1) % len(LISTA_GANCHOS_CONQUISTADOR)
    return gancho, novo_indice


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
- Você tem total liberdade para citar livros, filósofos, teorias e autores para dar peso de autoridade à mensagem.

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
    if historico_estilos is None:
        historico_estilos = []
    opcoes = [e for e in ESTILOS_COPY if e not in historico_estilos]
    if not opcoes:
        opcoes = ESTILOS_COPY
    return random.choice(opcoes)



# ==========================================
# CTAs ORGANIZADOS POR CATEGORIA (32 itens)
# Fornecidos pelo usuário para alternar objetivos estrategicamente
# ==========================================
CTAS_POR_CATEGORIA = {
    "seguir": [
        "Se isso fez sentido para você, talvez este perfil seja para você.",
        "Aqui a gente faz perguntas que quase ninguém faz.",
        "Se você gosta de pensar diferente, acompanhe este perfil.",
        "Se esse assunto te interessa, ainda tem muito conteúdo por aqui.",
        "Se você procura respostas diferentes, fique por aqui.",
        "Se você gosta de entender o comportamento humano, siga.",
        "Se você acredita que sempre existe outra perspectiva, acompanhe.",
        "Talvez essa seja apenas uma das perguntas que você precisava fazer."
    ],
    "comentario": [
        "Quero saber sua resposta.",
        "O que você faria?",
        "Concorda ou discorda?",
        "Qual foi sua primeira reação?",
        "Resuma sua opinião em uma palavra.",
        "Você já viveu isso?",
        "O que você pensa sobre isso?",
        "Existe outra forma de enxergar isso?"
    ],
    "compartilhamento": [
        "Envie para alguém que precisa ouvir isso.",
        "Compartilhe com quem pensa diferente.",
        "Mostre isso para um amigo.",
        "Essa conversa merece continuar.",
        "Quem você conhece que responderia diferente?",
        "Compartilhe e compare as respostas.",
        "Quero saber o que outra pessoa responderia.",
        "Vale a pena ouvir uma segunda opinião."
    ],
    "salvamento": [
        "Salve para refletir depois.",
        "Guarde isso.",
        "Você pode querer lembrar disso amanhã.",
        "Vale a pena voltar aqui.",
        "Salve antes de esquecer.",
        "Essa reflexão merece ser revisitada.",
        "Nem toda resposta aparece na primeira leitura.",
        "Guarde essa ideia."
    ]
}

# ─────────────────────────────────────────────────────────────────────
# LISTA INTERCALADA DE CTAs — Garante que o objetivo de engajamento
# (seguir, comentar, compartilhar, salvar) mude a cada postagem de forma
# alternada e balanceada, passando por cada uma das 32 referências.
# ─────────────────────────────────────────────────────────────────────
LISTA_CTAS_SEQUENCIAL = []
for i in range(8):
    LISTA_CTAS_SEQUENCIAL.append(("seguir", CTAS_POR_CATEGORIA["seguir"][i]))
    LISTA_CTAS_SEQUENCIAL.append(("comentario", CTAS_POR_CATEGORIA["comentario"][i]))
    LISTA_CTAS_SEQUENCIAL.append(("compartilhamento", CTAS_POR_CATEGORIA["compartilhamento"][i]))
    LISTA_CTAS_SEQUENCIAL.append(("salvamento", CTAS_POR_CATEGORIA["salvamento"][i]))

def proximo_cta(indice_atual=0):
    """Retorna o próximo CTA da sequência intercalada, reiniciando após o último.

    Returns:
        categoria (str): O objetivo do CTA (seguir, comentario, compartilhamento, salvamento)
        referencia (str): Frase base a ser adaptada pela IA.
        novo_indice (int): Próximo índice para salvar no estado.
    """
    indice_atual = indice_atual % len(LISTA_CTAS_SEQUENCIAL)
    categoria, referencia = LISTA_CTAS_SEQUENCIAL[indice_atual]
    novo_indice = (indice_atual + 1) % len(LISTA_CTAS_SEQUENCIAL)
    return categoria, referencia, novo_indice

