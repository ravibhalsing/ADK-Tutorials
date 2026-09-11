# Module 01 — official documentation cross-reference

| Topic | Page |
|---|---|
| LlmAgent / Agent — all constructor params | https://adk.dev/agents/llm-agents/ |
| Agents overview (types) | https://adk.dev/agents/ |
| Runtime overview (adk run / web / api_server / ambient) | https://adk.dev/runtime/ |
| Event Loop (Runner ↔ agent, yield/pause, state commit timing) | https://adk.dev/runtime/ → "Event Loop" |
| Runtime Config (`RunConfig`, `StreamingMode`, `max_llm_calls`) | https://adk.dev/runtime/runconfig/ |
| API server (endpoints, curl, camelCase JSON) | https://adk.dev/runtime/api-server/ |
| Command line (`adk run` flags) | https://adk.dev/runtime/ → "Command Line" |
| Web interface / Visual Builder | https://adk.dev/runtime/ → "Web Interface" |
| Python get-started (project layout, first run) | https://adk.dev/get-started/python/ |
| CLI reference | https://adk.dev/api-reference/cli/ |
| Python API reference | https://adk.dev/api-reference/python/ |

## Confirmed behaviour on this machine (ADK 2.8.0, 2026-09-05)

Running `ex02/inspect_events.py` (prompt triggers one `word_count` tool call):

- **`StreamingMode.NONE`** → **3 events**: `functionCall` → `functionResponse` → final `text`
  (`is_final_response()` true only on the last). `event.partial` is `None`.
- **`StreamingMode.SSE`** → **6 events**: the `functionCall` arrives twice
  (`partial=True` then `partial=False`), then `functionResponse`, then two
  `partial=True` text fragments, then the final `partial=False` text with
  `is_final_response()` true.
- `event.usage_metadata` carries `prompt_token_count` / `candidates_token_count` /
  `total_token_count` on model events (may be `None` on some partial fragments).
- `event.author` is the agent `name` (`"assistant"` / `"multi_tool_agent"`), or `"user"`.
- `event.actions.state_delta` is `{}` here — no tool writes state yet (that's Module 08).

`run_multiturn.py`: 3 turns over one session ⇒ 8 stored events; session history alone
carries context (no `output_key`, no state writes). Two sessions with different
`user_id` do not share anything.

`ex03` API server: `GET /list-apps`, `POST /apps/{app}/users/{user}/sessions/{sid}`
(409 if it exists), `POST /run` (array of events, ~8s), `POST /run_sse`
(`data: {…}` lines, ~16s, ends at EOF). Wire JSON is camelCase.

## Key classes / imports

```python
from google.adk.agents import Agent, LlmAgent           # Agent is an alias
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner, InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.adk.events import Event
from google.genai import types                           # types.Content, types.Part
```

Session service methods are **async** and keyword-only:
`await session_service.create_session(app_name=..., user_id=..., session_id=..., state=...)`,
`await session_service.get_session(app_name=..., user_id=..., session_id=...)`.

`runner.run_async(user_id=..., session_id=..., new_message=types.Content(...), run_config=...)`
is an async generator of `Event`. `runner.run(...)` is the sync generator equivalent.

## ADK 1.x → 2.x notes

- Session service calls are async in 2.x (were sync in early 0.x).
- App/agent folder names must start with a letter (Pydantic-validated `App.name`).
- `global_instruction` is deprecated → use `GlobalInstructionPlugin` (Module 15).
- `output_schema` + `tools` on the same agent is only supported on newer models
  (e.g. Gemini 3); otherwise separate them.
