from __future__ import annotations

from pathlib import Path

from aurora.dados.repositorio import Repositorio

_repositorio: Repositorio | None = None
_regulamento: Path | None = None


def definir_dados(repositorio: Repositorio, regulamento: Path) -> None:
    global _repositorio, _regulamento
    _repositorio = repositorio
    _regulamento = regulamento


def obter_repositorio() -> Repositorio:
    if _repositorio is None:
        raise RuntimeError("repositorio nao inicializado")
    return _repositorio


def obter_regulamento() -> Path:
    if _regulamento is None:
        raise RuntimeError("regulamento nao inicializado")
    return _regulamento
