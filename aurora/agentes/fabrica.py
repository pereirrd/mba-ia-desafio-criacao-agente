from google.adk import Agent
from google.genai import types

from aurora.agentes.instrucoes import INSTRUCAO_PRINCIPAL
from aurora.agentes.instrucoes import INSTRUCAO_REGULAMENTO
from aurora.agentes.instrucoes import INSTRUCAO_RESERVAS
from aurora.agentes.instrucoes import INSTRUCAO_VISITANTES
from aurora.tools.regulamento import consultar_regulamento
from aurora.tools.reservas import cancelar_reserva
from aurora.tools.reservas import consultar_disponibilidade
from aurora.tools.reservas import listar_reservas
from aurora.tools.reservas import reservar_area
from aurora.tools.visitantes import autorizar_visitante
from aurora.tools.visitantes import listar_visitantes


def criar_principal(modelo: str) -> Agent:
    geracao = types.GenerateContentConfig(temperature=0)
    reservas = Agent(
        name="reservas",
        model=modelo,
        description="Reserva, cancela e consulta a agenda do salão, da churrasqueira e da quadra.",
        instruction=INSTRUCAO_RESERVAS,
        tools=[listar_reservas, consultar_disponibilidade, reservar_area, cancelar_reserva],
        disallow_transfer_to_peers=True,
        generate_content_config=geracao,
    )
    visitantes = Agent(
        name="visitantes",
        model=modelo,
        description="Lista e autoriza visitantes do apartamento autenticado.",
        instruction=INSTRUCAO_VISITANTES,
        tools=[listar_visitantes, autorizar_visitante],
        disallow_transfer_to_peers=True,
        generate_content_config=geracao,
    )
    regulamento = Agent(
        name="regulamento",
        model=modelo,
        description="Responde dúvidas do regulamento interno consultando um único capítulo.",
        instruction=INSTRUCAO_REGULAMENTO,
        tools=[consultar_regulamento],
        disallow_transfer_to_peers=True,
        generate_content_config=geracao,
    )
    return Agent(
        name="principal",
        model=modelo,
        description="Assistente do Residencial Aurora. Encaminha o morador aos especialistas.",
        instruction=INSTRUCAO_PRINCIPAL,
        sub_agents=[reservas, visitantes, regulamento],
        generate_content_config=geracao,
    )
