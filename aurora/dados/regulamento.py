from __future__ import annotations

import re

from aurora.dados.repositorio import normalizar

_TOPICOS: tuple[tuple[str, str], ...] = (
    ("piscina", "iv"),
    ("academia", "v"),
    ("brinquedoteca", "v"),
    ("playground", "v"),
    ("salao", "vi"),
    ("churrasqueira", "vi"),
    ("quadra", "vi"),
    ("portaria", "vii"),
    ("visitante", "vii"),
    ("encomenda", "vii"),
    ("animal", "viii"),
    ("cachorro", "viii"),
    ("pet", "viii"),
    ("mudanca", "ix"),
    ("obra", "x"),
    ("reforma", "x"),
    ("garagem", "xi"),
    ("veiculo", "xi"),
    ("lixo", "xii"),
    ("recicl", "xii"),
    ("multa", "xiii"),
    ("penalidade", "xiii"),
    ("silencio", "iii"),
    ("sossego", "iii"),
)


def selecionar_capitulo(pergunta: str, regulamento: str) -> str | None:
    pergunta_normalizada = normalizar(pergunta)
    pontuacao: dict[str, int] = {}
    for palavra, numero in _TOPICOS:
        if palavra in pergunta_normalizada:
            pontuacao[numero] = pontuacao.get(numero, 0) + 1
    if not pontuacao:
        return None
    numero = max(pontuacao, key=pontuacao.get)
    padrao = re.compile(rf"capitulo {re.escape(numero)}\b")
    return next(
        (
            corpo
            for titulo, corpo in _capitulos(regulamento)
            if padrao.search(normalizar(titulo))
        ),
        None,
    )


def _capitulos(regulamento: str) -> list[tuple[str, str]]:
    partes = re.split(r"(?=^## )", regulamento, flags=re.MULTILINE)
    return [
        (parte.splitlines()[0], parte.strip())
        for parte in partes
        if parte.startswith("## ")
    ]
