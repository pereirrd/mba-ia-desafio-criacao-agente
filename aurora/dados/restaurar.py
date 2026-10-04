from __future__ import annotations

from pathlib import Path

from aurora.config import AppConfig
from aurora.config import carregar_config
from aurora.dados.repositorio import Repositorio


def restaurar(config: AppConfig) -> None:
    config.var_dir.mkdir(parents=True, exist_ok=True)
    _remover_sqlite(config.condominio_db)
    repositorio = Repositorio(config.condominio_db)
    try:
        repositorio.carregar_json(config.dados_dir)
    finally:
        repositorio.fechar()


def abrir_repositorio(config: AppConfig) -> Repositorio:
    config.var_dir.mkdir(parents=True, exist_ok=True)
    novo = not config.condominio_db.exists()
    repositorio = Repositorio(config.condominio_db)
    if novo:
        repositorio.carregar_json(config.dados_dir)
    return repositorio


def _remover_sqlite(caminho: Path) -> None:
    for sufixo in ("", "-wal", "-shm"):
        alvo = Path(f"{caminho}{sufixo}")
        if alvo.exists():
            alvo.unlink()


def main() -> None:
    config = carregar_config()
    restaurar(config)
    print(f"Dados restaurados em {config.condominio_db}")
