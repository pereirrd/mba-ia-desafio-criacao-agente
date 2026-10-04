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


def listar_visitantes(tool_context: ToolContext) -> dict:
    """Lista os visitantes autorizados do apartamento autenticado nesta sessão."""
    apartamento = apartamento_da_sessao(tool_context)
    if apartamento is None:
        return {"ok": False, "motivo": ConstantesErro.SESSAO_SEM_APARTAMENTO}
    visitantes = obter_repositorio().listar_visitantes(apartamento)
    return {
        "visitantes": [
            {"nome": visitante.nome, "data": visitante.data}
            for visitante in visitantes
        ]
    }


def autorizar_visitante(nome: str, data: str, tool_context: ToolContext) -> dict:
    """Autoriza a entrada de um visitante. A gravação só ocorre depois da confirmação do sistema."""
    apartamento = apartamento_da_sessao(tool_context)
    if apartamento is None:
        return {"ok": False, "motivo": ConstantesErro.SESSAO_SEM_APARTAMENTO}
    nome_limpo = nome.strip()
    if not nome_limpo:
        return {"ok": False, "motivo": ConstantesErro.NOME_INVALIDO}
    if not data_valida(data):
        return {"ok": False, "motivo": ConstantesErro.DATA_INVALIDA}
    if aguardando_confirmacao(tool_context):
        return pedir_confirmacao(
            tool_context,
            ConstantesRequisicao.ACAO_AUTORIZAR_VISITANTE,
            {"nome": nome_limpo, "data": data},
        )
    if confirmacao_negada(tool_context):
        return {"ok": False, "motivo": ConstantesErro.CONFIRMACAO_NEGADA}
    obter_repositorio().autorizar_visitante(apartamento, nome_limpo, data)
    return {"ok": True, "nome": nome_limpo, "data": data}
