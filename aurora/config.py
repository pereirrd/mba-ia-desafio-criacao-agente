from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from aurora.constantes import ConstantesAplicacao


@dataclass(frozen=True)
class AppConfig:
    modelo: str
    raiz: Path
    dados_dir: Path
    var_dir: Path
    condominio_db: Path
    sessoes_db: Path
    regulamento: Path


def raiz_do_projeto() -> Path:
    return Path(__file__).resolve().parents[1]


def carregar_config() -> AppConfig:
    load_dotenv(raiz_do_projeto() / ".env")
    chave = os.getenv("GOOGLE_API_KEY", "").strip()
    if chave:
        os.environ["GOOGLE_API_KEY"] = chave
    modelo = os.getenv("GEMINI_MODEL", "").strip() or ConstantesAplicacao.MODELO_PADRAO
    raiz = raiz_do_projeto()
    var_dir = raiz / "var"
    return AppConfig(
        modelo=modelo,
        raiz=raiz,
        dados_dir=raiz / "dados",
        var_dir=var_dir,
        condominio_db=var_dir / "condominio.db",
        sessoes_db=var_dir / "sessoes.db",
        regulamento=raiz / "dados" / "regulamento.md",
    )
