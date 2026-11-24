import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from memory_agent.memory import MemoryStore


class FakeCollection:
    """In-memory stand-in for a ChromaDB collection (word-overlap 'similarity')."""

    def __init__(self):
        self.rows = {}  # id -> (document, metadata)

    def count(self):
        return len(self.rows)

    def add(self, documents, ids, metadatas=None):
        for i, (doc, id_) in enumerate(zip(documents, ids)):
            if id_ in self.rows:
                raise ValueError("duplicate id")
            self.rows[id_] = (doc, metadatas[i] if metadatas else None)

    def query(self, query_texts, n_results):
        if n_results > len(self.rows):
            raise ValueError("n_results larger than collection")  # chroma warns/errors similarly
        words = set(query_texts[0].lower().split())
        ranked = sorted(self.rows.values(), key=lambda r: -len(words & set(r[0].lower().split())))
        return {"documents": [[doc for doc, _ in ranked[:n_results]]]}

    def get(self, include=None):
        ids = list(self.rows)
        return {
            "ids": ids,
            "documents": [self.rows[i][0] for i in ids],
            "metadatas": [self.rows[i][1] for i in ids],
        }

    def delete(self, ids):
        for i in ids:
            self.rows.pop(i, None)


@pytest.fixture
def store():
    return MemoryStore(FakeCollection())


class FakeAPIError(Exception):
    def __init__(self, code, message="error"):
        super().__init__(f"{code} {message}")
        self.code = code


class _Msg:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Msg(content)


class FakeResponse:
    def __init__(self, text):
        self.choices = [_Choice(text)]


class FakeCompletions:
    def __init__(self, behaviours):
        self.behaviours = list(behaviours)  # each: str reply or Exception to raise
        self.calls = []

    def create(self, model, messages, max_tokens=None):
        self.calls.append({"model": model, "messages": messages, "max_tokens": max_tokens})
        action = self.behaviours.pop(0)
        if isinstance(action, Exception):
            raise action
        return FakeResponse(action)


class FakeChat:
    def __init__(self, behaviours):
        self.completions = FakeCompletions(behaviours)


class FakeOpenAIClient:
    def __init__(self, behaviours):
        self.chat = FakeChat(behaviours)
