from memory_agent.config import load_settings


def test_env_var_is_used(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", ' "abc123" ')
    monkeypatch.setenv("MEMORY_TOP_K", "99")
    s = load_settings()
    assert s.api_key == "abc123"      # quotes/spaces stripped
    assert s.top_k == 10              # clamped


def test_missing_key_gives_none_not_crash(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr("memory_agent.config.load_dotenv", lambda: None)
    assert load_settings().api_key is None


def test_falls_back_to_streamlit_secrets(monkeypatch):
    import sys, types
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr("memory_agent.config.load_dotenv", lambda: None)
    fake_st = types.SimpleNamespace(secrets={"OPENROUTER_API_KEY": "from-secrets"})
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    assert load_settings().api_key == "from-secrets"


def test_default_model_and_override(monkeypatch):
    monkeypatch.setattr("memory_agent.config.load_dotenv", lambda: None)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    assert load_settings().model == "openrouter/free"
    monkeypatch.setenv("OPENROUTER_MODEL", "vendor/some-model:free")
    assert load_settings().model == "vendor/some-model:free"
