# 🧠 Personal AI Agent with Long-Term Memory

An AI assistant powered by **OpenRouter** (free model router `openrouter/free`) and **ChromaDB** that remembers what you tell it across sessions. Available as a **Streamlit web app** and as the original **command-line** tool.

## Problem statement
Typical chatbots forget everything when a session ends, so users must repeat personal context every time.

## Proposed solution
Every message is stored in a local vector database. When you send a new message, the most semantically similar past memories are retrieved and given to the model as context, so replies are personalised and consistent over time.

## Features
- **Persistent semantic memory** (ChromaDB): recall is by meaning, not exact keywords.
- **Web UI** (Streamlit): chat, memory vault, add / filter / delete memories, JSON export, delete-all with confirmation.
- **Memory profiles**: separate memory per profile name.
- **Short replies**: the assistant is instructed to keep answers concise (short greeting, 1-3 sentence answers).
- **Honest demo mode**: without an API key, memory still works but no AI reply is generated or faked.
- **Robust AI calls**: retries on rate limits / temporary errors, free-models-only guard (paid models are refused), friendly error messages, API key never exposed.
- **CLI** (`agent.py`) with the original `show memory` and `quit` commands.

## Tech stack
Python 3.12 (3.10+ works), Streamlit, ChromaDB, openai SDK (pointed at OpenRouter), python-dotenv, pytest.

## How it works
1. User sends a message.
2. `MemoryStore.search` finds the top-k most similar stored memories.
3. `OpenRouterClient.generate` sends recent chat history plus those memories (as data-only context) to OpenRouter.
4. On success the message is saved to memory; on failure nothing is saved, so a retry never duplicates it.

## Project structure
```
app.py                 Streamlit UI
agent.py               CLI
memory_agent/          config.py, memory.py (ChromaDB), llm.py (OpenRouter), service.py (orchestration)
tests/                 pytest suite (fakes for ChromaDB and OpenRouter)
DEPLOYMENT.md  TESTING.md  .env.example  requirements.txt
```

## Setup
```bash
git clone https://github.com/siddhanthjain1405-debug/Python-Project-AI.git
cd Python-Project-AI
python -m venv .venv
.venv\Scripts\Activate.ps1                             # Windows PowerShell (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
Copy-Item .env.example .env                            # Mac/Linux: cp .env.example .env
# open .env and put your real OPENROUTER_API_KEY in it
streamlit run app.py                                   # web UI
python agent.py                                        # or the CLI
```
If PowerShell blocks the activate script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
Get a free key at https://openrouter.ai/keys. Without a key the app starts in demo mode.

## API configuration
| Setting | Where | Default |
|---|---|---|
| `OPENROUTER_API_KEY` | `.env` (local) or Streamlit Secrets (cloud) | none (demo mode) |
| `OPENROUTER_MODEL` | `.env` / Secrets | `openrouter/free` |
| `MEMORY_DIR` | `.env` | `./agent_brain` |
| `MEMORY_TOP_K` | `.env` | `3` |

The app talks to OpenRouter's OpenAI-compatible endpoint (`https://openrouter.ai/api/v1`). **Only free models are allowed**: `openrouter/free` or a model id ending in `:free`. Any other model name is refused before a request is sent, and there is no fallback to another model, so a paid model is never called. Replies are capped at 600 tokens and the system prompt asks for short answers.

## Testing results
See [TESTING.md](TESTING.md) for exactly what was and was not verified.

## Demo script for evaluators
1. Chat: "My name is Ayush and I study computer science." then "I love playing chess."
2. Stop the app, start it again (memory persists on disk).
3. Ask: "What is my name and what game do I like?" and expand **Memories recalled**.
4. Open **Memory vault**: add, filter, delete and export memories.

## Limitations
- Every message is stored, including questions; there is no automatic fact extraction yet.
- On free hosting (e.g. Streamlit Community Cloud) the disk is ephemeral, so memory can reset when the app restarts. Profiles are not password-protected.

## Future scope
LLM-based fact extraction and de-duplication, user login, a hosted vector database for durable memory, memory expiry, voice input.
