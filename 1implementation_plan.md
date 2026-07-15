# Plano: Growth Analytics & Motor de Hipóteses Científicas

Este plano detalha a reestruturação do sistema de análises do nosso bot. O objetivo é transformá-lo em um cientista de dados autônomo: ele não apenas medirá curtidas e views, mas formulará teorias, executará experimentos controlados semanais, calculará a confiança estatística dos resultados e consolidará esse aprendizado em uma "Memória Estratégica" injetada na IA.

---

## 🛠️ 1. Nova Estrutura de Armazenamento e Processamento

Dividiremos as responsabilidades de análise em dois momentos para evitar ruídos diários na IA e garantir estabilidade.

### Ingestão Diária (Todos os dias às 04:00 BRT)
* **Ação:** O script `rodar_analytics.py --only-collect` é disparado pelo cron.
* **Processo:**
  1. Conecta ao Instagram Graph API.
  2. Coleta métricas brutas de todos os posts recentes do histórico (incluindo Stories antes que expirem).
  3. Salva os dados brutos no Firebase Firestore e no arquivo local `metricas.json`.
  4. **Nenhum cálculo analítico de recomendação é gerado aqui.**

### Fechamento Semanal (Todas as Segundas-feiras às 04:15 BRT)
* **Ação:** O script `rodar_analytics.py --full-analysis` é disparado logo após a coleta.
* **Processo:**
  1. Carrega todas as métricas históricas de posts salvos no Firebase.
  2. Calcula o **Growth Score** (métrica unificada de crescimento) de cada postagem.
  3. Calcula o **ICC (Índice de Conversão de Curiosidade)** de cada Tema, Gancho e CTA.
  4. Executa a análise estatística agregando os dados em 5 ciclos concêntricos:
     * **Semanal (7 dias)** — microajustes e tendências quentes.
     * **Mensal (30 dias)** — consolidação tática de médio prazo.
     * **Trimestral (90 dias)** — estabilização de temas.
     * **Semestral (180 dias)** — tendências de longo prazo.
     * **Anual (365 dias)** — âncora estratégica e essência da marca.
  5. Roda o **Motor de Hipóteses** para analisar experimentos e criar novas metas de teste.
  6. Consolida a memória e atualiza o arquivo `recomendacoes.json` que a IA consome.

---

## 📊 2. As Novas Métricas de Funil (Nível 1 ao 10)

Calcularemos no código as seguintes métricas a partir dos dados brutos coletados:

| Nível | Métrica | Fórmula de Cálculo no Código | O que mede / Diagnóstico |
|---|---|---|---|
| **Nível 1** | **CTR do Feed** | $\text{Views} / \text{Alcance}$ | Eficiência do **Hook / Slide 1**. Se baixo, o hook falhou. |
| **Nível 2** | **Retenção Média** | $\frac{\text{Tempo Médio Assistido (s)}}{\text{Duração Total do Reels (s)}} \times 100$ | Eficiência do roteiro (**Atos 2 e 3**). Se baixo, o meio do vídeo é chato. |
| **Nível 3** | **Engajamento de Valor** | $\text{Compartilhamentos} + \text{Salvamentos}$ | Utilidade real (**Ato 4**). Se baixo, a promessa final foi fraca. |
| **Nível 4** | **Taxa de Curiosidade** | $\text{Visitas ao Perfil} / \text{Views}$ | Se o vídeo despertou vontade de conhecer quem o criou. |
| **Nível 5** | **Conversão do Perfil** | $\text{Seguidores Ganhos} / \text{Visitas ao Perfil}$ | Se a Bio, foto de perfil e grid de posts convencem a seguir. |
| **Nível 6** | **Eficiência Geral** | $\text{Seguidores} / \text{Views}$ | Custo de Aquisição Orgânica de Seguidor. |
| **Nível 7** | **Eficiência por Tema** | Agrupamento de Níveis 1-6 por Tema | Identifica quais temas geram atração (views) vs conversão (seguidores). |
| **Nível 8** | **Eficiência do Hook** | Agrupamento de Níveis 1-6 por Estilo de Gancho | Ex: *Perguntas que Gridem* vs *Paradoxos*. |
| **Nível 9** | **Eficiência do CTA** | Agrupamento de Níveis 1-6 por Tipo de Chamada | Ex: *CTA de Comentário* vs *CTA de Seguir*. |
| **Nível 10**| **ICC (Santo Graal)** | $\text{Seguidores} / \text{Visitas}$ (filtrado por Tema) | Descobre qual assunto transforma curiosos em seguidores reais. |

### 🏆 A Nota Final: Growth Score
Cada post receberá um score de sucesso unificado:
$$\text{Growth Score} = 0.35 \times \text{Conversão do Perfil} + 0.20 \times \text{Taxa de Curiosidade} + 0.20 \times \text{Retenção Média} + 0.15 \times \frac{\text{Shares}}{\text{Views}} + 0.10 \times \frac{\text{Saves}}{\text{Views}}$$

---

## 🧠 3. O Motor de Hipóteses Científicas

Criaremos o arquivo [`core/analytics/hipoteses.py`](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/analytics/hipoteses.py) para gerenciar o conhecimento estratégico de forma estatística.

### Estrutura de uma Hipótese em Código
As hipóteses serão gravadas na coleção `hipoteses_estratega` no Firebase / arquivo local:
```json
{
  "id": "gancho_pergunta_vs_afirmacao",
  "descricao": "Ganchos no formato 'Pergunta que Agride' geram mais retenção de 3s do que 'Afirmação que Choca'.",
  "tipo_teste": "gancho",
  "variavel_a": "pergunta_que_agride",
  "variavel_b": "afirmacao_que_choca",
  "metrica_alvo": "retencao_inicial",
  "amostra_a": 28,
  "amostra_b": 24,
  "media_a": 0.45,
  "media_b": 0.31,
  "confianca_estatistica": 0.94,
  "status": "confirmada"  // "pouca_evidencia", "confirmada", "rejeitada"
}
```

### O Ciclo Científico Semanal:
1. **Cálculo da Confiança Estatística (Teste de Significado):**
   * O robô utilizará um cálculo simplificado de desvio padrão e intervalo de confiança:
     $$\text{Confiança} = 1 - \text{p-value}$$
   * Se $\text{Confiança} \ge 90\%$ e as amostras A e B forem $\ge 15$, a hipótese é **confirmada** (se A > B) ou **rejeitada** (se B $\ge$ A).
   * Se a amostra for insuficiente, ela permanece em `"pouca_evidencia"`.
2. **Definição de Experimento Ativo:**
   * Se houver uma hipótese importante em `"pouca_evidencia"`, o bot ativa um **Experimento de Campo**.
   * Durante essa semana, ele força o gerador de prompts (`prompts.py`) a revezar rigorosamente entre a Variavel A e a Variavel B para obter dados limpos de comparação.
3. **Consolidação na Memória Estratégica:**
   * Hipóteses **confirmadas** são injetadas permanentemente nas instruções do Gemini:
     * *Exemplo:* `[MEMÓRIA ESTRATÉGICA CONSOLIDADA] Hipótese Validada: Ganchos em formato de 'Desafio' geram 22% mais conversão. Regra: Priorize esse formato no Ato 1 sempre que possível.`
     * *Exemplo:* `[MEMÓRIA ESTRATÉGICA CONSOLIDADA] Hipótese Validada: Posts de Psicologia convertem 14% menos visitas em seguidores que Filosofia. Regra: Ao falar de Psicologia, use um tom mais filosófico e reflexivo para mitigar a perda.`
   * Nunca mais o robô testará o que já foi provado estatisticamente.

---

## 🗺️ 4. Cronograma de Implementação e Impacto no Bot

### Fase 1: Ingestão de Dados e Novas Métricas (Dias 1 a 3)
* **Mudança no Trabalhador:** O robô passa a calcular o **Growth Score** e as 10 novas métricas de funil na segunda-feira.
* **Onde muda:** [`coletor.py`](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/analytics/coletor.py), [`analisador.py`](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/analytics/analisador.py).
* **Armazenamento:** Atualização do schema no Firebase com novos campos de cálculo e o campo `growth_score` no histórico.

### Fase 2: Divisão Diária/Semanal no Cron (Dia 4)
* **Mudança no Trabalhador:** Cron diário executa apenas coleta rápida (Stories e Reels da véspera). Cron de segunda-feira roda a análise pesada e ajusta as diretrizes do Gemini.
* **Onde muda:** [`rodar_via_cron.py`](file:///c:/Users/kali/Desktop/my-bot-instagram-main/rodar_via_cron.py), [`rodar_analytics.py`](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/analytics/rodar_analytics.py).

### Fase 3: Motor de Hipóteses e Memória Estratégica (Dias 5 a 7)
* **Mudança no Trabalhador:** O robô avalia a confiança de suas teorias, seleciona testes semanais e insere regras estritas de copy baseadas no que foi provado cientificamente.
* **Onde muda:** Novo arquivo [`hipoteses.py`](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/analytics/hipoteses.py) e integrações no [`prompts.py`](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/ai/prompts.py).

### Futuro (500+ postagens): Modelo Preditivo
* Com os dados consolidados pelo Motor de Hipóteses e Growth Score, implementaremos um analisador preditivo que estima a probabilidade de um roteiro cru atingir determinada performance antes mesmo de ser postado.
