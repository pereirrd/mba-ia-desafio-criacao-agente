from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Sequence

from aurora.constantes import ConstantesAplicacao


@dataclass(frozen=True)
class Pendencia:
    id: str
    acao: str
    detalhes: dict[str, str]
    invocation_id: str


def listar_pendentes(eventos: Sequence[Any]) -> list[Pendencia]:
    respondidos = {
        resposta.id
        for evento in eventos
        for resposta in evento.get_function_responses()
        if resposta.name == ConstantesAplicacao.NOME_CONFIRMACAO and resposta.id
    }
    return [
        _pendencia(evento.invocation_id, chamada)
        for evento in eventos
        for chamada in evento.get_function_calls()
        if chamada.name == ConstantesAplicacao.NOME_CONFIRMACAO
        and chamada.id
        and chamada.id not in respondidos
    ]


def buscar_pendente(eventos: Sequence[Any], confirmacao_id: str) -> Pendencia | None:
    return next((pendente for pendente in listar_pendentes(eventos) if pendente.id == confirmacao_id), None)


def _pendencia(invocation_id: str, chamada: Any) -> Pendencia:
    args = dict(chamada.args or {})
    ferramenta = args.get("toolConfirmation") or args.get("tool_confirmation") or {}
    if not isinstance(ferramenta, dict):
        ferramenta = {}
    payload = ferramenta.get("payload") or {}
    if not isinstance(payload, dict):
        payload = {}
    detalhes = payload.get("detalhes") or {}
    if not isinstance(detalhes, dict):
        detalhes = {}
    acao = payload.get("acao")
    if not isinstance(acao, str) or not acao:
        original = args.get("originalFunctionCall") or {}
        acao = original.get("name", "") if isinstance(original, dict) else ""
    return Pendencia(
        id=chamada.id,
        acao=acao,
        detalhes={str(chave): str(valor) for chave, valor in detalhes.items()},
        invocation_id=invocation_id or "",
    )
