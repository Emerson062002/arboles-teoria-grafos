"""Persistent local storage for graph analyses using SQLite."""

import json
import os
from pathlib import Path
import sqlite3
from contextlib import contextmanager


class AnalysisStorageError(Exception):
    """Raised when a database operation fails."""


class AnalysisRepository:
    """Stores analyses and returns the most recent saved graphs."""

    def __init__(self, database_path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_sqlite()

    @classmethod
    def from_environment(cls):
        default_path = Path(__file__).resolve().parents[2] / ".data" / "analyses.sqlite3"
        return cls(os.environ.get("ANALYSIS_DB_PATH", str(default_path)))

    def _connect_sqlite(self):
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _sqlite_session(self):
        connection = self._connect_sqlite()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize_sqlite(self):
        with self._sqlite_session() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS graph_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT (
                        strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    ),
                    vertices TEXT NOT NULL,
                    edges TEXT NOT NULL,
                    result TEXT NOT NULL
                )
                """
            )

    def save(self, vertices, edges, result):
        values = (
            json.dumps(vertices, ensure_ascii=False, allow_nan=False),
            json.dumps(edges, ensure_ascii=False, allow_nan=False),
            json.dumps(result, ensure_ascii=False, allow_nan=False),
        )
        try:
            with self._sqlite_session() as connection:
                cursor = connection.execute(
                    "INSERT INTO graph_analyses (vertices, edges, result) VALUES (?, ?, ?)",
                    values,
                )
                return cursor.lastrowid
        except sqlite3.Error as error:
            raise AnalysisStorageError("Falló la escritura en SQLite.") from error

    def recent(self, limit=50):
        try:
            with self._sqlite_session() as connection:
                rows = connection.execute(
                    """
                    SELECT id, created_at, vertices, edges, result
                    FROM graph_analyses
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        except sqlite3.Error as error:
            raise AnalysisStorageError("Falló la consulta en SQLite.") from error
        return [
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "vertices": json.loads(row["vertices"]),
                "edges": json.loads(row["edges"]),
                "analysis": json.loads(row["result"]),
            }
            for row in rows
        ]
