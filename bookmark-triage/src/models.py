"""Project-wide constants and simple helpers."""

from __future__ import annotations

STATUSES = {
    "imported",
    "bucketed",
    "queued",
    "processed",
    "side_bucket",
    "error",
}

SITE_BUCKETS = {
    "x",
    "instagram",
    "youtube",
    "github",
    "docs",
    "web",
    "other",
}

BUILD_KEYWORDS = {
    "ai",
    "llm",
    "gpt",
    "agent",
    "automation",
    "api",
    "code",
    "coding",
    "developer",
    "repo",
    "tool",
    "workflow",
    "build",
    "python",
    "javascript",
    "local model",
    "ollama",
}

DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
