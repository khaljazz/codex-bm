"""SQLite helpers for bookmark triage."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            domain TEXT,
            site_bucket TEXT,
            source_type TEXT,
            status TEXT NOT NULL,
            is_build_related INTEGER,
            short_summary TEXT,
            tags_json TEXT,
            main_category TEXT,
            sub_category TEXT,
            usefulness_score INTEGER,
            build_score INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_status ON bookmarks(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_bucket ON bookmarks(site_bucket)")
    conn.commit()
