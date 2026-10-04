from fastapi.testclient import TestClient

from aurora.aplicacao import criar_aplicacao
from tests.suporte import config_de_teste


def test_api_dados_iniciais_sessao_e_confirmacao_inexistente(tmp_path):
    cliente = TestClient(criar_aplicacao(config_de_teste(tmp_path)))

    reservas = cliente.get("/apartamentos/101/reservas")
    visitantes = cliente.get("/apartamentos/302/visitantes")
    assert reservas.status_code == 200
    assert reservas.json() == [{"codigo": "RSV-1377", "area": "quadra", "data": "2030-03-09"}]
    assert visitantes.status_code == 200
    assert visitantes.json() == [{"nome": "Marina Duarte", "data": "2030-03-16"}]

    criada = cliente.post("/sessoes", json={"apartamento": "101"})
    assert criada.status_code == 201
    session_id = criada.json()["session_id"]

    eventos = cliente.get(f"/sessoes/{session_id}/eventos")
    assert eventos.status_code == 200
    assert isinstance(eventos.json(), list)

    inexistente = cliente.get("/sessoes/sessao-inexistente/eventos")
    assert inexistente.status_code == 404

    confirmacao = cliente.post(
        f"/sessoes/{session_id}/confirmacoes",
        json={"id": "id-inexistente", "confirmado": True},
    )
    assert confirmacao.status_code == 409
    assert cliente.get("/apartamentos/101/reservas").json() == [
        {"codigo": "RSV-1377", "area": "quadra", "data": "2030-03-09"}
    ]
