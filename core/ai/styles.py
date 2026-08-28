import random

# ==========================================
# ESTILOS DE COPY (abordagem narrativa / tons)
# ==========================================
ESTILOS_COPY = [
    "Fazer uma pergunta: crie curiosidade abrindo uma lacuna na mente do leitor (ex: 'Você acredita que controla sua própria mente?')",
    "Criar um conflito interno: exponha uma contradição de comportamento cotidiana (ex: 'Você quer mudar de vida, mas repete os mesmos hábitos.')",
    "Quebrar uma crença: vá contra o senso comum imediatamente (ex: 'O maior erro é achar que falta tempo.')",
    "Prometer revelar algo: instigue o leitor com um segredo ou mecânica oculta (ex: 'Existe uma mentira silenciosa que está destruindo sua paz.')",
]

# ==========================================
# GANCHOS ORGANIZADOS POR CATEGORIA
# Frases autorais, autocontidas e de alta compartilhabilidade (estilo "indiretas" e "espelhos de vida").
# ==========================================
GANCHOS_POR_CATEGORIA = {

    "curiosidade": [
        "Nunca se esqueça que...",
        "Eu acho que você está esquecendo de uma coisa,",
        "Existe algo que você esconde até de si mesmo.",
        "O que ninguém te conta sobre ficar em silêncio...",
        "Tem algo na sua rotina destruindo sua paz em segredo.",
        "Se você soubesse o que acontece quando aprende a dizer não...",
        "Poucos percebem, mas esta atitude muda tudo.",
        "Existe uma regra não dita sobre a sua mente.",
        "O segredo para se libertar do que te paralisa...",
        "Quando você entender isso, nada mais te abala.",
    ],
    "ironia": [
        "A mente que busca progresso não se prende ao passado.",
        "É irônico como gastamos energia onde nada se constrói.",
        "Reclamar do cansaço enquanto adia a disciplina é uma escolha.",
        "Cobrar respeito do mundo começa no respeito aos seus princípios.",
        "O medo de falhar paralisa apenas quem ignora o próprio valor.",
        "As reações imaturas revelam onde o trabalho interno ainda falta.",
        "Falar de maturidade é fácil; mantê-la sob pressão é o teste.",
        "Buscar validação externa é assinar a dependência da sua paz.",
        "Quem busca clareza não cultiva a bagunça mental.",
        "Defender a desculpa que te atrasa é adiar a própria liberdade.",
    ],
    "sabedoria": [
        "Quem aprendeu na disciplina enxerga a vida com serenidade e clareza.",
        "Não importa o tempo acumulado no erro: reconstrua o seu futuro agora.",
        "Aquilo que foge do seu controle não deve consumir a sua paz.",
        "A dor da disciplina é temporária; o peso da omissão é permanente.",
        "Seu tempo não sumiu — foi diluído nas distrações sem propósito.",
        "O silêncio diante da provocação é a expressão máxima de autocontrole.",
        "Preservar a paz interna é o investimento mais valioso de um homem.",
        "As atitudes constantes revelam quem merece estar na sua jornada.",
        "Um lar estruturado e em paz vale mais do que o aplauso da multidão.",
        "A lealdade silenciosa supera qualquer promessa ruidosa.",
    ],
    "magnetismo": [
        "Preste atenção. O princípio a seguir pode mudar a sua perspectiva.",
        "Existe uma verdade sutil que poucos têm a maturidade de aceitar.",
        "Isso exige discernimento — e quem compreende, transforma sua realidade.",
        "A verdadeira serenidade surge quando você domina a si mesmo.",
        "Não é sobre esforço desordenado. É sobre direção e maestria.",
        "Quando você enxerga este padrão, recusa imediatamente o medíocre.",
        "Verdades fundamentais exigem coragem no início, mas libertam para sempre.",
        "Este entendimento poupará anos de desgastes desnecessários.",
        "Existe um abismo entre quem apenas deseja e quem executa com firmeza.",
        "Se você busca evolução real, esta reflexão é para você.",
    ],
    "intriga": [
        "O maior erro do homem não é errar, é...",
        "Se você se viu cedendo a esse velho padrão...",
        "Existe um veneno sutil roubando sua calma diária.",
        "Aquilo não te destruiu, mas algo em você mudou...",
        "O 'momento perfeito' é apenas sua fuga mais silenciosa.",
        "Seu 'não consigo' na verdade é um convite para...",
        "Quando você parar de culpar os outros, isso acontece...",
        "Sua mente te engana quando te diz que...",
        "A decisão que você mais adia é a que mais te libertaria.",
        "Existe uma armadilha disfarçada de proteção na sua vida.",
    ],
    "pergunta": [
        "Quer um conselho prático que pouca gente te dá?",
        "Você realmente escolhe as batalhas que decide lutar?",
        "E se seu maior obstáculo for a sua própria apressada?",
        "Até quando você vai adiar a vida que merece construir?",
        "Você já se perguntou por que repete o mesmo erro?",
        "O que você faria hoje se não tivesse medo do julgamento?",
        "Sua paz é verdadeira ou você só se acostumou com o incômodo?",
        "Você está construindo seu sonho ou realizando o de outra pessoa?",
        "Vale a pena perder sua saúde mental para provar algo aos outros?",
        "Por que você exige do parceiro a maturidade que você não pratica?",
    ],
    "dilema": [
        "A escolha que separa quem constrói o futuro de quem só assiste a vida passar...",
        "No momento da crise, você busca um culpado ou assume o comando?",
        "O dilema que todo homem enfrenta antes de mudar de patamar...",
        "Você prefere a dor temporária da disciplina ou a dor vitalícia do arrependimento?",
        "Aceitar o conforto medíocre hoje ou pagar o preço da grandeza amanhã?",
        "O divisor de águas entre quem sonha e quem realmente executa...",
        "Sua postura diante da derrota define o tamanho da sua vitória futura.",
        "Você domina suas emoções ou é refém do seu estado de espírito?",
    ],
}

# ─────────────────────────────────────────────────────────────────────
# LISTA SEQUENCIAL MESTRA — todos os ganchos na ordem de cadastro.
# ─────────────────────────────────────────────────────────────────────
LISTA_GANCHOS_SEQUENCIAL = [
    gancho for categoria in GANCHOS_POR_CATEGORIA.values() for gancho in categoria
]


# ==========================================
# GANCHOS CONQUISTADOR — ganchos diretos de altíssimo impacto visual e emocional
# ==========================================
LISTA_GANCHOS_CONQUISTADOR = [
    "Nunca se esqueça de quem esteve lá nos seus piores dias.",
    "O homem que passou pelo inferno não se assusta com fumaça.",
    "Não absorva a pressa do mundo. Viva no seu próprio ritmo.",
    "A paz de espírito é a maior riqueza que você pode construir.",
    "Ficar sozinho quando você precisa de apoio te transforma para sempre.",
    "Sem fazer barulho, sem se gabar: no silêncio, a vida flui melhor.",
    "Não prolongue ciclos falidos por causa de boas memórias passadas.",
    "Sua paciência não é fraqueza — é controle absoluto da sua mente.",
    "Busque sua paz e deixe os outros ficarem com a razão.",
    "A resposta mais elegante para quem te desrespeita é a sua ausência.",
    "Quando você aprende a ficar em paz sozinho, o básico já não te atrai.",
    "Se você não é o 'sim' de alguém, jamais se submeta a ser o 'talvez'.",
    "Você muda o mundo ao seu redor no dia em que muda sua mente.",
    "Não prometa nada na empolgação e não tome decisões na raiva.",
    "A disciplina é a ponte entre quem você é hoje e quem quer se tornar.",
    "Quem tem propósito forte não perde tempo tentando provar nada.",
    "Honre a sua palavra e cuide de quem corre ao seu lado no escuro.",
    "Você não precisa de mais tempo — precisa de mais foco e menos distrações.",
    "Deixe que os resultados falem por você. Trabalhe em silêncio.",
    "O respeito se constrói com atitudes constantes, não com discursos bonitos.",
    "Coragem não é ausência de medo, é agir mesmo com o coração acelerado.",
    "Proteja seu lar, sua família e sua mente de influências tóxicas.",
    "Quem se perdoa pelo passado consegue finalmente construir o futuro.",
    "A verdadeira força é sereno por fora e inabalável por dentro.",
    "Não venda sua liberdade por uma ilusão de conforto temporário.",
    "A maturidade chega quando você para de reagir a tudo que te irrita.",
    "Pare de tentar salvar quem não quer ser salvo. Salve a si mesmo.",
    "A constância diária vence o talento sem disciplina todas as vezes.",
    "Construa uma vida da qual você não precise tirar férias para escapar.",
    "A gratidão em dias difíceis é o maior ato de fé que existe.",
    "Seja leal aos seus princípios, mesmo quando ninguém estiver olhando.",
    "Sua mente é seu maior aliado ou seu pior algoz: você escolhe o que alimenta.",
    "Não perca energia discutindo com quem só quer vencer o argumento.",
    "A verdadeira coragem é ser honesto consigo mesmo sobre suas falhas.",
    "Crie hábitos que sua versão do futuro vai te agradecer por ter mantido.",
    "O medo do julgamento alheio é a gaiola de quem vive para impressionar.",
    "Nada substitui o valor de deitar na cama com a consciência limpa.",
    "Crie o hábito de focar na solução enquanto os fracos reclamam do problema.",
    "A vida não fica mais fácil, é você que se torna mais forte e sábio.",
    "Aprenda a valorizar quem te apoia no anonimato e nos momentos difíceis.",
    "Trate sua atenção como o recurso mais caro da sua vida — porque ele é.",
    "Quem domina a própria raiva domina qualquer situação no caos.",
    "Não confunda paciência com acomodação: saiba a hora exata de agir.",
    "Seja a referência de serenidade e firmeza para as pessoas que você ama.",
    "O segredo da mudança é focar toda a energia na construção do novo.",
    "A verdadeira liberdade é poder dizer 'não' sem sentir culpa.",
    "Sua história só começa a mudar quando você assume 100% da responsabilidade.",
    "Valorize a simplicidade das coisas reais em um mundo cheio de aparências.",
    "Mantenha os pés no chão, a mente afiada e o coração em paz.",
    "O tempo revela quem é de verdade. Confie no processo e siga firme."
]


# ==========================================
# ARQUITETURAS NARRATIVAS (6 formatos rotativos)
# Garante que o fluxo de entrega da mensagem mude a cada postagem,
# quebrando a mesmice do clássico "Problema-Solução".
# ==========================================
ARQUITETURAS_NARRATIVAS = [
    {
        "nome": "Visão de Grandeza",
        "descricao": "Identifique uma ambição ardente do leitor logo após o gancho, eleve o estado de espírito (mostre o topo) e então entregue o princípio prático para chegar lá."
    },
    {
        "nome": "O Ponto de Virada",
        "descricao": "Fale como se estivesse compartilhando o momento exato em que a sua vida mudou ('O dia em que a chave virou para mim...'). Use a primeira pessoa do plural ('nós') para criar aliança de poder com o ouvinte."
    },
    {
        "nome": "Pergunta & Investigação Magnética",
        "descricao": "Faça uma série de perguntas e vá guiando o leitor passo a passo para desmascarar as próprias desculpas, revelando que ele já tem o poder que procura."
    },
    {
        "nome": "Metáfora de Alta Frequência",
        "descricao": "Use uma analogia de poder e magnitude (como a aerodinâmica de um jato, a precisão de um atirador, a gravidade de um planeta) para explicar a mentalidade vencedora de forma puramente visual e eletrizante."
    },
    {
        "nome": "Confronto de Autoridade",
        "descricao": "Abordagem crua, direta e magnética. Quebre a ilusão da mediocridade e chame o leitor para assumir o controle absoluto da própria vida agora mesmo, com energia de líder."
    },
    {
        "nome": "A Cena do Triunfo",
        "descricao": "Crie uma cena curta INÉDITA com um personagem sem nome em um cenário de sucesso (NÃO copie o exemplo antigo das 23h). Narre o momento da vitória silenciosa e deixe que a lição prática surja da atitude dele."
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

🎯 CAPAS E TÍTULOS DE IMPACTO (REGRA DA CAPA LIMPA):
- A frase da capa ou primeiro slide DEVE ter no MÁXIMO 5 PALAVRAS. Proibido colocar parágrafos ou frases longas cobrindo a tela do vídeo. Use um gancho curto, provocador e cortante.

🔥 DORES REAIS E CONCRETAS (CHEGA DE ABSTRAÇÃO):
- Proibido usar frases poéticas abstratas e vazias que não dizem nada ao leitor. Foque em conflitos e dores reais da rotina: dinheiro, procrastinação, falta de foco, ansiedade com o futuro, decisões difíceis, acordar sem propósito.

💬 PALAVRA-CHAVE DE ENGAJAMENTO DINÂMICA:
- Para posts de atração, conversão e entrega de e-books/materiais, utilize a palavra-chave fornecida associada ao tema do PDF. Instrua o leitor a comentar essa palavra-chave (destacada em aspas simples) para receber o material.

❌ PROIBIDO — NUNCA use estas frases de autoajuda vazia:
- "Acredite em você", "Você é capaz", "Nunca desista", "Foco e determinação"
- "Seja a melhor versão de si mesmo", "Saia da zona de conforto"
- "O sucesso é para quem corre atrás", "A vida é uma jornada"
- "Faça acontecer", "Você tem o poder", "Hoje é o dia"
- NUNCA use tom professoral, arrogante ou palavras artificiais de auto-promoção (ex: "Poucos sabem disso..."). Fale de igual para igual.
- Você tem total liberdade para citar livros, filósofos, teorias e autores para dar peso de autoridade à mensagem.

✅ OBRIGATÓRIO — o tom cirúrgico e atraente:
- O primeiro slide deve ser um gancho cliffhanger curto e cortante. Ele DEVE quebrar o padrão e parar o scroll.
- Use linguagem direta, falada e visceral (coloquial do Brasil).
- Use sentenças curtas e parágrafos de uma linha. Textos longos matam a retenção.

🧠 PERCEPÇÃO DE VALOR (DO INÍCIO AO FIM DA MENSAGEM):
Todo conteúdo deve fazer o leitor sentir que acabou de receber um insight difícil de encontrar.
- Evite frases motivacionais genéricas, conselhos óbvios, listas superficiais e clichês.
- Prefira: revelar o mecanismo psicológico por trás do comportamento, explicar o motivo invisível que gera o problema, apresentar uma mudança de perspectiva que aumente a clareza do leitor, entregar um princípio aplicável imediatamente.

🛡️ AUTORIDADE MORAL:
Nunca tente convencer o leitor de que você tem autoridade. Faça com que ele conclua isso sozinho pela qualidade da explicação:
- Explique causas antes de soluções.
- Revele mecanismos antes de recomendações.
- Mostre princípios antes de técnicas.

🎯 O CONCEITO CENTRAL (Filtro de Qualidade):
Toda postagem gerada deve aumentar ativamente uma destas três percepções no leitor:
1. "Nunca tinha pensado por esse ângulo."
2. "Agora entendi por que isso acontece."
3. "Isso vale muito mais do que o tempo que levei para consumir."
Se nenhuma dessas sensações estiver presente do início ao fim, a postagem está superficial e deve ser reescrita.
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
# Referências de tom e intenção — a IA adapta ao contexto de cada post.
# Estruturas variadas: pergunta, observação, desafio, convite, consequência.
# O CTA deve nascer como extensão natural do conteúdo — nunca como comando seco.
# ==========================================
CTAS_POR_CATEGORIA = {
    "seguir": [
        "Se você reconheceu esse padrão em você, cada post aqui vai aprofundar o que você acabou de entender.",
        "O raciocínio continua — e o próximo post vai mais fundo. Quem acompanha desde o início vê os padrões se conectando.",
        "Isso não é conteúdo isolado. É uma construção diária. Cada post aprofunda o anterior.",
        "Aqui a gente vai mais fundo do que o óbvio — todos os dias. Fique por aqui se quer continuar nesse nível.",
        "Você reconheceu esse padrão. O próximo vai te surpreender mais.",
        "Poucos lugares na internet falam sobre isso com essa profundidade. Esse é um deles.",
        "Se isso abriu uma pergunta que você não consegue parar de pensar, ela será respondida nos próximos posts.",
        "O que você viu aqui é apenas a entrada. Acompanhe para não perder o que vem depois.",
        "Mente que para de questionar para de crescer. Esse perfil é pra quem não para.",
        "Cada post aqui é um tijolo numa construção maior. Quem acompanha desde o início enxerga a obra completa.",
        "Se você quer entender o comportamento humano no nível que poucos chegam, está no lugar certo.",
        "Esse tipo de conteúdo não aparece no feed de quem não procura. Fique por aqui — vale.",
        "Esses padrões mudam a forma como você lê as situações. E isso não tem volta."
    ],
    "comentario": [
        "Agora a pergunta real: onde você já viveu exatamente isso?",
        "Qual das duas escolhas você tomaria? Não tem resposta certa — mas a sua diz muita coisa.",
        "Isso te gerou uma certeza ou abriu uma dúvida nova? Conta aqui embaixo.",
        "Pensa numa situação concreta da sua vida onde esse padrão apareceu. Escreve ela aqui.",
        "Se você pudesse resumir isso em uma palavra, qual seria?",
        "É fácil reconhecer esse mecanismo nos outros. Difícil é ser honesto sobre quando você mesmo esteve nele.",
        "Qual parte disso bateu mais forte em você — e por quê?",
        "Às vezes um conteúdo resolve uma questão e abre três novas. Se foi assim, escreve aqui.",
        "Você já tomou uma decisão diferente depois de entender um princípio parecido com esse?",
        "O que você diria para alguém que está no início desse ciclo agora?",
        "Se você tivesse entendido isso 5 anos atrás, o que teria mudado?",
        "Qual é o maior obstáculo que te impede de aplicar isso hoje?",
        "Você concorda que a maioria das pessoas nunca chega nesse nível de consciência sobre isso?"
    ],
    "compartilhamento": [
        "Você já pensou numa pessoa específica enquanto lia isso. Manda pra ela.",
        "Tem alguém na sua vida que está no meio desse ciclo agora — e que precisa ver isso.",
        "A mensagem certa no momento certo muda uma decisão. Envia para quem precisa dessa mudança.",
        "Esse tipo de conversa precisa acontecer mais. Compartilha com alguém com quem você quer ter ela.",
        "Conhecimento parado em você não multiplica. Espalha.",
        "Quem você conhece que responderia diferente a essa pergunta? Manda pra ela e descobre.",
        "Às vezes a pessoa que está do seu lado não sabe que está nesse padrão. Compartilha silenciosamente.",
        "Se isso foi útil pra você, provavelmente vai ser útil pra alguém do seu círculo também.",
        "Pensa no seu grupo de pessoas mais próximas — quantas precisavam ouvir exatamente isso hoje?",
        "Tem conteúdo que é bom guardar pra si. Esse não é um deles — é melhor dividir.",
        "A diferença entre quem cresce e quem estagna muitas vezes é o conteúdo que eles consomem. Compartilha.",
        "Se você faz parte de um grupo, leva esse raciocínio pra ele. Vale uma conversa.",
        "Você vai querer que a pessoa certa veja isso. Manda agora enquanto ainda está fresco."
    ],
    "salvamento": [
        "Guarda isso. Você vai lembrar desse post num momento específico da sua vida.",
        "Tem conteúdo que faz sentido na primeira leitura. Esse vai fazer mais sentido na segunda — quando você estiver no meio de uma decisão.",
        "Essa ideia cresce com o tempo. Salva e volta aqui em 30 dias.",
        "Você não vai querer buscar isso de novo quando precisar. Salva agora.",
        "Na primeira vez você entende. Na segunda você aplica. Na terceira, você ensina alguém.",
        "Esse princípio não é pra usar só hoje. Guarda para quando o momento chegar.",
        "Salva antes de esquecer. O feed engole tudo — menos o que você decidiu manter.",
        "Esse checklist mental vai ser útil na próxima vez que você enfrentar essa situação.",
        "Quando a mente estiver agitada, você vai querer ter isso à mão. Salva.",
        "Informação que não é revisitada vira ruído. Salva e revisa quando precisar.",
        "Essa é uma daquelas reflexões que amadurecem. Salva para ler de novo depois.",
        "O que parece óbvio hoje pode ser exatamente o que você precisa ouvir amanhã. Guarda.",
        "Salva e compartilha depois — quando você tiver vivido isso e quiser mostrar que entendeu."
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
# e subpasta de áudio para criar sinestesia pura de alta classe.
# =====================================================================
SENTIMENTOS_CONFIG = {
    # ── Família 1: Desejo & Aspiração (Inspirador, nobre, alta classe)
    "poder": {
        "tom": "Transmita autoridade incansável, magnetismo e domínio. Use frases firmes. Fale de auto-maestria e de viver no topo.",
        "busca_imagem": ["exclusive luxury gala evening event elegant man in suit 4k", "determined male leader walking night city lights power cinematic", "luxury sports car driving night city golden lighting", "confident leader standing modern skyscraper penthouse balcony city night view"],
        "pasta_audio": "desejo_poder"
    },
    "luxuria": {
        "tom": "Desperte o desejo pelo extraordinário, pelo acesso restrito e pela vida que a maioria apenas sonha em ter.",
        "busca_imagem": ["luxury lifestyle elegant person night city lights golden bokeh", "high end luxury gala event chic woman in dress 35mm", "exclusive penthouse balcony city night view 4k", "exclusive VIP luxury event warm lighting cinematic"],
        "pasta_audio": "desejo_poder"
    },
    "sensualidade": {
        "tom": "Trabalhe com o magnetismo do mistério, da autoconfiança inabalável e da atração fatal que a clareza gera.",
        "busca_imagem": ["charismatic leader speaking on stage golden lights 35mm", "confident elegant person smiling bright city lights night", "magnetic portrait warm evening lighting cinematic", "stylish couple walking city night golden lighting architecture"],
        "pasta_audio": "desejo_poder"
    },
    "prazer": {
        "tom": "Conecte com a satisfação genuína da vitória, o êxtase de viver nos seus próprios termos. Celebração nobre.",
        "busca_imagem": ["stylish couple celebrating victory luxury penthouse night 35mm", "person celebrating victory looking at epic sunrise mountain", "exclusive group of friends laughing luxury rooftop night", "triumph celebration golden lights cinematic"],
        "pasta_audio": "desejo_poder"
    },
    "plenitude": {
        "tom": "Foque na sensação de governo absoluto sobre a própria vida. O alívio poderoso de saber exatamente quem você é.",
        "busca_imagem": ["majestic sunrise over ocean person looking far 35mm", "peaceful but powerful stance grand canyon morning light", "serene leader looking over bright city skyline", "calm confidence person bright morning sunlight cinematic"],
        "pasta_audio": "conexao_lealdade"
    },

    # ── Família 2: Tensão & Ação (Foco, despertar, virada de jogo)
    "escassez": {
        "tom": "Gere senso de urgência para a grandeza. O tempo não está acabando para sofrer, está passando enquanto o topo te espera.",
        "busca_imagem": ["luxury car driving night city golden lights cinematic", "stylish person walking fast city lights evening 35mm", "dynamic movement illuminated modern city architecture", "urgent action fast pace city life golden blur"],
        "pasta_audio": "tensao_acao"
    },
    "raiva": {
        "tom": "Manifeste uma indignação eletrizante contra a mediocridade. Uma energia de revolta que impulsiona para a ação extrema.",
        "busca_imagem": ["determined leader walking fast night city lights 35mm", "focused person looking at city skyline intense lighting", "powerful dynamic stance modern architecture bright lights cinematic", "fierce determined look person walking evening city"],
        "pasta_audio": "tensao_acao"
    },
    "ousadia": {
        "tom": "Toque no perigo de viver uma vida morna e esquecível. Provoque a coragem e a fome de arriscar alto.",
        "busca_imagem": ["person standing edge of cliff looking at sunrise cinematic", "confident leader standing modern skyscraper penthouse balcony 35mm", "daring person walking golden hour city skyline", "fearless leader looking at city night lights"],
        "pasta_audio": "tensao_acao"
    },
    "desafio": {
        "tom": "Faça perguntas provocadoras de alto nível. Desafie o leitor a subir o próprio sarrafo e parar de aceitar o básico.",
        "busca_imagem": ["elegant man in suit staring direct camera cinematic lighting 35mm", "confident smile looking directly at camera golden light", "challenging confident posture city skyline background", "leader standing tall modern architecture cinematic"],
        "pasta_audio": "tensao_acao"
    },
    "curiosidade": {
        "tom": "Abra loops mentais com o 'segredo dos que chegam lá'. O magnetismo do que a elite sabe e a massa ignora.",
        "busca_imagem": ["exclusive luxury event doorway glowing golden light 35mm", "mystery silhouette walking night city golden lights", "illuminated book glowing magical light knowledge", "discover hidden luxury architecture glowing golden light cinematic"],
        "pasta_audio": "tensao_acao"
    },

    # ── Família 3: Conexão & Lealdade (Elegância, valores e autoridade)
    "amor": {
        "tom": "Aborde a força imbatível de quem constrói algo para quem ama. A paixão que levanta impérios.",
        "busca_imagem": ["stylish couple walking city night golden lighting 35mm", "joyful family walking golden hour beach cinematic", "warm powerful embrace golden hour sunlight", "loyal team celebrating luxury penthouse lights"],
        "pasta_audio": "conexao_lealdade"
    },
    "carinho": {
        "tom": "Fale com o magnetismo de um líder que cuida da sua tribo. Uma voz forte, mas que eleva quem está perto.",
        "busca_imagem": ["leader shaking hands elegant event 35mm", "mentor talking with student bright stage", "warm genuine smile connection bright sunlight", "loyal team walking together city night cinematic"],
        "pasta_audio": "conexao_lealdade"
    },
    "afeto": {
        "tom": "Celebre a irmandade de quem corre pelo mesmo objetivo. A energia de um time imbatível.",
        "busca_imagem": ["elegant team huddle modern architecture 35mm", "friends laughing sunset rooftop luxury event", "people celebrating around golden hour sunset", "loyal crew walking together confident slow motion"],
        "pasta_audio": "conexao_lealdade"
    },
    "alegria": {
        "tom": "Celebre vitórias de forma nobre e eufórica. A felicidade extrema de viver no pico de performance.",
        "busca_imagem": ["exclusive luxury party celebrating golden lights 35mm", "champagne pop celebration luxury yacht sunny day", "radiant laughter group of winners penthouse lights", "pure joy celebrating elegant event cinematic"],
        "pasta_audio": "conexao_lealdade"
    },
    "esperanca": {
        "tom": "Mostre que a glória é inevitável para quem não para. Uma visão épica e grandiosa do futuro.",
        "busca_imagem": ["epic sunrise over futuristic city bright golden light 35mm", "person looking at mountain peak sun shining", "triumphant leader on stage golden lights", "soaring eagle flying into bright sun cinematic"],
        "pasta_audio": "conexao_lealdade"
    }
}


