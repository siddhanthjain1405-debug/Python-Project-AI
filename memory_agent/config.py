"""Configuration loaded from environment variables (and an optional .env file)."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# OpenRouter's free model router: picks a free model automatically. Only free models are allowed.
DEFAULT_MODEL = "openrouter/free"
BASE_URL = "https://openrouter.ai/api/v1"
MAX_OUTPUT_TOKENS = 600
MAX_MESSAGE_CHARS = 4000


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    model: str
    memory_dir: str
    top_k: int


def _clean(value: str | None) -> str | None:
    """Strip whitespace and stray quotes; return None for empty values."""
    if value is None:
        return None
    value = value.strip().strip('"').strip("'").strip()
    return value or None


def _get(name: str) -> str | None:
    """Read a setting: environment variable / .env first, then Streamlit secrets
    (used on Streamlit Cloud). Returns None if it is set in neither place."""
    value = _clean(os.getenv(name))
    if value is not None:
        return value
    try:
        import streamlit as st

        secret = st.secrets[name]  # raises if there is no secrets file or key
        return _clean(str(secret))
    except Exception:
        return None


def _int_env(name: str, default: int, low: int, high: int) -> int:
    raw = _get(name)
    if raw is None:
        return default
    try:
        return max(low, min(high, int(raw)))
    except ValueError:
        return default


def load_settings() -> Settings:
    """Read settings from the environment. Never raises for a missing API key."""
    load_dotenv()
    return Settings(
        api_key=_get("OPENROUTER_API_KEY"),
        model=_get("OPENROUTER_MODEL") or DEFAULT_MODEL,
        memory_dir=_get("MEMORY_DIR") or "./agent_brain",
        top_k=_int_env("MEMORY_TOP_K", default=3, low=1, high=10),
    )
