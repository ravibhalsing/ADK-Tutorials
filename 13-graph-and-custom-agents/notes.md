# Module 13 — official documentation cross-reference

| Topic | Page |
|---|---|
| Graph workflows overview | https://adk.dev/graphs/ |
| Routes (sequential + conditional edges) | https://adk.dev/graphs/routes/ |
| Dynamic workflows | https://adk.dev/graphs/dynamic/ |
| Human input nodes | https://adk.dev/graphs/human-input/ |
| Data handling | https://adk.dev/graphs/data-handling/ |
| Custom agents | https://adk.dev/agents/custom-agents/ |

## Confirmed on this machine (ADK 2.8.0, Vertex, gemini-2.5-flash, 2026-09-05)

### Workflow graph
- `from google.adk import Workflow, Event`.
- `Workflow(*, name, description="", edges=[...], max_concurrency=None, retry_config=None,
  timeout=None, input_schema=, output_schema=, state_schema=, rerun_on_resume=True,
  wait_for_output=False, graph=None)`.
- **Sequential:** `edges=[("START", node_a, node_b, node_c)]`. Verified: fn → LlmAgent →
  fn all chained; `Event.output` carries the value between nodes.
- **Function node:** a plain callable `def f(node_input) -> Event: return Event(output=...)`.
  The **first** node receives the raw user `types.Content` (stringifies oddly) — unwrap
  `node_input.parts`.
- **Agent node:** just put the `LlmAgent` object in the edges tuple.
- **Routing:** node emits `Event(output=x, actions=EventActions(route=x))`; edge
  `(router, {"BUG": h1, "BILLING": h2, "OTHER": h3})` picks the branch. Verified with a
  triage classifier. Docs' `Event(route=...)` / `Event(message=...)` shorthand is NOT in
  2.8 — use `EventActions(route=...)`. `_graph.py` also supports `DEFAULT_ROUTE` key and
  list-of-routes fan-out.
- `event.node_info.path` (camelCase attr `nodeInfo`) = e.g. `"flow@1/normalize@1"`.
- **LIMITATION:** `Workflow` cannot be an `LlmAgent` sub-agent in 2.8 (this is *why*
  `SequentialAgent`/`LoopAgent`/`ParallelAgent` are deprecated-but-not-removed).

### Custom BaseAgent
- `class X(BaseAgent): async def _run_async_impl(self, ctx: InvocationContext) ->
  AsyncGenerator[Event, None]: ... yield ...`.
- `from google.adk.agents.invocation_context import InvocationContext`.
- `BaseAgent` is a Pydantic model → non-field attrs need `pydantic.PrivateAttr()`;
  sub-agents also pass through `super().__init__(sub_agents=[...])`.
- Call a sub-agent: `async for e in sub_agent.run_async(ctx): yield e`.
- Read state: `ctx.session.state.get(k)`. **Write** state: via a yielded
  `Event(actions=EventActions(state_delta={...}))` — direct mutation doesn't persist.
- Verified: generate → LoopAgent(critic, reviser)×2 → tone_checker → `if tone == NEGATIVE:
  regenerate` (conditional restart — impossible with plain workflow agents).

## Imports

```python
from google.adk import Workflow, Event
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import EventActions        # route=, state_delta=, escalate=
from pydantic import PrivateAttr
```


- ex01: a sleepy dragon
- ex02: New standing desk, 749 dollars (you should get NEEDS APPROVAL)
- ex03: You charged my card twice (it should route to BILLING)
