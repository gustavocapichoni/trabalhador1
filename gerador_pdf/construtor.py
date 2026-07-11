"""
construtor.py - Construtor Visual do PDF

Design inspirado no gerador-de-pdf-cristão:
- Fundos com degrades vibrantes por pagina (ciano->azul, roxo->fucsia, etc.)
- Cards sólidos sem borda visivel, apenas preenchimento colorido
- Layout tipo Bento Grid na capa (card grande + cards menores)
- Texto bem espaçado, branco puro, tipografia limpa
- 3 paletas de cor rotativas por semana
"""
import os
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos


# ─── Paletas de Cor (espelhadas nos gradientes do App.tsx) ───
# Cada paleta tem cores para cada pagina, inspiradas nas classes CSS do original
TEMAS = [
    {   # Tema 1: Ciano/Azul/Roxo (semanas 1,4,7...)
        "nome": "ciano_azul",
        "paginas": [
            (22, 211, 238, 59, 130, 246),    # capa: ciano -> azul
            (59, 130, 246, 168, 85, 247),    # cap1: azul -> roxo
            (168, 85, 247, 217, 70, 239),    # cap2: roxo -> fucsia
            (217, 70, 239, 99, 102, 241),    # cap3: fucsia -> indigo
            (99, 102, 241, 37, 99, 235),     # citacao: indigo -> azul
            (99, 102, 241, 37, 99, 235),     # acao: indigo -> azul
            (15, 23, 42, 30, 58, 138),       # fechamento: slate -> azul escuro
        ],
        "cor_destaque": (22, 211, 238),
        "cor_card1": (22, 211, 238, 59, 130, 246),
        "cor_card2": (168, 85, 247, 244, 114, 182),
        "cor_card3": (99, 102, 241, 168, 85, 247),
        "cor_card4": (59, 130, 246, 99, 102, 241),
    },
    {   # Tema 2: Roxo/Laranja/Ouro (semanas 2,5,8...)
        "nome": "roxo_ouro",
        "paginas": [
            (124, 58, 237, 245, 101, 0),     # capa: roxo -> laranja
            (245, 101, 0, 234, 179, 8),      # cap1: laranja -> amarelo
            (234, 179, 8, 22, 163, 74),      # cap2: ouro -> verde
            (22, 163, 74, 6, 182, 212),      # cap3: verde -> ciano
            (6, 182, 212, 99, 102, 241),     # citacao: ciano -> indigo
            (6, 182, 212, 99, 102, 241),     # acao
            (15, 23, 42, 30, 58, 138),       # fechamento
        ],
        "cor_destaque": (245, 158, 11),
        "cor_card1": (124, 58, 237, 245, 101, 0),
        "cor_card2": (234, 179, 8, 22, 163, 74),
        "cor_card3": (22, 163, 74, 6, 182, 212),
        "cor_card4": (99, 102, 241, 124, 58, 237),
    },
    {   # Tema 3: Rosa/Coral/Indigo (semanas 3,6,9...)
        "nome": "rosa_indigo",
        "paginas": [
            (244, 114, 182, 239, 68, 68),    # capa: rosa -> vermelho
            (239, 68, 68, 245, 101, 0),      # cap1: vermelho -> laranja
            (245, 101, 0, 234, 179, 8),      # cap2: laranja -> ouro
            (234, 179, 8, 22, 163, 74),      # cap3: ouro -> verde
            (22, 163, 74, 6, 182, 212),      # citacao: verde -> ciano
            (22, 163, 74, 6, 182, 212),      # acao
            (15, 23, 42, 30, 58, 138),       # fechamento
        ],
        "cor_destaque": (244, 114, 182),
        "cor_card1": (244, 114, 182, 239, 68, 68),
        "cor_card2": (239, 68, 68, 245, 101, 0),
        "cor_card3": (99, 102, 241, 244, 114, 182),
        "cor_card4": (22, 163, 74, 6, 182, 212),
    }
]


def sanitizar(texto: str) -> str:
    """Remove caracteres fora do range latin-1 para o fpdf2."""
    mapa = {
        "\u201c": '"', "\u201d": '"',
        "\u2018": "'", "\u2019": "'",
        "\u2013": "-", "\u2014": "-",
        "\u2026": "...",
    }
    for orig, sub in mapa.items():
        texto = texto.replace(orig, sub)
    # Remove qualquer outro caracter nao suportado
    return texto.encode("latin-1", errors="ignore").decode("latin-1")


def escolher_tema() -> dict:
    semana = datetime.now().isocalendar()[1]
    tema = TEMAS[semana % 3]
    print(f"[Construtor] Tema visual da semana: '{tema['nome']}'")
    return tema


class PDFBuilder(FPDF):

    def __init__(self, tema: dict):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.tema = tema
        self.set_auto_page_break(auto=False)
        self.set_font("Helvetica", size=11)

    # ── Utilitários internos ──────────────────────────────────────────────────

    def _fundo_degradê(self, r1, g1, b1, r2, g2, b2, faixas=40):
        """Pinta o fundo da página com um degradê simulado de cima para baixo."""
        altura_faixa = 297 / faixas
        for i in range(faixas):
            t = i / (faixas - 1)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            self.set_fill_color(r, g, b)
            self.rect(0, i * altura_faixa, 210, altura_faixa + 0.5, style="F")

    def _card_solido(self, x, y, w, h, r1, g1, b1, r2=None, g2=None, b2=None, faixas=20):
        """Desenha um card com fundo degradê horizontal (ou sólido se só 1 cor)."""
        if r2 is None:
            self.set_fill_color(r1, g1, b1)
            self.rect(x, y, w, h, style="F")
        else:
            largura_faixa = w / faixas
            for i in range(faixas):
                t = i / (faixas - 1)
                r = int(r1 + (r2 - r1) * t)
                g = int(g1 + (g2 - g1) * t)
                b = int(b1 + (b2 - b1) * t)
                self.set_fill_color(r, g, b)
                self.rect(x + i * largura_faixa, y, largura_faixa + 0.5, h, style="F")

    def _titulo(self, texto, y, tamanho=22, cor=(255, 255, 255), negrito=True, largura=170, x=20):
        self.set_font("Helvetica", "B" if negrito else "", tamanho)
        self.set_text_color(*cor)
        self.set_xy(x, y)
        texto_limpo = sanitizar(texto)
        self.multi_cell(largura, tamanho * 0.48, texto_limpo, align="C",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        return self.get_y()

    def _paragrafo(self, texto, x, y, largura, tamanho=10, cor=(235, 245, 255), italico=False):
        """Renderiza um parágrafo e retorna a nova posição Y."""
        self.set_font("Helvetica", "I" if italico else "", tamanho)
        self.set_text_color(*cor)
        self.set_xy(x, y)
        texto_limpo = sanitizar(texto)
        self.multi_cell(largura, tamanho * 0.52, texto_limpo, align="J",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        return self.get_y()

    # ── Páginas ───────────────────────────────────────────────────────────────

    def construir_capa(self, conteudo: dict):
        """Página 1: Capa com titulo grande + Bento Grid de 4 cards."""
        self.add_page()
        t = self.tema
        r1, g1, b1, r2, g2, b2 = t["paginas"][0]
        self._fundo_degradê(r1, g1, b1, r2, g2, b2)

        # Titulo principal
        self._titulo(sanitizar(conteudo["titulo_pdf"]), 28, tamanho=26, negrito=True)
        self._titulo(sanitizar(conteudo["subtitulo_pdf"]), 60, tamanho=12,
                     cor=(220, 240, 255), negrito=False)

        # Bento Grid: card grande esquerda + 2 cards menores direita
        cards = conteudo.get("capa_cards", [])
        cores_cards = [
            t["cor_card1"], t["cor_card2"], t["cor_card3"], t["cor_card4"]
        ]

        # Card grande (A Nevoa) - coluna esquerda, altura total
        if len(cards) > 0:
            cr1, cg1, cb1, cr2, cg2, cb2 = cores_cards[0]
            self._card_solido(12, 78, 88, 178, cr1, cg1, cb1, cr2, cg2, cb2)
            # overlay semitransparente
            self.set_fill_color(0, 0, 0)
            self.set_alpha = lambda a: None  # fpdf2 sem suporte a alpha nativo
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(255, 255, 255)
            self.set_xy(16, 84)
            self.cell(80, 8, sanitizar(cards[0]["titulo"]))
            self._paragrafo(sanitizar(cards[0]["texto"]), 16, 96, 80, tamanho=9, cor=(240, 250, 255))

        # Card Solucao - canto superior direito
        if len(cards) > 1:
            cr1, cg1, cb1, cr2, cg2, cb2 = cores_cards[1]
            self._card_solido(105, 78, 93, 75, cr1, cg1, cb1, cr2, cg2, cb2)
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(255, 255, 255)
            self.set_xy(109, 84)
            self.cell(85, 8, sanitizar(cards[1]["titulo"]))
            self._paragrafo(sanitizar(cards[1]["texto"]), 109, 96, 85, tamanho=9)

        # Card Proposito - meio inferior direito
        if len(cards) > 2:
            cr1, cg1, cb1, cr2, cg2, cb2 = cores_cards[2]
            self._card_solido(105, 158, 93, 50, cr1, cg1, cb1, cr2, cg2, cb2)
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(255, 255, 255)
            self.set_xy(109, 163)
            self.cell(85, 8, sanitizar(cards[2]["titulo"]))
            self._paragrafo(sanitizar(cards[2]["texto"]), 109, 174, 85, tamanho=9)

        # Card Verdade - inferior direito (menor, com citacao)
        if len(cards) > 3:
            cr1, cg1, cb1, cr2, cg2, cb2 = cores_cards[3]
            self._card_solido(105, 213, 93, 43, cr1, cg1, cb1, cr2, cg2, cb2)
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(255, 255, 255)
            self.set_xy(109, 217)
            self.cell(85, 8, sanitizar(cards[3]["titulo"]))
            self._paragrafo(sanitizar(cards[3]["texto"]), 109, 227, 85, tamanho=8, italico=True)

        # Rodape
        self.set_font("Helvetica", "", 8)
        self.set_text_color(200, 220, 255)
        self.set_xy(20, 280)
        self.cell(170, 6, "Produzido com zelo, fe e proposito.", align="C")

    def construir_capitulo(self, capitulo: dict, indice_pagina: int):
        """Página de capítulo com fundo degradê único e texto narrativo arejado."""
        self.add_page()
        t = self.tema
        cores = t["paginas"][min(indice_pagina, len(t["paginas"]) - 1)]
        r1, g1, b1, r2, g2, b2 = cores
        self._fundo_degradê(r1, g1, b1, r2, g2, b2)

        # Label do capitulo
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(220, 240, 255)
        self.set_xy(20, 18)
        self.cell(170, 6, f"CAPITULO {capitulo['numero']}", align="C")

        # Linha fina
        self.set_draw_color(255, 255, 255)
        self.set_line_width(0.2)
        self.line(50, 28, 160, 28)

        # Titulo do capitulo
        self._titulo(sanitizar(capitulo["titulo"]), 32, tamanho=20, negrito=True)

        # Parágrafos bem espaçados - fonte maior para preencher a página
        y_atual = 58
        for i, paragrafo in enumerate(capitulo.get("paragrafos", [])):
            italico = (i == 1)
            cor = (245, 252, 255) if not italico else (225, 238, 255)
            y_atual = self._paragrafo(
                sanitizar(paragrafo), 18, y_atual, 174,
                tamanho=12, cor=cor, italico=italico
            )
            y_atual += 12  # espaço entre parágrafos

    def construir_pagina_citacao(self, citacao: str, indice_pagina: int):
        """Página de citação de destaque num card grande centralizado."""
        self.add_page()
        t = self.tema
        cores = t["paginas"][min(indice_pagina, len(t["paginas"]) - 1)]
        r1, g1, b1, r2, g2, b2 = cores
        self._fundo_degradê(r1, g1, b1, r2, g2, b2)

        self._titulo("A Verdade Inabalavel", 30, tamanho=18)

        # Card semi-transparente: usa cor de destaque bem escura (30% da cor original)
        rd, gd, bd = t["cor_destaque"]
        r_card = max(0, min(255, int(r2 * 0.5)))
        g_card = max(0, min(255, int(g2 * 0.5)))
        b_card = max(0, min(255, int(b2 * 0.5)))
        self._card_solido(15, 65, 180, 145, r_card, g_card, b_card)

        # Linha de borda sutil
        self.set_draw_color(255, 255, 255)
        self.set_line_width(0.2)
        self.rect(15, 65, 180, 145, style="D")

        self._paragrafo(
            f'"{sanitizar(citacao)}"',
            25, 82, 160, tamanho=13, cor=(245, 252, 255), italico=True
        )

    def construir_plano_acao(self, plano: dict, indice_pagina: int):
        """Página do Plano de Ação com cards horizontais modernos."""
        self.add_page()
        t = self.tema
        cores = t["paginas"][min(indice_pagina, len(t["paginas"]) - 1)]
        r1, g1, b1, r2, g2, b2 = cores
        self._fundo_degradê(r1, g1, b1, r2, g2, b2)

        # Titulo e subtitulo
        self._titulo(sanitizar(plano.get("titulo_secao", "Plano de Acao")), 22, tamanho=20)
        self._titulo(sanitizar(plano.get("subtitulo", "")), 46, tamanho=11,
                     cor=(210, 230, 255), negrito=False)

        # Cards horizontais dos passos
        cores_numeros = [
            (59, 130, 246),
            (168, 85, 247),
            (217, 70, 239),
            (99, 102, 241),
        ]
        y_atual = 60
        for i, passo in enumerate(plano.get("passos", [])):
            if y_atual > 258:
                break

            # Card de fundo usando a cor do destaque escurecida
            rd, gd, bd = t["cor_destaque"]
            r_card = max(0, min(255, int(r2 * 0.45)))
            g_card = max(0, min(255, int(g2 * 0.45)))
            b_card = max(0, min(255, int(b2 * 0.45)))
            self._card_solido(15, y_atual, 180, 48, r_card, g_card, b_card)
            self.set_draw_color(255, 255, 255)
            self.set_line_width(0.1)
            self.rect(15, y_atual, 180, 48, style="D")

            # Numero em quadrado colorido
            cr, cg, cb = cores_numeros[i % len(cores_numeros)]
            self._card_solido(19, y_atual + 6, 15, 15, cr, cg, cb)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(255, 255, 255)
            self.set_xy(19, y_atual + 8)
            self.cell(15, 8, str(passo["numero"]), align="C")

            # Titulo do passo
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(255, 255, 255)
            self.set_xy(38, y_atual + 8)
            self.cell(152, 8, sanitizar(passo["titulo"]))

            # Descricao
            self._paragrafo(
                sanitizar(passo["descricao"]), 38, y_atual + 20,
                152, tamanho=10, cor=(220, 238, 255)
            )

            y_atual += 55

        # Rodape
        self.set_font("Helvetica", "", 8)
        self.set_text_color(200, 220, 255)
        self.set_xy(20, 280)
        self.set_draw_color(200, 220, 255)
        self.set_line_width(0.1)
        self.line(20, 278, 190, 278)
        self.cell(170, 6, "Produzido com zelo, fe e proposito.", align="C")

    def construir_fechamento(self, fechamento: str, rodape: str, indice_pagina: int):
        """Última página: fechamento sóbrio e inspiracional."""
        self.add_page()
        t = self.tema
        cores = t["paginas"][min(indice_pagina, len(t["paginas"]) - 1)]
        r1, g1, b1, r2, g2, b2 = cores
        self._fundo_degradê(r1, g1, b1, r2, g2, b2)

        self._titulo("Agora e a sua vez.", 55, tamanho=22, negrito=True)

        # Linha divisora elegante
        cr, cg, cb = t["cor_destaque"]
        self.set_draw_color(cr, cg, cb)
        self.set_line_width(0.8)
        self.line(60, 90, 150, 90)

        self._paragrafo(sanitizar(fechamento), 20, 100, 170, tamanho=11,
                        cor=(235, 245, 255))

        self.set_font("Helvetica", "B", 9)
        self.set_text_color(180, 210, 255)
        self.set_xy(20, 272)
        self.cell(170, 6, sanitizar(rodape), align="C")


def construir_pdf(conteudo: dict, caminho_saida: str) -> str:
    """Monta o PDF completo e salva no caminho indicado."""
    print("[Construtor] Montando o PDF visual...")

    tema = escolher_tema()
    pdf = PDFBuilder(tema)

    pdf.construir_capa(conteudo)
    print("   Capa gerada.")

    for i, capitulo in enumerate(conteudo.get("capitulos", [])):
        pdf.construir_capitulo(capitulo, indice_pagina=i + 1)
        print(f"   Capitulo {capitulo['numero']} ({capitulo['titulo']}) gerado.")

    pdf.construir_pagina_citacao(conteudo.get("citacao_destaque", ""), indice_pagina=4)
    print("   Pagina de citacao gerada.")

    pdf.construir_plano_acao(conteudo.get("plano_acao", {}), indice_pagina=5)
    print("   Plano de acao gerado.")

    pdf.construir_fechamento(
        conteudo.get("fechamento", ""),
        conteudo.get("rodape", "Produzido com zelo, fe e proposito."),
        indice_pagina=6
    )
    print("   Fechamento gerado.")

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    pdf.output(caminho_saida)
    print(f"\n[Construtor] PDF salvo em: {caminho_saida}")
    return caminho_saida
