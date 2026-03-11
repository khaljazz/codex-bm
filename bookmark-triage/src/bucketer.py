"""Site bucket assignment logic."""

from __future__ import annotations

import sqlite3


def classify_site_bucket(url: str, domain: str) -> str:
    domain = (domain or "").lower()
    url_l = (url or "").lower()

    if "instagram.com" in domain:
        return "instagram"
    if "youtube.com" in domain or "youtu.be" in domain:
        return "youtube"
    if domain in {"x.com", "twitter.com"} or domain.endswith(".x.com") or domain.endswith(".twitter.com"):
        return "x"
    if "github.com" in domain:
        return "github"
    if "docs." in domain or "/docs" in url_l or "readthedocs" in domain:
        return "docs"
    if domain:
        return "web"
    return "other"


def bucket_bookmarks(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute(
        "SELECT id, url, domain FROM bookmarks WHERE status IN ('imported', 'error') OR site_bucket IS NULL"
    ).fetchall()

    updated = 0
    buckets: dict[str, int] = {}
    for row in rows:
        bucket = classify_site_bucket(row["url"], row["domain"])
        conn.execute(
            "UPDATE bookmarks SET site_bucket = ?, status = 'bucketed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (bucket, row["id"]),
        )
        updated += 1
        buckets[bucket] = buckets.get(bucket, 0) + 1

    conn.commit()
    return {"updated": updated, **buckets}
