from __future__ import annotations

from google.adk.tools.tool_context import ToolContext

from aurora.constantes import ConstantesErro
from aurora.constantes import ConstantesRequisicao
from aurora.dados.acesso import obter_repositorio
from aurora.tools.sessao import aguardando_confirmacao
from aurora.tools.sessao import apartamento_da_sessao
from aurora.tools.sessao import confirmacao_negada
from aurora.tools.sessao import data_valida
from aurora.tools.sessao import pedir_confirmacao


def listar_reservas(tool_context: ToolContext) -> dict:
    """Lista as reservas ativas do apartamento autenticado nesta sessão."""
    apartamento = apartamento_da_sessao(tool_context)
    if apartamento is None:
        return {"ok": False, "motivo": ConstantesErro.SESSAO_SEM_APARTAMENTO}
    reservas = obter_repositorio().listar_reservas(apartamento)
    return {
        "reservas": [
            {"codigo": reserva.codigo, "area": reserva.area, "data": reserva.data}
            for reserva in reservas
        ]
    }


def consultar_disponibilidade(area: str, data: str, tool_context: ToolContext) -> dict:
    """Informa se a área está livre ou ocupada na data, sem identificar o titular."""
    if apartamento_da_sessao(tool_context) is None:
        return {"ok": False, "motivo": ConstantesErro.SESSAO_SEM_APARTAMENTO}
    registro = obter_repositorio().resolver_area(area)
    if registro is None:
        return {"ok": False, "motivo": ConstantesErro.AREA_DESCONHECIDA}
    if not data_valida(data):
        return {"ok": False, "motivo": ConstantesErro.DATA_INVALIDA}
    return {"disponivel": obter_repositorio().data_livre(registro.id, data)}


def reservar_area(area: str, data: str, tool_context: ToolContext) -> dict:
    """Reserva a área na data para o apartamento autenticado. Área com taxa fica pendente de confirmação."""
    apartamento = apartamento_da_sessao(tool_context)
    if apartamento is None:
        return {"ok": False, "motivo": ConstantesErro.SESSAO_SEM_APARTAMENTO}
    registro = obter_repositorio().resolver_area(area)
    if registro is None:
        return {"ok": False, "motivo": ConstantesErro.AREA_DESCONHECIDA}
    if not data_valida(data):
        return {"ok": False, "motivo": ConstantesErro.DATA_INVALIDA}
    if not obter_repositorio().data_livre(registro.id, data):
        return {"ok": False, "motivo": ConstantesErro.DATA_OCUPADA}
    if registro.taxa > 0:
        if aguardando_confirmacao(tool_context):
            return pedir_confirmacao(
                tool_context,
                ConstantesRequisicao.ACAO_RESERVAR,
                {"area": registro.id, "data": data},
            )
        if confirmacao_negada(tool_context):
            return {"ok": False, "motivo": ConstantesErro.CONFIRMACAO_NEGADA}
    codigo = obter_repositorio().criar_reserva(apartamento, registro.id, data)
    if codigo is None:
        return {"ok": False, "motivo": ConstantesErro.DATA_OCUPADA}
    return {"ok": True, "codigo": codigo, "area": registro.id, "data": data}


def cancelar_reserva(area: str, data: str, tool_context: ToolContext) -> dict:
    """Cancela a reserva ativa do apartamento autenticado para a área e a data informadas."""
    apartamento = apartamento_da_sessao(tool_context)
    if apartamento is None:
        return {"ok": False, "motivo": ConstantesErro.SESSAO_SEM_APARTAMENTO}
    registro = obter_repositorio().resolver_area(area)
    if registro is None:
        return {"ok": False, "motivo": ConstantesErro.AREA_DESCONHECIDA}
    if not data_valida(data):
        return {"ok": False, "motivo": ConstantesErro.DATA_INVALIDA}
    cancelou = obter_repositorio().cancelar_reserva(apartamento, registro.id, data)
    if not cancelou:
        return {"ok": False, "motivo": ConstantesErro.RESERVA_NAO_ENCONTRADA}
    return {"ok": True, "area": registro.id, "data": data}
