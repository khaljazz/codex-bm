"""CLI entrypoint for bookmark triage."""

from __future__ import annotations

import argparse
from pathlib import Path

from bucketer import bucket_bookmarks
from classifier import classify_queued, queue_candidates
from db import get_connection, init_db
from exporter import export_all
from importer import import_bookmarks
from models import DEFAULT_OLLAMA_MODEL, DEFAULT_OLLAMA_URL

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BASE_DIR / "data" / "bookmarks.db"
DEFAULT_EXPORT_DIR = BASE_DIR / "data" / "exports"


def _print_counts(title: str, counts: dict[str, int]) -> None:
    print(f"\n{title}")
    for key, value in counts.items():
        print(f"  - {key}: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local bookmark triage tool (Phase 1)")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite database")

    sub = parser.add_subparsers(dest="command", required=True)

    import_cmd = sub.add_parser("import", help="Import bookmarks from txt/csv")
    import_cmd.add_argument("--input", required=True, help="Input file path (.txt or .csv)")

    sub.add_parser("bucket", help="Assign site buckets")
    sub.add_parser("queue", help="Mark likely build candidates")

    classify_cmd = sub.add_parser("classify", help="Classify queued bookmarks using local Ollama")
    classify_cmd.add_argument("--model", default=DEFAULT_OLLAMA_MODEL, help="Ollama model name")
    classify_cmd.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="Ollama API URL")
    classify_cmd.add_argument("--limit", type=int, default=None, help="Optional max queued items to process")

    export_cmd = sub.add_parser("export", help="Export Phase 1 CSV outputs")
    export_cmd.add_argument("--out", default=str(DEFAULT_EXPORT_DIR), help="Export directory")

    all_cmd = sub.add_parser("run-all", help="Run import -> bucket -> queue -> classify -> export")
    all_cmd.add_argument("--input", required=True, help="Input file path (.txt or .csv)")
    all_cmd.add_argument("--model", default=DEFAULT_OLLAMA_MODEL, help="Ollama model name")
    all_cmd.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="Ollama API URL")
    all_cmd.add_argument("--limit", type=int, default=None, help="Optional max queued items to process")
    all_cmd.add_argument("--out", default=str(DEFAULT_EXPORT_DIR), help="Export directory")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    conn = get_connection(args.db)
    init_db(conn)

    if args.command == "import":
        _print_counts("Import complete", import_bookmarks(conn, args.input))
    elif args.command == "bucket":
        _print_counts("Bucketing complete", bucket_bookmarks(conn))
    elif args.command == "queue":
        _print_counts("Queueing complete", queue_candidates(conn))
    elif args.command == "classify":
        _print_counts(
            "Classification complete",
            classify_queued(conn, model=args.model, ollama_url=args.ollama_url, limit=args.limit),
        )
    elif args.command == "export":
        _print_counts("Export complete", export_all(conn, args.out))
    elif args.command == "run-all":
        _print_counts("Import complete", import_bookmarks(conn, args.input))
        _print_counts("Bucketing complete", bucket_bookmarks(conn))
        _print_counts("Queueing complete", queue_candidates(conn))
        _print_counts(
            "Classification complete",
            classify_queued(conn, model=args.model, ollama_url=args.ollama_url, limit=args.limit),
        )
        _print_counts("Export complete", export_all(conn, args.out))

    conn.close()


if __name__ == "__main__":
    main()
