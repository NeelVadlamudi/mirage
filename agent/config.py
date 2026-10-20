"""Settings for the audit agent API, read from environment variables."""

import os


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


# Agent model setting: "gemini-flash-lite" or "ollama-local".
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-flash-lite")
GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-3.5-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OLLAMA_AGENT_MODEL = os.getenv("OLLAMA_AGENT_MODEL", "qwen2.5:7b")

# Origins allowed to call the API from a browser (comma-separated).
ALLOWED_ORIGINS = _split_csv(os.getenv("ALLOWED_ORIGINS", "http://localhost:8000"))

# Key required in the X-API-Key header to approve or reject a proposal. When unset, decisions are disabled.
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

# /docs, /redoc and /openapi.json. Off on the public service (render.yaml).
ENABLE_API_DOCS = os.getenv("ENABLE_API_DOCS", "true").strip().lower() not in ("0", "false", "no")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
