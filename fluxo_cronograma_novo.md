# Cronograma Estrategico do Bot - Nova Versao

> Atualizado em: Julho/2026
> Objetivo: Reduzir spam, recuperar entrega organica e criar funil diario de captacao de leads.

---

## MADRUGADA

### 04:00 - Analytics e Coleta Diaria (Todo dia)
Script: core/analytics/rodar_analytics.py --only-collect
Status: ATIVO
O que faz: Coleta metricas de todos os posts do Instagram e YouTube e salva no Firebase.
Nao gera recomendacoes. E a "alimentacao silenciosa" do sistema de inteligencia do bot.
Domingo: Alem da coleta, roda a Analise Semanal e envia o Relatorio por e-mail.

---

### 04:30 - Reels Leads - Capturador de Leads Diario (Todo dia)
Script: main.py --type reels_leads
Status: ATIVO
Estrategia:
- Roda durante o pico de visitas silenciosas do perfil (entre 03h e 06h).
- Funciona como um "trailer cinematografico" do PDF gratuito da semana.
- Gancho do dia: Estrutura de abertura sorteada (ex: pergunta que agride, dado estatistico).
- Sentimento do dia: A dor da Fase 4 e construida com base na emocao do dia.
- Tom: Mentor de desenvolvimento pessoal, nunca vendedor agressivo.
- CTA: Convite generoso e gratuito para o link na bio, sem pressao comercial.
- Usopp (10 Fases): Estrutura narrativa de persuasao completa e intacta.

---

### 05:00 - Gerador de PDF (So Domingo)
Script: gerador_pdf/gerador.py
Status: ATIVO (apenas Domingo)
O que faz: Gera o novo PDF gratuito da semana. Esse PDF e a oferta central de todos os
Reels Leads da semana seguinte.

---

## MANHA

### 06:00 - Reels da Manha (Seg a Dom)
Script: main.py --type reels
Status: ATIVO
O que faz: Primeiro post de alto impacto do dia. Focado em viralizar e atrair novos seguidores.
Usa o tema sequencial do dia com gancho, estilo e trilha sonora sorteados.

---

### 06:40 - Story da Manha (Seg a Dom)
Script: main.py --type story_manha
Status: ATIVO
O que faz: Sequencia de stories encadeados logo apos o Reels. Aprofunda a reflexao do tema do dia.

---

### 08:00 - Relatorio Semanal (So nas Segundas-feiras)
Script: core/reports/weekly.py
Status: ATIVO
O que faz: Envia um e-mail com o desempenho da semana (top posts, metricas, recomendacoes).

---

## TARDE

### 12:00 - Reels do Almoco (Todo dia)
Script: main.py --type reels
Status: ATIVO
O que faz: Segundo post de atracao do dia, no horario de almoco. Foca em viralizar no
feed de exploracao com tema diferente do da manha.

---

## NOITE

### 18:00 - Pexels Story Noturno - Storytelling (Todo dia)
Script: main.py --type pexels_story_noite
Status: ATIVO
Estrategia (Nova - Storytelling Cinematografico de 10 a 12 slides):
- Ato 1 (slides 1-3): O personagem em uma cena noturna concreta que o espectador reconhece.
- Ato 2 (slides 4-6): O conflito interno - o leitor pensa "isso sou eu".
- Ato 3 (slides 7-9): A virada, baseada nos livros de referencia do tema do dia.
- Ato 4 (slides 10-11): A promessa do amanha + CTA charmoso integrado a historia.
- Visual: Filtro warm_amber (tons ambar/dourado) ativado automaticamente para aconchego emocional.

---

### 22:00 - Reels Conquistador (Todo dia)
Script: main.py --type reels_conquistador
Status: ATIVO
O que faz: Post noturno focado em conquista de publico premium. Usa animacoes cinematicas e
estrutura de roteiro propria.

---

## POSTS DESATIVADOS

| Post                      | Horario | Motivo                                                              |
|---------------------------|---------|---------------------------------------------------------------------|
| Pexels Story Motivacional | 07:00   | Causava spam. Substituido pelo Storytelling das 18h.                |
| Carrossel                 | 09:00   | Menor desempenho. Sera usado manualmente uma vez por semana.        |
| Story da Tarde            | 17:00   | Baixo engajamento. Removido para reduzir carga diaria.              |
| Reels Noite               | 18:00   | Substituido pelo Pexels Story Noturno (Storytelling) no mesmo horario. |

---

## RESUMO DO NOVO VOLUME DIARIO

| Indicador                         | Antes           | Depois                        |
|-----------------------------------|-----------------|-------------------------------|
| Publicacoes por dia               | 9               | 5                             |
| Entrega organica                  | Prejudicada     | Recuperada                    |
| Captacao de leads durante a semana| 0 (so domingo)  | 1 por dia (todo dia as 04:30) |
| Pexels Story Noite                | B-roll generico | Storytelling com filtro ambar |

---

## VISAO DA SEMANA - QUADRO COMPLETO

| Horario | Seg          | Ter          | Qua          | Qui          | Sex          | Sab          | Dom                  |
|---------|--------------|--------------|--------------|--------------|--------------|--------------|----------------------|
| 04:00   | Coleta       | Coleta       | Coleta       | Coleta       | Coleta       | Coleta       | Coleta + Analise     |
| 04:30   | Leads        | Leads        | Leads        | Leads        | Leads        | Leads        | Leads                |
| 05:00   | -            | -            | -            | -            | -            | -            | Gera PDF             |
| 06:00   | Reels        | Reels        | Reels        | Reels        | Reels        | Reels        | Reels                |
| 06:40   | Story Manha  | Story Manha  | Story Manha  | Story Manha  | Story Manha  | Story Manha  | Story Manha          |
| 08:00   | Relatorio    | -            | -            | -            | -            | -            | -                    |
| 12:00   | Reels        | Reels        | Reels        | Reels        | Reels        | Reels        | Reels                |
| 18:00   | Storytelling | Storytelling | Storytelling | Storytelling | Storytelling | Storytelling | Storytelling         |
| 22:00   | Conquistador | Conquistador | Conquistador | Conquistador | Conquistador | Conquistador | Conquistador         |

Total por dia comum (Seg-Sab): 5 publicacoes no feed
Total no Domingo: 5 publicacoes + coleta estendida + analise + relatorio + PDF
