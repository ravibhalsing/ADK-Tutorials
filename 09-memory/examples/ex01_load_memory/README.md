# Example 01 — `load_memory` (agent-invoked recall)

```powershell
python run.py
```

## Captured output

```
--- Turn 1 (session A): capture ---
user> I'm allergic to shellfish and my project deadline is March 14.
agent> Noted. You're allergic to shellfish and your project deadline is March 14th.

(session A saved to memory)

--- Turn 2 (session B, brand new): recall ---
user> When is my deadline, and is there anything I can't eat?
  [tool] load_memory({'query': 'deadline and dietary restrictions'})
agent> Your project deadline is March 14, and you are allergic to shellfish.
```

## Flow

1. Session A: a plain agent acknowledges the fact.
2. `await memory_service.add_session_to_memory(completed_session_A)` — archive it.
3. Session B is **brand new** (no shared history). The recall agent has `load_memory` in
   `tools`, so the model issues `load_memory(query=...)`, ADK searches memory, and the
   answer comes from the hits.

`InMemoryMemoryService` does keyword matching — it still found "deadline" and "shellfish".
Real deployments use `VertexAiMemoryBankService` (semantic) — see `../ex04`.
