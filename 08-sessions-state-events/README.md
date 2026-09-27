# Module 08 — Sessions, State & Events

> **Goal:** understand the data model behind every conversation — `Session`, `Event`,
> `State` — the four state scopes, the *right* ways to write state, and how to make it
> **persist** with `DatabaseSessionService`.
>
> **Docs:** [Sessions](https://adk.dev/sessions/) ·
> [State](https://adk.dev/sessions/state/) ·
> [Session object](https://adk.dev/sessions/session/) ·
> [Events](https://adk.dev/events/)

---

## 1. The three objects

```
Session                         one conversation thread
├── id / app_name / user_id     identity  (addressed by the triple app/user/session)
├── state: dict                 the scratchpad — key/value, serializable only
├── events: list[Event]         append-only history of everything that happened
└── last_update_time
```

- **`Event`** — one immutable step: a user message, a model reply, a tool call, a tool
  result, a state change, an error. Carries `content`, `author`, `actions`
  (`state_delta`, `artifact_delta`, …), `usage_metadata`, ids, timestamps.
- **`State`** — the mutable key/value store *inside* a session. History is in `events`;
  the current values are in `state`. They stay consistent because every state change
  rides on an event as a `state_delta`.

---

## 2. State scopes — the prefix decides everything

| Prefix | Scope | Persists (DB/Vertex)? | Use for |
|---|---|---|---|
| *(none)* | this **session** | yes | task progress, current intent, per-conversation flags |
| `user:` | all sessions of this **user_id** | yes | preferences, profile, saved tokens |
| `app:` | all users of this **app_name** | yes | global config, feature flags, shared templates |
| `temp:` | this **invocation** only | **no** — discarded after the turn | intermediate values, tool→tool hand-off |

```python
ctx.state["booking_step"]        = "confirm"      # session
ctx.state["user:preferred_lang"] = "fr"           # user
ctx.state["app:discount_code"]   = "SAVE10"       # app
ctx.state["temp:raw_response"]   = {...}          # invocation
```

`temp:` is shared between a parent agent and its sub-agents within one invocation.
With `InMemorySessionService` *everything* is lost on restart — the prefixes only differ
once you use a persistent service.

---

## 3. Writing state — the three correct ways

### a) `output_key` — capture the agent's final text

```python
LlmAgent(name="summarizer", output_key="summary", instruction="Summarize in 2 sentences.")
# -> state["summary"] = "<the text>"  (or the parsed object if output_schema is set)
```

### b) `context.state` in a tool or callback — **the recommended way**

```python
def my_tool(x: str, tool_context: ToolContext) -> dict:
    n = tool_context.state.get("call_count", 0)
    tool_context.state["call_count"] = n + 1
    tool_context.state["temp:last_x"] = x
    return {"status": "success"}
# the change is captured into the event's state_delta automatically
```

### c) `EventActions.state_delta` + `append_event` — for out-of-band / bulk updates

```python
from google.adk.events import Event, EventActions

evt = Event(author="system", actions=EventActions(state_delta={
    "task_status": "active",
    "user:login_count": session.state.get("user:login_count", 0) + 1,
    "temp:needs_validation": True,
}))
await session_service.append_event(session, evt)
```

### ❌ Never do this

```python
s = await session_service.get_session(...)
s.state["key"] = "value"          # WRONG
```
It bypasses event history, **won't persist** with a DB/Vertex service, isn't thread-safe,
and doesn't bump `last_update_time`. Reading `s.state` is fine; writing it is not.

---

## 4. `SessionService` implementations

| Service | Construct | Persists? | Use |
|---|---|---|---|
| `InMemorySessionService()` | — | no | dev, tests, examples |
| `DatabaseSessionService(db_url=...)` | `google-adk[db]` | yes | self-hosted prod (Cloud SQL, RDS, local SQLite) |
| `VertexAiSessionService(project=, location=)` | `google-adk[gcp]` + Agent Engine | yes, managed | Agent Engine deploys (Module 23) |

`db_url` examples:
```python
"sqlite+aiosqlite:///./sessions.db"                        # local file
"postgresql+asyncpg://user:pass@host:5432/adk"             # Postgres
"mysql+aiomysql://user:pass@host:3306/adk"                 # MySQL
"postgresql+asyncpg://user:pass@/adk?host=/cloudsql/PROJECT:REGION:INSTANCE"  # Cloud SQL socket
```

Wire it into the `Runner` (or `adk` CLI / API server):
```python
runner = Runner(agent=root_agent, app_name="app", session_service=DatabaseSessionService(db_url))
```
```bash
adk run my_agent --session_service_uri "sqlite+aiosqlite:///./sessions.db"
adk api_server   --session_service_uri "postgresql+asyncpg://..."
```

### Operations (all async)

```python
await session_service.create_session(app_name=, user_id=, session_id=?, state=?)
await session_service.get_session(app_name=, user_id=, session_id=)
await session_service.list_sessions(app_name=, user_id=)
await session_service.delete_session(app_name=, user_id=, session_id=)
await session_service.append_event(session, event)
```

Schema migrations: `adk migrate session --session_service_uri ...` after an ADK upgrade.

---

## 5. Examples

| Folder | Shows |
|---|---|
| `ex01_writing_state/` | the 3 write methods side by side + the "don't mutate directly" failure |
| `ex02_state_scopes/` | `user:` / `app:` / `temp:` / session across two users and two sessions, on SQLite so it's real |
| `ex03_database_persistence/` | `DatabaseSessionService`; run the script **twice** — the conversation survives; list/get/delete |
| `ex04_event_history/` | dump every `Event` of a stored session: authors, content kinds, `state_delta`, usage |

---

## 6. Production notes

- **Pick the backend by deploy target:** Cloud Run → `DatabaseSessionService` on Cloud
  SQL; Agent Engine → `VertexAiSessionService` (automatic); GKE → your choice.
- **Connection pooling.** `DatabaseSessionService` uses a SQLAlchemy async engine — tune
  pool size for your concurrency; use the Cloud SQL connector / a proxy.
- **Concurrency.** `append_event` serializes writes per session (row lock). Two requests
  on the *same* session still race at the app layer — design for it.
- **PII & retention.** `state` and `events` often hold personal data. Set a TTL / archival
  job; support hard delete (`delete_session`) for GDPR/DSAR. Consider field-level
  encryption for sensitive `state`.
- **Size.** Event history grows unbounded. Long conversations → context compression
  (Module 10) and/or periodic summarize-and-truncate.
- **Migrations.** Run `adk migrate session` in your deploy pipeline after ADK upgrades.
- **Backups.** It's your database — back it up like one.

---

## 7. Exercises

1. In `ex01`, add a 4th "wrong" path that mutates `get_session().state` directly, then
   re-fetch — show the change vanished (with the DB service).
2. In `ex02`, add a second `app_name` and confirm `app:` state does **not** cross apps.
3. Run `ex03` three times. On run 2 and 3 the agent should greet you by the name you
   gave on run 1. Then `delete_session` and confirm it forgets.
4. Point `adk run` at a Postgres URL (spin up `docker run postgres`) and have a
   conversation; inspect the `sessions` / `events` tables with `psql`.
5. Write a `state_delta` event that bumps a `user:visit_count` and a `temp:` flag in one
   `append_event`; verify only the `user:` one is in the next session you open.

---

## 8. Checklist

- [ ] Explain `Session` vs `Event` vs `State`
- [ ] Choose the right prefix for a given piece of data
- [ ] Write state 3 correct ways; say why direct mutation fails
- [ ] Stand up `DatabaseSessionService` with a SQLite `db_url` and prove persistence
- [ ] List / get / delete sessions
- [ ] Read `state_delta` off an event in stored history

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| State change "doesn't stick" | you mutated `session.state` directly — use `context.state` / `state_delta` |
| `ModuleNotFoundError: aiosqlite` | `pip install "google-adk[db]"` |
| `sqlite+sqlite:///` errors | use the async driver: `sqlite+aiosqlite:///./sessions.db` |
| `user:`/`app:` state not shared | you're on `InMemorySessionService` — switch to DB/Vertex |
| `temp:` value gone next turn | that's correct — `temp:` lives only for one invocation |
| DB schema errors after ADK upgrade | `adk migrate session --session_service_uri ...` |
| Two turns on one session clobber each other | app-layer race; don't run concurrent turns on the same session id |
