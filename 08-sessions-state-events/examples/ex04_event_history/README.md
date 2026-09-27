# Example 04 — Event history of a stored session

Reads the SQLite DB written by `ex03` and dumps every `Event`. No LLM calls.

```powershell
python ..\ex03_database_persistence\run.py     # once or twice, to build history
python run.py
```

## Captured output

```
session 9841a128-...
  final state = {'user:name': 'Ravindra'}
  6 events:

  # 1  author=user       text[20]               final=True
  # 2  author=host       call:remember_name     final=False  tok=153
  # 3  author=host       resp:remember_name     final=False
       state_delta = {'user:name': 'Ravindra'}
  # 4  author=host       text[77]               final=True   tok=181
  # 5  author=user       text[3]                final=True
  # 6  author=host       text[29]               final=True   tok=236
```

## Takeaways

- The event log is the **source of truth**; `state` is a projection of all the
  `state_delta`s. Here `user:name` was set by the `state_delta` on event #3.
- Each model step records `usage_metadata` (token counts) — this is your per-turn cost data.
- `author` is `"user"` or the agent name.
- Note `is_final_response()` is `True` for **user** events too (events #1, #5) — it means
  "not partial, no pending tool call", not "the agent's answer". In a UI you gate on
  `event.author != "user"` **and** `is_final_response()`.
