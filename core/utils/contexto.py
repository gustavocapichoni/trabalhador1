# -*- coding: utf-8 -*-
"""
Módulo utilitário para gerenciamento de contexto de postagem (core/utils/contexto.py)
Armazena variáveis de execução temporárias para enriquecer o Firestore com metadados do post.
"""

_contexto = {}

def registrar_contexto(chave, valor):
    global _contexto
    _contexto[chave] = valor

def obter_contexto(chave, default=""):
    global _contexto
    return _contexto.get(chave, default)

def limpar_contexto():
    global _contexto
    _contexto.clear()
