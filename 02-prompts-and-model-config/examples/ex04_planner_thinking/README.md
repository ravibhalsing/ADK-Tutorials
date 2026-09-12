# Example 04 — Planners & thinking

```powershell
python run.py            # BuiltInPlanner, thinking_budget=1024, include_thoughts=True
python run.py --noplan   # no planner
python run.py --react    # PlanReActPlanner
```

## Captured results (word problem: two trains, when do they meet?)

| Mode | thought *parts* surfaced | `thoughts_token_count` | total tokens | answer quality |
|---|---|---|---|---|
| `--noplan` | 0 | ~288 | ~826 | Gemini 2.5 **still thinks by default** |
| `BuiltInPlanner` (budget 1024) | 0* | ~994 | ~1681 | more thorough working |
| `--react` (`PlanReActPlanner`) | 1 | ~1819 | ~3327 | explicit `/*PLANNING*/…/*REASONING*/`, answer `16:18` |

\* The thinking clearly happened (see the token count), but on Vertex `us-central1` +
`gemini-2.5-flash` the **thought-summary parts are not surfaced** as `part.thought=True`
content. That surfacing varies by model and endpoint — don't build UI that depends on it.

## Takeaways

- **Gemini 2.5 models think by default.** You pay for it (`thoughts_token_count`) whether
  or not you add a planner. Set `ThinkingConfig(thinking_budget=0)` to switch it off for
  cheap/fast/simple tasks (see `../ex02_generate_config`).
- **`BuiltInPlanner`** is how you *tune* that native thinking — set the budget, and
  request thought summaries with `include_thoughts=True`.
- **`PlanReActPlanner`** is different: it prompt-engineers an explicit textual
  Plan → Act → Reason structure into the response. Works on any model, costs the most
  tokens, and the plan is visible in the output text.
- Default (no planner) is right for most agents. Reach for a planner when the task needs
  multi-step decomposition *before* the agent acts or calls tools.

## Where thoughts appear in the event stream

When they are surfaced, thought parts are `types.Part` objects with `part.thought == True`
inside `event.content.parts`, on non-final events. They never appear in the
`is_final_response()` event, so a normal chat UI ignores them automatically.
