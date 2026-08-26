import json
import sqlite3
import time
from datetime import datetime, timezone
from typing import Optional

from app.config import settings


def get_connection():
    return sqlite3.connect(settings.log_database)


def init_logging():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS query_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            question TEXT NOT NULL,
            intent TEXT,
            parameters TEXT,
            cypher TEXT,
            result TEXT,
            duration_ms INTEGER,
            success INTEGER NOT NULL,
            error TEXT
        )
        """
    )

    connection.commit()
    connection.close()


def log_query(
    question: str,
    intent: Optional[str],
    parameters: Optional[dict],
    cypher: Optional[str],
    result: Optional[object],
    duration_ms: int,
    success: bool,
    error: Optional[str] = None,
):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO query_logs (
            created_at,
            question,
            intent,
            parameters,
            cypher,
            result,
            duration_ms,
            success,
            error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            question,
            intent,
            json.dumps(
                parameters,
                ensure_ascii=False,
                default=str,
            ),
            cypher,
            json.dumps(
                result,
                ensure_ascii=False,
                default=str,
            ),
            duration_ms,
            1 if success else 0,
            error,
        ),
    )

    connection.commit()
    connection.close()


class Timer:
    def __init__(self):
        self.started = time.perf_counter()

    def elapsed_ms(self) -> int:
        return int(
            (time.perf_counter() - self.started) * 1000
        )