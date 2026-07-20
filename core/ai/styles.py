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
# GANCHOS CONQUISTADOR — ciclo sequencial próprio (50 ganchos de alto impacto)
# ==========================================
LISTA_GANCHOS_CONQUISTADOR = [
    "A sabedoria silenciosa que protege as nossas maiores decisões.",
    "E se a verdadeira liberdade for exatamente o oposto do que a maioria busca?",
    "A força extraordinária de quem escolhe a paz ao barulho do mundo.",
    "O valor inestimável de uma amizade sincera em tempos de conexões rasas.",
    "Como encontrar clareza mental quando tudo ao redor tenta nos distrair.",
    "A beleza invisível das escolhas feitas longe dos holofotes e da aprovação.",
    "O verdadeiro caráter de um homem se revela no que ele cultiva no silêncio.",
    "A estabilidade real não está no que acumulamos, mas na nossa postura.",
    "Uma mente em paz vale muito mais do que o sucesso obtido no caos.",
    "A sabedoria milenar de semear em silêncio e deixar o tempo agir.",
    "Quem governa o seu pensamento quando a tempestade mental se aproxima?",
    "A verdadeira riqueza é ter a liberdade de escolher onde colocar sua energia.",
    "O valor do caráter reside nos princípios que você se recusa a negociar.",
    "A construção de um legado sólido começa nas escolhas mais simples do dia.",
    "A paz de espírito é o maior escudo contra as ilusões do mundo moderno.",
    "A lealdade não é uma moeda de troca, é o reflexo de quem somos.",
    "Como blindar a sua mente contra a pressa e a ansiedade da massa.",
    "A verdadeira força não precisa fazer barulho para ser notada.",
    "O princípio atemporal que nos ensina a valorizar as pequenas sementes.",
    "De que serve vencer lá fora se o seu lar vive em conflito?",
    "O silêncio maduro é, muitas vezes, a resposta mais sábia de todas.",
    "A liberdade começa quando deixamos de ser escravos da aprovação alheia.",
    "A importância de termos limites claros para proteger a nossa paz vital.",
    "Como cultivar a consistência diária nos dias mais difíceis e comuns.",
    "O valor de manter a palavra dada, mesmo quando seria mais fácil recuar.",
    "A sabedoria de focar apenas naquilo que está sob o nosso controle direto.",
    "Uma conversa sincera tem o poder de curar o que o orgulho tenta esconder.",
    "A verdadeira jornada de crescimento pessoal não tem platéia nem aplausos.",
    "Como blindar o nosso foco contra o excesso de informação inútil.",
    "O alívio genuíno de viver uma vida baseada na verdade e na simplicidade.",
    "A sabedoria milenar que mostra: a paciência é a maior aliada da clareza.",
    "Quem caminha ao seu lado quando a tempestade da vida se aproxima?",
    "A diferença sutil entre ter metas claras e viver prisioneiro da ansiedade.",
    "A beleza das alianças verdadeiras que suportam o teste do tempo.",
    "Como a auto-maestria nos liberta dos impulsos momentâneos e impulsivos.",
    "O valor de cultivar a gratidão pelo que já foi construído até aqui.",
    "A sabedoria de olhar para dentro antes de tentar responder ao mundo.",
    "A verdadeira liberdade é poder deitar a cabeça no travesseiro com a consciência limpa.",
    "A força silenciosa de proteger o seu círculo mais íntimo de pessoas.",
    "Como a maturidade nos ensina a valorizar o essencial e descartar o supérfluo.",
    "O poder de uma mente serena que não reage a toda provocação do ambiente.",
    "A sabedoria de aceitar as mudanças com calma e recomeçar com firmeza.",
    "O caráter sólido se constrói na constância das escolhas invisíveis.",
    "A beleza de viver uma vida com propósito, sem pressa e sem comparações.",
    "A importância de honrar a história e os valores de quem veio antes.",
    "Como a paz interna se reflete na qualidade de todas as nossas decisões.",
    "O verdadeiro valor de estar presente para quem realmente importa para você.",
    "A sabedoria de aprender com os erros sem carregar o peso da culpa.",
    "A força de quem se mantém fiel aos seus princípios em qualquer cenário.",
    "O maior ato de integridade é ser a mesma pessoa no palco e nos bastidores."
]


# ==========================================
# ARQUITETURAS NARRATIVAS (6 formatos rotativos)
# Garante que o fluxo de entrega da mensagem mude a cada postagem,
# quebrando a mesmice do clássico "Problema-Solução".
# ==========================================
ARQUITETURAS_NARRATIVAS = [
    {
        "nome": "Problema-Solução Clássico",
        "descricao": "Identifique a dor cotidiana do leitor logo após o gancho, aprofunde o incômodo (bata na ferida) e então entregue o insight/passo prático como recompensa."
    },
    {
        "nome": "Confissão Pessoal / Storytelling",
        "descricao": "Fale como se estivesse compartilhando um erro ou aprendizado pessoal do próprio palestrante ('Eu já estive exatamente onde você está agora...'). Use a primeira pessoa do plural ('nós') para criar aliança com o ouvinte."
    },
    {
        "nome": "Pergunta & Investigação Cirúrgica",
        "descricao": "Faça uma série de perguntas e vá guiando o leitor passo a passo para desmascarar as próprias desculpas ou mentiras mentais, revelando a raiz real do problema."
    },
    {
        "nome": "Metáfora / Analogia do Cotidiano",
        "descricao": "Use uma analogia física rica (como o funcionamento de uma represa, uma xícara transbordando, uma árvore sem raízes) para explicar um padrão de comportamento de forma extremamente visual."
    },
    {
        "nome": "Confronto e Alerta de Tempo",
        "descricao": "Abordagem crua e direta. Alerte o leitor de que o tempo está passando, destrua a falsa ilusão de conforto e chame-o para agir imediatamente com firmeza e autoridade."
    },
    {
        "nome": "Micro-Fábula de Personagem",
        "descricao": "Apresente uma cena curta com um personagem sem nome ('Às 23h, ele olhou para as telas...'). Narre a dor dele e deixe que a lição prática surja do desfecho natural da cena."
    }
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


def proxima_arquitetura(indice_atual=0):
    """Retorna a próxima arquitetura narrativa da sequência linear, reiniciando após a última."""
    indice_atual = indice_atual % len(ARQUITETURAS_NARRATIVAS)
    arquitetura = ARQUITETURAS_NARRATIVAS[indice_atual]
    novo_indice = (indice_atual + 1) % len(ARQUITETURAS_NARRATIVAS)
    return arquitetura, novo_indice


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
# CTAs ORGANIZADOS POR CATEGORIA (52 itens)
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
        "Talvez essa seja apenas uma das perguntas que você precisava fazer.",
        "Quem entende o valor do silêncio encontra espaço aqui. Siga.",
        "Acompanhe nossa jornada se você busca profundidade diária.",
        "Se você quer blindar sua mente contra o ruído moderno, siga o perfil.",
        "A evolução pessoal exige constância. Una-se à nossa jornada diária.",
        "Siga se você prefere a verdade que incomoda à mentira que conforta."
    ],
    "comentario": [
        "Quero saber sua resposta.",
        "O que você faria?",
        "Concorda ou discorda?",
        "Qual foi sua primeira reação?",
        "Resuma sua opinião em uma palavra.",
        "Você já viveu isso?",
        "O que você pensa sobre isso?",
        "Existe outra forma de enxergar isso?",
        "Qual dessas verdades bateu mais forte em você?",
        "Você já esteve do outro lado dessa situação?",
        "Comente qual o seu maior obstáculo ao aplicar isso hoje.",
        "Deixe sua percepção sincera aqui embaixo.",
        "Se você pudesse mudar apenas uma atitude hoje, qual seria?"
    ],
    "compartilhamento": [
        "Envie para alguém que precisa ouvir isso.",
        "Compartilhe com quem pensa diferente.",
        "Mostre isso para um amigo.",
        "Essa conversa merece continuar.",
        "Quem você conhece que responderia diferente?",
        "Compartilhe e compare as respostas.",
        "Quero saber o que outra pessoa responderia.",
        "Vale a pena ouvir uma segunda opinião.",
        "Envie isso para a pessoa que compartilha dos seus princípios.",
        "Espalhe essa reflexão com quem valoriza a sabedoria prática.",
        "Compartilhe silenciosamente com quem precisa acordar hoje.",
        "Leve essa mensagem para quem faz parte do seu círculo de ferro.",
        "Envie para alguém com quem você quer crescer junto."
    ],
    "salvamento": [
        "Salve para refletir depois.",
        "Guarde isso.",
        "Você pode querer lembrar disso amanhã.",
        "Vale a pena voltar aqui.",
        "Salve antes de esquecer.",
        "Essa reflexão merece ser revisitada.",
        "Nem toda resposta aparece na primeira leitura.",
        "Guarde essa ideia.",
        "Salve este post para ler quando a mente estiver agitada.",
        "Guarde este checklist mental para a sua próxima decisão difícil.",
        "Salve para reler nos dias em que o foco parecer distante.",
        "Guarde essa chave de sabedoria na sua coleção.",
        "Salve para garantir que esse princípio se torne um hábito."
    ]
}

# ─────────────────────────────────────────────────────────────────────
# LISTA INTERCALADA DE CTAs — Garante que o objetivo de engajamento
# (seguir, comentar, compartilhar, salvar) mude a cada postagem de forma
# alternada e balanceada, passando por cada uma das 52 referências.
# ─────────────────────────────────────────────────────────────────────
LISTA_CTAS_SEQUENCIAL = []
for i in range(13):
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


# =====================================================================
# CAIXA DE SENTIMENTOS (15 emoções)
# Mapeia cada sentimento para diretrizes de copy, termos de busca de imagem,
# e subpasta de áudio para criar sinestesia pura.
# =====================================================================
SENTIMENTOS_CONFIG = {
    # ── Família 1: Desejo & Aspiração (Ideal para inspirar e gerar conexão de alta qualidade)
    "poder": {
        "tom": "Transmita autoridade incansável e domínio das emoções. Use frases firmes e seguras. Fale de auto-maestria.",
        "busca_imagem": ["mountain climber peak sunrise", "ancient stone castle storm", "eagle flying high mountain", "epic sunset silhouette cliff"],
        "pasta_audio": "desejo_poder"
    },
    "luxuria": {
        "tom": "Desperte o desejo pelo extraordinário e pelo conhecimento restrito aos 1%. Fale sobre segredos ocultos e exclusividade.",
        "busca_imagem": ["luxury dark study warm light", "city lights night top view skyscrapers", "glowing gold key velvet", "rich texture shadows gold"],
        "pasta_audio": "desejo_poder"
    },
    "sensualidade": {
        "tom": "Trabalhe com o magnetismo do mistério e o poder do silêncio atraente. Fale com classe, sem vulgaridade.",
        "busca_imagem": ["warm sunset silhouette shadow", "candle light bedroom dark room", "coffee cup steam soft morning light", "aesthetic smoke mystery"],
        "pasta_audio": "desejo_poder"
    },
    "prazer": {
        "tom": "Conecte com a satisfação genuína de colher frutos do esforço e viver sob seus próprios termos. Sensação de conquista.",
        "busca_imagem": ["person walking beach sunset ocean", "relaxing cozy fire cabin rain", "peaceful walk forest sunlight", "person smiling sun rays face"],
        "pasta_audio": "desejo_poder"
    },
    "plenitude": {
        "tom": "Foque no alívio de se sentir completo e em paz consigo mesmo. Acabe com a sensação de estar correndo em vão.",
        "busca_imagem": ["calm ocean surface horizon morning", "zen garden bonsai peaceful", "vast empty desert warm sky", "sunbeams through clouds sky"],
        "pasta_audio": "conexao_lealdade"
    },

    # ── Família 2: Tensão & Ação (Excelente para engajamento frio, ganchos rápidos de 2s e comentários)
    "escassez": {
        "tom": "Gere senso de urgência e perda de tempo. Chame a atenção para a velocidade com que os anos passam enquanto o leitor hesita.",
        "busca_imagem": ["hourglass flowing sand macro", "vintage pocket watch shadow", "ticking clock wall shadows", "dark autumn leaves falling"],
        "pasta_audio": "tensao_acao"
    },
    "raiva": {
        "tom": "Manifeste indignação fria contra a mediocridade, a distração fácil e a hipocrisia social do mundo atual.",
        "busca_imagem": ["stormy dark sea big waves", "heavy storm lightning clouds", "fire sparks black background", "person screaming silhouette shadow"],
        "pasta_audio": "tensao_acao"
    },
    "medo": {
        "tom": "Toque na dor inconsciente e no perigo de continuar na mesma situação de estagnação por covardia de mudar.",
        "busca_imagem": ["foggy dark forest path mystery", "shadowy corridor lone light", "rainy window night city light blurred", "empty bench mist park"],
        "pasta_audio": "tensao_acao"
    },
    "duvida": {
        "tom": "Faça perguntas perturbadoras. Desafie as verdades que o leitor julga inabaláveis. Crie incerteza intelectual.",
        "busca_imagem": ["misty mountain lake reflection", "foggy street lamp night silhouette", "dusty library bookshelves darkness", "open door light dark room"],
        "pasta_audio": "tensao_acao"
    },
    "curiosidade": {
        "tom": "Abra loops mentais com promessas de revelação sobre o comportamento humano. O leitor precisa virar a tela.",
        "busca_imagem": ["ancient leather book dust", "magnifying glass text map", "brass compass glowing light", "microscope laboratory slide science"],
        "pasta_audio": "tensao_acao"
    },

    # ── Família 3: Conexão & Lealdade (Ideal para Stories e aquecimento de base de seguidores)
    "amor": {
        "tom": "Aborde com altruísmo puro, empatia real e proteção aos valores familiares. O valor do sacrifício por quem se ama.",
        "busca_imagem": ["warm hands holding together family", "heart shape light shadow", "parents child walking park sunset", "single red rose winter snow"],
        "pasta_audio": "conexao_lealdade"
    },
    "carinho": {
        "tom": "Fale com tom de proximidade e cuidado de um verdadeiro mentor. Acolha e ofereça suporte prático com calma.",
        "busca_imagem": ["sleeping puppy kitten warm blanket", "steaming tea mug cozy room", "gentle rain window plants inside", "soft fireplace light wood cabin"],
        "pasta_audio": "conexao_lealdade"
    },
    "afeto": {
        "tom": "Mostre a importância das alianças verdadeiras e amizades de aço. Construa pontes emocionais seguras.",
        "busca_imagem": ["two friends laughing talking street", "warm hug silhouette sunset", "people sitting around campfire", "handshake business partners warm"],
        "pasta_audio": "conexao_lealdade"
    },
    "alegria": {
        "tom": "Celebre vitórias reais, a beleza da natureza e a felicidade sincera de viver com propósito.",
        "busca_imagem": ["sunflower field golden hour", "glorious waterfall sun rays", "person jumping freedom mountain peak", "bright green forest summer morning"],
        "pasta_audio": "conexao_lealdade"
    },
    "esperanca": {
        "tom": "Mostre que mesmo na noite mais escura, a alvorada virá. Dê perspectivas positivas de crescimento real.",
        "busca_imagem": ["sun rays breaking through storm clouds", "green plant growing crack concrete", "light at the end of tunnel", "starry sky clear night desert"],
        "pasta_audio": "conexao_lealdade"
    }
}


