# Gerador de PDF Semanal

Este módulo é responsável por gerar o PDF da semana, fazer upload para o Firebase Storage
e registrar a campanha no Firestore para que a Landing Page puxe automaticamente.

## Estrutura

```
gerador_pdf/
├── gerador.py          → Script principal (gera o PDF)
├── uploader.py         → Faz o upload pro Firebase Storage e salva no Firestore
├── conteudo.py         → Lógica de geração de conteúdo (via Gemini AI)
├── requirements.txt    → Dependências Python
└── README.md           → Este arquivo
```

## Como funciona

1. O `gerador.py` chama o `conteudo.py` para gerar o texto do PDF via IA.
2. O `gerador.py` monta o PDF visual usando a biblioteca `fpdf2`.
3. O `uploader.py` faz o upload do PDF para o Firebase Storage e gera o link público.
4. O `uploader.py` salva o título e o link na coleção `campanhas` do Firestore.
5. A Landing Page lê automaticamente essa coleção e exibe o PDF correto da semana.

## Como rodar

```bash
python gerador.py
```
