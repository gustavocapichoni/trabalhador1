# 🤖 Visão Geral Completa — Bot Instagram Autônomo

---

## 📅 Rotina Diária (O que o bot faz sozinho todo dia)

| Horário | Postagem | Descrição |
|---|---|---|
| **06:00** | 🎬 Reels Matinal | Storytelling com neurociência. Gancho → Loop → Valor → Validação |
| **06:05** | 📖 Story Manhã | Sequência de 3-4 frases para reflexão profunda |
| **07:00** | 🎥 Pexels Story | Vídeo B-roll cinematográfico com narração |
| **09:00** | 📑 Carrossel | 3 ou 5 slides alternados. Foco em salvamentos |
| **12:00** | 🎬 Reels Almoço | Mesmo formato do matinal, tema diferente |
| **17:00** | 📖 Story Tarde | Sequência de 2 frases. Quebra de expectativa |
| **18:00** | 🎬 Reels Noite | Arco narrativo do dia — reflexão do que viveu |
| **19:00** | 🎥 Pexels Story Noite | B-roll noturno. Tom contemplativo |
| **22:00** | 🎯 **Reels Conquistador** *(NOVO)* | Funil VSL de 7 passos. Atração pura de público |

**Total: 9 postagens/dia**

---

### 🌙 Tarefas de Manutenção (Automáticas, sem postar)
| Horário | Tarefa |
|---|---|
| **04:00** | 📥 Coleta silenciosa de métricas do Instagram |
| **07:00** | 🔑 Verificação de validade do token |
| **Toda Segunda 04:30** | 📊 Cruzamento de dados (Macro vs Micro) |
| **Toda Segunda 08:00** | 📋 Relatório semanal por e-mail |

---

## 🧠 Todas as Funcionalidades do Sistema

### ✅ Geração de Conteúdo (IA)
- **8 Temas**: Espiritualidade, Filosofia, Psicologia, Finanças, Liberdade, Conexões, Superação, Propósito
- **6 Sub-ângulos por tema**: Visões específicas e não-óbvias de cada assunto
- **5 Estilos de Copy**: Revelação científica, Quebra de ilusão, Diagnóstico cirúrgico, Alerta de perigo, Polarização
- **8 Ganchos Narrativos**: Frases de abertura poderosas para posts comuns
- **7 Ganchos Conquistador**: Ganchos agressivos para o VSL das 22h (*E se..., Por que não..., etc.*)
- **Sistema Anti-Repetição**: Salva os últimos 5 ângulos/ganchos/estilos usados e os exclui do próximo sorteio
- **Múltiplas chaves Gemini**: Rotação automática entre 5 chaves se uma esgotar a cota

### ✅ Visual e Mídia
- **4 fontes Premium**: Oswald, Inter, Playfair, Montserrat (baixadas automaticamente)
- **Imagens**: 3 níveis de fallback — IA (Pollinations) → Unsplash → Cor sólida
- **Vídeos Reels**: Slideshow 9:16 com música de fundo da biblioteca local
- **Vídeos Pexels**: B-roll real de bancos de vídeo com narração em texto

### ✅ Analytics — Inteligência de Dados
- **Coleta diária de métricas**: Likes, Comentários, Shares, Saves, Alcance, Impressões
- **Métricas avançadas**: Tempo médio assistido (Reels), Taps Back/Forward (Stories), Profile Visits, Follows
- **Score de Performance**: Fórmula ponderada que valoriza Retenção (Saves × 3, Shares × 2)
- **Cruzamento de Dados**: 5 períodos simultâneos — Semanal, Mensal, Trimestral, Semestral, Anual
- **Roleta Viciada**: Distribui os temas proporcionalmente ao score. Ex: Psicologia 50%, Finanças 30%, outros 20%
- **Hierarquia Macro > Micro**: O relatório Anual domina a estratégia; o Semanal refina a tática
- **Firebase (Firestore)**: Todos os dados gravados na nuvem automaticamente

### ✅ Reels Conquistador (22h) — *(Implementado Hoje)*
- **Loop Cego de Temas**: Ignora a Roleta Viciada e varre os 8 temas em sequência forçada
- **Funil VSL de 7 passos**: Dor → Causa Raiz → Solução → Benefício → Autoridade → CTA
- **Ganchos Agressivos exclusivos**: "E se...", "Você está fazendo errado...", "Será que..."
- **CTA de Ação direta**: Focado em clique/follow, sem perguntas reflexivas

### ✅ Publicação e Notificação
- **Publica automaticamente** via API oficial do Instagram Graph
- **E-mail de confirmação** após cada post bem-sucedido
- **E-mail de alerta** se der algum erro crítico
- **E-mail de alerta** se o token do Instagram estiver perto de vencer

---

## 🛠️ O Que Fizemos Hoje

1. **💀 Matamos o Analytics Diário Ansioso** — separamos Coleta (todo dia, silencioso) de Análise (só às Segundas)
2. **📊 Implantamos o Cruzamento de Dados** — 5 períodos analisados em paralelo com hierarquia Macro > Micro
3. **🎲 Criamos a Roleta Viciada** — distribuição proporcional de temas por score real de performance
4. **🔄 Sistema Anti-Repetição** — ângulos, ganchos e estilos não se repetem nos últimos 5 posts
5. **🎯 Reels Conquistador (22h)** — novo post diário com funil VSL de atração de público
6. **🔤 Corrigimos as fontes** — Oswald, Inter, Playfair e Montserrat agora baixam com sucesso

---

## ❓ Sua Pergunta: O bot evita repetir imagens e vídeos?

**Resposta: PARCIALMENTE.** Veja o que existe e o que falta:

| Camada | Status | Detalhe |
|---|---|---|
| Texto (ângulos/ganchos/estilos) | ✅ **Protegido** | Memória dos últimos 5. Não repete. |
| Música de fundo | ✅ **Sorteio aleatório** | Sorteia da biblioteca local a cada post |
| Imagem de fundo (Unsplash) | ⚠️ **Parcial** | A *busca* é a mesma por tema, mas o Unsplash retorna fotos diferentes a cada chamada |
| Vídeo de fundo (Pexels) | ⚠️ **Parcial** | Igual ao Unsplash — a query pode ser parecida mas o vídeo retornado varia |

> **Ponto cego**: se o bot postar 2 Reels sobre Psicologia no mesmo dia, a query do Unsplash/Pexels será idêntica e podem vir imagens parecidas. A correção seria salvar o histórico de `pexels_query` usadas no `estado.json` e forçar uma query diferente quando repetir.

---

## 🚀 Próximos Passos (em ordem de prioridade)

| # | Tarefa | Impacto |
|---|---|---|
| 1 | **Subir o código no GitHub** (adicionar `reels_conquistador` no cron job do `.yml`) | 🔴 Urgente — o Conquistador não vai rodar sem isso |
| 2 | **Anti-repetição de queries visuais** (Unsplash/Pexels) | 🟡 Médio — evitar grid repetitivo |
| 3 | **Integração de Narração** (ElevenLabs ou MiniMax/Hailuo) | 🟡 Médio — vídeos com voz humana |
| 4 | **Tabelas novas no Firebase** para métricas avançadas (navegação de Stories) | 🟡 Médio — já coletamos, mas a estrutura pode melhorar |

---

## ⚙️ O que adicionar no GitHub antes de subir

### 1. Secrets (Configurações → Secrets → Actions)
Nenhum secret novo foi adicionado hoje. Os que você precisa ter:
`GEMINI_API_KEY_1` até `GEMINI_API_KEY_5`---, `---PEXELS_API_KEY`, `---UNSPLASH_ACCESS_KEY`, `---IG_ACCESS_TOKEN`, `---IG_ACCOUNT_ID`, `---SMTP_EMAIL`, `---SMTP_PASSWORD`, `---NOTIFY_EMAIL`

### 2. Cron Job Novo no `.github/workflows/instagram_bot.yml`
Adicionar o agendamento das **22h (UTC-3 = 01:00 UTC)**:
```yaml
- cron: '0 1 * * *'   # 22:00 horário de Brasília → Reels Conquistador
```
E no `rodar_via_cron.py` adicionar o `elif` para esse horário chamar `reels_conquistador`.

### 3. Opção Manual no Workflow
Adicionar `reels_conquistador` na lista de `choices` do `workflow_dispatch` para você poder disparar manualmente.
