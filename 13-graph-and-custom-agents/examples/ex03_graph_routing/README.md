# Example 03 — `Workflow` conditional routing

`START → classify (LLM) → router (fn) → { BUG | BILLING | OTHER }`

```powershell
python run.py
```

## Captured output

```
user> The export button throws a 500 error every time.
  -> 'BUG'
  -> "Filed a bug ticket. Engineering will investigate; update in 2 business days."

user> You charged my card twice this month.
  -> 'BILLING'
  -> "Routed to billing. They'll review your account and reply within 24 hours."

user> Do you have a mobile app?
  -> 'OTHER'
  -> "Thanks for reaching out - a support generalist will follow up shortly."
```

## Takeaways

```python
def router(node_input) -> Event:
    label = str(node_input).strip().upper()
    route = label if label in {"BUG", "BILLING"} else "OTHER"
    return Event(output=route, actions=EventActions(route=route))   # <-- emit the route

wf = Workflow(name="triage", edges=[
    ("START", classify, router),
    (router, {"BUG": bug_handler, "BILLING": billing_handler, "OTHER": other_handler}),
])
```

- The classifier is the only LLM call; every branch after it is deterministic code.
- A node emits a route with **`EventActions(route=...)`** — `Event(route=...)` shorthand
  from the docs isn't in ADK 2.8.
- The dict edge `{value: node}` matches the emitted route (exact, case-sensitive). Add a
  `DEFAULT_ROUTE` key for a catch-all.
- This is the graph API's sweet spot: a predictable, inspectable switchboard.
