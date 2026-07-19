# Fluxo & Cronograma Real do Sistema
> Gerado com dados 100% verificados no código-fonte de cada arquivo.

---

## Como o Sistema é Ativado

```
  cron-job.org (externo)
       │  Dispara o workflow manualmente em cada horário configurado
       ▼
  GitHub Actions  (.github/workflows/instagram_bot.yml)
       │  Só tem trigger: workflow_dispatch (ativação manual)
       │  NÃO tem on: schedule no YAML
       ▼
  rodar_via_cron.py
       │  Lê a hora atual no Brasil (UTC-3)
       │  Decide o que executar com if/elif hora == X
       ▼
  Script alvo (main.py, gerador.py, rodar_analytics.py, etc.)
```

---

## Cronograma Completo por Hora e Dia

> Fonte: `rodar_via_cron.py` (arquivo que roda em produção)

| Hora BRT | Seg | Ter | Qua | Qui | Sex | Sáb | Dom |
|----------|-----|-----|-----|-----|-----|-----|-----|
| **04:00** | Coleta | Coleta | Coleta | Coleta | Coleta | Coleta | Coleta + Análise Semanal + Relatório |
| **05:00** | — | — | — | — | — | — | Gera PDF |
| **06:00** | Reels + Story Manhã | Reels + Story Manhã | Reels + Story Manhã | Reels + Story Manhã | Reels + Story Manhã | Reels + Story Manhã | Reels Leads |
| **07:00** | Pexels Story | Pexels Story | Pexels Story | Pexels Story | Pexels Story | Pexels Story | Pexels Story |
| **08:00** | — | — | — | — | — | — | — |
| **09:00** | Carousel | Carousel | Carousel | Carousel | Carousel | Carousel | Carousel |
| **12:00** | Reels | Reels | Reels | Reels | Reels | Reels | Reels |
| **17:00** | Story Tarde | Story Tarde | Story Tarde | Story Tarde | Story Tarde | Story Tarde | Story Tarde |
| **18:00** | Reels Noite | Reels Noite | Reels Noite | Reels Noite | Reels Noite | Reels Noite | Reels Noite |
| **19:00** | Pexels Story Noite | Pexels Story Noite | Pexels Story Noite | Pexels Story Noite | Pexels Story Noite | Pexels Story Noite | Pexels Story Noite |
| **22:00** | Conquistador | Conquistador | Conquistador | Conquistador | Conquistador | Conquistador | Conquistador |

> **Total por dia comum (Seg–Sáb):** 9 publicações  
> **Total no Domingo:** 9 publicações + coleta estendida + análise + relatório + PDF

---

## Detalhamento de Cada Tarefa

### 🔵 04:00 — Coleta Diária (Todo dia)
**Script:** `core/analytics/rodar_analytics.py --only-collect`  
**O que faz:**
1. `coletor.py` → busca posts do `historico_posts` no Firebase + busca posts recentes pela API do Instagram → coleta métricas de engajamento (likes, views, shares, saves, reach, watch_time) → salva em `metricas_posts` no Firebase + `analytics/dados/metricas.json` local
2. `coletor_youtube.py` → busca vídeos do canal via YouTube Search API → coleta métricas da Data API (views, likes) + Analytics API (minutosAssistidos, averageViewDuration) → salva em `metricas_posts_youtube` no Firebase + `analytics/dados/metricas_youtube.json` local  
**⚠️ NÃO gera recomendações.** Apenas coleta dados brutos.

### 🟣 04:00 — Análise Semanal + Relatório (Só Domingo)
**Scripts:** `analisador_semanal.py` + `core/reports/weekly.py`  
**O que faz:**
1. `analisador_semanal.py` → lê últimos 7 dias de `metricas.json` → calcula ranking por tema, formato, estilo, horário e dia da semana → salva `analytics/dados/recomendacoes_semanais.json`
2. `weekly.py` → lê `historico_posts` no Firebase + métricas locais → monta relatório com top 5 por views/likes/shares/saves + top 6 horários de ouro → envia por e-mail SMTP

> **NOTA:** O `analisador_semanal.py` usa `calcular_score()` (score legado), não o `growth_score`. O `ajustador.py` (que usa growth_score e gera `recomendacoes.json`) **não é chamado automaticamente** — só é chamado manualmente via `workflow_dispatch → analytics`.

### 🟢 05:00 — Gerador de PDF (Só Domingo)
**Script:** `gerador_pdf/gerador.py`  
**O que faz (em sequência):**
1. `decisor.py` → lê `recomendacoes.json` (⚠️ com bug na chave — veja falhas) → escolhe tema e livro (com anti-repetição via `historico_pdfs` no Firebase)
2. `conteudo.py` → gera o conteúdo narrativo completo via Gemini API
3. `gerar_pdf.py` → monta o PDF visual com capa, capítulos e plano de ação usando fpdf2 e as fontes locais
4. `uploader.py` → copia o PDF para o repositório `gustavo_8k` clonado → faz `git push` → retorna URL pública via jsDelivr com hash do commit
5. Registra campanha em `campanhas` (Firebase) + histórico em `historico_pdfs` (Firebase)
6. Salva `gerador_pdf/output/ultimo_conteudo.json` (lido pelo reels_leads às 06:00)

### 🟡 06:00 Domingo — Reels Leads (Só Domingo)
**Script:** `main.py --type reels_leads`  
**Depende de:** `gerador_pdf/output/ultimo_conteudo.json` gerado às 05:00  
**O que faz:**
1. `gemini.py` → lê `ultimo_conteudo.json` via `leitor_pdf.py` → busca últimos 6 posts de `historico_reels_leads` (Firebase) para anti-repetição → gera roteiro de 5 fases com Gemini
2. `pexels_story.py` → busca clipes na API do Pexels (com anti-repetição via `historico_midia` no Firebase) → monta vídeo animado MP4 com texto e música
3. `uploader.py` → sobe o MP4 para catbox.moe (fallbacks: litterbox → tmpfiles → file.io → transfer.sh)
4. `instagram.py` → publica como Reels no Instagram
5. `main.py → registrar_postagem()` → salva em `historico_posts` + `historico_reels_leads` (Firebase)

### 🔴 06:00 Seg–Sáb — Reels + Story Manhã
**Scripts:** `main.py --type reels` + `main.py --type story_manha` (com 10s de intervalo)  
**O que faz (Reels):**
1. `gemini.py` → lê analytics (`recomendacoes.json` + `recomendacoes_semanais.json`) → lê hipóteses confirmadas (Firebase) → lê histórico do tema (Firebase) → lê Olhos da Rede (RSS + Google Trends + YouTube API) → seleciona tema sequencial do dia → gera roteiro com 4–8 slides
2. `motor_visual.py` → busca imagem fundo (Unsplash → Pexels → Pixabay → Pollinations IA → biblioteca local) com anti-repetição via `historico_midia` (Firebase) → aplica gradient, fonte do dia, logo → salva JPGs
3. `reels.py` → monta slideshow com animação do dia + música da fila (`fila_musicas_musicas` no Firebase) → renderiza MP4 com MoviePy
4. Sobe, publica no Instagram + YouTube (se `POSTAR_NO_YOUTUBE=true`)

**O que faz (Story Manhã — story_manha):**
1. `gemini.py` → gera sequência de 4–8 frases conectadas
2. `motor_visual.py` → gera slides (sem vídeo final)
3. `reels.py` → monta sem vídeo de encerramento (`incluir_video_final=False`)
4. `instagram.py` → publica como stories em sequência (MP4, com aguardar processamento entre cada)

### 🟠 07:00 — Pexels Story (Todo dia)
**Script:** `main.py --type pexels_story`  
**O que faz:** Igual ao Reels Leads mas sem o PDF. Busca clipes do Pexels, gera vídeo B-roll narrativo com slides animados.

### 🟤 09:00 — Carousel (Todo dia)
**Script:** `main.py --type carousel`  
**O que faz:**
1. `gemini.py` → gera título + 5–8 slides de texto + slide de CTA
2. `motor_visual.py` → gera imagem panorâmica larga (2160×1080) e faz panning para cada slide (1080×1080) com efeito contínuo → salva JPGs numerados
3. `instagram.py` → sobe cada slide como filho de carrossel → aguarda processamento → publica

### 🔵 12:00 — Reels Almoço (Todo dia)
**Script:** `main.py --type reels`  
**Mesmo fluxo do Reels 06:00.** Tema continuado do dia (usa `tema_do_dia` salvo no estado).

### 🟢 17:00 — Story Tarde (Todo dia)
**Script:** `main.py --type story_tarde`  
**O que faz:**
1. `gemini.py` → gera 2 frases (slides separados)
2. `motor_visual.py → _gerar_estatico()` → gera 2 JPGs (1080×1920)
3. `reels.py → gerar_video_story_individual()` → converte cada JPG em MP4 de 10s com música contínua (música começa em 0s no slide 1, em 10s no slide 2)
4. `instagram.py` → publica os 2 stories em sequência com 15s de espera entre eles

### 🔴 18:00 — Reels Noite (Todo dia)
**Script:** `main.py --type reels_noite`  
**Mesmo fluxo do Reels 06:00.** Gera um Reels narrativo diferente, usando o mesmo tema do dia.

### 🟠 19:00 — Pexels Story Noite (Todo dia)
**Script:** `main.py --type pexels_story_noite`  
**Mesmo fluxo do pexels_story das 07:00**, mas identificado como formato "noite" para diferenciação de contexto.

### 🟣 22:00 — Reels Conquistador (Todo dia)
**Script:** `main.py --type reels_conquistador`  
**Diferente dos outros Reels:**
- **NÃO usa analytics** para escolher tema — usa um **ciclo cego fixo** pelos 8 temas em ordem sequencial (estado: `index_conquistador`)
- Objetivo: atingir públicos novos com cada tema rotacionado
- Usa `pexels_story.py` para gerar vídeo B-roll cinematográfico
- Publica no Instagram às 22h para capturar audiência noturna

---

## Dependências Entre Etapas

```
[Domingo 04:00 — Coleta]
     └──→ metricas.json (local) + Firebase
              └──→ [Domingo 04:00 — Análise Semanal]
                       └──→ recomendacoes_semanais.json (local)
                                └──→ [Todo dia 06:00–22:00 — gemini.py lê este arquivo]

[Domingo 04:00 — Relatório]
     └──→ E-mail enviado (não bloqueia nada)

[Domingo 05:00 — PDF]
     └──→ ultimo_conteudo.json (local, salvo no Git pelo workflow)
              └──→ [Domingo 06:00 — Reels Leads]

[Execução Manual: analytics via workflow_dispatch]
     └──→ rodar_analytics.py (sem --only-collect)
              ├──→ recomendacoes.json (local)
              │        └──→ [Todo dia 06:00–22:00 — gemini.py lê para roleta de temas]
              │        └──→ [Domingo 05:00 — decisor.py lê para escolher tema do PDF]
              └──→ motor_hipoteses.py → memoria_estrategica.json + Firebase
                       └──→ [gemini.py injecta hipóteses confirmadas no prompt]
```

> **PONTO CRÍTICO:** O `recomendacoes.json` (usado pelo `gemini.py` para a **roleta viciada de temas**) só é gerado quando o analytics COMPLETO (`rodar_analytics.py` sem `--only-collect`) roda. Isso **não acontece automaticamente** no cronograma atual — apenas na execução manual via `workflow_dispatch → analytics`. A coleta das 04:00 roda com `--only-collect` e **não** atualiza as recomendações.

---

## Tipos de Post e Seus Geradores

| Tipo | Gerador Visual | Publicador | Formato Final |
|------|---------------|-----------|---------------|
| `story` | `motor_visual.py → _gerar_estatico()` | `instagram.py` tipo STORIES | JPG → Instagram Story |
| `story_manha` | `motor_visual.py → _gerar_reels()` + `reels.py` | `instagram.py` tipo STORIES sequencial | MP4 (sem vídeo final) |
| `story_tarde` | `motor_visual.py → _gerar_estatico()` + `reels.py → gerar_video_story_individual()` | `instagram.py` tipo STORIES sequencial | MP4 (10s por slide) |
| `carousel` | `motor_visual.py → _gerar_carrossel()` | `instagram.py` tipo CAROUSEL | JPGs filhos → Carrossel |
| `reels` | `motor_visual.py → _gerar_reels()` + `reels.py → gerar_video_reels()` | `instagram.py` tipo REELS | MP4 animado |
| `reels_noite` | Mesmo do reels | `instagram.py` tipo REELS | MP4 animado |
| `pexels_story` | `pexels_story.py` (clipes Pexels) | `instagram.py` tipo REELS | MP4 B-roll |
| `pexels_story_noite` | Mesmo do pexels_story | `instagram.py` tipo REELS | MP4 B-roll |
| `reels_conquistador` | `pexels_story.py` (modo conquistador) | `instagram.py` tipo REELS | MP4 B-roll |
| `reels_leads` | `pexels_story.py` (modo leads, bitrate 3000k) | `instagram.py` tipo REELS | MP4 (max ~67MB) |

---

## Estado do Bot — O que Cada Chave Guarda

> Fonte: `estado_migrado.json` (cópia local do `bot_config/app_state` no Firebase)

| Chave no estado | O que controla |
|-----------------|----------------|
| `tema_do_dia` | Tema ativo para o dia (ex: `"espiritualidade"`) |
| `data_tema_do_dia` | Data de quando o tema do dia foi definido |
| `index_tema_diario` | Próximo índice na lista de temas (rotação sequencial) |
| `index_conquistador` | Próximo índice do ciclo cego do Conquistador |
| `indice_gancho` | Índice do próximo gancho (posts normais) |
| `indice_gancho_conquistador` | Índice do próximo gancho (Conquistador) |
| `indice_cta` | Índice do próximo CTA a usar |
| `historico_angulos` | Últimos 25 sub-ângulos usados (para anti-repetição) |
| `historico_estilos` | Últimos estilos sorteados |
| `historico_midia` | Últimas 15 mídias usadas (IDs Pexels/Unsplash/Pixabay) |
| `fila_musicas_musicas` | Fila embaralhada de músicas do Instagram (sem repetição) |
| `fila_musicas_musicas-youtube` | Fila embaralhada de músicas do YouTube |

---

## Fluxo de Upload de Mídia (Todo Reels/Story em Vídeo)

```
MP4 gerado localmente no runner
    │
    ▼ uploader.py (5 serviços em cadeia)
    ├── catbox.moe (até 200MB, permanente) ──→ sucesso → retorna URL
    ├── litterbox.catbox.moe (até 1GB, 72h) ──→ sucesso → retorna URL
    ├── tmpfiles.org (extrai link /dl/ via regex) ──→ sucesso → retorna URL
    ├── file.io (1 download apenas) ──→ sucesso → retorna URL
    └── transfer.sh (14 dias) ──→ sucesso → retorna URL
    
URL pública retornada
    │
    ▼ instagram.py
    ├── Cria container (POST /media com video_url=URL)
    ├── Aguarda processamento (poll status_code a cada 8s, até 25 tentativas = 200s)
    └── Publica (POST /media_publish com creation_id)
```

---

## O que é Salvo no Git a Cada Execução

> Fonte: `.github/workflows/instagram_bot.yml` linhas 124–133

```yaml
git add gerador_pdf/output/ultimo_conteudo.json || true
git commit -m "chore: atualizar estado [skip ci]"
git pull --rebase origin main || true
git push
```

**Apenas `ultimo_conteudo.json` é salvo.**
O `estado_migrado.json` **não é salvo** — ele é gerado em tempo de execução como cópia do Firebase.
O `analytics/dados/` **não é salvo** — regenerado a cada coleta via Firebase.
