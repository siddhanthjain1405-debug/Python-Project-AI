"""Long-term memory backed by a ChromaDB persistent collection."""

import json
import re
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from .config import MAX_MESSAGE_CHARS

# The original project stored everything in this collection, so the
# "default" profile keeps using it and existing memories remain visible.
LEGACY_COLLECTION = "personal_memory"


class MemoryStoreError(Exception):
    """Raised for invalid memory operations or database failures."""


@dataclass(frozen=True)
class MemoryItem:
    id: str
    text: str
    created_at: str  # ISO timestamp, or "" for memories saved by older versions


def collection_name_for(profile: str) -> str:
    """Map a free-form profile name to a valid ChromaDB collection name."""
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", (profile or "").strip()).strip("-_").lower()
    slug = slug[:40] or "default"
    if slug == "default":
        return LEGACY_COLLECTION
    return f"mem-{slug}"


class MemoryStore:
    """Thin, testable wrapper around a Chroma-style collection."""

    def __init__(self, collection):
        self._collection = collection

    def count(self) -> int:
        return self._collection.count()

    def add(self, text: str, source: str = "chat") -> str:
        text = (text or "").strip()
        if not text:
            raise MemoryStoreError("Memory text cannot be empty.")
        if len(text) > MAX_MESSAGE_CHARS:
            raise MemoryStoreError(f"Memory text is too long (max {MAX_MESSAGE_CHARS} characters).")
        memory_id = uuid.uuid4().hex  # unique even after deletions
        metadata = {"created_at": datetime.now(timezone.utc).isoformat(), "source": source}
        try:
            self._collection.add(documents=[text], ids=[memory_id], metadatas=[metadata])
        except Exception as exc:  # chromadb raises many different types
            raise MemoryStoreError(f"Could not save memory: {exc}") from exc
        return memory_id

    def search(self, query: str, k: int = 3) -> list[str]:
        """Return up to k stored texts most similar in meaning to the query."""
        total = self.count()
        if total == 0 or not (query or "").strip():
            return []
        try:
            result = self._collection.query(query_texts=[query], n_results=min(k, total))
        except Exception as exc:
            raise MemoryStoreError(f"Memory search failed: {exc}") from exc
        documents = (result.get("documents") or [[]])[0]
        return [doc for doc in documents if doc]

    def list_items(self) -> list[MemoryItem]:
        """All memories, newest first (memories without a timestamp go last)."""
        try:
            data = self._collection.get(include=["documents", "metadatas"])
        except Exception as exc:
            raise MemoryStoreError(f"Could not read memories: {exc}") from exc
        ids = data.get("ids") or []
        documents = data.get("documents") or []
        metadatas = data.get("metadatas") or []
        items = []
        for index, memory_id in enumerate(ids):
            metadata = (metadatas[index] if index < len(metadatas) else None) or {}
            items.append(
                MemoryItem(
                    id=memory_id,
                    text=documents[index] if index < len(documents) else "",
                    created_at=str(metadata.get("created_at", "")),
                )
            )
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    def delete(self, memory_id: str) -> None:
        try:
            self._collection.delete(ids=[memory_id])
        except Exception as exc:
            raise MemoryStoreError(f"Could not delete memory: {exc}") from exc

    def clear(self) -> int:
        """Delete every memory in this profile; returns how many were removed."""
        ids = [item.id for item in self.list_items()]
        if ids:
            try:
                self._collection.delete(ids=ids)
            except Exception as exc:
                raise MemoryStoreError(f"Could not clear memories: {exc}") from exc
        return len(ids)

    def export_json(self) -> str:
        return json.dumps(
            [{"id": i.id, "text": i.text, "created_at": i.created_at} for i in self.list_items()],
            indent=2,
            ensure_ascii=False,
        )


def _use_modern_sqlite() -> None:
    """ChromaDB needs SQLite >= 3.35. Some hosts (e.g. Streamlit Cloud) ship an
    older one; if the optional `pysqlite3` wheel is installed, use it instead."""
    try:
        import pysqlite3  # type: ignore

        sys.modules["sqlite3"] = sys.modules.pop("pysqlite3", pysqlite3)
    except ImportError:
        pass


def open_store(profile: str = "default", path: str = "./agent_brain") -> MemoryStore:
    """Open (or create) the persistent memory for a profile."""
    _use_modern_sqlite()
    try:
        import chromadb

        client = chromadb.PersistentClient(path=path)
        collection = client.get_or_create_collection(name=collection_name_for(profile))
    except Exception as exc:
        raise MemoryStoreError(f"Could not open the memory database at '{path}': {exc}") from exc
    return MemoryStore(collection)
