import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from midi_analyzer_tagger.core import AnalysisPayload


class AnalysisDatabase:
    """SQLite backend for storing per-file analysis payloads."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def create_tables(self) -> None:
        if not self.connection:
            raise RuntimeError("Database not connected")

        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                family TEXT,
                duration REAL,
                note_count INTEGER,
                metadata TEXT,
                analyzed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS tags (
                file_id INTEGER NOT NULL,
                concept_name TEXT NOT NULL,
                level_name TEXT,
                level_index INTEGER,
                level_weight INTEGER,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
                UNIQUE(file_id, concept_name)
            );

            CREATE TABLE IF NOT EXISTS raw_features (
                file_id INTEGER NOT NULL,
                concept_name TEXT NOT NULL,
                value TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
                UNIQUE(file_id, concept_name)
            );

            CREATE TABLE IF NOT EXISTS normalized_features (
                file_id INTEGER NOT NULL,
                concept_name TEXT NOT NULL,
                value TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
                UNIQUE(file_id, concept_name)
            );
            """
        )
        self.connection.commit()

    def store(self, file_path: str | Path, payload: AnalysisPayload) -> int:
        if not self.connection:
            raise RuntimeError("Database not connected")

        path = str(file_path)
        with self.connection:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO files
                (path, family, duration, note_count, metadata, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    path,
                    payload.family,
                    payload.metadata.get("duration"),
                    payload.metadata.get("note_count"),
                    json.dumps(payload.metadata),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

            row = self.connection.execute("SELECT id FROM files WHERE path = ?", (path,)).fetchone()
            file_id = row["id"]

            self.connection.execute("DELETE FROM tags WHERE file_id = ?", (file_id,))
            self.connection.execute("DELETE FROM raw_features WHERE file_id = ?", (file_id,))
            self.connection.execute("DELETE FROM normalized_features WHERE file_id = ?", (file_id,))

            for concept_name, level in payload.tags.items():
                self.connection.execute(
                    """
                    INSERT OR REPLACE INTO tags
                    (file_id, concept_name, level_name, level_index, level_weight)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        file_id,
                        concept_name,
                        level.name if level else None,
                        level.index if level else None,
                        level.weight if level else None,
                    ),
                )

            for concept_name, value in payload.raw_features.items():
                self.connection.execute(
                    """
                    INSERT OR REPLACE INTO raw_features
                    (file_id, concept_name, value)
                    VALUES (?, ?, ?)
                    """,
                    (file_id, concept_name, json.dumps(value)),
                )

            for concept_name, value in payload.normalized_features.items():
                self.connection.execute(
                    """
                    INSERT OR REPLACE INTO normalized_features
                    (file_id, concept_name, value)
                    VALUES (?, ?, ?)
                    """,
                    (file_id, concept_name, json.dumps(value)),
                )

        return file_id

    def __enter__(self):
        self.connect()
        self.create_tables()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
