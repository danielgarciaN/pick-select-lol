from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_DB_PATH = os.getenv("DB_PATH", "./data/draft_assistant.db")


def get_db_path() -> Path:
    path = Path(DEFAULT_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_conn(db_path: str | None = None) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path or str(get_db_path()))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str | None = None) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS champions (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                key_str TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                icon_url TEXT
            );

            CREATE TABLE IF NOT EXISTS player (
                puuid TEXT PRIMARY KEY,
                game_name TEXT NOT NULL,
                tag_line TEXT NOT NULL,
                region TEXT NOT NULL,
                last_sync TEXT
            );

            CREATE TABLE IF NOT EXISTS mastery (
                puuid TEXT NOT NULL,
                champion_id INTEGER NOT NULL,
                points INTEGER NOT NULL,
                level INTEGER NOT NULL,
                last_play_time INTEGER,
                PRIMARY KEY (puuid, champion_id)
            );

            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY,
                patch TEXT,
                queue_id INTEGER,
                game_creation INTEGER,
                duration INTEGER
            );

            CREATE TABLE IF NOT EXISTS my_participation (
                match_id TEXT NOT NULL,
                puuid TEXT NOT NULL,
                champion_id INTEGER NOT NULL,
                role TEXT,
                lane TEXT,
                win INTEGER,
                kills INTEGER,
                deaths INTEGER,
                assists INTEGER,
                cs INTEGER,
                PRIMARY KEY (match_id, puuid)
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope TEXT NOT NULL,
                champion_id INTEGER,
                role TEXT,
                text TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                condition_type TEXT NOT NULL,
                condition_value TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_value TEXT NOT NULL,
                weight REAL NOT NULL,
                note TEXT
            );
            """
        )


def set_state(key: str, value: str, db_path: str | None = None) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO app_state(key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
              value=excluded.value,
              updated_at=CURRENT_TIMESTAMP
            """,
            (key, value),
        )


def get_state(key: str, db_path: str | None = None) -> str | None:
    with get_conn(db_path) as conn:
        row = conn.execute("SELECT value FROM app_state WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None
