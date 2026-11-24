"""Chat orchestration: recall memories, ask the model, save the new memory."""

from dataclasses import dataclass, field

from .config import MAX_MESSAGE_CHARS
from .llm import OpenRouterClient
from .memory import MemoryStore


@dataclass
class ChatResult:
    reply: str | None  # None in demo mode (no AI was called)
    memories_used: list[str] = field(default_factory=list)
    demo_mode: bool = False


def chat_with_memory(
    store: MemoryStore,
    llm: OpenRouterClient | None,
    message: str,
    history: list[dict] | None = None,
    top_k: int = 3,
) -> ChatResult:
    """Process one user message.

    - Memories are recalled BEFORE the new message is saved, so the message
      never retrieves itself.
    - If `llm` is None (no API key) we run in demo mode: memory still works,
      but no AI reply is produced and none is faked.
    - If the AI call fails, AIError propagates and nothing is saved, so the
      user can simply retry without creating a duplicate memory.
    """
    message = (message or "").strip()
    if not message:
        raise ValueError("Please enter a message.")
    if len(message) > MAX_MESSAGE_CHARS:
        raise ValueError(f"Message is too long (max {MAX_MESSAGE_CHARS} characters).")

    memories = store.search(message, k=top_k)

    if llm is None:
        store.add(message)
        return ChatResult(reply=None, memories_used=memories, demo_mode=True)

    reply = llm.generate(message, memories, history)
    store.add(message)
    return ChatResult(reply=reply, memories_used=memories, demo_mode=False)
