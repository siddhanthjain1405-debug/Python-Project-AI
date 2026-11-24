"""Personal AI Agent with long-term memory (OpenRouter + ChromaDB)."""

from .config import Settings, load_settings
from .llm import AIError, OpenRouterClient
from .memory import MemoryItem, MemoryStore, MemoryStoreError, open_store
from .service import ChatResult, chat_with_memory

__all__ = [
    "AIError",
    "ChatResult",
    "OpenRouterClient",
    "MemoryItem",
    "MemoryStore",
    "MemoryStoreError",
    "Settings",
    "chat_with_memory",
    "load_settings",
    "open_store",
]
