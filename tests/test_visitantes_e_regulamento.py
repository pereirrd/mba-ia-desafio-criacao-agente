from aurora.tools.regulamento import consultar_regulamento
from aurora.tools.visitantes import autorizar_visitante
from tests.suporte import contexto
from tests.suporte import repositorio_inicial


def test_visitante_so_grava_depois_da_confirmacao(tmp_path):
    repositorio = repositorio_inicial(tmp_path)
    sessao = contexto("101")

    pendente = autorizar_visitante("Joana Ribeiro", "2030-04-21", sessao)

    assert pendente["motivo"] == "confirmacao_pendente"
    assert sessao.pedidos[0]["payload"]["detalhes"] == {"nome": "Joana Ribeiro", "data": "2030-04-21"}
    assert repositorio.listar_visitantes("101") == []

    negado = autorizar_visitante("Joana Ribeiro", "2030-04-21", contexto("101", confirmado=False))
    assert negado["motivo"] == "confirmacao_negada"
    assert repositorio.listar_visitantes("101") == []

    gravado = autorizar_visitante("Joana Ribeiro", "2030-04-21", contexto("101", confirmado=True))
    assert gravado == {"ok": True, "nome": "Joana Ribeiro", "data": "2030-04-21"}
    visitantes = repositorio.listar_visitantes("101")
    assert [(item.nome, item.data) for item in visitantes] == [("Joana Ribeiro", "2030-04-21")]
    assert all(item.nome != "Marina Duarte" for item in visitantes)


def test_duvida_da_piscina_devolve_somente_o_capitulo_iv(tmp_path):
    repositorio_inicial(tmp_path)

    resposta = consultar_regulamento("Até que horas a piscina funciona aos domingos?")
    trecho = resposta["trecho"]

    assert resposta["encontrado"] is True
    assert trecho.count("## Capítulo") == 1
    assert "Capítulo IV" in trecho
    assert "das 9h às 20h" in trecho
    assert "Disposições gerais" not in trecho
    assert "plástico bolha lilás" not in trecho
    assert "lona xadrez vermelha" not in trecho
    assert "coleira refletiva cor de mostarda" not in trecho
