from __future__ import annotations

from aurora.dados.acesso import obter_regulamento
from aurora.dados.regulamento import selecionar_capitulo


def consultar_regulamento(pergunta: str) -> dict:
    """Consulta somente o capítulo do regulamento interno que trata do assunto da pergunta."""
    texto = obter_regulamento().read_text(encoding="utf-8")
    trecho = selecionar_capitulo(pergunta, texto)
    if trecho is None:
        return {"encontrado": False}
    return {"encontrado": True, "trecho": trecho}
