# Example 04 — `VertexAiMemoryBankService` (managed, semantic)

Needs an **Agent Engine** instance (it hosts the Memory Bank and managed sessions).

## One-time setup

```python
# pip install "google-cloud-aiplatform[adk,agent_engines]"
import vertexai
from vertexai import agent_engines
vertexai.init(project="gcp-learning-469104", location="us-central1")
ae = agent_engines.create()                 # empty engine — just for memory + sessions
print(ae.resource_name)                      # projects/.../reasoningEngines/NNNNNNNNNN
```

`.env`:
```
AGENT_ENGINE_ID=NNNNNNNNNN
```

```powershell
python run.py       # without AGENT_ENGINE_ID it prints these steps and exits
```

## What's different from `InMemory`

```python
memory_service  = VertexAiMemoryBankService(project=P, location=L, agent_engine_id=ENGINE)
session_service = VertexAiSessionService(project=P, location=L)
```

- **Semantic search**, not keyword.
- **Consolidation**: "I'm vegetarian and I live in Pune" becomes durable facts
  (`user is vegetarian`, `user location: Pune`) rather than a raw transcript line — so a
  later "suggest a lunch spot" retrieves the *facts*, not the sentence.
- Fully managed persistence; pairs with `VertexAiSessionService` (Module 08 / 23).
- CLI: `adk web agents/ --memory_service_uri "agentengine://NNNNNNNNNN"`.

## Cost / ops

Memory Bank ingestion + consolidation is billed and asynchronous. Don't block the
request on it — the `after_agent_callback` in this example is fine for a demo; in prod,
enqueue the save. Deletion APIs exist for right-to-be-forgotten.
