"""Command-line version of the Memory Agent.

Run with:  python agent.py
Commands:  'show memory' lists stored memories, 'quit' exits.
For the web interface run:  streamlit run app.py
"""

from memory_agent import (
    AIError,
    OpenRouterClient,
    MemoryStoreError,
    chat_with_memory,
    load_settings,
    open_store,
)


def main() -> None:
    settings = load_settings()

    try:
        store = open_store("default", settings.memory_dir)
    except MemoryStoreError as exc:
        print(f"Error: {exc}")
        return

    try:
        llm = OpenRouterClient(settings.api_key, settings.model) if settings.api_key else None
    except AIError as exc:
        print(f"Error: {exc}")
        return
    if llm is None:
        print("⚠️  OPENROUTER_API_KEY is not set: running in DEMO mode (memories are saved and "
              "recalled, but no AI replies are generated).")

    print("🧠 Memory Agent is online! (Type 'quit' to exit, or 'show memory' to look inside)")

    history: list[dict] = []
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nShutting down...")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Shutting down...")
            break

        if user_input.lower() == "show memory":
            items = store.list_items()
            print("\n--- 🗄️ LOOKING INSIDE THE VAULT ---")
            if not items:
                print("Memory is totally empty!")
            for item in items:
                print(f"[{item.id}] -> {item.text}")
            continue

        try:
            result = chat_with_memory(store, llm, user_input, history, settings.top_k)
        except (ValueError, AIError, MemoryStoreError) as exc:
            print(f"\n⚠️  {exc}")
            continue

        if result.memories_used:
            print("\n[Memories recalled: " + " | ".join(result.memories_used) + "]")

        if result.demo_mode:
            print("Agent: (demo mode - no AI reply. Message saved to memory.)")
        else:
            print(f"Agent: {result.reply}")
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": result.reply})


if __name__ == "__main__":
    main()
