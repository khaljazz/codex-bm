"""Candidate selection and Ollama classification."""

from __future__ import annotations

import json
import sqlite3
from urllib import error, request

from models import BUILD_KEYWORDS, DEFAULT_OLLAMA_MODEL, DEFAULT_OLLAMA_URL


def likely_build_candidate(url: str, domain: str, site_bucket: str) -> bool:
    if site_bucket in {"instagram", "other"}:
        return False
    if site_bucket in {"github", "docs"}:
        return True

    haystack = f"{url} {domain}".lower()
    return any(k in haystack for k in BUILD_KEYWORDS)


def queue_candidates(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT id, url, domain, site_bucket FROM bookmarks WHERE status='bucketed'").fetchall()
    queued = 0
    side_bucket = 0

    for row in rows:
        if likely_build_candidate(row["url"], row["domain"], row["site_bucket"] or "other"):
            conn.execute("UPDATE bookmarks SET status='queued', updated_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
            queued += 1
        else:
            conn.execute("UPDATE bookmarks SET status='side_bucket', updated_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
            side_bucket += 1

    conn.commit()
    return {"queued": queued, "side_bucket": side_bucket}


def _build_prompt(url: str, domain: str, site_bucket: str) -> str:
    return f"""
Classify this bookmark for software/build usefulness.
Return ONLY compact JSON with this exact schema:
{{
  "is_build_related": true/false,
  "short_summary": "string under 160 chars",
  "tags": ["tag1", "tag2"],
  "main_category": "ai|coding|app_building|automation|agents|local_llm|api|tools|other",
  "sub_category": "short string",
  "usefulness_score": integer 1-10,
  "build_score": integer 1-10,
  "notes": "short optional note"
}}
Rules:
- Be strict and practical.
- If not useful for building/coding/AI work, set is_build_related false.
- Output valid JSON only.
Input:
url={url}
domain={domain}
site_bucket={site_bucket}
""".strip()


def _call_ollama(prompt: str, model: str, ollama_url: str) -> dict:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(ollama_url, data=body, headers={"Content-Type": "application/json"}, method="POST")

    with request.urlopen(req, timeout=90) as resp:
        raw = resp.read().decode("utf-8")
    outer = json.loads(raw)
    return json.loads(outer.get("response", "{}"))


def classify_queued(conn: sqlite3.Connection, model: str = DEFAULT_OLLAMA_MODEL, ollama_url: str = DEFAULT_OLLAMA_URL, limit: int | None = None) -> dict[str, int]:
    sql = "SELECT id, url, domain, site_bucket FROM bookmarks WHERE status='queued' ORDER BY id"
    if limit:
        sql += f" LIMIT {int(limit)}"
    rows = conn.execute(sql).fetchall()

    processed = 0
    errors = 0

    for row in rows:
        prompt = _build_prompt(row["url"], row["domain"], row["site_bucket"])
        try:
            parsed = _call_ollama(prompt, model=model, ollama_url=ollama_url)
            tags = parsed.get("tags", [])
            if not isinstance(tags, list):
                tags = []

            conn.execute(
                """
                UPDATE bookmarks
                SET status='processed',
                    is_build_related=?,
                    short_summary=?,
                    tags_json=?,
                    main_category=?,
                    sub_category=?,
                    usefulness_score=?,
                    build_score=?,
                    notes=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (
                    1 if parsed.get("is_build_related") else 0,
                    str(parsed.get("short_summary", ""))[:200],
                    json.dumps(tags, ensure_ascii=False),
                    str(parsed.get("main_category", "other"))[:80],
                    str(parsed.get("sub_category", ""))[:120],
                    int(parsed.get("usefulness_score", 1) or 1),
                    int(parsed.get("build_score", 1) or 1),
                    str(parsed.get("notes", ""))[:400],
                    row["id"],
                ),
            )
            processed += 1
        except (json.JSONDecodeError, ValueError, TypeError, error.URLError, error.HTTPError, TimeoutError) as exc:
            conn.execute(
                "UPDATE bookmarks SET status='error', notes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (f"classification_error: {type(exc).__name__}: {exc}", row["id"]),
            )
            errors += 1

    conn.commit()
    return {"processed": processed, "errors": errors}
