import json
import threading

from aurora.tools.reservas import cancelar_reserva
from aurora.tools.reservas import consultar_disponibilidade
from aurora.tools.reservas import reservar_area
from tests.suporte import contexto
from tests.suporte import repositorio_inicial


def test_data_ocupada_nao_revela_titular(tmp_path):
    repositorio = repositorio_inicial(tmp_path)
    sessao = contexto("101")

    disponibilidade = consultar_disponibilidade("salão de festas", "2030-03-16", sessao)
    reserva = reservar_area("salao-de-festas", "2030-03-16", sessao)
    texto = json.dumps({"disponibilidade": disponibilidade, "reserva": reserva}, ensure_ascii=False)

    assert disponibilidade == {"disponivel": False}
    assert reserva == {"ok": False, "motivo": "data_ocupada"}
    assert "RSV-4821" not in texto
    assert "302" not in texto
    assert sessao.pedidos == []
    assert [item.codigo for item in repositorio.listar_reservas("302")] == ["RSV-4821"]
    assert [item.codigo for item in repositorio.listar_reservas("101")] == ["RSV-1377"]


def test_cancela_somente_a_reserva_do_apartamento_da_sessao(tmp_path):
    repositorio = repositorio_inicial(tmp_path)
    sessao = contexto("101")

    alheia = cancelar_reserva("salão de festas", "2030-03-16", sessao)
    propria = cancelar_reserva("quadra", "2030-03-09", sessao)
    texto = json.dumps({"alheia": alheia, "propria": propria}, ensure_ascii=False)

    assert alheia == {"ok": False, "motivo": "reserva_nao_encontrada"}
    assert propria == {"ok": True, "area": "quadra", "data": "2030-03-09"}
    assert "RSV-4821" not in texto
    assert "RSV-1377" not in texto
    assert sessao.pedidos == []
    assert [item.codigo for item in repositorio.listar_reservas("302")] == ["RSV-4821"]
    assert repositorio.listar_reservas("101") == []
    assert repositorio.codigo_existe("RSV-1377")

    nova = reservar_area("quadra", "2030-03-09", sessao)
    assert nova["ok"] is True
    assert nova["codigo"] != "RSV-1377"
    assert repositorio.codigo_existe("RSV-1377")
    assert repositorio.codigo_existe(nova["codigo"])


def test_salao_so_grava_depois_da_confirmacao(tmp_path):
    repositorio = repositorio_inicial(tmp_path)
    pendente = contexto("101")

    primeiro = reservar_area("Salão de festas", "2030-04-20", pendente)

    assert primeiro["motivo"] == "confirmacao_pendente"
    assert pendente.pedidos[0]["payload"]["detalhes"] == {"area": "salao-de-festas", "data": "2030-04-20"}
    assert repositorio.listar_reservas("101")[0].codigo == "RSV-1377"

    negado = reservar_area("salao-de-festas", "2030-04-20", contexto("101", confirmado=False))
    assert negado == {"ok": False, "motivo": "confirmacao_negada"}
    assert len(repositorio.listar_reservas("101")) == 1

    gravada = reservar_area("salao-de-festas", "2030-04-20", contexto("101", confirmado=True))
    assert gravada["ok"] is True
    assert gravada["area"] == "salao-de-festas"
    assert gravada["data"] == "2030-04-20"
    salao = [
        item
        for item in repositorio.listar_reservas("101")
        if item.area == "salao-de-festas" and item.data == "2030-04-20"
    ]
    assert len(salao) == 1
    assert salao[0].codigo not in {"RSV-1377", "RSV-4821", "RSV-2950"}


def test_gravacao_simultanea_aceita_somente_uma_reserva(tmp_path):
    repositorio = repositorio_inicial(tmp_path)
    barreira = threading.Barrier(2)
    resultados: list[str | None] = []

    def gravar(apartamento: str) -> None:
        barreira.wait()
        resultados.append(repositorio.criar_reserva(apartamento, "salao-de-festas", "2030-05-11"))

    threads = [threading.Thread(target=gravar, args=(apartamento,)) for apartamento in ("101", "201")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert resultados.count(None) == 1
    assert len([codigo for codigo in resultados if codigo]) == 1
    salao = [
        reserva
        for apartamento in ("101", "201")
        for reserva in repositorio.listar_reservas(apartamento)
        if reserva.area == "salao-de-festas" and reserva.data == "2030-05-11"
    ]
    assert len(salao) == 1
