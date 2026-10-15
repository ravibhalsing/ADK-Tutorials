# Example 03 — `LoopAgent` iterative refinement

`LoopAgent(max_iterations=3, sub_agents=[writer, critic, Stopper])` — repeats
writer → critic → stopper until the critic says `APPROVED` or the cap is hit.

```powershell
python run.py
```

## Captured output

```
  [iter 1] draft='Sustainable hydration, one refill at a time.'  critic='APPROVED'

finished after 1 iteration(s)
final tagline: Sustainable hydration, one refill at a time.
critic verdict: APPROVED
```

(The critic approved on round 1 here. Tighten `RUBRIC` and it will run 2-3 rounds, then
stop at `max_iterations` if never satisfied.)

## Takeaways

- **`LoopAgent` doesn't stop itself.** Two mechanisms, both present here:
  - `max_iterations=3` — hard safety cap
  - `Stopper` (a `BaseAgent`) yields `Event(actions=EventActions(escalate=True))` when the
    critic approves → the loop breaks
- State carries across iterations: `writer` reads the `draft` and `feedback` it/​the
  critic wrote last round.
- ⚠️ The `Stopper` writes its iteration counter via **`state_delta`** on the yielded event
  — a direct `ctx.session.state["x"] = ...` in a custom agent would **not persist**
  (Module 08). First version of this example hit exactly that bug.
