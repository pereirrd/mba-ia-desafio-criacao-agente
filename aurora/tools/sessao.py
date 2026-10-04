from __future__ import annotations

import re

from google.adk.tools.tool_context import ToolContext

from aurora.constantes import ConstantesAplicacao
from aurora.constantes import ConstantesErro

_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def apartamento_da_sessao(tool_context: ToolContext) -> str | None:
    valor = tool_context.state.get(ConstantesAplicacao.CHAVE_APARTAMENTO)
    if not isinstance(valor, str) or not valor.strip():
        return None
    return valor


def data_valida(data: str) -> bool:
    return _DATA.fullmatch(data) is not None


def pedir_confirmacao(tool_context: ToolContext, acao: str, detalhes: dict[str, str]) -> dict[str, str]:
    tool_context.request_confirmation(
        hint=f"Confirme a acao {acao}.",
        payload={"acao": acao, "detalhes": detalhes},
    )
    tool_context.actions.skip_summarization = True
    return {"ok": False, "motivo": ConstantesErro.CONFIRMACAO_PENDENTE}


def confirmacao_negada(tool_context: ToolContext) -> bool:
    confirmacao = tool_context.tool_confirmation
    return confirmacao is not None and not confirmacao.confirmed


def aguardando_confirmacao(tool_context: ToolContext) -> bool:
    return tool_context.tool_confirmation is None
