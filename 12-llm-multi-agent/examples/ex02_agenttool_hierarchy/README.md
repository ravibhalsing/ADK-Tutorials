# Example 02 — Hierarchical decomposition with `AgentTool`

`writer` → `research` → (`facts_agent`, `summarizer`), each level calling the next as a
**tool**.

```powershell
python run.py
```

## Captured output

```
user> Write about the Great Barrier Reef.

  [writer] calls research

[writer]>
The Great Barrier Reef is the world's largest coral reef system, extending ~2,300 km
along Australia's northeast coast and visible from space. ... it lost roughly half its
shallow-water coral between 1995 and 2017.
```

## Takeaways

- `tools=[agent_tool.AgentTool(agent=child)]` — the child is invoked like a function; its
  answer is returned to the caller, which keeps control.
- Only `writer calls research` shows in the top-level event stream. `research`'s calls to
  `facts_agent` and `summarizer` happen **inside** that tool call.
- The final event's `author` is `writer` — control came back up (contrast: `sub_agents`
  transfer would leave the deepest agent talking to the user).
- `facts_agent` uses a stand-in `fact_lookup` tool; in production that'd be `google_search`
  (Module 04).
- Keep hierarchies shallow — each level is ≥1 model call with a fresh prompt.
