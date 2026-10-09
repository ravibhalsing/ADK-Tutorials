# Module 09 — official documentation cross-reference

| Topic | Page |
|---|---|
| Memory (services, tools, auto-save, consolidation) | https://adk.dev/sessions/memory/ |
| Sessions/state (contrast) | https://adk.dev/sessions/state/ |
| Grounding / Vertex AI Search (doc RAG) | https://adk.dev/grounding/ (Module 04) |

## Confirmed on this machine (ADK 2.8.0, Vertex, 2026-09-05)

- `from google.adk.memory import InMemoryMemoryService, VertexAiMemoryBankService,
  VertexAiRagMemoryService` — all import.
- `from google.adk.tools import load_memory, preload_memory` → `LoadMemoryTool` /
  `PreloadMemoryTool` instances (drop into `tools=[...]`).
- **`search_memory(*, app_name, user_id, query)`** → `SearchMemoryResponse` with
  `.memories` (each has `.content.parts`).
- **`add_session_to_memory(session)`** — positional session only for InMemory.
- **`add_events_to_memory(*, app_name, user_id, events, session_id=None,
  custom_metadata=None)`** — this is how you seed an InMemory "docs" corpus (one `Event`
  per snippet, `author="docs"`).
- **`add_memory(app_name, user_id, memories=[MemoryEntry(...)])`** — **`InMemoryMemoryService`
  raises `NotImplementedError`**; only `VertexAiMemoryBankService` supports direct writes
  (with `custom_metadata={"enable_consolidation": True}` for fact consolidation).
- **`tool_context.search_memory(query)`** works inside a `FunctionTool` (async).
- **Auto-save**: `after_agent_callback=async def(cb): await cb.add_session_to_memory()`.
  Verified: session 2 recalled session 1 facts with NO manual add/search (ex02).
- **`preload_memory`** injects hits pre-model each turn; `load_memory` is a
  model-invoked tool. Both verified.
- InMemory search is keyword-based — found "deadline"/"shellfish"/"retention" fine in
  the examples; won't do semantic matching.
- ex03: combined a doc fact ("SAML = Enterprise only") with a conversation memory
  ("we're on Pro") to answer "no SAML for you".
- `VertexAiMemoryBankService(project, location, agent_engine_id)` +
  `VertexAiSessionService(project, location)` — need an Agent Engine
  (`vertexai.agent_engines.create()`); ex04 is the pattern, not run here.

## Imports

```python
from google.adk.memory import (
    InMemoryMemoryService, VertexAiMemoryBankService, VertexAiRagMemoryService,
)
from google.adk.tools import load_memory, preload_memory   # + ToolContext.search_memory
from google.adk.sessions import VertexAiSessionService
```
