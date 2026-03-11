# Bookmark Triage (Phase 1)

A simple local Python command-line app that helps you process a large bookmark list and isolate the best links for AI/coding/build work.

## What this project does

- Imports bookmarks from `.txt` or `.csv`
- Deduplicates by URL (safe `UNIQUE` constraint in SQLite)
- Buckets each bookmark by site/domain (`x`, `instagram`, `youtube`, `github`, `docs`, `web`, `other`)
- Stores everything in local SQLite (`data/bookmarks.db`)
- Tracks handling status for every bookmark
- Finds likely build-related candidates
- Calls local Ollama only for candidates and stores structured JSON results
- Exports key CSV outputs for review

## Folder structure

```text
bookmark-triage/
  data/
    bookmarks.db
    input/
    exports/
  src/
    db.py
    models.py
    importer.py
    bucketer.py
    classifier.py
    exporter.py
    utils.py
    main.py
  README.md
  requirements.txt
```

## Requirements

- Windows 10
- Python 3.14
- Ollama installed and running locally

## Install dependencies

This project uses only Python standard library modules.

```bash
pip install -r requirements.txt
```

(There are no external packages in Phase 1.)

## Run Ollama locally

1. Start Ollama service (if not already running).
2. Pull a model (example):
   - `ollama pull llama3.1:8b`
3. Check model list:
   - `ollama list`

The app calls Ollama via local HTTP API:

- Default URL: `http://127.0.0.1:11434/api/generate`
- Default model: `llama3.1:8b`

You can override model with `--model` in the classify commands.

## Input file

Place your input file in `data/input/` (or anywhere and pass full path).

Supported formats:
- `.txt` (one URL per line)
- `.csv` (tries `url`, `link`, `href` column first, else first column)

## How to run (step-by-step)

Open terminal in `bookmark-triage/` and run:

```bash
python src/main.py import --input data/input/bookmarks.txt
python src/main.py bucket
python src/main.py queue
python src/main.py classify --model llama3.1:8b
python src/main.py export
```

Or run full pipeline:

```bash
python src/main.py run-all --input data/input/bookmarks.txt --model llama3.1:8b
```

Optional classify limit (useful for small test batches):

```bash
python src/main.py classify --model llama3.1:8b --limit 50
```

## Output files

Exports are saved under `data/exports/`:

- `ai_build_ranked.csv` (sorted by `build_score DESC`, then `usefulness_score DESC`)
- `instagram_bucket.csv`
- `youtube_bucket.csv`
- `x_non_build.csv`
- `other_buckets.csv`

## Status values

Bookmarks are tracked with statuses:
- `imported`
- `bucketed`
- `queued`
- `processed`
- `side_bucket`
- `error`

## Common errors and fixes

### 1) `classification_error: URLError` or connection refused
- Ollama is not running.
- Start Ollama, then rerun:
  - `python src/main.py classify --model llama3.1:8b`

### 2) `classification_error: JSONDecodeError`
- Model returned invalid JSON.
- Retry with smaller batch:
  - `python src/main.py classify --model llama3.1:8b --limit 20`
- Try a model better at strict JSON output.

### 3) File not found during import
- Check path and filename.
- Use full path or place files in `data/input/`.

### 4) Duplicate URLs are skipped
- This is expected behavior. URL column is unique in SQLite.

## Notes

- No frontend in Phase 1.
- No FastAPI in Phase 1.
- No ORM in Phase 1.
- SQLite + standard library only.
