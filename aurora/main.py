from __future__ import annotations

import uvicorn

from aurora.aplicacao import criar_aplicacao
from aurora.config import carregar_config
from aurora.constantes import ConstantesAplicacao

config = carregar_config()
app = criar_aplicacao(config)


def main() -> None:
    uvicorn.run(
        "aurora.main:app",
        host=ConstantesAplicacao.HOST,
        port=ConstantesAplicacao.PORTA,
    )
