from __future__ import annotations

import json
import secrets
import sqlite3
import threading
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from aurora.constantes import ConstantesAplicacao


@dataclass(frozen=True)
class AreaEntity:
    id: str
    nome: str
    taxa: float


@dataclass(frozen=True)
class ReservaEntity:
    codigo: str
    apartamento: str
    area: str
    data: str
    status: str


@dataclass(frozen=True)
class VisitanteEntity:
    apartamento: str
    nome: str
    data: str


def normalizar(valor: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", valor)
    sem_acento = "".join(caractere for caractere in sem_acento if not unicodedata.combining(caractere))
    return " ".join(sem_acento.lower().split())


class Repositorio:
    def __init__(self, caminho: Path) -> None:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self._trava = threading.Lock()
        self._conexao = sqlite3.connect(caminho, check_same_thread=False, isolation_level=None)
        self._conexao.row_factory = sqlite3.Row
        self._conexao.execute("PRAGMA journal_mode=WAL")
        self._conexao.execute("PRAGMA busy_timeout=5000")
        self._criar_schema()

    def fechar(self) -> None:
        with self._trava:
            self._conexao.close()

    def carregar_json(self, dados_dir: Path) -> None:
        apartamentos = json.loads((dados_dir / "apartamentos.json").read_text(encoding="utf-8"))
        areas = json.loads((dados_dir / "areas.json").read_text(encoding="utf-8"))
        reservas = json.loads((dados_dir / "reservas.json").read_text(encoding="utf-8"))
        visitantes = json.loads((dados_dir / "visitantes.json").read_text(encoding="utf-8"))
        with self._trava:
            self._conexao.execute("BEGIN IMMEDIATE")
            try:
                self._conexao.execute("DELETE FROM visitantes")
                self._conexao.execute("DELETE FROM reservas")
                self._conexao.execute("DELETE FROM areas")
                self._conexao.execute("DELETE FROM apartamentos")
                self._conexao.executemany(
                    "INSERT INTO apartamentos (numero, morador) VALUES (?, ?)",
                    [(item["numero"], item["morador"]) for item in apartamentos],
                )
                self._conexao.executemany(
                    "INSERT INTO areas (id, nome, taxa) VALUES (?, ?, ?)",
                    [(item["id"], item["nome"], item["taxa"]) for item in areas],
                )
                self._conexao.executemany(
                    """
                    INSERT INTO reservas (codigo, apartamento, area, data, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            item["codigo"],
                            item["apartamento"],
                            item["area"],
                            item["data"],
                            ConstantesAplicacao.STATUS_ATIVA,
                        )
                        for item in reservas
                    ],
                )
                self._conexao.executemany(
                    "INSERT INTO visitantes (apartamento, nome, data) VALUES (?, ?, ?)",
                    [(item["apartamento"], item["nome"], item["data"]) for item in visitantes],
                )
                self._conexao.execute("COMMIT")
            except Exception:
                self._rollback()
                raise

    def apartamento_existe(self, numero: str) -> bool:
        with self._trava:
            linha = self._conexao.execute(
                "SELECT 1 FROM apartamentos WHERE numero = ?",
                (numero,),
            ).fetchone()
        return linha is not None

    def listar_areas(self) -> list[AreaEntity]:
        with self._trava:
            linhas = self._conexao.execute(
                "SELECT id, nome, taxa FROM areas ORDER BY id"
            ).fetchall()
        return [AreaEntity(id=linha["id"], nome=linha["nome"], taxa=float(linha["taxa"])) for linha in linhas]

    def resolver_area(self, texto: str) -> AreaEntity | None:
        chave = normalizar(texto)
        chave_sem_hifen = chave.replace("-", " ")
        return next(
            (
                area
                for area in self.listar_areas()
                if chave in {normalizar(area.id), normalizar(area.nome), normalizar(area.id).replace("-", " ")}
                or chave_sem_hifen in {normalizar(area.nome), normalizar(area.id).replace("-", " ")}
            ),
            None,
        )

    def listar_reservas(self, apartamento: str) -> list[ReservaEntity]:
        with self._trava:
            linhas = self._conexao.execute(
                """
                SELECT codigo, apartamento, area, data, status
                FROM reservas
                WHERE apartamento = ? AND status = ?
                ORDER BY data, codigo
                """,
                (apartamento, ConstantesAplicacao.STATUS_ATIVA),
            ).fetchall()
        return [_reserva(linha) for linha in linhas]

    def listar_visitantes(self, apartamento: str) -> list[VisitanteEntity]:
        with self._trava:
            linhas = self._conexao.execute(
                """
                SELECT apartamento, nome, data
                FROM visitantes
                WHERE apartamento = ?
                ORDER BY data, nome
                """,
                (apartamento,),
            ).fetchall()
        return [
            VisitanteEntity(apartamento=linha["apartamento"], nome=linha["nome"], data=linha["data"])
            for linha in linhas
        ]

    def data_livre(self, area: str, data: str) -> bool:
        with self._trava:
            linha = self._conexao.execute(
                """
                SELECT 1 FROM reservas
                WHERE area = ? AND data = ? AND status = ?
                """,
                (area, data, ConstantesAplicacao.STATUS_ATIVA),
            ).fetchone()
        return linha is None

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
                        (codigo, apartamento, area, data, ConstantesAplicacao.STATUS_ATIVA),
                    )
                    self._conexao.execute("COMMIT")
                    return codigo
                except sqlite3.IntegrityError as erro:
                    self._rollback()
                    if "reservas.codigo" in str(erro):
                        continue
                    return None
        return None

    def cancelar_reserva(self, apartamento: str, area: str, data: str) -> bool:
        with self._trava:
            self._conexao.execute("BEGIN IMMEDIATE")
            try:
                linha = self._conexao.execute(
                    """
                    SELECT codigo FROM reservas
                    WHERE apartamento = ? AND area = ? AND data = ? AND status = ?
                    """,
                    (apartamento, area, data, ConstantesAplicacao.STATUS_ATIVA),
                ).fetchone()
                if linha is None:
                    self._conexao.execute("COMMIT")
                    return False
                self._conexao.execute(
                    "UPDATE reservas SET status = ? WHERE codigo = ?",
                    (ConstantesAplicacao.STATUS_CANCELADA, linha["codigo"]),
                )
                self._conexao.execute("COMMIT")
                return True
            except Exception:
                self._rollback()
                raise

    def codigo_existe(self, codigo: str) -> bool:
        with self._trava:
            linha = self._conexao.execute(
                "SELECT 1 FROM reservas WHERE codigo = ?",
                (codigo,),
            ).fetchone()
        return linha is not None

    def autorizar_visitante(self, apartamento: str, nome: str, data: str) -> None:
        with self._trava:
            self._conexao.execute(
                "INSERT INTO visitantes (apartamento, nome, data) VALUES (?, ?, ?)",
                (apartamento, nome, data),
            )

    def _criar_schema(self) -> None:
        self._conexao.executescript(
            """
            CREATE TABLE IF NOT EXISTS apartamentos (
                numero TEXT PRIMARY KEY,
                morador TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS areas (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                taxa REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reservas (
                codigo TEXT PRIMARY KEY,
                apartamento TEXT NOT NULL,
                area TEXT NOT NULL,
                data TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('ativa', 'cancelada'))
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_reservas_area_data_ativa
                ON reservas (area, data)
                WHERE status = 'ativa';
            CREATE TABLE IF NOT EXISTS visitantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                apartamento TEXT NOT NULL,
                nome TEXT NOT NULL,
                data TEXT NOT NULL
            );
            """
        )

    def _codigo_inedito(self) -> str:
        while True:
            codigo = f"RSV-{secrets.token_hex(4).upper()}"
            linha = self._conexao.execute(
                "SELECT 1 FROM reservas WHERE codigo = ?",
                (codigo,),
            ).fetchone()
            if linha is None:
                return codigo

    def _rollback(self) -> None:
        try:
            self._conexao.execute("ROLLBACK")
        except sqlite3.Error:
            return


def _reserva(linha: sqlite3.Row) -> ReservaEntity:
    return ReservaEntity(
        codigo=linha["codigo"],
        apartamento=linha["apartamento"],
        area=linha["area"],
        data=linha["data"],
        status=linha["status"],
    )
