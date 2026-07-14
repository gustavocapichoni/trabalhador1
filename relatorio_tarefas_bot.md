# Relatorio Completo: Todas as Tarefas do Trabalhador (Bot Instagram)

Analise linha a linha de todos os arquivos do projeto `my-bot-instagram-main`.

---

## VISAO GERAL DA ARQUITETURA

O bot opera em cinco grandes pilares:

1. **Geracao de Conteudo** (IA + Contextualizacao)
2. **Producao Visual** (imagens e videos)
3. **Publicacao** (Instagram API)
4. **Inteligencia de Dados** (analytics, relatorios, auto-ajuste)
5. **Gerador de PDF Semanal**

---

## PILAR 1 — GERACAO DE CONTEUDO (via IA)

### `core/ai/gemini.py` — O Cerebro Central

| # | Tarefa | Detalhe |
|---|--------|---------|
| 1 | Gerenciar roleta de chaves Gemini | Tenta ate 10 chaves GEMINI_API_KEY_N em sequencia. Evita usar a mesma chave repetidamente. |
| 2 | Fallback para Groq | Se todas as chaves Gemini falharem, chama a API do Groq (llama-3.3-70b-versatile). |
| 3 | Fallback para OpenRouter | Se Groq tambem falhar, usa OpenRouter como terceiro recurso. |
| 4 | Construir prompt anti-repeticao | Le o estado atual (ultimos angulos usados, hooks, estilos) para instruir a IA a nao repetir. |
| 5 | Injetar dados dos Olhos da Rede | Adiciona no prompt as tendencias do momento (RSS, YouTube) coletadas pela olhos_da_rede.py. |
| 6 | Injetar dados de analytics | Adiciona no prompt as recomendacoes semanais e cruzadas. |
| 7 | Gerar conteudo por tipo de post | Chama a IA com prompts especificos para: carousel, story_manha, story_tarde, reels, reels_noite, reels_conquistador, reels_leads, pexels_story, pexels_story_noite. |
| 8 | Sortear tema via roleta viciada | Escolhe o tema do post proporcionalmente ao desempenho historico de cada tema (analytics). |
| 9 | Sortear angulo e sub-angulo | Escolhe aleatoriamente dentro das categorias de prompts.py, garantindo variedade. |
| 10 | Sortear estilo de copy | Escolhe o tom da escrita (provocativo, curioso, empatico, etc.) entre opcoes da styles.py. |
| 11 | Registrar o conteudo gerado no estado | Salva angulo, hook e estilo usados para evitar repeticao nas proximas execucoes. |

### `core/ai/olhos_da_rede.py` — Espionagem de Tendencias

| # | Tarefa | Detalhe |
|---|--------|---------|
| 12 | Buscar noticias via RSS | Consulta feeds RSS de portais de psicologia, filosofia e comportamento. |
| 13 | Buscar tendencias no YouTube | Consulta a API do YouTube para encontrar videos em alta nos temas do perfil. |
| 14 | Filtrar e sumarizar conteudo relevante | Filtra os resultados por tema e cria um resumo para injetar no prompt da IA. |

### `core/ai/prompts.py` — Biblioteca de Temas e Angulos

| # | Tarefa | Detalhe |
|---|--------|---------|
| 15 | Fornecer 8 temas principais | Espiritualidade, Filosofia, Psicologia, Financas, Liberdade, Conexoes, Superacao, Proposito. |
| 16 | Fornecer dezenas de sub-angulos por tema | Cada tema tem de 8 a 15+ angulos narrativos diferentes. |
| 17 | Fornecer multiplos tipos de hook | Categorias de abertura: gatilho de identidade, pergunta incomoda, afirmacao contraintuitiva, etc. |
| 18 | Regras de identidade do conteudo | Define que o bot deve soar profundo, nao ser coach generico, evitar frases de auto-ajuda cliche. |

### `core/ai/styles.py` — Estilos de Escrita

| # | Tarefa | Detalhe |
|---|--------|---------|
| 19 | Fornecer biblioteca de estilos de copy | Ex: "Filosofico Direto", "Ironico Inteligente", "Emotivo Profundo", etc. |
| 20 | Controlar anti-repeticao de estilo | Armazena no estado os ultimos estilos usados para evitar monotonia. |

---

## PILAR 2 — PRODUCAO VISUAL

### `core/design/motor_visual.py` — Geracao de Imagens Estaticas

| # | Tarefa | Detalhe |
|---|--------|---------|
| 21 | Buscar fundo no Unsplash (Nivel 1) | API de fotos reais com orientacao e query por tema. Verifica se a imagem foi usada recentemente. |
| 22 | Buscar fundo no Pexels (Nivel 2) | Fallback do Unsplash. Tenta multiplos queries tematicos. |
| 23 | Buscar fundo no Pixabay (Nivel 3) | Terceiro nivel de fallback. Adapta orientacao (vertical, horizontal, all). |
| 24 | Gerar imagem por IA com Pollinations (Nivel 4) | Ultimo recurso online. Usa prompt cinematografico gerado pelo gerador_prompts.py. |
| 25 | Usar biblioteca local (Nivel 5) | Le imagens salvas em biblioteca_local/imagens/tema/. |
| 26 | Fundo solido escuro de emergencia (Nivel 6) | Ultima salvaguarda caso tudo falhe. |
| 27 | Aplicar mesh gradient inteligente | Sobrepos gradiente artistico na imagem de fundo (via efeitos.py). |
| 28 | Gerar carrossel panoramico | Corta a imagem de fundo em fatias com efeito de "panning" para criar ilusao de movimento entre slides. Inclui slide de capa e slide de CTA aleatorio. |
| 29 | Gerar fundos para Reels (imagem estatica) | Gera as imagens de fundo de cada slide do reels SEM texto (o texto e animado depois). Busca imagem diferente por slide. |
| 30 | Gerar post estatico (Story/Feed) | Gera a arte com layout aleatorio (classic, bottom, ou quote). Suporta multiplos slides em sequencia. |
| 31 | Aplicar marca dagua dourada | Desenha "GUSTAVO_8K_" em dourado com efeito glow em todas as artes. |
| 32 | Aplicar logo do projeto | Tenta carregar e sobrepor o logo de biblioteca_local/logo/. |
| 33 | Sistema de fonte do dia | Usa uma fonte diferente para cada dia da semana (identidade visual diaria). |

### `core/design/gerador_prompts.py` — Criacao de Prompts de Imagem

| # | Tarefa | Detalhe |
|---|--------|---------|
| 34 | Gerar prompt cinematografico | Combina aleatoriamente cenario, personagem, objeto, clima, enquadramento e estilo fotografico por tema para criar um prompt realista para IA de imagens. |

### `core/media/reels.py` — Producao de Video Animado

| # | Tarefa | Detalhe |
|---|--------|---------|
| 35 | Gerenciar fila de musicas | Le todos os MP3 da pasta biblioteca_local/musicas/, cria fila embaralhada no estado para garantir que cada musica so se repita apos todas serem usadas. |
| 36 | Gerar audio de silencio de emergencia | Caso nao haja MP3, cria silencio via FFmpeg como fallback. |
| 37 | Montar slideshow animado (Reels) | Une imagens de fundo + textos animados + musica de fundo em um video MP4. |
| 38 | Aplicar 7 animacoes de texto diferentes | Uma animacao por dia da semana: Maquina de Escrever (Seg), Surgimento por Palavras (Ter), Fade In (Qua), Zoom-In (Qui), Slide de Baixo (Sex), Glitch/Vibracao (Sab), Karaoke Dourado (Dom). |
| 39 | Aplicar 7 animacoes de imagem diferentes | Uma transicao de imagem diferente por dia: Fade In, Slide Direita, Zoom In, Slide Baixo, Slide Esquerda, Zoom Out, Slide Topo. |
| 40 | Acoplar video final de logo | Concatena um video.mp4 da pasta de logo ao fim do reels, com a musica continuando por cima. |
| 41 | Gerar video individual de Story | Converte uma imagem estatica em video MP4 de 10 segundos com musica sincronizada. |

### `core/media/pexels_story.py` — Producao de Video com Fundo Real

| # | Tarefa | Detalhe |
|---|--------|---------|
| 42 | Buscar video vertical no Pixabay (Nivel 1) | Filtra videos com altura maior que largura. Baixa adaptado a quantidade de slides necessarios. |
| 43 | Buscar video vertical no Pexels (Nivel 2) | Fallback do Pixabay. Filtra explicitamente por arquivos verticais. |
| 44 | Usar videos locais como complemento | Se APIs retornarem poucos videos, complementa com arquivos da biblioteca_local/videos/. |
| 45 | Concatenar multiplos videos | Para reels_leads (longo), baixa e concatena varios videos, redimensionando para tamanho uniforme. |
| 46 | Calcular duracao dinamica do video | Para reels_leads, calcula a duracao necessaria baseada no numero de slides (~5s por slide, max 3 min). |
| 47 | Renderizar texto sobre video ao vivo | Overlay de texto com 4 tipos de animacao: typewriter, fade, reveal, static (sorteados). |
| 48 | Renderizar CTA final em destaque dourado | O ultimo slide recebe fundo escurecido e borda dourada para maximo impacto. |
| 49 | Aplicar efeitos cinematograficos | Sorteia entre: sem efeito, tarjas cinematicas, vignette escuro. |
| 50 | Adicionar assinatura dourada no rodape | Desenha "GUSTAVO_8K_" com efeito glow dourado em cada frame do video. |
| 51 | Limitar bitrate do reels_leads | Restringe a 3000kbps para manter o arquivo abaixo de 100MB (limite do catbox.moe). |
| 52 | Adicionar audio de fundo | Loopeia o MP3 se necessario para cobrir toda a duracao do video. |

---

## PILAR 3 — PUBLICACAO NO INSTAGRAM

### `core/publisher/uploader.py` — Upload de Midia

| # | Tarefa | Detalhe |
|---|--------|---------|
| 53 | Upload no catbox.moe (Nivel 1) | Envia arquivo ate 200MB e retorna URL publica permanente. |
| 54 | Upload no litterbox.catbox.moe (Nivel 2) | Fallback: ate 1GB, valido por 72h. |
| 55 | Upload no tmpfiles.org (Nivel 3) | Extrai URL direta de download do HTML da pagina. |
| 56 | Upload no file.io (Nivel 4) | Uso unico (1 download). |
| 57 | Upload no transfer.sh (Nivel 5) | Via HTTP PUT, valido 14 dias. |

### `core/publisher/instagram.py` — Publicacao via Meta API

| # | Tarefa | Detalhe |
|---|--------|---------|
| 58 | Publicar Story unico | Cria container de imagem + publica como Story. |
| 59 | Publicar Stories em sequencia | Publica multiplos stories um apos o outro (com 15s de intervalo). Suporta imagem e video. |
| 60 | Publicar Carrossel | Cria containers filhos por slide, container pai, aguarda processamento e publica. |
| 61 | Publicar Reels/Video | Cria container de Reels, aguarda processamento da Meta e publica. |
| 62 | Aguardar processamento de container | Faz polling na API da Meta (status_code == FINISHED) antes de publicar. |
| 63 | Retry inteligente de publicacao | Lida com erros especificos: erro 2207027 (midia nao pronta) faz retry com backoff crescente; erro 9007 (story expirado) pula silenciosamente; erro 190 (token invalido) lanca excecao fatal. |

### `core/publisher/email_notifier.py` — Notificacoes por E-mail

| # | Tarefa | Detalhe |
|---|--------|---------|
| 64 | Enviar e-mail de monitoramento | Envia alertas via SMTP (Gmail SSL) para o e-mail configurado. |
| 65 | Verificar expiracao do token Instagram | Consulta debug_token da API do Facebook e alerta se o token expira em 10 dias ou menos. Envia e-mail de alerta automatico. |

---

## PILAR 4 — INTELIGENCIA DE DADOS

### `core/analytics/coletor.py` — Coleta de Metricas

| # | Tarefa | Detalhe |
|---|--------|---------|
| 66 | Sincronizar metricas do Firebase Firestore | Baixa o historico completo de metricas de todos os posts. |
| 67 | Coletar metricas de Feed/Carrossel | Impressions, reach, saves, shares, profile_visits, follows. |
| 68 | Coletar metricas de Reels | Views, avg_watch_time, total_watch_time, reach, saves, shares. |
| 69 | Coletar metricas de Stories | Impressions, reach, navigation (taps), replies, follows. |
| 70 | Salvar metricas no Firebase | Persiste cada coleta no Firestore com merge (nao sobrescreve). |
| 71 | Respeitar janela de tempo por tipo | Stories: coleta em ate 24h. Feed/Reels: aguarda 24h e coleta por ate 14 dias. |

### `core/analytics/analisador.py` — Analise de Performance

| # | Tarefa | Detalhe |
|---|--------|---------|
| 72 | Calcular score de performance por post | Formula ponderada: saves x3 + shares x2 + comments x2 + likes + reach x0.05. Bonificacoes especificas por tipo (ex: taps_back para stories, watch_time para reels). |
| 73 | Analisar padroes por periodo (semanal a anual) | Agrupa scores por tema, formato e estilo de copy. |
| 74 | Calcular distribuicao proporcional | Transforma medias de score em percentuais para a "roleta viciada" de temas. |

### `core/analytics/analisador_semanal.py` — Analise Semanal Profunda

| # | Tarefa | Detalhe |
|---|--------|---------|
| 75 | Analisar 7 dias de dados | Agrega por tema, formato, estilo, horario e dia da semana. |
| 76 | Gerar ranking de temas | Ordena temas por score medio, identifica melhor e pior. |
| 77 | Gerar ranking de horarios de pico | Identifica em qual hora do dia os posts tiveram melhor desempenho. |
| 78 | Gerar ranking do melhor dia da semana | Identifica qual dia da semana gera mais engajamento. |
| 79 | Gerar contexto estrategico para a IA | Escreve um texto em linguagem natural com os insights para injetar no prompt do Gemini. |
| 80 | Salvar recomendacoes semanais | Escreve analytics/dados/recomendacoes_semanais.json. |

### `core/analytics/ajustador.py` — Cruzamento Macro vs. Micro

| # | Tarefa | Detalhe |
|---|--------|---------|
| 81 | Cruzar dados de multiplos periodos | Compara analises semanal, mensal, trimestral, semestral e anual. |
| 82 | Priorizar estrategia de longo prazo | A distribuicao final de pesos (roleta) vem sempre do periodo mais macro disponivel. |
| 83 | Gerar contexto Macro vs. Micro | Cria texto estrategico explicando tendencia de longo prazo vs. tatica de curto prazo. |
| 84 | Salvar recomendacoes cruzadas | Escreve analytics/dados/recomendacoes.json. |

### `core/analytics/leitor_pdf.py` — Leitura do PDF Semanal

| # | Tarefa | Detalhe |
|---|--------|---------|
| 85 | Ler o ultimo PDF gerado | Abre gerador_pdf/output/ultimo_conteudo.json e extrai titulo, dor principal e metodo. |
| 86 | Criar resumo para o reels_leads | Fornece o contexto do PDF ao prompt da IA para criar o roteiro de venda do material. |

### `core/reports/weekly.py` — Relatorio Semanal

| # | Tarefa | Detalhe |
|---|--------|---------|
| 87 | Descobrir ID da conta Instagram | Auto-detecta o IG_ACCOUNT_ID via Meta API se nao estiver configurado. |
| 88 | Buscar metricas gerais da conta | Seguidores, total de publicacoes, nome, username. |
| 89 | Listar posts dos ultimos 7 dias | Historico do estado local. |
| 90 | Top 5 posts mais visualizados | Com frase visual, legenda e link do Instagram. |
| 91 | Top 5 posts mais curtidos | Idem. |
| 92 | Top 5 posts mais compartilhados | Idem. |
| 93 | Top 5 posts mais salvos | Idem. |
| 94 | Top 6 horarios com maior media de views | Detalha melhor formato, tema e abordagem por horario. |
| 95 | Enviar relatorio por e-mail | Consolida tudo e envia ao dono via SMTP. |

### `core/reports/periodic.py` — Relatorios Periodicos

| # | Tarefa | Detalhe |
|---|--------|---------|
| 96 | Gerar relatorio mensal (30 dias) | Totais, medias, rankings, top posts por views/curtidas/shares/saves. |
| 97 | Gerar relatorio trimestral (90 dias) | Idem. |
| 98 | Gerar relatorio semestral (180 dias) | Idem. |
| 99 | Gerar relatorio anual (365 dias) | Idem. |
| 100 | Enviar relatorio periodico por e-mail | Formata e envia via SMTP. |

---

## PILAR 5 — GERADOR DE PDF SEMANAL

### `gerador_pdf/gerador.py` — Orquestrador do PDF

| # | Tarefa | Detalhe |
|---|--------|---------|
| 101 | Ler analytics + tendencias e decidir tema | Via decisor.py: analisa dados de performance e escolhe o tema e livro da semana. |
| 102 | Gerar narrativa completa via Gemini | Via conteudo.py: cria um PDF de 8 paginas com personagem, dor, jornada, metodo e plano de acao. |
| 103 | Montar PDF visual com ReportLab | Via gerar_pdf.py: layout com gradientes, Bento Cards, tipografia premium e marca. |
| 104 | Upload do PDF para Firebase Storage | Via uploader.py: sobe o arquivo e registra a campanha no Firestore. |

### `gerador_pdf/conteudo.py` — Narrativa IA do PDF

| # | Tarefa | Detalhe |
|---|--------|---------|
| 105 | Sortear nome de personagem | Escolhe um nome masculino aleatorio para humanizar a narrativa. |
| 106 | Gerar capa com 4 Bento Cards | IA cria textos para "A Nevoa", "A Solucao", "O Proposito" e "A Verdade". |
| 107 | Gerar 5 capitulos narrativos | Cada capitulo com 3 paragrafos: cena cinematografica, conflito interno, contextualizacao/resolucao. |
| 108 | Gerar citacao de destaque | Frase original poderosa que resume a transformacao. |
| 109 | Gerar Plano de Acao de 4 passos | Passos praticos derivados do tema do livro base. |
| 110 | Gerar fechamento inspiracional | Paragrafo final motivacional da edicao. |
| 111 | Fallback de emergencia | Conteudo estatico pre-escrito caso todas as chaves Gemini falhem. |

### `gerador_pdf/gerar_pdf.py` — Layout Visual

| # | Tarefa | Detalhe |
|---|--------|---------|
| 112 | Download automatico de fontes premium | Baixa Inter e Space Grotesk do Google Fonts automaticamente. |
| 113 | Gerar capa com Bento Grid | Layout de cards coloridos com gradientes, decoracoes geometricas e hierarquia visual. |
| 114 | Gerar paginas de capitulos | Fundo com gradiente diferente por capitulo, cabecalho estilizado, texto justificado. |
| 115 | Gerar pagina de citacao | Fundo escuro, citacao em box translucido, versiculo biblico. |
| 116 | Gerar pagina do Plano de Acao | Tabela estilizada com badges coloridos numerados por passo. |
| 117 | Numeracao de paginas elegante | Rodape com opacidade reduzida em todas as paginas. |

---

## INFRAESTRUTURA E ORQUESTRACAO

### `gerenciador.py` — Agendador Principal

| # | Tarefa | Detalhe |
|---|--------|---------|
| 118 | Postar Story da Manha | story_manha — executa diariamente as 8h. |
| 119 | Postar Reels do dia | reels — executa as 10h. |
| 120 | Postar Carrossel | carousel — executa as 12h. |
| 121 | Postar Story da Tarde | story_tarde — executa as 14h. |
| 122 | Postar Pexels Story (video) | pexels_story — executa as 16h. |
| 123 | Postar Reels da Noite | reels_noite — executa as 18h. |
| 124 | Postar Pexels Story Noturno | pexels_story_noite — executa as 20h. |
| 125 | Postar Reels Conquistador | reels_conquistador — executa as 21h. |
| 126 | Postar Reels de Leads | reels_leads — video longo de vendas do PDF, executa em horario especifico. |
| 127 | Coleta diaria de metricas | coletor.rodar_coleta() — executa a noite para coletar dados da API. |
| 128 | Analytics semanal | analisador_semanal.analisar_semana() — todo domingo. |
| 129 | Relatorio semanal | weekly.gerar_e_enviar_relatorio() — toda segunda-feira. |
| 130 | Verificacao diaria do token | verificar_expiracao_token() — monitora expiracao das credenciais. |

### `core/config/state.py` — Gerenciamento de Estado

| # | Tarefa | Detalhe |
|---|--------|---------|
| 131 | Salvar historico de posts | Registra tipo, tema, data, post_id, estilo de copy de cada publicacao. |
| 132 | Controlar midias recentes usadas | Lista de IDs de imagens/videos usados recentemente para evitar repeticao visual. |
| 133 | Sincronizar estado com Firebase | Le e escreve estado_migrado.json no Firebase Realtime Database para persistencia em nuvem. |
| 134 | Controlar fila de musicas | Persiste no estado a ordem das musicas para o sistema de fila sem repeticao. |

### `core/config/settings.py` — Configuracoes

| # | Tarefa | Detalhe |
|---|--------|---------|
| 135 | Gerenciar multiplas chaves Gemini | Le GEMINI_API_KEY_1 ate GEMINI_API_KEY_10 do arquivo .env. |
| 136 | Gerenciar chaves de imagens | Unsplash, Pexels, Pixabay. |
| 137 | Gerenciar credenciais Instagram | IG_ACCESS_TOKEN e IG_ACCOUNT_ID. |
| 138 | Gerenciar SMTP e e-mail | Para notificacoes e relatorios. |
| 139 | Gerenciar Firebase | FIREBASE_CREDENTIALS_JSON para persistencia em nuvem. |

---

## RESUMO NUMERICO

| Categoria | Qtd de Tarefas |
|-----------|----------------|
| Geracao de Conteudo (IA) | 20 |
| Producao Visual (imagens) | 14 |
| Producao de Video | 11 |
| Publicacao (Instagram API) | 11 |
| Coleta e Analise de Dados | 19 |
| Relatorios | 9 |
| Gerador de PDF | 17 |
| Infraestrutura e Estado | 9 |
| **TOTAL** | **~139 tarefas** |
