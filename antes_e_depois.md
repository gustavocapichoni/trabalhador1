# Antes e Depois das Alterações do Bot de Instagram

Este documento detalha o que acontecia antes das modificações e como o sistema se comportará a partir de agora com as atualizações feitas nos scripts de geração de mídia, inteligência artificial e áudio.

---

## 1. Tamanho do Texto por Slide
**Contexto**: O tempo de duração de um slide de texto no vídeo é de 5 segundos.

### ANTES ❌
- **Reels Leads**: Não havia um limitador de palavras no código. O Gemini às vezes gerava parágrafos longos, forçando o espectador a ler rápido demais.
- **Story da Tarde**: O limitador automático truncava textos com mais de 18 palavras, o que ainda gerava leitura apertada para os 5 segundos disponíveis.

### DEPOIS ✅
- **Reels Leads e Story da Tarde**: O limite nos prompts e no código (`gemini.py`) foi reduzido para **10 palavras por slide** (garantindo no máximo 3 linhas por slide para leitura confortável).
- **Sem Corte de Palavras (Preservação do Sentido)**: Removemos a tesoura que cortava frases com `...`. O sistema agora avisa nos logs se a IA passar do limite sugerido, mas exibe a frase completa sem jamais prejudicar o sentido da mensagem.

---

## 2. Estrutura do CTA (Últimos Slides)
**Contexto**: A forma como o PDF era apresentado e oferecido nos formatos em vídeo.

### ANTES ❌
- Os slides eram divididos de maneira inflexível (exatamente 6 no Reels).
- O PDF muitas vezes era "jogado" logo no meio da identificação do problema.
- A CTA poderia ser genérica ou um texto único enorme no final (chegando a 6 linhas acumuladas na tela).

### DEPOIS ✅
- **Transição Suave**: Criamos uma estrutura que permite dividir o desfecho de forma limpa.
- **Story da Tarde (5 a 6 slides)**: Atualizado para ter obrigatoriamente entre 5 e 6 slides. Isso impede que o Gemini delete o CTA ou junte tudo. Estrutura: Slide 1 (Gancho) → Slides 2 e 3 (Contexto/Problema) → Slide 4 (Transição + Título do PDF) → Slide 5 ou 6 (CTA Final "Comente 'SABEDORIA'").
- **CTA Curto de no Máximo 3 Linhas**: A chamada para ação no slide final do *Story da Tarde* e do *Reels Leads* foi reduzida no prompt para caber em **no máximo 3 linhas** (2 linhas para o comando de comentar + 1 linha para o benefício).

---

## 3. Visual da Chamada de Ação (Degradê + Cor da Palavra-Chave)
**Contexto**: O processamento visual do texto renderizado em `pexels_story.py`.

### ANTES ❌
- Ao chegar no último slide (CTA), o texto mudava para branco e a palavra "SABEDORIA" ficava dourada, perdendo o degradê.
- Havia duplicação visual e texto "fantasma" vazando por trás da palavra-chave por conta da sombra.

### DEPOIS ✅
- **Degradê Preservado**: O degradê colorido se mantém no slide final para *Reels Leads* (Roxo ou Rosa) e *Story da Tarde* (Dourado/Bronze).
- **Eliminação de Texto Fantasma**: A máscara de degradê e a camada de sombra (`shadow_draw`) agora pulam a palavra-chave. Apenas a camada final pinta a palavra em destaque com sombra própria.
- **Cores Exclusivas por Formato**:
  - **Story da Tarde**: A palavra **'SABEDORIA'** é destacada em **Verde Neon / Esmeralda Vibrante `(RGB: 0, 230, 118)`**.
  - **Reels Leads**: A palavra **'SABEDORIA'** é mantida no clássico **Dourado Ouro `(RGB: 255, 215, 0)`**.

---

## 4. Gerador de Imagens com IA (FLUX.1)
**Contexto**: A origem das imagens de fundo usadas nos Reels (manhã/noite), Story da Manhã e Carrossel.

### ANTES ❌
- O bot baixava imagens de bancos públicos em cascata (**Unsplash → Pexels → Pixabay**).
- O sistema não tinha controle sobre a atmosfera visual e fotos podiam repetir.

### DEPOIS ✅
- O bot usa o modelo **FLUX.1-schnell** da Hugging Face via `gradio_client` para **gerar imagens originais do zero**.
- **Rodízio entre 5 contas (tokens)** com retry inteligente (pula na hora em cota; tenta 3x em erros de conexão).
- **100% Noturnas**: Matriz com 15 subtemas de solidão urbana, 20 cidades globais, 10 efeitos atmosféricos (neve, chuva, neblina) e 10 ângulos aéreos (~30.000 combinações sem repetição).
- Bancos de imagens mantidos como emergência automática.

---

## 5. Padronização de Vídeos de Fundo (Pexels / Pixabay)
**Contexto**: A busca de vídeos em HD/4K usados no *Story Tarde, Pexels Story (Manhã/Noite), Reels Leads e Reels Conquistador*.

### ANTES ❌
- As buscas de vídeo podiam trazer cenas diurnas, campos, academias ou pessoas estudando em salas claras.

### DEPOIS ✅
- **Filtro de Tema Unificado**: As buscas foram higienizadas e padronizadas para a estética de **Solidão Urbana Contemporânea à Noite** (`contemporary urban solitude night city street golden amber light 35mm`).
- Todos os vídeos de fundo agora seguem a mesma identidade noturna, misteriosa e cinemática das imagens de IA.

---

## 6. Sincronização e Rodízio de Músicas da Biblioteca Local
**Contexto**: A seleção de áudios MP3 da pasta `biblioteca_local/musicas` e `musicas-youtube`.

### ANTES ❌
- A fila no estado gravava caminhos absolutos do servidor Linux (`/home/runner/...`). Ao rodar localmente ou adicionar músicas novas, o sistema não as reconhecia e repetia sempre as mesmas poucas músicas.

### DEPOIS ✅
- **Nomes de Arquivo Limpos**: A fila grava apenas os nomes dos arquivos MP3, funcionando perfeitamente em Windows e Linux.
- **Detecção Automática de Músicas Novas**: Ao adicionar qualquer `.mp3` novo na pasta, o bot reconhece imediatamente e adiciona à fila sem repetir faixas até concluir o ciclo completo.

---

## 7. Arquivos Criados ou Alterados no Projeto
- `core/media/flux_gerador.py` *(novo)* — Módulo gerador FLUX.1 com matriz noturna e rodízio de 5 tokens.
- `core/design/motor_visual.py` — Injeção do Nível 0 (FLUX) na cascata de imagens.
- `core/media/pexels_story.py` — Ajustes de CTA sem sombra fantasma, cor verde no Story Tarde, 3 linhas no CTA, higienização noturna de vídeos e ampliação do filtro estrito para bloquear estádios, festas e bebidas.
- `core/media/reels.py` — Sincronização automática de músicas novas e nomes limpos no rodízio de áudio.
- `core/ai/gemini.py` — Prompts ajustados para 10 palavras max por slide, 5-6 slides no Story Tarde, CTA de 3 linhas e atualização das buscas visuais do Conquistador para o tema Solidão Urbana Contemporânea Noturna.
- `requirements.txt` — Adicionado `gradio_client` para permitir a execução da IA na nuvem.

---

## 8. Padronização da Identidade Visual (Prompts do Conquistador e Filtro de Vídeos)
**Contexto**: A seleção de vídeos em plataformas externas (Pexels / Pixabay) e a formulação de buscas geradas pela IA.

### ANTES ❌
- O **Reels Conquistador** solicitava a busca por *"stadium concert crowd lights"*, o que trazia vídeos de estádio de futebol e torcida (ex: estádio do Galatasaray).
- O **Reels Leads** e outros formatos por vezes traziam cenas descontextualizadas com pessoas em bares ou bebidas devido a buscas abertas.
- Faltavam filtros específicos para impedir que termos esportivos ou de festas fossem consultados no Pexels.

### DEPOIS ✅
- **Prompts de IA Alinhados**: O prompt do `reels_conquistador` em `gemini.py` foi atualizado para focar no tema mestre: *"contemporary urban solitude, high rise city lights, penthouse terrace night view, golden bokeh 35mm"*, eliminando requisições a estádios e shows.
- **Filtro Estrito Ampliado (Blacklist)**: Adicionamos os termos `"stadium"`, `"soccer"`, `"football"`, `"crowd"`, `"party"`, `"drinking"`, `"alcohol"`, `"bar"`, `"wine"`, `"beer"` à lista `TERMOS_PROIBIDOS_VIDEO` em `pexels_story.py`.
- **Harmonia Visual Mantida**: A alternância rica de degradês (Dourado Âmbar e Visão Profética Roxo/Azul) e a liberdade de enquadramentos urbanos noturnos foram preservadas, garantindo que 100% dos vídeos de fundo sejam cinematográficos, elegantes e perfeitamente integrados à identidade visual da marca.

---

## 9. Otimização de Conversão e Capas Limpas (Palavra-Chave 'SABEDORIA')
**Contexto**: Estratégia de engajamento, legendas e legibilidade visual dos títulos das postagens.

### ANTES ❌
- **Capas Poluídas**: Textos e parágrafos longos ocupavam mais de 60% da tela do vídeo na capa, criando um "muro de texto" e dificultando a leitura rápida.
- **Frases Abstratas**: Textos poéticos/filosóficos desconectados de problemas concretos do cotidiano, gerando baixo índice de comentários.
---

## 10. Reformulação da Página Final do E-book / PDF Semanal
**Contexto**: A apresentação da oportunidade/método na última página do PDF gerado semanalmente (`gerador_pdf/gerar_pdf.py`).

### ANTES ❌
- **Venda Agressiva**: Continha selos promocionais chamativos como `"OFERTA EXCLUSIVA"`, `"De R$ 299 por R$ 79,90"` e `"ECONOMIA DE R$ 219,10"`, descaracterizando a elegância do e-book.
- **Botão Pouco Atraente**: Usava textos com foco comercial direto.

### DEPOIS ✅
- **Abordagem Sutil e Furtiva**: Mantido apenas o cabeçalho nobre `LEITORES DO CÓDIGO DA SABEDORIA` e um subtítulo convidativo (*"Uma descoberta nos bastidores para quem chegou até o final"*).
- **Texto Reflexivo e Empático**: Narrativa focada em pessoas e trabalhadores que buscam evoluir com método + inteligência artificial na prática.
- **CTA Chamativo em Dourado**: Adicionado o destaque `✦ DESBLOQUEIE SEU ACESSO COM 30% OFF ✦` com o cupom exclusivo **`SABEDORIA30`**.
- **Novo Botão**: Alterado com precisão para **`VER OPORTUNIDADE`** com link clicável direto.

---

## 11. Nova Paleta Oficial de Texto: Prata Metálico (`#D8DCE3`)
**Contexto**: A cor padrão dos textos e tipografia renderizados sobre as imagens e vídeos de todas as postagens da agenda.

### ANTES ❌
- Os textos usavam o branco puro `RGB: (255, 255, 255)` / `#FFFFFF`, gerando contraste comum e genérico.

### DEPOIS ✅
- **Prata Metálico Clássico (`#D8DCE3` / RGB: 216, 220, 227)**: Padronizado como a nova cor principal de texto em todo o sistema (`templates.py`, `efeitos.py`, `motor_visual.py`).
- **Harmonia nos Degradês**: A cor central/transição dos degradês do *Reels Leads* e *Story da Tarde* foi atualizada de branco para Prata Metálico, criando um visual sofisticado e premium.
- **Prata Fosco Suave (`#BEC4CE` / RGB: 190, 196, 206)**: Definido para subtítulos e elementos secundários.

---

## 12. Vídeos de Alta Retenção (3 Slides Rápidos / 12 a 15 Segundos)
**Contexto**: O tempo de duração total, ritmo de transição e quantidade de palavras nos formatos em vídeo (`pexels_story`, `pexels_story_noite`, `reels_conquistador` e `reels_leads`).

### ANTES ❌
- **Vídeos Longos e Lentos**: Os vídeos duravam entre 26 e 30 segundos (muito tempo para o padrão de consumo rápido do Instagram/Reels/Stories).
- **Textos Excessivos**: A IA pedia entre 10 e 15 palavras por slide, gerando quebras de linhas pesadas e perda de retenção.
- **Slides em Excesso**: Sequências com 4 a 6 slides que tornavam o vídeo arrastado.

### DEPOIS ✅
- **Exatamente 3 Slides Rápidos**: Fixado no prompt da IA (`gemini.py`) para gerar no máximo 3 frases cirúrgicas (*Slide 1: Gancho*, *Slide 2: Revelação/Ponte*, *Slide 3: Fechamento/CTA*).
- **Frases Curtas (5 a 8 palavras)**: Leitura rápida e visual limpo com soco de retenção.
- **Duração Otimizada (12s a 15s no máximo)**:
  - *Slide 1 (Gancho)*: Exibido por apenas 3.0s a 3.5s para prender o scroll no primeiro segundo.
  - *Slides 2 e 3*: Exibidos por ~4.0s a 4.5s cada.
- **Loop Perfeito**: O vídeo encerra com rapidez, estimulando o usuário a assistir novamente (aumentando a taxa de repetição e engajamento pelo algoritmo).
- *(O Story da Tarde foi preservado intacto).*

---

## 13. Desativação do TikTok e Proteção de Segredos
**Contexto**: Manutenção de código, limpeza de integrações e segurança de repositório.

### ANTES ❌
- Arquivos de autenticação, dependências e webhooks do TikTok ocupavam espaço no projeto sem uso ativo.
- Tokens de acesso estavam gravados com fallbacks no código.

### DEPOIS ✅
- **Remoção Limpa do TikTok**: Excluídos com segurança os arquivos `core/publisher/tiktok.py`, `autenticar_tiktok.py` e arquivos de verificação sem afetar nenhum outro módulo.
- **Leitura 100% via Variáveis de Ambiente**: Os tokens do Hugging Face/FLUX agora são lidos exclusivamente do `.env` / GitHub Secrets, garantindo conformidade total com o *GitHub Push Protection*.



