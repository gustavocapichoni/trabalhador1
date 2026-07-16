# O Roteiro Visceral — Reels Conquistador

O formato `reels_conquistador` será desconectado da estrutura padrão do bot para se tornar um canal de expressão pura da sua visão de mundo em 8 atos sequenciais, usando a fonte **Playfair** e uma estética de texto em degradê.

> [!IMPORTANT]
> **Revisão Necessária:** Verifique a nova paleta de cores do degradê e a estrutura narrativa no prompt abaixo. Se estiver 100% de acordo, autorize para começarmos a escrever os códigos.

## Proposed Changes

### 1. Efeito Degradê e Animação (`core/media/pexels_story.py`)
Criaremos uma nova função gráfica para pintar os textos do Conquistador com um degradê tricolor suave, em vez de uma cor sólida. A animação "máquina de escrever" (letra por letra) continuará existindo para prender a atenção.
- **Top:** Roxo Neon
- **Centro:** Branco (para garantir legibilidade)
- **Base:** Azul Elétrico Esfumaçado
*Técnica: Máscara alpha na biblioteca PIL para recortar um fundo degradê gerado matematicamente com formato das letras.*

```python
# A fonte será forçada para Playfair apenas para o Conquistador
estilo_do_dia = "Playfair" if tipo == "reels_conquistador" else obter_fonte_do_dia()
```

### 2. O Novo Prompt do Criador (`core/ai/gemini.py`)
Substituiremos a linha 375 (`elif tipo == "reels_conquistador":`) por esta diretriz profunda:

```python
    elif tipo == "reels_conquistador":

        prompt = f"""
        Você é a manifestação de uma filosofia de vida profunda, focada na verdade absoluta e na liberdade.
        Sua visão não é materialista. Seus pilares são: Família, Amizade, Igualdade, Verdade e Liberdade.

        INSPIRAÇÕES LITERÁRIAS OBRIGATÓRIAS (Suas mensagens devem soar como uma fusão de):
        - "Armadilhas da Mente" (Augusto Cury) - Foco na gestão da emoção e consciência.
        - Livros Sapienciais: "Provérbios e Sabedoria de Salomão".
        - Evangelhos puros: A sabedoria de Jesus (Evangelho de Mateus e João) e textos apócrifos.
        - "O Poder da Ação" (Paulo Vieira) - Foco em despertar, consistência e execução.

        O QUE VOCÊ REPUDIA (NUNCA USE OU VALORIZE):
        - Pessoas arrogantes e soberbas.
        - Filosofia barata de autoajuda vazia.
        - Amor falso e interesses materialistas.
        - Traição de princípios.

        ESTRUTURA OBRIGATÓRIA DO VÍDEO (EXATAMENTE 8 CENAS EM SEQUÊNCIA):
        O vídeo será uma reflexão contínua, profunda e de alto impacto emocional. 
        Não use gatilhos de vendas. Não peça para seguir. NÃO USE CTA (Call to Action) em nenhuma cena. Apenas entregue a verdade nua e crua e vá embora.

        CRIE UM VÍDEO MANIFESTO EM 8 CENAS CURTAS (Máximo de 15 palavras por cena):
        - Cena 1: Uma abertura reflexiva ou um soco no estômago sobre a realidade/verdade.
        - Cena 2: O aprofundamento do choque moral ou emocional (a armadilha que vivemos).
        - Cena 3: A sabedoria atemporal que revela a ilusão (influência de Salomão/Jesus).
        - Cena 4: O resgate dos valores reais (família, igualdade, amigos verdadeiros).
        - Cena 5: O despertar para a ação correta e corajosa (Poder da Ação).
        - Cena 6: A ruptura com o falso (rejeição da arrogância e da filosofia barata).
        - Cena 7: A reconexão com a verdadeira essência e liberdade da consciência.
        - Cena 8: A frase final de impacto. Cortante, reflexiva, que deixe a mente do leitor ecoando. (NUNCA PEÇA AÇÃO AQUI, apenas termine a reflexão).

        LEGENDA DO POST:
        - Máximo de 3 linhas de reflexão poética e direta sobre o tema abordado.
        - SEM HASHTAGS.
        - SEM PEDIDO DE COMENTÁRIO OU COMPARTILHAMENTO.

        Responda APENAS em formato JSON válido assim:
        {{
          "pexels_query": "3 palavras em INGLÊS para buscar vídeo de fundo profundo (ex: calm mountain, rain forest, morning sun)",
          "slides": [
            "Texto da Cena 1",
            "Texto da Cena 2",
            "Texto da Cena 3",
            "Texto da Cena 4",
            "Texto da Cena 5",
            "Texto da Cena 6",
            "Texto da Cena 7",
            "Texto da Cena 8"
          ],
          "legenda": "Sua legenda aqui"
        }}
        """
```

## Open Questions
- Devo aplicar o Degradê Neon/Azul apenas nas fontes do formato `reels_conquistador` ou você quer esse visual de luxo vazando para os demais Reels diários do bot? 

## Verification Plan
1. Injetar a lógica matemática de matriz de cores para degradê no `pexels_story.py` (usando `numpy` para transição Roxo->Branco->Azul).
2. Forçar a tipografia `Playfair`.
3. Atualizar o prompt do Gemini isolando os CTAs.
4. Executar um dry-run exportando um frame de teste `.jpg` ou `.mp4` para verificarmos a estética do degradê.
