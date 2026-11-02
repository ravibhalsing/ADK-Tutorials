# Module 13 — Graph Workflows & Custom Agents

> **Goal:** two ways to orchestrate with full control — the **`Workflow`** graph API
> (declarative nodes + edges, the ADK 2.x successor to `SequentialAgent` &co.) and a
> **custom `BaseAgent`** (arbitrary Python control flow).
>
> **Docs:** [Graph workflows](https://adk.dev/graphs/) ·
> [Routes](https://adk.dev/graphs/routes/) ·
> [Dynamic workflows](https://adk.dev/graphs/dynamic/) ·
> [Human input](https://adk.dev/graphs/human-input/) ·
> [Custom agents](https://adk.dev/agents/custom-agents/)

---

## 1. Three ways to control flow (recap + new)

| Approach | Flow defined by | Best for |
|---|---|---|
| Workflow **agents** (Module 11) — `SequentialAgent`… | code, fixed | *deprecated* → use `Workflow` |
| **`Workflow` graph** (this module) | a declarative graph of nodes + edges | deterministic, structured processes; mixing code and AI nodes; explicit routing |
| **Custom `BaseAgent`** (this module) | your Python (`if`, `while`, try/except) | logic a graph can't express cleanly — conditional restarts, complex retries, state machines |

---

## 2. `Workflow` — the graph API

```python
from google.adk import Workflow, Event
from google.adk.events import EventActions

def normalize(node_input) -> Event:          # a function node
    return Event(output=str(node_input).strip().lower())

classify = LlmAgent(name="classify", model=M, instruction="...")   # an agent node

wf = Workflow(
    name="flow",
    edges=[
        ("START", normalize, classify, apply_policy),   # sequential chain
    ],
)
```

- **Nodes** can be plain functions, `LlmAgent`s, `BaseTool`s, or human-input nodes.
- **`("START", a, b, c)`** = run `a → b → c` in order. `START` is where input enters.
  Multiple `START` rows = parallel paths.
- A node **receives** its predecessor's `Event.output` and **returns** `Event(output=...)`.
  The *first* node gets the raw user `types.Content` — unwrap it (`node_input.parts`).
- Run it exactly like an agent: `Runner(agent=wf, ...)`.

### Conditional routing

```python
def router(node_input) -> Event:
    label = str(node_input).strip().upper()
    return Event(output=label, actions=EventActions(route=label))   # emit a route

wf = Workflow(name="triage", edges=[
    ("START", classify, router),
    (router, {"BUG": bug_handler, "BILLING": billing_handler, "OTHER": other_handler}),
])
```

- A node emits a route via **`Event(actions=EventActions(route="BUG"))`**.
  (The docs' shorthand `Event(route=...)` isn't in ADK 2.8 — use `EventActions`.)
- `(source, {value: node, ...})` picks the branch whose key matches the emitted route.
- `DEFAULT_ROUTE` as a key catches anything unmatched.
- Routes can be `str`, `int`, or `bool`; a node can emit a **list** to fan out.

`Workflow` also takes `max_concurrency`, `retry_config`, `timeout`, `input_schema` /
`output_schema` / `state_schema`, and `rerun_on_resume`.

> **Limitation (ADK 2.8):** a `Workflow` **cannot yet be a sub-agent of an `LlmAgent`**.
> Until that lands, an `LlmAgent` that needs a deterministic sub-flow still uses the
> deprecated `SequentialAgent`/`LoopAgent`/`ParallelAgent`.

---

## 3. Custom `BaseAgent`

Subclass, implement `_run_async_impl`, `yield` events, call sub-agents from your own
control flow:

```python
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from pydantic import PrivateAttr

class StoryFlow(BaseAgent):
    _refine: LoopAgent = PrivateAttr()          # non-field attrs need PrivateAttr

    def __init__(self, **kw):
        super().__init__(name="story_flow", sub_agents=[generator, tone_checker], **kw)
        self._refine = LoopAgent(name="refine", max_iterations=2, sub_agents=[critic, reviser])

    async def _run_async_impl(self, ctx: InvocationContext):
        async for e in generator.run_async(ctx): yield e
        async for e in self._refine.run_async(ctx): yield e
        async for e in tone_checker.run_async(ctx): yield e

        if (ctx.session.state.get("tone") or "").upper().startswith("NEGATIVE"):
            async for e in generator.run_async(ctx): yield e   # <-- conditional restart
```

- `BaseAgent` is a Pydantic model — declare sub-agent references with `PrivateAttr()` (or
  pass them through `sub_agents=`), not bare attributes.
- Read/write state via `ctx.session.state` for *reading*; **write via yielded events'
  `EventActions(state_delta=...)`** — a direct `ctx.session.state["x"] = ...` from a
  custom agent doesn't persist (Module 08 / 11 · ex03).
- Everything you `yield` flows to the Runner and the caller.

---

## 4. Examples

| Folder | Shows |
|---|---|
| `ex01_custom_agent/` | `BaseAgent` with a conditional restart the workflow agents can't express |
| `ex02_graph_workflow/` | `Workflow` sequential graph: fn node → LLM node → fn node (expense policy) |
| `ex03_graph_routing/` | `Workflow` conditional routing: classify → router → {BUG, BILLING, OTHER} |

---

## 5. Production notes

- **Prefer the graph for deterministic flows** — it's declarative, inspectable, testable,
  and the parts that don't need AI genuinely don't call a model.
- **Custom agents = more power, more responsibility.** No structural guarantees — test
  every branch, guard against stuck states, make resumption idempotent.
- **Retries & timeouts** belong on the graph (`retry_config`, `timeout` on `Workflow`),
  not hand-rolled, where possible.
- **Human-input nodes** pause the graph; the run is resumed later (like Module 03's
  long-running tools). Persist the session so you can resume across restarts.
- **`state_schema`** on a `Workflow` gives you a typed, validated state object — worth it
  for anything non-trivial.
- Trace node-by-node (`event.node_info.path`); alert on nodes that error or a router that
  keeps hitting `DEFAULT_ROUTE`.

---

## 6. Exercises

1. Add a `RETRY` route to `ex03` that loops back to `classify` when the label is unclear.
2. Give `ex02` a `state_schema` (Pydantic) and read the amount from typed state instead
   of regex.
3. In `ex01`, cap the conditional restart at 2 attempts (add a counter via `state_delta`).
4. Build a graph with two `START` rows (parallel) that join at a `synthesize` node.
5. Add a human-input node to `ex03`'s BILLING branch (approve refund y/n).

---

## 7. Checklist

- [ ] Build a sequential `Workflow` with function and agent nodes
- [ ] Build a routing `Workflow` (`EventActions(route=...)` + dict edge)
- [ ] Unwrap the first node's `types.Content` input
- [ ] Write a custom `BaseAgent` with `_run_async_impl`, `PrivateAttr` sub-agents, and a conditional branch
- [ ] Persist state from a custom agent correctly (via yielded event `state_delta`)
- [ ] State the ADK 2.8 limitation (Workflow ⊄ LlmAgent)

---

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| first node gets a weird stringified `Content` | unwrap: `" ".join(p.text for p in node_input.parts)` if `hasattr(node_input, "parts")` |
| `Event(route=...)` → `TypeError` | use `Event(actions=EventActions(route="X"))` |
| routing always hits one branch | the router's emitted route must exactly match a dict key (case!); add `DEFAULT_ROUTE` |
| custom agent state change lost | write via `yield Event(actions=EventActions(state_delta={...}))`, not `ctx.session.state[...] =` |
| `BaseAgent` sub-agent attr → Pydantic error | use `PrivateAttr()` or pass via `sub_agents=` |
| want a Workflow inside an LlmAgent | not supported in 2.8 — use `SequentialAgent`/`LoopAgent` for that sub-flow |
