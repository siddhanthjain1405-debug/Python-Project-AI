# Testing

## Automated tests (fakes for ChromaDB and the OpenRouter client)
```powershell
pip install -r requirements-dev.txt
python -m pytest -q
```
Expected: **37 passed**.

### Result recorded in the build sandbox
| Check | Result |
|---|---|
| 37 tests (memory, OpenRouter wrapper, free-only guard, chat service, config) | **37 passed**, run with a small pytest stand-in because the sandbox had no internet (real pytest could not be installed) |
| `python -m py_compile` on `app.py`, `agent.py`, `memory_agent/*` | passed |

Please re-run `python -m pytest -q` on your PC: that is the real confirmation.

## NOT verified (no internet, no package index, no API key in the sandbox)
- `pip install -r requirements.txt` (including the new `openai` package).
- `streamlit run app.py`: the UI was not launched here.
- Real ChromaDB persistence and the first-time embedding model download.
- A real OpenRouter reply, and the real invalid-key error. The tests only use fake clients.
- Whether `openrouter/free` has a free model available at the moment you test (free capacity can be busy).

## Manual end-to-end checklist
- [ ] `streamlit run app.py` starts and the page loads.
- [ ] No key: Demo mode shown; message saved to memory.
- [ ] With key: sidebar says OpenRouter connected; "hi" gets a one-line reply.
- [ ] "My name is X", then "what is my name?": reply uses the memory; "Memories recalled" shows it.
- [ ] Wrong key pasted in the sidebar: readable error, nothing saved.
- [ ] Stop and restart the app: memories still in the vault.
- [ ] Vault: add, filter, delete, export JSON, delete-all.
- [ ] Empty and 4000+ character messages are rejected politely.
