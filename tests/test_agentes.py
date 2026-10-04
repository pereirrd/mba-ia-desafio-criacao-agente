import inspect

from aurora.agentes.fabrica import criar_principal
from aurora.agentes.instrucoes import INSTRUCAO_PRINCIPAL
from aurora.constantes import ConstantesAplicacao
from aurora.tools.regulamento import consultar_regulamento
from aurora.tools.reservas import cancelar_reserva
from aurora.tools.reservas import consultar_disponibilidade
from aurora.tools.reservas import listar_reservas
from aurora.tools.reservas import reservar_area
from aurora.tools.visitantes import autorizar_visitante
from aurora.tools.visitantes import listar_visitantes


def test_principal_nao_carrega_regulamento_e_tem_especialistas():
    principal = criar_principal(ConstantesAplicacao.MODELO_PADRAO)
    ferramentas = {
        getattr(ferramenta, "__name__", getattr(ferramenta, "name", ""))
        for especialista in principal.sub_agents
        for ferramenta in especialista.tools
    }

    assert principal.instruction == INSTRUCAO_PRINCIPAL
    assert "Capítulo" not in principal.instruction
    assert "Art." not in principal.instruction
    assert "das 9h às 20h" not in principal.instruction
    assert len(principal.sub_agents) >= 2
    assert {"reservar_area", "autorizar_visitante", "consultar_regulamento"} <= ferramentas
    assert principal.tools == []
    for ferramenta in (
        listar_reservas,
        consultar_disponibilidade,
        reservar_area,
        cancelar_reserva,
        listar_visitantes,
        autorizar_visitante,
        consultar_regulamento,
    ):
        assert "apartamento" not in inspect.signature(ferramenta).parameters
