# Example 02 — `Workflow` sequential graph

`START → normalize (fn) → extract_amount (LLM) → apply_policy (fn)` — one AI node, the
rest deterministic Python.

```powershell
python run.py
```

## Captured output

```
user> Taxi from the airport, $37.50
  [normalize@1]    -> 'Taxi from the airport, $37.50'
  [apply_policy@1] -> 'AUTO-APPROVED: $37.50'

user> New standing desk and chair, 749 dollars total
  [apply_policy@1] -> 'NEEDS APPROVAL: $749.00 exceeds the $500 auto-approve limit'

user> Lunch with the team
  [apply_policy@1] -> 'REJECTED: no amount found'
```

## Takeaways

```python
wf = Workflow(name="expense_flow",
              edges=[("START", normalize, extract_amount, apply_policy)])
```

- A **function node** is any `def f(node_input) -> Event: return Event(output=...)`.
- The **first** node gets the raw user `types.Content` — `normalize` unwraps
  `node_input.parts`.
- The **agent node** (`extract_amount`) is just the `LlmAgent` object dropped into the
  tuple; it turns free text into a bare number.
- `apply_policy` is pure Python — the `$500` rule never touches a model, so it's exact
  and free.
- `event.node_info.path` → `"expense_flow@1/normalize@1"` etc.
