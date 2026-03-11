"""CSV export functions for Phase 1 outputs."""

from __future__ import annotations

import csv
from pathlib import Path
import sqlite3

EXPORT_COLUMNS = [
    "id",
    "url",
    "domain",
    "site_bucket",
    "status",
    "is_build_related",
    "short_summary",
    "tags_json",
    "main_category",
    "sub_category",
    "usefulness_score",
    "build_score",
    "notes",
]


def _write_csv(path: Path, rows: list[sqlite3.Row]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in EXPORT_COLUMNS})
    return len(rows)


def export_all(conn: sqlite3.Connection, export_dir: str) -> dict[str, int]:
    out = Path(export_dir)
    counts: dict[str, int] = {}

    ai_rows = conn.execute(
        """
        SELECT * FROM bookmarks
        WHERE is_build_related = 1
        ORDER BY build_score DESC, usefulness_score DESC, id ASC
        """
    ).fetchall()
    counts["ai_build_ranked.csv"] = _write_csv(out / "ai_build_ranked.csv", ai_rows)

    insta_rows = conn.execute("SELECT * FROM bookmarks WHERE site_bucket='instagram' ORDER BY id").fetchall()
    counts["instagram_bucket.csv"] = _write_csv(out / "instagram_bucket.csv", insta_rows)

    yt_rows = conn.execute("SELECT * FROM bookmarks WHERE site_bucket='youtube' ORDER BY id").fetchall()
    counts["youtube_bucket.csv"] = _write_csv(out / "youtube_bucket.csv", yt_rows)

    x_rows = conn.execute(
        """
        SELECT * FROM bookmarks
        WHERE site_bucket='x' AND COALESCE(is_build_related, 0)=0
        ORDER BY id
        """
    ).fetchall()
    counts["x_non_build.csv"] = _write_csv(out / "x_non_build.csv", x_rows)

    other_rows = conn.execute(
        """
        SELECT * FROM bookmarks
        WHERE site_bucket NOT IN ('instagram', 'youtube', 'x')
          AND COALESCE(is_build_related, 0)=0
        ORDER BY id
        """
    ).fetchall()
    counts["other_buckets.csv"] = _write_csv(out / "other_buckets.csv", other_rows)

    return counts
