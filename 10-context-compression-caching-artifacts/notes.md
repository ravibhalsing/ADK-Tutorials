# Module 10 — official documentation cross-reference

| Topic | Page |
|---|---|
| Context compaction | https://adk.dev/context/compaction/ |
| Context caching | https://adk.dev/context/caching/ |
| Artifacts | https://adk.dev/artifacts/ |
| RunConfig (`save_input_blobs_as_artifacts`) | https://adk.dev/runtime/runconfig/ |

## Confirmed on this machine (ADK 2.8.0, Vertex, gemini-2.5-flash, 2026-09-05)

- Compaction & caching config live on **`App`**, passed to `Runner(app=..., session_service=...)`:
  - `from google.adk.apps.app import App, EventsCompactionConfig`
  - `from google.adk.agents.context_cache_config import ContextCacheConfig`
  - `App(*, name, root_agent, plugins, events_compaction_config, context_cache_config,
    resumability_config)`
  - `Runner(*, app=None, app_name=None, agent=None, ..., session_service (required),
    artifact_service=None, memory_service=None)`

- **Compaction (ex03)** `EventsCompactionConfig(compaction_interval=3, overlap_size=1)`:
  after enough events, a **compaction event** appears in `session.events` (author `user`,
  empty content) with `event.actions.compaction` = object holding `start_timestamp`,
  `end_timestamp`, `compacted_content` (a `Content` with the LLM summary). Verified: the
  agent still answered "what's my name / trip length" from an early turn via the summary.
  Params also: `token_threshold`, `event_retention_size` (token-based, takes priority),
  `summarizer=LlmEventSummarizer(...)`.

- **Caching (ex04)** `ContextCacheConfig(min_tokens=1024, ttl_seconds=600, cache_intervals=10)`
  with a ~7k-token static instruction:
  - turn 1: `usage_metadata.prompt_token_count=6861`, `cached_content_token_count=6119`,
    `event.cache_metadata` = "Fingerprint-only: 0 contents, fingerprint=..."
  - turn 2: `prompt=6888`, `cached=6880` (~99%), `cache_metadata` =
    "Cache <id>: used 1 invocations, cached 2 contents, expires in 9.7min"
  - Defaults: `min_tokens=0`, `ttl_seconds=1800`, `cache_intervals=10`. Gemini 2.0+.

- **Artifacts (ex01, ex02)**:
  - `from google.adk.artifacts import InMemoryArtifactService, GcsArtifactService`
  - `from google.adk.tools.load_artifacts_tool import LoadArtifactsTool`
  - `types.Part.from_bytes(data=bytes, mime_type="text/plain")`.
  - `await tool_context.save_artifact(filename=, artifact=part)` → version int (0,1,2…).
  - `await tool_context.load_artifact(filename=, version=None)` → latest / specific.
  - `await tool_context.list_artifacts()` → list of names (keeps `user:` prefix).
  - Direct service API: `artifact_service.list_artifact_keys(app_name=, user_id=,
    session_id=)`, `.list_versions(...filename=)`, `.load_artifact(...)`.
  - `user:` prefix → cross-session artifact. Verified: `meeting.txt` got versions [0,1];
    `user:prefs` version [0].
  - `LoadArtifactsTool()` call arg is `artifact_names=[...]`.
  - Uploaded file = extra `types.Part.from_bytes(...)` in the user message `Content`.

## Imports

```python
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.artifacts import InMemoryArtifactService, GcsArtifactService
from google.adk.tools.load_artifacts_tool import LoadArtifactsTool
from google.genai import types   # types.Part.from_bytes, types.Blob
```
