The big picture

Think of an AI agent like a customer-support chat widget. Every time a message goes back and forth, three things matter:

- Session — one conversation thread (like one WhatsApp chat window)
- State — the "memory" attached to that thread (the user's name, their theme preference, what they're negotiating for a refund)
- Events — the append-only log of everything that happened in that thread (every message, every tool call, every memory update) — like a bank statement, not editable, just recorded

Real use case: a support bot that needs to (1) remember your name across messages, (2) remember your account tier across all your chats even if you close and reopen the tab, (3) show a "banner" message to every customer, and (4) let a human agent later audit exactly what the bot said and did. That's exactly what these 4 examples demonstrate, one concept each.

ex01 — the right ways to save memory

Real-world analogy: you're filling out a form (state) while talking to a bank teller (agent). There are only 3 legit ways the form gets updated, and one fake way that looks like it works but doesn't.

1. output_key (run.py:42) — whatever the agent says as its final reply automatically gets saved into state under that key. Like the teller writing your last statement into your file automatically.
2. tool_context.state[...] (run.py:32) — inside a tool function (e.g., note_topic), you write directly to state. Like the teller manually jotting "customer wants a loan" into your file.
3. EventActions.state_delta + append_event (run.py:65-69) — updating state without an LLM call at all, e.g. a background job incrementing a visit counter. Like the branch manager updating your file overnight based on a report, no conversation needed.
4. The wrong way (run.py:75, near the line you selected) — grabbing the session object you fetched earlier and just doing s.state["hacked"] = "nope". This is like scribbling on a photocopy of your bank file — it feels like you changed something, but the real file (the database) never saw it. s2 = await svc.get_session(...) re-fetches from the DB and proves the change is gone. Lesson: session objects in memory are snapshots, not live links to the database — you must go through the session service to persist anything.

ex02 — state scopes (who sees what)

Real-world analogy: a hotel.
- plain key (step) — sticky note in this specific room, only visible in that one session
- user: prefix — a preference stored on your loyalty-card profile (e.g. "dark theme"), visible in every room you book (every session), but not to other guests
- app: prefix — the lobby announcement board — every guest, every room sees it
- temp: prefix — a whiteboard note that gets erased the moment this particular visit/interaction ends — never saved anywhere permanent

This matters in real apps: you don't want User A's session preferences leaking to User B, but you DO want a "system maintenance banner" (app:) to show to everyone, and you don't want throwaway scratch calculations (temp:) cluttering the permanent record.

ex03 — persistence (surviving a restart)

Real-world analogy: saving your progress in a video game instead of losing everything when you close the app.

DatabaseSessionService writes to an actual SQLite file (ex03.db) instead of just RAM. Run the script once — it asks your name. Close it. Run it again — it remembers you and greets you by name, because it pulled the saved user:name state back out of the database (run.py:80). This is the difference between a toy demo chatbot (forgets everything when the server restarts) and a real product (Slack bot, customer support tool) where users expect it to remember them days later.

--list and --reset are just admin utilities — like an admin panel to see or wipe stored conversations.

ex04 — event history (the audit trail)

Real-world analogy: your bank statement, or a call-center's "call recording + transcript" for compliance.

This script doesn't talk to any AI at all — it just opens ex03's database and prints every Event that ever happened in that session: who said what (author), whether it was a text reply or a tool call, and what state changed as a result (state_delta).

Real use case: if a customer disputes "the bot promised me a refund," you replay the event log to see exactly what was said and when — not just the final state, but the full timeline. This is also how you'd debug "why did state end up wrong" — you look at every state_delta in order rather than guessing.

How it all connects

┌─────────────┬───────────────────────────────────────┬─────────┐
│   Concept   │         Real-world equivalent         │ Example │
├─────────────┼───────────────────────────────────────┼─────────┤
│ Session     │ one conversation thread               │ all     │
├─────────────┼───────────────────────────────────────┼─────────┤
│ State       │ the "customer profile" attached to it │ ex01    │
├─────────────┼───────────────────────────────────────┼─────────┤
│ Scopes      │ who else can see that profile data    │ ex02    │
├─────────────┼───────────────────────────────────────┼─────────┤
│ Persistence │ saving so it survives a restart       │ ex03    │
├─────────────┼───────────────────────────────────────┼─────────┤
│ Events      │ immutable audit log of everything     │ ex04    │
└─────────────┴───────────────────────────────────────┴─────────┘



# Module 08 — official documentation cross-reference

| Topic | Page |
|---|---|
| Sessions overview | https://adk.dev/sessions/ |
| State (prefixes, update methods, warnings) | https://adk.dev/sessions/state/ |
| Session object & SessionService | https://adk.dev/sessions/session/ |
| Events | https://adk.dev/events/ |
| Memory (next module) | https://adk.dev/sessions/memory/ |

## Confirmed on this machine (ADK 2.8.0, 2026-09-05)

- **Install:** `pip install "google-adk[db]"` → SQLAlchemy 2.0 + aiosqlite. `pip check` clean.
- `DatabaseSessionService(db_url="sqlite+aiosqlite:///<abs-or-rel-path>")`. **Async driver
  is required** (`+aiosqlite`, `+asyncpg`, `+aiomysql`).
- All ops are `await`ed: `create_session(app_name=, user_id=, session_id=?, state=?)`,
  `get_session(...)`, `list_sessions(app_name=, user_id=)` → `.sessions`,
  `delete_session(...)`, `append_event(session, event)`.
- **Verified persistence**: process 1 creates a session + writes `user:name`; process 2
  (fresh interpreter) `list_sessions` → resumes → agent has full history + `{user:name?}`.
- **State scopes verified** on SQLite: `step` (session) only in the writing session;
  `user:theme` in all of that user's sessions, not other users'; `app:banner` everywhere;
  `temp:` never visible on a later read.
- **Write methods**: (a) `output_key` on the agent; (b) `tool_context.state[...] = ...`
  in a tool (auto-captured into that event's `state_delta`); (c) `append_event(s,
  Event(author="system", actions=EventActions(state_delta={...})))`. Direct mutation of a
  `get_session()` result does **not** persist (verified).
- **`Event.is_final_response()`** = `skip_summarization or long_running_tool_ids or
  (no function calls/responses and not partial and no trailing code result)`. It is
  **True for user-authored events too** — gate a UI on `author != "user"` as well.
- Event fields seen in stored history: `author`, `content.parts` (text / function_call /
  function_response), `actions.state_delta`, `usage_metadata.total_token_count`,
  `is_final_response()`.

## CLI

```bash
adk run  <agent> --session_service_uri "sqlite+aiosqlite:///./sessions.db"
adk api_server    --session_service_uri "postgresql+asyncpg://user:pw@host/db"
adk migrate session --session_service_uri "<url>"     # after an ADK upgrade
```

## Imports

```python
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
# VertexAiSessionService needs google-adk[gcp] + Agent Engine
from google.adk.events import Event, EventActions
```
