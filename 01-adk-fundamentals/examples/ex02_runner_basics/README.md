# Example 02 — Runner basics & the Event stream

Build the `Runner` yourself (the production shape), run a multi-turn conversation, and
dissect every `Event`.

## Files

| File | What it teaches |
|---|---|
| `agent.py` | tiny agent, one `word_count` tool (so the stream has a call + response) |
| `run_multiturn.py` | `Runner` + `InMemorySessionService` by hand; history carries; sessions are isolated |
| `inspect_events.py` | prints **every field of every event** — study this next to README §3 |

## Run

```powershell
# from THIS folder, venv active
python run_multiturn.py
python inspect_events.py           # StreamingMode.NONE
python inspect_events.py --sse     # StreamingMode.SSE — watch partial events
```

## `run_multiturn.py` — captured output

```
=== One session, three turns (history must carry) ===
  [alice] you: My favourite colour is teal. Remember that.
  [alice] bot: Okay, I'll remember that your favorite color is teal.
  [alice] you: How many words were in my previous message?
  [alice] bot: There were 7 words in your previous message.
  [alice] you: What's my favourite colour?
  [alice] bot: Your favorite color is teal.

=== Two sessions, no leakage ===
  [bob]   you: The secret word is 'volcano'. Keep it.
  [bob]   bot: Okay, I'll keep 'volcano' in mind.
  [carol] you: What is the secret word?
  [carol] bot: I don't have a secret word.
  [bob]   you: What is the secret word?
  [bob]   bot: The secret word is 'volcano'.

=== Inspect stored session state / history ===
  alice session has 8 events, state={}
```

Takeaways:
- Turn 3 works because **session history** is replayed to the model each turn — nothing
  was written to `state` (that's Module 08; `state={}` here).
- `carol` can't see `bob`'s secret: different `user_id` → different session → no shared data.
- 8 events = 3 user messages + 3 final answers + (1 tool call + 1 tool response) for the
  `word_count` turn.

## `inspect_events.py` — what you should see

**`StreamingMode.NONE` → 3 events:**

| # | content | `is_final_response()` | `partial` |
|---|---|---|---|
| 1 | `call word_count({'text': ...})` | False | None |
| 2 | `response word_count={'status':'success','words':9,...}` | False | None |
| 3 | `text[...]` (the answer) | **True** | None |

**`StreamingMode.SSE` → 6 events:** the `functionCall` appears twice (`partial=True`
then `partial=False`), then the response, then two `partial=True` text fragments, then
the final `partial=False` text with `is_final_response()` True.

The lesson: in SSE mode you get progressive fragments, but **only the final non-partial
event commits `actions`/`state_delta`** — so a UI can render tokens live without risking
half-applied state.

> Occasionally a `--sse` run raises a transient streaming error from Vertex
> (`aggregator_gen`). Just re-run; it's not a code bug.

## Exercises

Do exercises 2–4 from the module README against these scripts.
