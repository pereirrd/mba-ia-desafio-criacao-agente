from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from aurora.config import AppConfig
from aurora.constantes import ConstantesAplicacao
from aurora.dados.acesso import definir_dados
from aurora.dados.repositorio import Repositorio


def config_de_teste(tmp_path: Path) -> AppConfig:
    dados = Path(__file__).resolve().parents[1] / "dados"
    return AppConfig(
        modelo=ConstantesAplicacao.MODELO_PADRAO,
        raiz=tmp_path,
        dados_dir=dados,
        var_dir=tmp_path / "var",
        condominio_db=tmp_path / "var" / "condominio.db",
        sessoes_db=tmp_path / "var" / "sessoes.db",
        regulamento=dados / "regulamento.md",
    )


def repositorio_inicial(tmp_path: Path) -> Repositorio:
    config = config_de_teste(tmp_path)
    repositorio = Repositorio(config.condominio_db)
    repositorio.carregar_json(config.dados_dir)
    definir_dados(repositorio, config.regulamento)
    return repositorio


def contexto(apartamento: str, confirmado: bool | None = None) -> SimpleNamespace:
    estado = SimpleNamespace(
        state={ConstantesAplicacao.CHAVE_APARTAMENTO: apartamento},
        tool_confirmation=None if confirmado is None else SimpleNamespace(confirmed=confirmado),
        actions=SimpleNamespace(skip_summarization=False),
        pedidos=[],
    )

    def request_confirmation(*, hint: str | None = None, payload: dict | None = None) -> None:
        estado.pedidos.append({"hint": hint, "payload": payload})

    estado.request_confirmation = request_confirmation
    return estado
