from pydantic import BaseModel
from pydantic import Field


class CriarSessaoRequest(BaseModel):
    apartamento: str


class CriarSessaoResponse(BaseModel):
    session_id: str


class MensagemRequest(BaseModel):
    texto: str


class ConfirmacaoRequest(BaseModel):
    id: str
    confirmado: bool


class ConfirmacaoPendenteResponse(BaseModel):
    id: str
    acao: str
    detalhes: dict[str, str]


class MensagemResponse(BaseModel):
    resposta: str
    confirmacoes_pendentes: list[ConfirmacaoPendenteResponse] = Field(default_factory=list)


class ReservaResponse(BaseModel):
    codigo: str
    area: str
    data: str


class VisitanteResponse(BaseModel):
    nome: str
    data: str
