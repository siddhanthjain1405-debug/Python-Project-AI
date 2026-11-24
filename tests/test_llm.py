import pytest

from memory_agent.llm import AIError, OpenRouterClient, build_system_instruction, is_free_model
from conftest import FakeAPIError, FakeOpenAIClient


def make(behaviours, model="openrouter/free"):
    fake = FakeOpenAIClient(behaviours)
    sleeps = []
    client = OpenRouterClient("key", model, client=fake, sleep=sleeps.append)
    return client, fake, sleeps


def test_requires_api_key():
    with pytest.raises(AIError):
        OpenRouterClient("", "openrouter/free")


@pytest.mark.parametrize("model", ["openrouter/free", "meta-llama/llama-3.3-70b-instruct:free"])
def test_free_models_allowed(model):
    assert is_free_model(model)
    OpenRouterClient("k", model)


@pytest.mark.parametrize("model", ["openai/gpt-4o", "anthropic/claude-sonnet-4", "", "openrouter/auto"])
def test_paid_models_refused_before_any_call(model):
    assert not is_free_model(model)
    with pytest.raises(AIError, match="not allowed"):
        OpenRouterClient("k", model)


def test_success_includes_memories_and_history():
    client, fake, _ = make(["Hello Ayush"])
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hey"}]
    assert client.generate("who am I?", ["Name is Ayush"], history) == "Hello Ayush"
    call = fake.chat.completions.calls[0]
    assert call["model"] == "openrouter/free"
    assert call["max_tokens"] and call["max_tokens"] <= 1000
    roles = [m["role"] for m in call["messages"]]
    assert roles == ["system", "user", "assistant", "user"]
    assert "Name is Ayush" in call["messages"][0]["content"]
    assert call["messages"][-1]["content"] == "who am I?"


def test_system_instruction_without_memories():
    assert "(none yet)" in build_system_instruction([])


def test_retries_rate_limit_then_succeeds():
    client, fake, sleeps = make([FakeAPIError(429), "ok"])
    assert client.generate("hi", []) == "ok"
    assert sleeps == [2] and len(fake.chat.completions.calls) == 2


def test_rate_limit_exhausted_gives_friendly_error():
    client, _, sleeps = make([FakeAPIError(429)] * 3)
    with pytest.raises(AIError, match="rate limit"):
        client.generate("hi", [])
    assert sleeps == [2, 4]


def test_invalid_key():
    client, fake, _ = make([FakeAPIError(401, "User not found.")])
    with pytest.raises(AIError, match="key was rejected"):
        client.generate("hi", [])
    assert len(fake.chat.completions.calls) == 1  # no retry on 401


def test_payment_required_is_explained_and_never_retried_with_another_model():
    client, fake, _ = make([FakeAPIError(402, "insufficient credits")])
    with pytest.raises(AIError, match="free models"):
        client.generate("hi", [])
    assert [c["model"] for c in fake.chat.completions.calls] == ["openrouter/free"]


def test_no_free_model_404_is_readable():
    client, _, _ = make([FakeAPIError(404)])
    with pytest.raises(AIError, match="No free model"):
        client.generate("hi", [])


def test_empty_reply_is_an_error():
    client, _, _ = make([""])
    with pytest.raises(AIError, match="empty reply"):
        client.generate("hi", [])


def test_none_choices_is_an_error_not_a_crash():
    client, fake, _ = make(["x"])
    fake.chat.completions.create = lambda **kw: type("R", (), {"choices": None})()
    with pytest.raises(AIError, match="empty reply"):
        client.generate("hi", [])


def test_unknown_error_is_wrapped_without_leaking_details():
    client, _, _ = make([RuntimeError("secret-internal-detail")])
    with pytest.raises(AIError) as info:
        client.generate("hi", [])
    assert "secret-internal-detail" not in str(info.value)


def test_system_instruction_asks_for_short_replies():
    assert "Keep replies short" in build_system_instruction([])
