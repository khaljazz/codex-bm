"""Import bookmark URLs from TXT or CSV files."""

from __future__ import annotations

import csv
from pathlib import Path
import sqlite3

from utils import extract_domain, is_valid_url, normalize_url, utc_now_iso


def _iter_urls_from_txt(path: Path):
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if stripped:
            yield stripped


def _iter_urls_from_csv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames:
            lowered = {name.lower(): name for name in reader.fieldnames}
            for key in ("url", "link", "href"):
                if key in lowered:
                    col = lowered[key]
                    for row in reader:
                        value = (row.get(col) or "").strip()
                        if value:
                            yield value
                    return
        f.seek(0)
        plain_reader = csv.reader(f)
        for row in plain_reader:
            if row and row[0].strip():
                yield row[0].strip()


def import_bookmarks(conn: sqlite3.Connection, input_path: str) -> dict[str, int]:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    source_type = path.suffix.lower().lstrip(".") or "txt"
    if source_type == "csv":
        raw_iter = _iter_urls_from_csv(path)
    else:
        raw_iter = _iter_urls_from_txt(path)

    counters = {"seen": 0, "inserted": 0, "duplicates": 0, "invalid": 0}

    for raw in raw_iter:
        counters["seen"] += 1
        url = normalize_url(raw)
        if not is_valid_url(url):
            counters["invalid"] += 1
            continue

        now = utc_now_iso()
        domain = extract_domain(url)
        try:
            conn.execute(
                """
                INSERT INTO bookmarks (
                    url, domain, source_type, status, created_at, updated_at
                ) VALUES (?, ?, ?, 'imported', ?, ?)
                """,
                (url, domain, source_type, now, now),
            )
            counters["inserted"] += 1
        except sqlite3.IntegrityError:
            counters["duplicates"] += 1

    conn.commit()
    return counters
