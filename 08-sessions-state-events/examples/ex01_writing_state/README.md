# Example 01 — Writing state, 3 right ways + 1 wrong

```powershell
python run.py        # creates ex01.db (SQLite via DatabaseSessionService)
```

## Captured output

```
after agent turn:
  state['current_topic'] = black holes           (method b: tool context.state)
  state['last_reply']    = Black holes are a fascinating subject! ...  (method a: output_key)
  'temp:noted_at' present? False                  (temp: dropped after the invocation)

after append_event (method c):
  state['turn'] = 1   state['user:visit_count'] = 1

wrong way (direct mutation of get_session().state):
  'hacked' in a freshly fetched session? False   <- change did NOT persist
```

## The four lessons

| # | Method | Code | When |
|---|---|---|---|
| a | `output_key` | `LlmAgent(output_key="last_reply")` | capture the agent's final text |
| b | `context.state` | `tool_context.state["current_topic"] = topic` | inside a tool / callback — **preferred** |
| c | `EventActions.state_delta` | `append_event(s, Event(actions=EventActions(state_delta={...})))` | out-of-band, bulk, or system updates |
| ✗ | direct mutation | `get_session().state["x"] = ...` | **never** — bypasses events, doesn't persist, races |

`temp:noted_at` was written by the tool but is gone by the time we re-fetch — `temp:`
lives only for that one invocation.
