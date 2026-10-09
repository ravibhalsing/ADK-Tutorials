# Example 02 — Auto-save + `preload_memory` (hands-off)

```powershell
python run.py
```

## Captured output

```
--- Session 1 ---
user> I take my coffee black, no sugar. And I have a dog named Biscuit.
agent> Got it! You like your coffee black, no sugar, and your dog's name is Biscuit.

--- Session 2 (new session, no manual memory calls) ---
user> How do I take my coffee, and what's my dog's name?
agent> You take your coffee black, no sugar, and your dog's name is Biscuit!
```

## Zero explicit memory calls

```python
async def auto_save(callback_context):
    await callback_context.add_session_to_memory()      # after EVERY turn

agent = Agent(..., tools=[preload_memory], after_agent_callback=auto_save)
```

- `after_agent_callback` archives the session automatically.
- `preload_memory` searches memory with the incoming message **before** the model runs
  and injects the hits — no `load_memory(...)` call appears in the event stream.
- Session 2 answered from session 1 with nothing wired up by hand.

This is the pattern for "an assistant that just knows the user". In production, move the
save off the request path (queue it) so latency isn't tied to memory ingestion.
