# Plano de Implementação: Evolução do Bot de Instagram

Este plano detalha o desenvolvimento do **Cérebro (Analytics Avançado)**, **Cientista de Dados em Tempo Real** e **Olhos da Rede Exponencial** para o bot de Instagram (`my-bot-instagram-main`).

> [!NOTE]
> **Explicação dos Termos Técnicos:**
> - **Análise Semântica de Comentários:** Leitura do texto dos comentários usando inteligência artificial para entender a intenção do público (dúvida, elogio, objeção).
> - **Quality Gate (Avaliador Crítico):** Um filtro de IA que analisa a legenda e imagem *antes* de postar. Se a ideia não for excelente, ele manda reescrever.
> - **Multimodalidade (Visão Computacional):** Habilidade da IA de "enxergar" imagens e vídeos para descobrir quais padrões visuais retêm mais a atenção.
> - **Newsjacking:** Estratégia de pegar carona em notícias ou assuntos que estão bombando hoje na internet para criar posts virais no seu nicho.

---

## User Review Required

> [!IMPORTANT]
> **Créditos e Limites de API:** 
> - A leitura de comentários usa chamadas adicionais à API do Instagram Graph.
> - A pré-avaliação crítica de posts gera 1 chamada extra à API do Gemini por postagem.
> - O monitoramento do Olhos da Rede usa chamadas gratuitas de RSS, Google Trends e YouTube Data API v3.

> [!TIP]
> O desenvolvimento será feito em 3 Fases Modulares. Cada fase pode ser ativada e testada de forma independente via modo `--dry-run` (modo de teste local sem postar).

---

## Open Questions

Não há perguntas pendentes no momento. Caso deseje incluir algum novo nicho específico ou fonte de notícias na varredura do *Olhos da Rede*, podemos adicionar facilmente na Fase 3.

---

## Proposed Changes

### Componente 1: O Cérebro (Analytics Avançado)

#### [NEW] [coletor_comentarios.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/analytics/coletor_comentarios.py)
- Coleta comentários dos posts mais recentes via API Graph do Instagram.
- Usa o Gemini para classificar cada comentário em: `duvida_tecnica`, `elogio`, `objecao`, `pedido_conteudo`.
- Armazena no Firebase na coleção `comentarios_posts` e compila uma lista de "Pautas Recomendadas por Seguidores".

#### [NEW] [avaliador_critico.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/ai/avaliador_critico.py)
- Implementa a função `avaliar_qualidade_post(rascunho)` que atribui uma nota de 0 a 10 antes da publicação.
- Avalia critérios: Força do Gancho (0-3), Clareza/Persuasão (0-3), Potencial de Salvamento/Compartilhamento (0-4).
- Se `nota < 7.5`, solicita automaticamente a reescrita do gancho e legenda.

#### [MODIFY] [coletor.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/analytics/coletor.py)
- Integra a chamada da coleta de comentários durante a rotina diária de métricas.

---

### Componente 2: O Cientista de Dados (Estratégia em Tempo Real)

#### [NEW] [matriz_estrategica.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/analytics/matriz_estrategica.py)
- Mapeia o rendimento histórico cruzando **Dia da Semana x Horário x Tom Emocional x Tipo de Gancho**.
- Retorna o estilo ideal para a postagem do momento (ex: "Domingo 18h -> Roteiro Narrativo com tom de vulnerabilidade").

#### [MODIFY] [gemini.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/ai/gemini.py)
- Adiciona a função `obter_briefing_cientista_dados()` que lê a matriz estratégica e as hipóteses confirmadas no Firebase.
- Injeta o briefing diretamente nas instruções do prompt antes da geração de conteúdo.

#### [MODIFY] [main.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/main.py)
- Intercepta a geração de conteúdo e aplica o filtro do **Avaliador Crítico** antes de enviar para o motor visual/Instagram.

---

### Componente 3: Os Olhos da Rede (Antena de Relevância Cultural Exponencial)

#### [MODIFY] [olhos_da_rede.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/ai/olhos_da_rede.py)
- Adiciona a função `detectar_clima_emocional()` que analisa o tom das notícias recentes (ex: Ansiedade, Foco, Esperança) e orienta a escolha do tom da legenda.
- Adiciona detecção de pautas quentes para **Newsjacking** (assuntos em alta no Google Trends no dia).
- Permite cadastrar canais/feeds de referência no nicho para capturar tendências em tempo real.

---

## Verification Plan

### Automated Tests
- Execução de testes em modo `--dry-run` para cada tipo de postagem:
  `python main.py --type reels --dry-run`
  `python main.py --type carousel --dry-run`
- Teste manual da rotina de analytics:
  `python core/analytics/rodar_analytics.py --ciclo semanal`

### Manual Verification
- Verificar no Firebase Firestore se as coleções `comentarios_posts`, `memoria_estrategica` e `historico_posts` estão recebendo os novos campos corretamente.
- Testar a reescrita automática do Avaliador Crítico forçando uma avaliação baixa em ambiente de teste.
