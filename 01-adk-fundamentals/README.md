# Module 01 — ADK Fundamentals & Your First Real Agent

> **Goal:** understand exactly what happens between "user types a message" and "agent
> replies" — the `Agent`, the `Runner`, the `Session`, and the **event loop** — and be
> able to run an agent three ways (`adk run`, `adk web`, programmatic `Runner`) and read
> its event stream.
>
> **Official docs:** [LLM agents](https://adk.dev/agents/llm-agents/) ·
> [Event Loop](https://adk.dev/runtime/) ·
> [API server](https://adk.dev/runtime/api-server/) ·
> [Runtime config](https://adk.dev/runtime/runconfig/) ·
> [Python get-started](https://adk.dev/get-started/python/)
>
> **Prereq:** Module 00 done — venv active, `verify_setup.py` passes, Vertex ADC working.

---

## 1. The four things every LLM agent has

```python
from google.adk.agents import Agent   # `Agent` is an alias for `LlmAgent`

root_agent = Agent(
    name="country_agent",              # 1. identity — unique, must start with a letter,
                                       #    not "user". Used for logging + multi-agent routing.
    model="gemini-2.5-flash",          # 2. the LLM that does the reasoning
    description="Answers questions about countries.",  # 3. one line — what other AGENTS
                                       #    read to decide whether to delegate here (Module 12)
    instruction="You answer questions about countries...",  # 4. the behavioural brief the
                                       #    model itself follows every turn
)
```

| Field | Who reads it | Notes |
|---|---|---|
| `name` | ADK (logs, traces), other agents | `^[a-zA-Z][a-zA-Z0-9_]*$`, avoid `user`. The **folder** name also becomes the "app name" with the same rule. |
| `model` | ADK → model provider | A string id (`"gemini-2.5-flash"`) resolves via Gemini/Vertex. A `LiteLlm(...)` object routes elsewhere (Module 14). |
| `description` | **other LLM agents** | Metadata for delegation. Ignored in a single-agent app, but always write it. |
| `instruction` | **this agent's model** | The system prompt. Task, persona, constraints, when to use which tool, output format. Module 02 goes deep. |

`instruction` and `description` are different jobs: `description` sells the agent to a
coordinator; `instruction` tells the agent how to behave.

### Instruction templating

`instruction` can be a plain string, or a string with placeholders filled from session
state at runtime:

- `{topic}` — insert `session.state["topic"]` (errors if missing)
- `{topic?}` — insert if present, silently skip if not
- `{artifact.report}` — insert the text of an artifact named `report`

Or a **callable** `(ReadonlyContext) -> str` for full programmatic control (Module 02).

---

## 2. What actually runs a turn: the event loop

You never call the model directly. This runs the show:

```
┌─────────┐   new_message    ┌──────────────────────────┐
│  your   │ ───────────────▶ │         Runner           │
│  code / │                  │  (the orchestrator)      │
│  adk cli│ ◀─────────────── │                          │
└─────────┘   async stream   └──────────┬───────────────┘
                of Events                │ creates InvocationContext,
                                         │ drives the agent, commits state
                                         ▼
                              ┌──────────────────────────┐
                              │   Agent + tools + model  │
                              │   yields Event, PAUSES,   │
                              │   resumes after Runner    │
                              │   commits the changes     │
                              └──────────────────────────┘
                                         │
                          ┌──────────────┼───────────────┐
                          ▼              ▼               ▼
                   SessionService  ArtifactService  MemoryService
```

The loop, step by step (from the [Event Loop docs](https://adk.dev/runtime/)):

1. **Runner** appends your `new_message` to the session history via `SessionService`.
2. Runner starts the agent. The agent builds an LLM request (history + instruction +
   tool schemas) and calls the model.
3. The agent **yields an `Event`** (e.g. "model wants to call `get_weather(city=…)`")
   and **pauses**.
4. Runner processes that event: commits any `state_delta` / `artifact_delta`, appends the
   event to history, forwards it to you.
5. Runner tells the agent to **resume**. It now sees committed state. It runs the tool,
   yields another event (the tool result), pauses again…
6. Model is called again with the tool result, produces the final text, agent yields a
   **final event** (`is_final_response() == True`).
7. Agent has nothing left to yield → the invocation ends.

**Why the pause/resume matters:** a state change you make in a tool is only *guaranteed
persisted* after the event carrying its `state_delta` has been yielded and processed by
the Runner. Don't rely on `state` you wrote earlier in the same tool call until the next
event boundary.

### Vocabulary

| Term | Meaning |
|---|---|
| **Invocation** | One user query → its complete processing (may span many model calls & tool calls). Has an `invocation_id`. |
| **Turn** | One user message + the agent's full response to it. |
| **Step** | One "model call + the tool calls it triggers" cycle inside an invocation. |
| **Event** | One immutable item in the stream / history: a message chunk, a tool call, a tool result, a state change, an error. |

---

## 3. The `Event` object — your debugging surface

Every item from `run_async` is an `Event`. Fields you'll use constantly:

| Field / method | What it tells you |
|---|---|
| `event.author` | `"user"` or the agent name that produced it |
| `event.content` | a `google.genai.types.Content` (role + parts); parts hold `text`, `function_call`, or `function_response` |
| `event.get_function_calls()` | list of `FunctionCall` (name, args) — the model wants a tool run |
| `event.get_function_responses()` | list of `FunctionResponse` (name, response) — a tool returned |
| `event.is_final_response()` | `True` for the user-facing answer event (not partial, no pending tool calls) |
| `event.partial` | `True` for a streaming text fragment (SSE mode); actions are **not** committed on partials |
| `event.turn_complete` | `True` when the agent is fully done with this turn |
| `event.actions` | an `EventActions`: `state_delta`, `artifact_delta`, `transfer_to_agent`, `escalate`, `skip_summarization` |
| `event.usage_metadata` | token counts (prompt / candidates / total) for this step — cost tracking |
| `event.invocation_id`, `event.id`, `event.timestamp` | correlation ids + time |
| `event.error_code`, `event.error_message` | set when a step failed |
| `event.long_running_tool_ids` | ids of long-running tools awaiting completion (Module 03) |

Rule of thumb for a chat UI: **render `event.content` when `event.is_final_response()`**,
and (optionally) stream `event.partial` text before that.

---

## 4. Running an agent — the three surfaces

All three use the **same** `Runner` + services underneath. They differ only in the shell
around it.

### A. `adk run <folder>` — terminal REPL

```powershell
# from the folder that CONTAINS the agent package
adk run ex01_multi_tool_agent
```
Interactive loop, `exit` to quit. Great for a quick behavioural check. Flags:
`--log_level DEBUG`, `--session_service_uri`, `--artifact_service_uri`,
`--replay <file.json>`, `--save_session`.

### B. `adk web` — the dev UI  ⚠️ development only

```powershell
adk web            # http://localhost:8000
```
Chat + a live **Events / Trace** inspector (see every model request, tool call, token
count), plus tabs for eval and artifacts. This is your primary debugging tool. It is
**not** a production server — no auth, single-process, in-memory by default.

### C. Programmatic `Runner` — the real thing

```python
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from country_agent.agent import root_agent

async def main():
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="country_app",
        session_service=session_service,
    )
    session = await session_service.create_session(
        app_name="country_app", user_id="u1"
    )
    msg = types.Content(role="user", parts=[types.Part(text="Capital of Japan?")])
    async for event in runner.run_async(
        user_id="u1", session_id=session.id, new_message=msg
    ):
        if event.is_final_response():
            print(event.content.parts[0].text)

asyncio.run(main())
```

`InMemoryRunner(agent, app_name="…")` is a shortcut that wires up in-memory
session/artifact/memory services for you (used in Module 00). Use the explicit `Runner`
when you need a real `SessionService` (Module 08) — that's the only change to go from
laptop to production.

### D. `adk api_server` — the production HTTP contract (preview here, deep in Module 21)

```powershell
adk api_server                 # FastAPI on http://localhost:8000, Swagger at /docs
```

```bash
# 1. list agents
curl http://localhost:8000/list-apps

# 2. create a session
curl -X POST http://localhost:8000/apps/ex01_multi_tool_agent/users/u1/sessions/s1 \
  -H "Content-Type: application/json" -d '{}'

# 3. run a turn (collect all events)
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"appName":"ex01_multi_tool_agent","userId":"u1","sessionId":"s1",
       "newMessage":{"role":"user","parts":[{"text":"weather in Paris?"}]}}'

# 3b. or stream events as they happen
curl -N -X POST http://localhost:8000/run_sse -H "Content-Type: application/json" \
  -d '{"appName":"ex01_multi_tool_agent","userId":"u1","sessionId":"s1",
       "newMessage":{"role":"user","parts":[{"text":"weather in Paris?"}]},"streaming":true}'
```

JSON is **camelCase** on the wire (`appName`, `userId`, `sessionId`, `newMessage`).
Sessions are addressed by the triple `app_name / user_id / session_id`.

---

## 5. Streaming vs non-streaming

Controlled by `RunConfig` passed to `run_async`:

```python
from google.adk.agents.run_config import RunConfig, StreamingMode

cfg = RunConfig(
    streaming_mode=StreamingMode.SSE,   # NONE (default) | SSE | BIDI
    max_llm_calls=200,                   # cost circuit-breaker (default 500)
)
async for event in runner.run_async(..., run_config=cfg):
    ...
```

| Mode | Behaviour | Use |
|---|---|---|
| `NONE` (default) | one complete `Event` per model response | most agents, batch, tools-heavy |
| `SSE` | many `partial=True` text events, then one final non-partial event | chat UIs that show text as it types |
| `BIDI` | bidirectional audio/video via the Gemini Live API | voice agents (Module 20) |

Key detail: on `partial=True` events, **`actions` are not committed** — only the final
non-partial event applies `state_delta`. So streaming never causes half-applied state.

---

## 6. Project layout recap

```
01-adk-fundamentals/
└── examples/
    ├── ex01_multi_tool_agent/     # canonical 2-tool agent; run via adk run / adk web
    │   ├── __init__.py            #   from . import agent
    │   ├── agent.py               #   root_agent = Agent(... tools=[get_weather, get_current_time])
    │   ├── .env / .env.example
    │   └── README.md
    ├── ex02_runner_basics/        # build Runner + InMemorySessionService by hand
    │   ├── __init__.py, agent.py
    │   ├── run_multiturn.py       #   one session, 3 turns, prints final responses
    │   ├── inspect_events.py      #   dumps EVERY event field — the learning tool
    │   └── README.md
    └── ex03_api_server/           # hit `adk api_server` over HTTP
        ├── (reuses ex01's agent)
        ├── client.py              #   httpx client: create session, /run, /run_sse
        ├── curl_examples.sh
        └── README.md
```

Do them in order. `ex02/inspect_events.py` is the one to study closely — it makes the
event loop concrete.

---

## 7. API surface introduced in this module

| Import | Purpose |
|---|---|
| `google.adk.agents.Agent` / `LlmAgent` | the agent |
| `google.adk.runners.Runner` | explicit orchestrator (bring your own services) |
| `google.adk.runners.InMemoryRunner` | Runner + all-in-memory services shortcut |
| `google.adk.sessions.InMemorySessionService` | ephemeral session store |
| `google.adk.agents.run_config.RunConfig`, `StreamingMode` | per-run behaviour |
| `google.genai.types.Content`, `types.Part` | the message format |
| `Event` (`google.adk.events.Event`) | items in the stream / history |

---

## 8. Exercises

1. **Trace reading.** Run `ex01` in `adk web`, ask "what's the weather in Tokyo and what
   time is it?". In the Events panel, count: how many model calls, how many tool calls,
   how many events total? Sketch the loop.
2. **Break `is_final_response`.** In `inspect_events.py`, print `event.is_final_response()`
   for every event. Confirm it's `True` exactly once per turn, and only for the text
   answer — not for tool-call or tool-result events.
3. **Streaming diff.** Run `ex02/run_multiturn.py` once with `StreamingMode.NONE` and once
   with `SSE`. Print `event.partial`. Explain what changed in the event count.
4. **Two users, one agent.** In `run_multiturn.py`, create two sessions with different
   `user_id`s, send each a different fact to "remember", then ask each to recall. Confirm
   state does not leak between sessions.
5. **HTTP path.** Start `adk api_server`, run `ex03/client.py`. Then replay the same
   conversation with raw `curl` from `curl_examples.sh`. Diff the JSON you get from
   `/run` vs `/run_sse`.

---

## 9. Checklist — move to Module 02 when you can:

- [ ] Name the four required-ish `Agent` fields and who consumes each
- [ ] Draw the Runner ↔ agent event loop and say where state is committed
- [ ] Define invocation / turn / step / event
- [ ] Given an `Event`, tell whether it's a tool call, tool result, partial text, or final answer
- [ ] Write a programmatic `Runner` + `InMemorySessionService` from scratch
- [ ] Explain what changes (and what doesn't) between `adk run`, `adk web`, `api_server`, and a `Runner` in your own code
- [ ] Explain `StreamingMode.NONE` vs `SSE` and why partial events don't commit state

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `adk run` / `adk web` can't find the agent | Run from the folder that *contains* the package; check `__init__.py` has `from . import agent` and `agent.py` defines `root_agent` |
| `TypeError: create_session() missing ... 'app_name'` | It's keyword-only and **async**: `await session_service.create_session(app_name=..., user_id=...)` |
| `Runtimewarning: coroutine ... was never awaited` | You forgot `await` on a session-service call, or `async for` on `run_async` |
| `event.content` is `None` | Not every event has content (pure state-change / control events). Guard with `if event.content and event.content.parts` |
| Final answer printed twice | You're printing on every event *and* on `is_final_response()`; pick one |
| `max_llm_calls` limit hit | A tool loop or bad instruction is causing repeated calls; inspect events, raise the limit only if legitimately needed |
| `curl /run` returns `{"detail":"Session not found"}` | Create the session first (`POST /apps/.../sessions/...`) |
