from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import settings


Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                requester TEXT NOT NULL,
                worker TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                due_date TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                source_channel TEXT,
                source_message_link TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                channel_id TEXT NOT NULL,
                remind_at TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                sent INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
