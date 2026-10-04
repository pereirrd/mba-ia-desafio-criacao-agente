from __future__ import annotations

from fastapi import FastAPI
from google.adk.apps.app import App
from google.adk.apps.app import ResumabilityConfig
from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService

from aurora.agentes.fabrica import criar_principal
from aurora.api.rotas import router
from aurora.config import AppConfig
from aurora.constantes import ConstantesAplicacao
from aurora.dados.acesso import definir_dados
from aurora.dados.restaurar import abrir_repositorio
from aurora.runtime import Runtime


def criar_aplicacao(config: AppConfig) -> FastAPI:
    config.var_dir.mkdir(parents=True, exist_ok=True)
    repositorio = abrir_repositorio(config)
    definir_dados(repositorio, config.regulamento)
    session_service = SqliteSessionService(db_path=str(config.sessoes_db))
    app_adk = App(
        name=ConstantesAplicacao.NOME_APP,
        root_agent=criar_principal(config.modelo),
        resumability_config=ResumabilityConfig(is_resumable=True),
    )
    runner = Runner(app=app_adk, session_service=session_service)
    api = FastAPI(title="Residencial Aurora")
    api.state.runtime = Runtime(
        repositorio=repositorio,
        session_service=session_service,
        runner=runner,
    )
    api.include_router(router)
    return api
