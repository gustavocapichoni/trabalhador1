import random
from core.ai.styles import REGRAS_COPY_BASE, sortear_gancho

# ==========================================
# TEMAS E SUB-ÂNGULOS APROFUNDADOS
# ==========================================
TEMAS_MAPEADOS = {
    "espiritualidade": {
        "nome": "Espiritualidade e Fé",
        "inspira": "Evangelhos de Mateus e João, Provérbios de Salomão, Cantares, O Homem Mais Inteligente da História (gestão de emoções de Jesus)",
        "query_unsplash": "ancient stone temple interior, glowing warm candlelight, soft volumetric light, ultra realistic, cinematic",
        "hashtags": ["#sabedoria", "#fe", "#proposito", "#espiritualidade", "#reflexao"],
        "sub_angulos": [
            "Fazer a sua parte no dia a dia é muito mais poderoso do que ficar apenas esperando milagres caírem do céu.",
            "O silêncio e a paciência como as armas mais fortes para blindar a sua paz mental contra o caos.",
            "Como o peso do ódio guardado destrói a sua energia, enquanto o ato de relevar e aceitar te liberta.",
            "Reconhecer seus erros silenciosamente te faz mais forte do que tentar provar que está certo o tempo todo.",
            "A diferença brutal entre uma fé de fachada para a internet e aquela que te levanta nos dias em que você está exausto."
        ]
    },
    "filosofia": {
        "nome": "Filosofia e Autoconhecimento",
        "inspira": "A Arte da Guerra (estratégia mental), O Vendedor de Sonhos (desconstrução do sistema), Estoicismo, PNL",
        "query_unsplash": "massive ancient library with golden light, tall bookshelves, warm sunlight through window, editorial photography, ultra realistic",
        "hashtags": ["#autoconhecimento", "#filosofia", "#sabedoria", "#estoicismo", "#reflexao"],
        "sub_angulos": [
            "O desgaste exaustivo de tentar agradar a todos enquanto você lentamente se perde de si mesmo.",
            "Quando você percebe que parar de se importar com o tribunal do julgamento alheio é a maior liberdade possível.",
            "Entender que tentar controlar tudo ao seu redor é a maneira mais rápida de enlouquecer de ansiedade.",
            "A guerra silenciosa e constante na sua cabeça te consome muito mais do que os problemas reais lá fora.",
            "O preço emocional altíssimo de tentar se encaixar num sistema que não tem absolutamente nada a ver com você."
        ]
    },
    "psicologia": {
        "nome": "Psicologia e Comportamento Humano",
        "inspira": "Rápido e Devagar (Sistema 1 e 2), Blink, Armadilhas da Mente, Neurociência aplicada",
        "query_unsplash": "bright clean modern workspace, warm daylight through large window, minimal desk with notebook, ultra realistic, editorial photography",
        "hashtags": ["#psicologia", "#decisao", "#mentalidade", "#comportamento", "#habito"],
        "sub_angulos": [
            "Por que o seu cérebro te sabota preferindo o sofrimento que você já conhece à dor de mudar de vida.",
            "O vício invisível em estímulos rápidos que te faz perder horas preciosas do seu dia rolando o feed.",
            "Sentir que não tem tempo, mas na verdade ter muito medo de dar o primeiro passo em direção ao que importa.",
            "A armadilha de planejar as coisas perfeitamente só para esconder o medo paralisante de falhar na prática.",
            "O peso de se sentir uma fraude, sabendo no fundo que você entrega só uma pequena fração do seu real potencial."
        ]
    },
    "financas": {
        "nome": "Mentalidade Financeira e Riqueza",
        "inspira": "Pai Rico Pai Pobre (ativos vs passivos), Mais Esperto que o Diabo (alienação), PNL focada em negócios",
        "query_unsplash": "luxurious executive office, floor to ceiling glass windows, warm sunlight, city view, modern architecture, ultra realistic, cinematic",
        "hashtags": ["#financas", "#riqueza", "#mentalidadefinanceira", "#sucesso", "#dinheiro"],
        "sub_angulos": [
            "A diferença brutal entre quem gasta para parecer rico na internet e quem foca em construir paz de espírito.",
            "Trabalhar o mês inteiro exausto para tentar impressionar pessoas que você, no fundo, nem gosta.",
            "O custo invisível e silencioso de nunca arriscar montar o seu negócio pelo medo paralisante de perder a 'segurança'.",
            "Por que a mentalidade de que ganhar mais dinheiro resolve tudo não te salva se faltar inteligência emocional para poupar.",
            "A prisão emocional de dever dinheiro e como isso contamina e destrói todas as outras áreas da sua vida."
        ]
    },
    "liberdade": {
        "nome": "Liberdade, Sonhos e Coragem de Começar",
        "inspira": "O Vendedor de Sonhos (liberdade mental), O Poder da Ação, Mais Esperto que o Diabo (quebrar a hipnose)",
        "query_unsplash": "beautiful sunset over vast ocean, warm orange and purple sky, sun rays reflecting on water, wide angle, ultra realistic, cinematic",
        "hashtags": ["#liberdade", "#sonhos", "#jornada", "#perseveranca", "#foco"],
        "sub_angulos": [
            "A dor profunda de perceber que você está adiando seus próprios sonhos para construir a meta de outra pessoa.",
            "O sacrifício solitário que ninguém curte na internet, mas que é o único caminho verdadeiro para a liberdade.",
            "A ilusão de esperar o 'momento perfeito' que, na verdade, é só a desculpa mais confortável que você arrumou para não agir.",
            "Quando a gaiola dourada do seu emprego confortável já não compensa a sua ansiedade diária e o cansaço.",
            "Como identificar se o seu cansaço é real ou é só o seu corpo pedindo para você desistir antes de tentar pra valer."
        ]
    },
    "conexoes": {
        "nome": "Relacionamentos e Inteligência Emocional",
        "inspira": "Como Fazer Amigos e Influenciar Pessoas, A Arte da Persuasão, construção de família e relacionamentos fortes",
        "query_unsplash": "cozy warm room interior, soft daylight from window, wooden table with coffee cup, plants nearby, peaceful atmosphere, ultra realistic",
        "hashtags": ["#relacionamentos", "#conexao", "#empatia", "#inteligenciaemocional", "#amor"],
        "sub_angulos": [
            "A beleza silenciosa e o trabalho invisível de se perdoar todos os dias para fazer um relacionamento dar certo.",
            "Nem todo afastamento é perda. Alguns te afastam silenciosamente porque a sua evolução e luz incomodam.",
            "O sacrifício diário que quase ninguém vê, mas que é o pilar que sustenta e protege a paz de uma família.",
            "Quando você descobre da pior forma que tolerar o desrespeito constante não é paciência, é medo de ficar sozinho.",
            "A importância de aprender a dizer um 'não' firme para os outros e finalmente dizer 'sim' para a sua saúde mental."
        ]
    },
    "superacao": {
        "nome": "Superação e Autossabotagem",
        "inspira": "O Poder do Hábito (loop do hábito), O Poder da Ação, A Arte da Guerra (disciplina inclemente)",
        "query_unsplash": "mountain climber reaching peak at sunrise, glowing horizon, vibrant sky, cinematic lighting, wide shot, ultra realistic",
        "hashtags": ["#superacao", "#foco", "#resiliencia", "#coragem", "#determinacao"],
        "sub_angulos": [
            "O seu maior inimigo é a voz na sua cabeça que manda você dormir mais cinco minutinhos quando ninguém está olhando.",
            "Entender que o conforto fácil é uma anestesia que mata o seu verdadeiro potencial, pouquinho a pouquinho, todos os dias.",
            "O ciclo repetitivo e exaustivo de se estressar, fugir para um hábito ruim e depois se encher de culpa antes de dormir.",
            "Por que esperar estar 'motivado' é a maior armadilha que existe, e a disciplina silenciosa é o que realmente te salva.",
            "A necessidade de escolher muito bem as suas batalhas, em vez de apanhar de todos os lados achando que isso é ser forte."
        ]
    },
    "proposito": {
        "nome": "Propósito e Legado",
        "inspira": "Eclesiastes, Provérbios de Salomão, Mais Esperto que o Diabo (propósito vs alienação), PNL (visão)",
        "query_unsplash": "colorful flower path leading to bright glowing horizon under blue sky, golden hour sunlight, wide angle, ultra realistic, cinematic",
        "hashtags": ["#proposito", "#legado", "#vida", "#intencao", "#evoluir"],
        "sub_angulos": [
            "A diferença imensa entre querer palmas na internet para inflar o ego e construir algo sólido que proteja sua família.",
            "O sentimento ensurdecedor de vazio que chega quando você conquista tudo materialmente, mas não sabe por que está vivo.",
            "O custo emocional de adiar a sua verdadeira missão de vida ano após ano, esperando as 'condições perfeitas'.",
            "O legado invisível e poderoso das suas pequenas decisões diárias que moldam o futuro de todos ao seu redor.",
            "A coragem gigantesca de deixar para trás o que você era para, finalmente, se tornar aquilo que você precisa ser."
        ]
    }
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
    
    ESTRATÉGIA DE CONTEÚDO BASEADA EM LIVROS:
    Você tem acesso ao conhecimento dos seguintes livros para este tema: {detalhes_tema['inspira']}
    Sua missão é:
    1. Buscar um princípio, método prático ou lição valiosa presente em algum destes livros.
    2. Usar esse método exato para formular uma mensagem, roteiro ou história altamente persuasiva para resolver a dor do usuário.
    3. ENTREGUE COMO SE O CONHECIMENTO FOSSE SEU. É ESTRITAMENTE PROIBIDO citar o nome do livro, do autor ou dar créditos. Pegue a genialidade da obra e passe como conteúdo original do nosso perfil.
    
    Ângulo específico para esta postagem: {sub_angulo}
    
    Gancho narrativo: {gancho}
    
    {contexto_analytics}
    """
    return instrucoes, sub_angulo, gancho
