# Example 04 — `AgentTool` vs `sub_agents`

```powershell
python run.py             # AgentTool — the specialist is a callable
python run.py --subagent  # sub_agent — the specialist takes over the turn
```

## Captured output

```
mode: AgentTool (call)
  [concierge] call poet({'request': 'monsoon'})
[final answer authored by: concierge]          <-- root presents the result
Dark clouds gather, winds begin to sigh, ...

mode: sub_agent (transfer)
  [concierge] call transfer_to_agent({'agent_name': 'poet'})
  [concierge] --> transfer_to_agent: poet
[final answer authored by: poet]               <-- specialist answers the user directly
The skies open wide, a grand display, ...
```

## The difference (look at `event.author` on the final answer)

| | `AgentTool(agent=poet)` | `sub_agents=[poet]` + transfer |
|---|---|---|
| How it's invoked | model calls `poet(...)` like any tool | model calls `transfer_to_agent("poet")` |
| Who authors the final answer | **`concierge`** (root) — it gets the poem back and wraps it | **`poet`** — it now owns the conversation |
| Control afterward | returns to root; root can call more tools, keep chatting | root is out of the loop for this turn |
| Good for | a bounded sub-task whose result the caller needs | a specialist that should run the dialogue |

## Notes

- The `--subagent` run prints a warning about `context_cache_config`: every transfer
  swaps the system instruction + tools, so the prompt prefix changes and can't be cached.
  For transfer-heavy trees, set `context_cache_config` on the `App` (Module 10).
- `AgentTool(agent=poet, skip_summarization=True)` would return the poem verbatim instead
  of letting the concierge rephrase it.
