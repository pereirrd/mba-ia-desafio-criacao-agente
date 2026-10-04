from __future__ import annotations

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Request

from aurora.api.esquemas import ConfirmacaoPendenteResponse
from aurora.api.esquemas import ConfirmacaoRequest
from aurora.api.esquemas import CriarSessaoRequest
from aurora.api.esquemas import CriarSessaoResponse
from aurora.api.esquemas import MensagemRequest
from aurora.api.esquemas import MensagemResponse
from aurora.api.esquemas import ReservaResponse
from aurora.api.esquemas import VisitanteResponse
from aurora.runtime import Runtime
from aurora.constantes import ConstantesAplicacao
from aurora.constantes import ConstantesErro
from aurora.sessao.confirmacao import buscar_pendente
from aurora.sessao.confirmacao import listar_pendentes
from aurora.sessao.execucao import executar
from aurora.sessao.execucao import mensagem_de_confirmacao
from aurora.sessao.execucao import mensagem_de_texto
from aurora.sessao.execucao import texto_da_resposta

router = APIRouter()


def _runtime(request: Request) -> Runtime:
    return request.app.state.runtime


async def _sessao_ou_404(runtime: Runtime, session_id: str):
    sessao = await runtime.session_service.get_session(
        app_name=ConstantesAplicacao.NOME_APP,
        user_id=ConstantesAplicacao.USUARIO_SESSAO,
        session_id=session_id,
    )
    if sessao is None:
        raise HTTPException(status_code=404, detail=ConstantesErro.SESSAO_NAO_ENCONTRADA)
    return sessao


def _resposta(texto: str, eventos: list) -> MensagemResponse:
    return MensagemResponse(
        resposta=texto,
        confirmacoes_pendentes=[
            ConfirmacaoPendenteResponse(id=pendente.id, acao=pendente.acao, detalhes=pendente.detalhes)
            for pendente in listar_pendentes(eventos)
        ],
    )


@router.post("/sessoes", status_code=201, response_model=CriarSessaoResponse)
async def criar_sessao(corpo: CriarSessaoRequest, request: Request) -> CriarSessaoResponse:
    runtime = _runtime(request)
    if not runtime.repositorio.apartamento_existe(corpo.apartamento):
        raise HTTPException(status_code=404, detail=ConstantesErro.APARTAMENTO_NAO_ENCONTRADO)
    sessao = await runtime.session_service.create_session(
        app_name=ConstantesAplicacao.NOME_APP,
        user_id=ConstantesAplicacao.USUARIO_SESSAO,
        state={ConstantesAplicacao.CHAVE_APARTAMENTO: corpo.apartamento},
    )
    return CriarSessaoResponse(session_id=sessao.id)


@router.post("/sessoes/{session_id}/mensagens", response_model=MensagemResponse)
async def enviar_mensagem(session_id: str, corpo: MensagemRequest, request: Request) -> MensagemResponse:
    runtime = _runtime(request)
    await _sessao_ou_404(runtime, session_id)
    eventos = [
        evento
        async for evento in executar(runtime.runner, session_id, mensagem_de_texto(corpo.texto))
    ]
    sessao = await _sessao_ou_404(runtime, session_id)
    return _resposta(texto_da_resposta(eventos), sessao.events)


@router.post("/sessoes/{session_id}/confirmacoes", response_model=MensagemResponse)
async def responder_confirmacao(
    session_id: str,
    corpo: ConfirmacaoRequest,
    request: Request,
) -> MensagemResponse:
    runtime = _runtime(request)
    sessao = await _sessao_ou_404(runtime, session_id)
    pendente = buscar_pendente(sessao.events, corpo.id)
    if pendente is None:
        raise HTTPException(status_code=409, detail=ConstantesErro.CONFIRMACAO_NAO_PENDENTE)
    eventos = [
        evento
        async for evento in executar(
            runtime.runner,
            session_id,
            mensagem_de_confirmacao(pendente, corpo.confirmado),
            invocation_id=pendente.invocation_id or None,
        )
    ]
    sessao = await _sessao_ou_404(runtime, session_id)
    return _resposta(texto_da_resposta(eventos), sessao.events)


@router.get("/sessoes/{session_id}/eventos")
async def listar_eventos(session_id: str, request: Request) -> list[dict]:
    runtime = _runtime(request)
    sessao = await _sessao_ou_404(runtime, session_id)
    return [evento.model_dump(mode="json") for evento in sessao.events]


@router.get("/apartamentos/{numero}/reservas", response_model=list[ReservaResponse])
def listar_reservas(numero: str, request: Request) -> list[ReservaResponse]:
    runtime = _runtime(request)
    return [
        ReservaResponse(codigo=reserva.codigo, area=reserva.area, data=reserva.data)
        for reserva in runtime.repositorio.listar_reservas(numero)
    ]


@router.get("/apartamentos/{numero}/visitantes", response_model=list[VisitanteResponse])
def listar_visitantes(numero: str, request: Request) -> list[VisitanteResponse]:
    runtime = _runtime(request)
    return [
        VisitanteResponse(nome=visitante.nome, data=visitante.data)
        for visitante in runtime.repositorio.listar_visitantes(numero)
    ]
