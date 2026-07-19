import random
from core.ai.styles import REGRAS_COPY_BASE, proximo_gancho, proximo_gancho_conquistador, GANCHOS_POR_CATEGORIA, proximo_cta

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
            "A diferença brutal entre uma fé de fachada para a internet e aquela que te levanta nos dias em que você está exausto.",
            "De que adianta tentar impressionar os outros se o seu lar vive em guerra silenciosa.",
            "A paciência na hora da ofensa diz mais sobre a sua força do que qualquer grito de raiva.",
            "Orar sem trabalhar é só uma desculpa espiritualizada para justificar a preguiça.",
            "A verdadeira paz não depende do mar calmo, mas de quem governa o seu barco por dentro.",
            "Julgar o erro alheio é o passatempo favorito de quem tem pavor de olhar no espelho.",
            "A sabedoria milenar mostra: colhemos exatamente o que plantamos, sem atalhos ou exceções.",
            "O silêncio diante do julgamento injusto é a maior demonstração de poder que existe.",
            "Sua fé madura é provada quando a sensação de abandono parece insuportável.",
            "Pedir direção a Deus e continuar de braços cruzados é zombar do próprio propósito.",
            "O orgulho te faz defender o seu erro; a humildade é o único caminho para a evolução real.",
            "Sua paz interna é cara demais para você entregar nas mãos de quem te critica.",
            "A ansiedade pelo amanhã revela apenas o quanto você acha que controla a vida sozinho.",
            "Perdoar não é dar razão a quem te feriu, é tirar o controle da sua mente da mão dele.",
            "Falar sobre amor na internet é fácil; difícil é tolerar quem testa sua paciência no cotidiano.",
            "A gratidão silenciosa muda mais a química do seu cérebro do que qualquer reclamação em voz alta.",
            "A sabedoria bíblica ensina: quem muito fala, muito erra. O silêncio poupa a alma.",
            "Você não precisa de um grande sinal divino, precisa de coragem para obedecer ao que já sabe.",
            "O peso da culpa passada consome o hoje. A aceitação e o recomeço são atos de fé.",
            "A hipocrisia de fingir santidade consome mais energia do que a coragem de assumir suas falhas.",
            "Sua fé real é o que você faz no escuro, quando absolutamente ninguém está te vigiando."
        ]
    },
    "filosofia": {
        "nome": "Filosofia e Autoconhecimento",
        "inspira": "A Arte da Guerra (estratégia mental), O Vendedor de Sonhos (desconstrução do sistema), PNL",
        "query_unsplash": "massive ancient library with golden light, tall bookshelves, warm sunlight through window, editorial photography, ultra realistic",
        "hashtags": ["#autoconhecimento", "#filosofia", "#sabedoria", "#reflexao"],
        "sub_angulos": [
            "O desgaste exaustivo de tentar agradar a todos enquanto você lentamente se perde de si mesmo.",
            "Quando você percebe que parar de se importar com o tribunal do julgamento alheio é a maior liberdade possível.",
            "Entender que tentar controlar tudo ao seu redor é a maneira mais rápida de enlouquecer de ansiedade.",
            "A guerra silenciosa e constante na sua cabeça te consome muito mais do que os problemas reais lá fora.",
            "O preço emocional altíssimo de tentar se encaixar num sistema que não tem absolutamente nada a ver com você.",
            "A ilusão de que o sucesso futuro apagará os problemas que você evita enfrentar hoje.",
            "Olhar para o próprio sofrimento como um professor, não como uma injustiça do universo.",
            "A liberdade real começa quando você prefere a verdade dolorosa à mentira confortável.",
            "Não controlamos os eventos externos, apenas a nossa interpretação sobre cada um deles.",
            "O perigo invisível de viver no automático, reagindo a tudo sem decidir nada de verdade.",
            "O que você tanto critica no outro geralmente é o espelho do que você esconde em si.",
            "A dor do crescimento é temporária; o sofrimento de ficar estagnado é uma sentença vitalícia.",
            "Riqueza mental é saber exatamente do que você pode abrir mão sem perder a sua paz.",
            "Seus maiores temores moram na sua imaginação, não na reality dos fatos.",
            "A pressa constante é o sintoma de uma mente que não aguenta ficar cinco minutos sozinha.",
            "Dizer 'sim' para tudo o que te pedem é o jeito mais rápido de apagar o seu próprio rumo.",
            "Sua mente é um jardim: o que você consome diariamente é a semente do seu humor amanhã.",
            "A sabedoria de aceitar a imperfeição da vida em vez de viver frustrado cobrando o ideal.",
            "A pessoa que tem medo de errar já escolheu a pior falha de todas: a inércia.",
            "Você não é os pensamentos que passam pela sua cabeça; você é a consciência que os observa.",
            "O vício em validação externa te transforma no escravo de pessoas que você nem respeita.",
            "A morte não é um evento futuro, é algo que acontece a cada segundo que você desperdiça.",
            "Grandes respostas filosóficas não servem de nada se não mudarem a forma como você trata as pessoas.",
            "O valor do tédio: a criatividade e a clareza só nascem quando o barulho diminui.",
            "A maturidade silenciosa de aceitar que você não precisa ter opinião sobre absolutamente tudo."
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
            "O peso de se sentir uma fraude, sabendo no fundo que você entrega só uma pequena fração do seu real potencial.",
            "Como o estresse crônico destrói sua tomada de decisão e te faz agir por puro impulso primitivo.",
            "O vício emocional em reclamar: como seu cérebro cria caminhos neurais para focar apenas no que dá errado.",
            "A ilusão da força de vontade: por que desenhar o ambiente ao seu redor funciona mais do que a pura disciplina.",
            "Dizer que vai começar amanhã é o analgésico que você usa para aliviar a culpa de não agir hoje.",
            "A procrastinação não é preguiça, é o seu cérebro tentando fugir de uma emoção desconfortável.",
            "Como pequenas micro-decisões acumuladas explicam 90% da vida que você tem hoje.",
            "O perigo do viés de confirmação: você só enxerga o que valida o seu papel de vítima.",
            "Você sabota seus relacionamentos pelo medo inconsciente de ser rejeitado quando se mostrar de verdade.",
            "Como o cansaço mental te faz repetir hábitos ruins que você jurou que nunca mais faria.",
            "O cérebro prefere economizar energia: a mudança exige um desconforto químico que você precisa tolerar.",
            "A necessidade infantil de controle absoluto que te impede de aceitar o fluxo natural da vida.",
            "O ciclo da ansiedade: quanto mais você evita o problema, maior ele parece na sua cabeça.",
            "Sua pressa em ver resultados destrói a constância necessária para alcançar qualquer coisa sólida.",
            "A dependência química do celular: como as notificações roubam o seu foco profundo e a sua clareza.",
            "O hábito de justificar seus erros como 'meu jeito de ser' sabota qualquer chance de mudança real.",
            "A fobia do silêncio: por que as pessoas ligam a TV ou o fone só para não ouvir a própria mente.",
            "O poder da atenção focada: onde você coloca sua energia mental determina seu estado emocional.",
            "Você repete a dinâmica familiar que tanto criticava nos seus pais sem perceber.",
            "O cérebro não distingue ameaça física de ameaça social: por isso o julgamento alheio dói como um soco.",
            "Mudar de comportamento exige perder o apego à história triste que você conta sobre si mesmo."
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
            "A prisão emocional de dever dinheiro e como isso contamina e destrói todas as outras áreas da sua vida.",
            "Riqueza real não se mede pelo que você compra, mas pelo tempo que você consegue sobreviver sem trabalhar.",
            "A armadilha de comprar coisas que você não precisa com dinheiro que não tem para preencher um vazio emocional.",
            "Você prefere a estabilidade da mediocridade à incerteza que acompanha a construção da verdadeira riqueza.",
            "O maior ativo financeiro que você pode construir é a sua própria capacidade de foco e execução.",
            "Tratar investimentos como um jogo de sorte é o caminho mais rápido para continuar na corrida dos ratos.",
            "A crença limitante de que o dinheiro corrompe as pessoas é a desculpa perfeita para a sua falta de atitude.",
            "Riqueza exige paciência entediante; a pressa de ficar rico rápido enriquece apenas os golpistas.",
            "O perigo do estilo de vida inflacionado: ganhar mais e gastar mais te mantém no mesmo lugar de sempre.",
            "A pobreza mental de quem acha que economizar centavos é mais importante do que aprender a gerar milhares.",
            "Se a sua única fonte de renda é um emprego CLT, você está a uma decisão de distância da ruína financeira.",
            "A ilusão de que a herança ou a sorte resolverá a sua desorganização financeira pessoal.",
            "Dinheiro é apenas um amplificador de quem você já é por dentro. O ganancioso vira monstro; o generoso vira farol.",
            "O custo silencioso de não investir em conhecimento prático: você paga caro demais pela sua própria ignorância.",
            "Trabalhar apenas pelo salário te transforma em um mercenário de si mesmo, vendendo o seu tempo barato.",
            "O preço emocional de depender financeiramente de parentes ou parceiros por pura comodidade.",
            "A diferença entre um passivo disfarçado de sonho e um ativo que coloca dinheiro no seu bolso.",
            "A obsessão pelo consumo de luxo é o atalho preferido de quem tem baixa autoimagem.",
            "O verdadeiro valor do dinheiro é a liberdade de dizer 'não' quando algo viola os seus valores.",
            "Construir patrimônio exige silêncio: quem enriquece de verdade não precisa provar nada a ninguém.",
            "Você nunca enriquecerá enquanto ver o dinheiro como um fim, e não como uma ferramenta de liberdade."
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
            "Como identificar se o seu cansaço é real ou é só o seu corpo pedindo para você desistir antes de tentar pra valer.",
            "A coragem de começar pequeno e ser ridicularizado no início é o pedágio obrigatório do sucesso.",
            "Seus sonhos exigem que você abandone a aprovação da sua família e dos seus amigos mais antigos.",
            "A pior prisão do mundo é a mente de quem sabe exatamente o que fazer, mas prefere a segurança da estagnação.",
            "O medo de errar te faz aceitar uma vida morna, onde nada dá muito errado, mas nada dá muito certo.",
            "Você diz que quer liberdade, mas tem pavor da responsabilidade de tomar suas próprias decisões.",
            "A jornada rumo à liberdade é chata, silenciosa e cheia de dias sem qualquer motivação.",
            "Deixar para trás pessoas que não querem crescer não é egoísmo, é pura sobrevivência mental.",
            "A ilusão de que o planejamento infinito substitui a execução crua e imperfeita.",
            "Você está cansado de tentar ou está cansado de insistir no erro que não traz nenhum resultado?",
            "O preço da liberdade é a solidão temporária enquanto você reconstrói os seus padrões mentais.",
            "Esperar que o governo, a empresa ou o destino facilitem o seu caminho é delegar o seu futuro.",
            "Quem quer ir para o topo precisa aprender a andar no escuro e tolerar a incerteza constante.",
            "O vício no conforto: como pequenos confortos diários destroem a sua ambição de construir algo grande.",
            "A diferença entre o sonhador infantil que só idealiza e o realizador inclemente que executa com dor.",
            "Se a sua vida hoje é idêntica à de 5 anos atrás, você não está seguro, está morrendo lentamente.",
            "A coragem de dizer 'basta' para situações abusivas ou medíocres que drenam a sua energia diária.",
            "O maior arrependimento na velhice não é o que você tentou e errou, mas os caminhos que você evitou por covardia.",
            "Seu propósito exige que você seja a ovelha negra do seu ciclo social atual.",
            "A verdadeira liberdade é mental: não adianta mudar de país se você levar a sua mente vitimista com você.",
            "O salto de fé: a rede de segurança só aparece depois que você tem a coragem de pular."
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
            "A importância de aprender a dizer um 'não' firme para os outros e finalmente dizer 'sim' para a sua saúde mental.",
            "Você atrai pessoas carentes porque usa a caridade emocional para tentar se sentir útil e amado.",
            "A ilusão de que um relacionamento resolverá a carência que você deveria curar sozinho.",
            "Cobrar do parceiro a maturidade que você mesmo se recusa a praticar no dia a dia.",
            "O perigo do rancor acumulado: pequenas mágoas não ditas viram uma muralha intransponível.",
            "Admirar o potencial de alguém em vez de aceitar a realidade de quem a pessoa escolhe ser hoje.",
            "A coragem de ter conversas difíceis em vez de acumular ressentimento sob o tapete da conveniência.",
            "Quem aceita migalhas emocionais por medo da solidão passará a vida inteira faminto de afeto real.",
            "A diferença entre conexões profundas baseadas em valores e alianças de conveniência baseadas no ego.",
            "Relacionamentos duradouros não vivem de paixão adolescente, mas de decisões diárias de lealdade e respeito.",
            "Você sabota quem te ama porque a paz emocional te parece um território estranho e desconfortável.",
            "O erro clássico de tentar mudar o outro para moldá-lo ao seu ideal egoísta de parceiro.",
            "A importância de proteger a privacidade do seu casal: o ruído externo destrói a cumplicidade.",
            "O peso de amizades que apenas drenam sua energia e cobram presença sem agregar nenhum valor real.",
            "A maturidade de perdoar o passado do outro sem usá-lo como arma nas discussões do presente.",
            "Saber ouvir de verdade exige calar a voz interna que fica apenas preparando a próxima resposta defensiva.",
            "O perigo de usar as redes sociais para comparar a sua rotina real com a capa de revista alheia.",
            "A lealdade silenciosa: defender o parceiro na ausência dele é o maior ato de respeito que existe.",
            "A carência te faz enxergar qualidades inexistentes em quem apenas te entrega o básico do básico.",
            "Um lar em paz vale mais do que qualquer sucesso financeiro obtido no caos absoluto.",
            "Terminar um ciclo falido exige coragem, mas insistir nele por puro orgulho é burrice emocional."
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
            "A necessidade de escolher muito bem as suas batalhas, em vez de apanhar de todos os lados achando que isso é ser forte.",
            "A dor do treino é insignificante perto do peso brutal do arrependimento de ter desistido no meio.",
            "Você se sabota porque, no fundo, tem pavor de alcançar o topo e descobrir que não sabe lidar com a responsabilidade.",
            "Desculpas são os tijolos que você usa para construir a parede da sua própria mediocridade.",
            "O cansaço real é físico; o esgotamento que te paralisa é apenas a sua mente tentando fugir do trabalho difícil.",
            "A constância tediosa vence o talento genial todas as vezes que o talento decide não trabalhar duro.",
            "Você diz que não consegue, mas a verdade é que você não quer pagar o preço diário e sem glamour do processo.",
            "Cada micro-vitória sobre a preguiça constrói a musculatura da sua autoconfiança de verdade.",
            "Parar de procurar culpados para a sua situação atual é o primeiro passo para assumir o controle do seu destino.",
            "A armadilha da comparação: olhar para a linha de chegada do outro enquanto você se recusa a dar a largada.",
            "O fracasso não define quem você é, mas a desculpa que você inventa após cair sim.",
            "A obsessão pela facilidade: você quer o resultado de 10 anos de esforço em duas semanas de tentativa morna.",
            "Sua mente mente para você: ela diz que você não aguenta mais só para te manter na zona de conforto química.",
            "Quebrar promessas que fez a si mesmo destrói a sua autoimagem e te transforma em um covarde mental.",
            "A disciplina não tira sua liberdade, ela cria a sua liberdade financeira, física e mental futuro.",
            "O poder de dizer 'no' para os prazeres imediatos para garantir o seu legado de longo prazo.",
            "Você não precisa de um dia perfeito para produzir; precisa produzir para transformar o dia comum em vitória.",
            "O medo do julgamento dos medíocres impede você de tentar voar alto de verdade.",
            "A superação real não tem platéia; ela acontece nos dias cinzas, quando você está sozinho e decide treinar com dor.",
            "A inércia é o pior veneno: começar é difícil, mas continuar é onde a mágica da consistência acontece.",
            "Você é o único responsável pela vida que tem hoje. Aceite isso e mude, ou cale-se e continue sofrendo."
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
            "A coragem gigantesca de deixar para trás o que você era para, finalmente, se tornar aquilo que você precisa ser.",
            "Propósito não é algo que você encontra na estrada; é algo que você constrói nas escolhas difíceis do dia a dia.",
            "De que serve acumular títulos e prêmios se as pessoas que moram com você não te respeitam como ser humano?",
            "O legado real não é o dinheiro que você deixa na conta, mas o caráter e a força que você planta nos seus filhos.",
            "Sua vaidade quer aprovação do mundo; seu propósito exige apenas que você seja útil para quem está próximo."
            "A ilusão de viver como se o tempo fosse infinito, desperdiçando anos preciosos com distrações idiotas.",
            "A sabedoria milenar de plantar árvores sob cujas sombras você sabe que nunca se sentará.",
            "Não seja apenas uma estatística de consumo: crie, ensine, construa e deixe o mundo melhor do que encontrou.",
            "O propósito maduro suporta o tédio, a dor e o cansaço porque a causa é maior do que o seu humor do dia.",
            "Você quer ser lembrado pelo que acumulou ou pela diferença profunda que fez na vida de quem te conheceu?",
            "A maior riqueza de um homem é a sua integridade moral nos momentos em que ele poderia lucrar na desonestidade.",
            "O legado silencioso: sua postura nos dias de crise ensina mais sobre caráter do que qualquer sermão ou livro."
        ]
    }
}

def montar_instrucoes_copy(detalhes_tema, contexto_analytics="", historico_angulos=None, indice_gancho=0, indice_cta=0, is_conquistador=False, sentimento_escolhido=None):
    """Monta o bloco de instrução de copy injetado em todos os prompts, evitando repetições."""
    if historico_angulos is None: historico_angulos = []
    
    # Sorteia Ângulo (Roleta anti-repetição)
    opcoes_angulos = [a for a in detalhes_tema["sub_angulos"] if a not in historico_angulos]
    if not opcoes_angulos: # Reseta se todos já foram usados
        # Remove os ângulos específicos deste tema do histórico do estado para reiniciar o ciclo
        for a in detalhes_tema["sub_angulos"]:
            if a in historico_angulos:
                historico_angulos.remove(a)
        opcoes_angulos = detalhes_tema["sub_angulos"]
    sub_angulo = random.choice(opcoes_angulos)
    
    # Avança o gancho na sequência linear (um por postagem, cicla ao chegar no último)
    if is_conquistador:
        gancho, novo_indice = proximo_gancho_conquistador(indice_gancho)
        categoria_gancho = "conflito"  # conquistador usa tom de desafio/conflito
    else:
        gancho, novo_indice, categoria_gancho = proximo_gancho(indice_gancho)

    # Avança o CTA na sequência linear (intercalando categorias de engajamento)
    categoria_cta, referencia_cta, novo_indice_cta = proximo_cta(indice_cta)

    # Descrições de cada categoria — orientam a IA sobre o FORMATO do Slide 1
    descricoes_categoria = {
        "pergunta_que_agride":       "PERGUNTA QUE AGRIDE — Abra com uma pergunta direta e desconfortável que force o leitor a se encarar no espelho.",
        "afirmacao_que_choca":       "AFIRMAÇÃO QUE CHOCA — Abra com uma verdade impopular e ousada que quebre a crença mais comum do leitor.",
        "declaracao_segunda_pessoa": "DECLARAÇÃO EM 2ª PESSOA — Abra com uma frase curtíssima falando diretamente para o 'Você', como se você já soubesse o segredo que ele esconde.",
        "segredo_revelacao":         "SEGREDO/REVELAÇÃO — Abra gerando curiosidade máxima: o leitor sente que está prestes a receber uma informação que ninguém mais tem.",
        "dado_estatistica":          "DADO/ESTATÍSTICA — Abra com um número, estudo ou fato científico chocante que mate as crenças do leitor com evidência.",
        "desafio":                   "DESAFIO — Convide o leitor a participar ativamente, como se fosse um teste ou uma aposta. Provoque-o a provar algo a si mesmo.",
        "curiosidade":               "CURIOSIDADE — Sugira que existe um detalhe oculto e valioso que pouquíssimas pessoas conhecem. Crie uma lacuna de informação irresistível.",
        "quebra_de_expectativa":     "QUEBRA DE EXPECTATIVA — Contrarie uma crença amplamente aceita. O leitor espera uma coisa e você entrega o oposto exato.",
        "reflexao":                  "REFLEXÃO — Faça o leitor olhar para dentro de si e questionar suas próprias escolhas. A pergunta ou frase deve ser perturbadoramente pessoal.",
        "paradoxo":                  "PARADOXO — Abra com uma contradição aparente que desafie a lógica. Quanto mais o leitor tenta resolver o paradoxo, mais fica preso no conteúdo.",
        "identidade":                "IDENTIDADE — Divida o mundo em dois grupos. O leitor instintivamente se pergunta: 'Em qual grupo estou?' Isso gera engajamento profundo.",
        "conflito":                  "CONFLITO — Tome uma posição polêmica ou discorde de uma ideia popular. Provoque reação emocional imediata — concordância ou indignação.",
        "comparacao":                "COMPARAÇÃO — Mostre um contraste 'antes vs. depois' ou 'jeito antigo vs. jeito novo'. A transformação implícita atrai o leitor a descobrir o que mudou.",
    }
    descricao_categoria = descricoes_categoria.get(categoria_gancho, "AFIRMAÇÃO QUE CHOCA — Abra com uma verdade impopular e ousada.")

    # Injeta a diretriz de sentimento do dia no copy base
    diretriz_sentimento = ""
    if sentimento_escolhido:
        from core.ai.styles import SENTIMENTOS_CONFIG
        config_emocional = SENTIMENTOS_CONFIG.get(sentimento_escolhido)
        if config_emocional:
            diretriz_sentimento = f"\n    DIRETRIZ DE SENTIMENTO DO DIA (Ativar Emoção: {sentimento_escolhido.upper()}):\n    - {config_emocional['tom']}\n    - Cada frase e palavra deve ser desenhada para evocar este exato sentimento no leitor.\n"

    instrucoes = f"""
    {REGRAS_COPY_BASE}
    {diretriz_sentimento}
    ESTRATÉGIA DE CONTEÚDO BASEADA EM LIVROS:
    Você tem acesso ao conhecimento dos seguintes livros para este tema: {detalhes_tema['inspira']}
    Sua missão é:
    1. Buscar um princípio, método prático ou lição valiosa presente em algum destes livros.
    2. Usar esse método exato para formular uma mensagem, roteiro ou história altamente persuasiva para resolver a dor do usuário.
    3. ENTREGUE COMO SE O CONHECIMENTO FOSSE SEU. É ESTRITAMENTE PROIBIDO citar o nome do livro, do autor ou dar créditos. Pegue a genialidade da obra e passe como conteúdo original do nosso perfil.

    DIRETRIZ DE CONTEÚDO (Ângulo de Inspiração):
    Ângulo específico sugerido: "{sub_angulo}"

    ===== ARQUITETURA OBRIGATÓRIA DOS 4 ATOS (PERSUASÃO SEQUENCIAL) =====
    Esta é a espinha dorsal de TODA postagem principal. Você é livre para criar o conteúdo
    de cada ato, mas a ORDEM e a FUNÇÃO de cada parte são absolutamente inegociáveis.

    ATO 1 — SLIDE 1 (INTERRUPÇÃO DE PADRÃO / GANCHO):
    Formato desta postagem: {descricao_categoria}
    Gancho de referência: "{gancho}"
    → Adapte este gancho ao tema e ao ângulo sugerido, mantendo a ESTRUTURA fiel ao formato acima.
    → Máximo 12 palavras. Curto, cortante. SEM explicação ainda — apenas o choque inicial.

    ATO 2 — SLIDES 2-3 (EFEITO ZEIGARNIK — Abertura de Loop de Curiosidade):
    → Abra um ciclo de curiosidade sem fechá-lo. Aprofunde a provocação do gancho.
    → O leitor PRECISA continuar para descobrir. Ex: "Existe uma razão que pouquíssimos percebem..." / "O que acontece depois disso mudou tudo."
    → PROIBIDO entregar a solução aqui. Só aumente a tensão e o mistério.

    ATO 3 — SLIDES 4-5 (PROBLEMA DO COTIDIANO — Identificação Visceral):
    → Mostre a dor concreta e reconhecível do dia a dia do leitor. Sem solução ainda.
    → O leitor deve pensar: "É exatamente isso que acontece comigo."
    → Seja específico e cotidiano. Nada de generalidades filosóficas. Aprofunde a ferida antes de curar.

    ATO 4 — SLIDES 6 EM DIANTE (DOPAMINA E RECOMPENSA — Entrega de Valor):
    → Entregue o insight, atalho ou segredo prático de alto valor percebido.
    → O leitor deve sentir que valeria dinheiro saber disso. Seja concreto e aplicável.
    → Trate quem chegou até aqui como alguém acima da média (ex: "Quem lê até aqui já entendeu o que a massa ignora").
    =====================================================================

    ===== DIRETRIZ OBRIGATÓRIA DE CTA (LEGENDA E FECHAMENTO) =====
    Para esta postagem, você DEVE construir a chamada para ação (CTA) na legenda focando no objetivo de: {categoria_cta.upper()}.
    
    Frase de referência para o tom: "{referencia_cta}"
    
    → Adapte esta referência de forma orgânica e inteligente para se fundir com o assunto do post de hoje.
    → O CTA da legenda deve obrigatoriamente seguir este formato e direcionamento estratégico.
    ==============================================================

    ESTRUTURA DE ESCRITA DE SUCESSO (Feedback do Analytics):
    - Estude as métricas de performance recentes no bloco abaixo. Identifique quais estilos e estruturas de copy (ex: diagnóstico cirúrgico, perguntas perturbadoras, alertas de perigo) estão trazendo os maiores scores de engajamento e salvamentos no perfil. Adapte a sua forma de escrever para focar nessa estrutura de sucesso!

    TENDÊNCIAS EM TEMPO REAL (Olhos da Rede):
    - Leia as notícias da semana, os vídeos mais vistos no YouTube deste tema e as buscas no Google Trends descritas no bloco abaixo.
    - FUSÃO OBRIGATÓRIA: Não use o ângulo sugerido de forma literal e repetitiva. Em vez disso, junte a lição teórica do livro/ângulo sugerido com a "vibe" ou assunto quente que as pessoas estão buscando e discutindo na internet agora (trazido pelos Olhos da Rede). Use a dor atual coletada nas redes como o cenário prático para ilustrar a lição.

    DADOS DE PERFORMANCE E CONTEXTO ATUAL:
    {contexto_analytics}
    """
    return instrucoes, sub_angulo, gancho, descricao_categoria, novo_indice, categoria_cta, referencia_cta, novo_indice_cta
