from __future__ import annotations

from dataclasses import dataclass

from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService

from aurora.dados.repositorio import Repositorio


@dataclass
class Runtime:
    repositorio: Repositorio
    session_service: SqliteSessionService
    runner: Runner
