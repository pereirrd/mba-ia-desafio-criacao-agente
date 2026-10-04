# Assistente do Residencial Aurora

API do assistente dos moradores. O modelo conduz a conversa. As regras de reserva, visitante, confirmação e isolamento de apartamento ficam no código.

## Arquitetura

O morador fala com o agente `principal`. Ele não executa reserva, visitante nem consulta ao regulamento: transfere o turno para um especialista. A transferência é o mecanismo do ADK (`sub_agents`), e cada especialista tem `disallow_transfer_to_peers=True` para não passar o turno a um par. A fábrica está em [aurora/agentes/fabrica.py](aurora/agentes/fabrica.py).

- **principal** — recebe a mensagem, identifica o assunto e transfere. A instrução está em `INSTRUCAO_PRINCIPAL` e não contém o regulamento. Não tem tools de dados.
- **reservas** — lista as reservas do apartamento da sessão, informa se uma data está livre ou ocupada, reserva e cancela. É especialista porque a agenda e a cobrança são um fluxo próprio, com confirmação só quando a área tem taxa.
- **visitantes** — lista e autoriza visitantes do apartamento da sessão. É especialista porque liberar entrada é outra ação, e ela sempre pede confirmação.
- **regulamento** — responde dúvidas chamando `consultar_regulamento`. É especialista para o texto do regulamento entrar só no evento dessa consulta, e não na instrução do principal nem nos outros turnos.

Reservas e visitantes são lidos e gravados pelas tools em [aurora/tools/reservas.py](aurora/tools/reservas.py) e [aurora/tools/visitantes.py](aurora/tools/visitantes.py), no SQLite `var/condominio.db`. A sessão do ADK fica em `var/sessoes.db`.

A confirmação de cobrança ou de acesso volta ao especialista que a pediu porque o `App` é retomável (`ResumabilityConfig(is_resumable=True)` em [aurora/aplicacao.py](aurora/aplicacao.py)). O Runner escolhe o agente pelo autor do evento `adk_request_confirmation`. A rota de confirmação manda o `FunctionResponse` com esse id e o `invocation_id` do mesmo evento.

## Garantias

### 1. Cobrança ou acesso só com confirmação

Área com taxa maior que zero pede confirmação antes de gravar. A quadra, taxa zero, grava direto. Autorizar visitante sempre pede confirmação, e o texto do morador não preenche `tool_confirmation`: só a rota faz isso.

O pedido grava `acao` e `detalhes` no payload. Reserva usa `area` e `data`. Visitante usa `nome` e `data`.

```53:61:aurora/tools/reservas.py
    if registro.taxa > 0:
        if aguardando_confirmacao(tool_context):
            return pedir_confirmacao(
                tool_context,
                ConstantesRequisicao.ACAO_RESERVAR,
                {"area": registro.id, "data": data},
            )
        if confirmacao_negada(tool_context):
            return {"ok": False, "motivo": ConstantesErro.CONFIRMACAO_NEGADA}
```

```39:46:aurora/tools/visitantes.py
    if aguardando_confirmacao(tool_context):
        return pedir_confirmacao(
            tool_context,
            ConstantesRequisicao.ACAO_AUTORIZAR_VISITANTE,
            {"nome": nome_limpo, "data": data},
        )
    if confirmacao_negada(tool_context):
        return {"ok": False, "motivo": ConstantesErro.CONFIRMACAO_NEGADA}
```

Id que não está pendente na sessão, inclusive um id já respondido, responde `409` e o Runner não é chamado.

```86:88:aurora/api/rotas.py
    pendente = buscar_pendente(sessao.events, corpo.id)
    if pendente is None:
        raise HTTPException(status_code=409, detail=ConstantesErro.CONFIRMACAO_NAO_PENDENTE)
```

A retomada envia `adk_request_confirmation` com o id pendente:

```42:53:aurora/sessao/execucao.py
def mensagem_de_confirmacao(pendente: Pendencia, confirmado: bool) -> types.Content:
    return types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id=pendente.id,
                    name=ConstantesAplicacao.NOME_CONFIRMACAO,
                    response={"confirmed": confirmado},
                )
            )
        ],
    )
```

### 2. Cada sessão pertence a um apartamento

O apartamento é gravado uma vez, na criação da sessão, em `state["apartamento"]`. Nenhuma tool declara esse argumento. Todas leem o valor da sessão.

```58:62:aurora/api/rotas.py
    sessao = await runtime.session_service.create_session(
        app_name=ConstantesAplicacao.NOME_APP,
        user_id=ConstantesAplicacao.USUARIO_SESSAO,
        state={ConstantesAplicacao.CHAVE_APARTAMENTO: corpo.apartamento},
    )
```

```13:17:aurora/tools/sessao.py
def apartamento_da_sessao(tool_context: ToolContext) -> str | None:
    valor = tool_context.state.get(ConstantesAplicacao.CHAVE_APARTAMENTO)
    if not isinstance(valor, str) or not valor.strip():
        return None
    return valor
```

Cancelar e listar filtram por esse apartamento. A consulta de agenda devolve só `disponivel`, sem código, sem número de outro apartamento e sem nome de morador (`consultar_disponibilidade` em [aurora/tools/reservas.py](aurora/tools/reservas.py)).

### 3. Nada se perde no reinício

Sessões e eventos ficam no `SqliteSessionService` (`var/sessoes.db`). Reservas e visitantes ficam em `var/condominio.db`. Reiniciar a API reabre os dois arquivos. O comando de restauração recria só o banco do condomínio, a partir dos JSON de `dados/`.

```22:28:aurora/aplicacao.py
    session_service = SqliteSessionService(db_path=str(config.sessoes_db))
    app_adk = App(
        name=ConstantesAplicacao.NOME_APP,
        root_agent=criar_principal(config.modelo),
        resumability_config=ResumabilityConfig(is_resumable=True),
    )
```

### 4. O regulamento é consultado, não carregado

`INSTRUCAO_PRINCIPAL` em [aurora/agentes/instrucoes.py](aurora/agentes/instrucoes.py) não traz o regulamento. A tool `consultar_regulamento` devolve um único capítulo, escolhido por `selecionar_capitulo`. A dúvida sobre a piscina aos domingos cai no Capítulo IV: aos domingos e feriados, funciona das 9h às 20h.

```35:40:aurora/dados/regulamento.py
def selecionar_capitulo(pergunta: str, regulamento: str) -> str | None:
    pergunta_normalizada = normalizar(pergunta)
    pontuacao: dict[str, int] = {}
    for palavra, numero in _TOPICOS:
        if palavra in pergunta_normalizada:
            pontuacao[numero] = pontuacao.get(numero, 0) + 1
```

### 5. Dois moradores, uma reserva

A exclusividade vale no `INSERT`, dentro de `BEGIN IMMEDIATE`, com índice único parcial. Conflito vira resultado normal da tool (`data_ocupada`), e a API responde `200`. O código novo é gerado na mesma transação e não reutiliza código cancelado: o cancelamento só muda `status` para `cancelada`.

```170:180:aurora/dados/repositorio.py
    def criar_reserva(self, apartamento: str, area: str, data: str) -> str | None:
        with self._trava:
            for _ in range(5):
                self._conexao.execute("BEGIN IMMEDIATE")
                codigo = self._codigo_inedito()
                try:
                    self._conexao.execute(
                        """
                        INSERT INTO reservas (codigo, apartamento, area, data, status)
                        VALUES (?, ?, ?, ?, ?)
                        """,
```

```250:252:aurora/dados/repositorio.py
            CREATE UNIQUE INDEX IF NOT EXISTS idx_reservas_area_data_ativa
                ON reservas (area, data)
                WHERE status = 'ativa';
```

## Como rodar

Pré-requisitos: Python 3.12 ou superior, [uv](https://docs.astral.sh/uv/) e uma chave do Google AI Studio.

Variáveis do `.env`, copiadas de `.env.example`:

- `GOOGLE_API_KEY`: chave do Google AI Studio. Obrigatória para conversar com o modelo.
- `GEMINI_MODEL`: modelo Gemini de cada agente. Opcional. Se ficar vazio, o padrão é `gemini-2.5-flash`.

```bash
uv sync
cp .env.example .env
uv run aurora-restaurar
uv run aurora-api
```

A API sobe em `http://localhost:8000`. `aurora-restaurar` recria `var/condominio.db` com os JSON de `dados/` e não apaga as sessões. Na primeira subida, se esse banco ainda não existir, a API também carrega os JSON. Para voltar aos dados iniciais com a API parada, rode `uv run aurora-restaurar` de novo.
