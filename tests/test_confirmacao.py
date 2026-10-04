from google.adk.events.event import Event
from google.genai import types

from aurora.constantes import ConstantesAplicacao
from aurora.sessao.confirmacao import buscar_pendente
from aurora.sessao.confirmacao import listar_pendentes


def _pedido(confirmacao_id: str, invocation_id: str) -> Event:
    return Event(
        invocation_id=invocation_id,
        author="reservas",
        content=types.Content(
            role="model",
            parts=[
                types.Part(
                    function_call=types.FunctionCall(
                        id=confirmacao_id,
                        name=ConstantesAplicacao.NOME_CONFIRMACAO,
                        args={
                            "toolConfirmation": {
                                "hint": "confirme",
                                "payload": {
                                    "acao": "reservar_area",
                                    "detalhes": {"area": "salao-de-festas", "data": "2030-04-20"},
                                },
                            }
                        },
                    )
                )
            ],
        ),
    )


def _resposta(confirmacao_id: str, invocation_id: str) -> Event:
    return Event(
        invocation_id=invocation_id,
        author="user",
        content=types.Content(
            role="user",
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(
                        id=confirmacao_id,
                        name=ConstantesAplicacao.NOME_CONFIRMACAO,
                        response={"confirmed": True},
                    )
                )
            ],
        ),
    )


def test_confirmacao_respondida_deixa_de_estar_pendente():
    aberta = _pedido("conf-aberta", "inv-1")
    fechada = _pedido("conf-fechada", "inv-2")
    eventos = [aberta, fechada, _resposta("conf-fechada", "inv-2")]

    pendentes = listar_pendentes(eventos)

    assert [item.id for item in pendentes] == ["conf-aberta"]
    assert pendentes[0].acao == "reservar_area"
    assert pendentes[0].detalhes == {"area": "salao-de-festas", "data": "2030-04-20"}
    assert pendentes[0].invocation_id == "inv-1"
    assert buscar_pendente(eventos, "conf-fechada") is None
    assert buscar_pendente(eventos, "id-inexistente") is None
