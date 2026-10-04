from __future__ import annotations

from collections.abc import AsyncIterator

from google.adk.runners import Runner
from google.genai import types

from aurora.constantes import ConstantesAplicacao
from aurora.sessao.confirmacao import Pendencia


async def executar(
    runner: Runner,
    session_id: str,
    mensagem: types.Content,
    invocation_id: str | None = None,
) -> AsyncIterator[object]:
    async for evento in runner.run_async(
        user_id=ConstantesAplicacao.USUARIO_SESSAO,
        session_id=session_id,
        new_message=mensagem,
        invocation_id=invocation_id,
    ):
        yield evento


def texto_da_resposta(eventos: list[object]) -> str:
    trechos = [
        parte.text
        for evento in eventos
        if getattr(evento, "content", None) is not None
        for parte in evento.content.parts or []
        if getattr(parte, "text", None) and not getattr(parte, "thought", False)
    ]
    return "\n".join(trecho.strip() for trecho in trechos if trecho.strip())


def mensagem_de_texto(texto: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=texto)])


def mensagem_de_confirmacao(pendente: Pendencia, confirmado: bool) -> types.Content:
    return types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id=pendente.id,
                    name=ConstantesAplicacao.NOME_CONFIRMACAO,
                    response={"confirmed": confirmado},
                )
            )
        ],
    )
