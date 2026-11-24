import pytest

from memory_agent.llm import AIError, OpenRouterClient
from memory_agent.service import chat_with_memory
from conftest import FakeAPIError, FakeOpenAIClient


def llm_with(*behaviours):
    return OpenRouterClient("k", "openrouter/free", client=FakeOpenAIClient(behaviours), sleep=lambda s: None)


def test_recalls_before_saving_and_saves_after_reply(store):
    store.add("My dog is called Bruno")
    llm = llm_with("Bruno!")
    result = chat_with_memory(store, llm, "what is my dog called", top_k=2)
    assert result.reply == "Bruno!"
    assert "My dog is called Bruno" in result.memories_used
    assert "what is my dog called" not in result.memories_used  # didn't retrieve itself
    assert store.count() == 2


def test_demo_mode_saves_but_does_not_fake_a_reply(store):
    result = chat_with_memory(store, None, "I love tea")
    assert result.demo_mode and result.reply is None
    assert store.count() == 1


def test_ai_failure_saves_nothing(store):
    llm = llm_with(FakeAPIError(401, "User not found."))
    with pytest.raises(AIError):
        chat_with_memory(store, llm, "hello")
    assert store.count() == 0


@pytest.mark.parametrize("bad", ["", "   ", "x" * 5000])
def test_invalid_messages_rejected(store, bad):
    with pytest.raises(ValueError):
        chat_with_memory(store, None, bad)
    assert store.count() == 0
