# Example 03 — `DatabaseSessionService` persistence

```powershell
python run.py            # run 1
python run.py            # run 2 — a NEW process, reads the same SQLite file
python run.py --list     # inspect stored sessions
python run.py --reset    # delete them
```

## Captured output

```
=== RUN 1 ===  (new process)
(no stored session — starting fresh)
user> Hello, I'm Ravindra.
agent> Hello Ravindra, it's nice to meet you! I've saved your name for future chats.
stored: 4 events, state={'user:name': 'Ravindra'}

=== RUN 2 ===  (a DIFFERENT process)
(resuming session 9841a128… from the database)
user> Hi!
agent> Hello Ravindra, welcome back!
stored: 6 events, state={'user:name': 'Ravindra'}

=== --list ===
  9841a128-...  events=6  state={'user:name': 'Ravindra'}
```

## Takeaways

```python
DB = "sqlite+aiosqlite:///./ex03.db"        # async driver required
svc = DatabaseSessionService(db_url=DB)
runner = Runner(agent=..., app_name=..., session_service=svc)
```

- Run 2 is a **separate Python process**. It found the prior session via
  `list_sessions`, re-`get_session`'d it, and the agent had full history + `user:name`
  from `{user:name?}` templating.
- `create_session`, `get_session`, `list_sessions`, `delete_session`, `append_event`
  are all `await`ed.
- The same works from the CLI:
  `adk run my_agent --session_service_uri "sqlite+aiosqlite:///./sessions.db"`.
- For prod, swap the `db_url` for Postgres/MySQL (`postgresql+asyncpg://…`). Nothing else
  changes.
