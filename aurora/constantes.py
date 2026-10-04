class ConstantesAplicacao:
    NOME_APP = "residencial_aurora"
    USUARIO_SESSAO = "morador"
    CHAVE_APARTAMENTO = "apartamento"
    NOME_CONFIRMACAO = "adk_request_confirmation"
    HOST = "0.0.0.0"
    PORTA = 8000
    MODELO_PADRAO = "gemini-2.5-flash"
    STATUS_ATIVA = "ativa"
    STATUS_CANCELADA = "cancelada"

    def __init__(self) -> None:
        raise TypeError("ConstantesAplicacao nao deve ser instanciada")


class ConstantesErro:
    APARTAMENTO_NAO_ENCONTRADO = "apartamento nao encontrado"
    SESSAO_NAO_ENCONTRADA = "sessao nao encontrada"
    CONFIRMACAO_NAO_PENDENTE = "nao existe confirmacao pendente com esse id nesta sessao"
    SESSAO_SEM_APARTAMENTO = "sessao_sem_apartamento"
    AREA_DESCONHECIDA = "area_desconhecida"
    DATA_INVALIDA = "data_invalida"
    DATA_OCUPADA = "data_ocupada"
    RESERVA_NAO_ENCONTRADA = "reserva_nao_encontrada"
    CONFIRMACAO_PENDENTE = "confirmacao_pendente"
    CONFIRMACAO_NEGADA = "confirmacao_negada"
    NOME_INVALIDO = "nome_invalido"

    def __init__(self) -> None:
        raise TypeError("ConstantesErro nao deve ser instanciada")


class ConstantesRequisicao:
    ACAO_RESERVAR = "reservar_area"
    ACAO_AUTORIZAR_VISITANTE = "autorizar_visitante"

    def __init__(self) -> None:
        raise TypeError("ConstantesRequisicao nao deve ser instanciada")


class ConstantesTrace:
    LOGGER = "aurora"

    def __init__(self) -> None:
        raise TypeError("ConstantesTrace nao deve ser instanciada")
