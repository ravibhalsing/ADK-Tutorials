# Module 12 — official documentation cross-reference

| Topic | Page |
|---|---|
| Multi-agent patterns (7 patterns) | https://adk.dev/workflows/patterns/ |
| Collaboration | https://adk.dev/workflows/collaboration/ |
| Agent routing | https://adk.dev/agents/routing/ |
| LLM agents (sub_agents, transfer flags) | https://adk.dev/agents/llm-agents/ |

## Confirmed on this machine (ADK 2.8.0, Vertex, gemini-2.5-flash, 2026-09-05)

- `LlmAgent(sub_agents=[...])` auto-adds a `transfer_to_agent` tool. The parent's model
  calls it; `event.actions.transfer_to_agent` holds the target name. After transfer, the
  target authors events (`event.author == "billing"`).
- **Coordinator (ex01)**: routing is driven by each sub-agent's **`description`**.
  Verified: billing question → `transfer_to_agent: billing`, then the follow-up stayed
  with `billing`. Technical question → `tech`.
- **AgentTool hierarchy (ex02)**: `from google.adk.tools import agent_tool`;
  `tools=[agent_tool.AgentTool(agent=child)]`. `writer → research → (facts_agent,
  summarizer)`. Nested calls happen *inside* the AgentTool — only the top-level call
  (`writer calls research`) shows in the parent's event stream. Final `event.author` =
  the caller (`writer`), i.e. control returns.
- **Transfer scoping (ex03)**: `disallow_transfer_to_parent=True`,
  `disallow_transfer_to_peers=True` on an `LlmAgent`. Verified:
  - open → coordinator→billing_expert→(billing transfers to)→shipping_expert (2 hops)
  - locked → coordinator→billing_expert, which handles its part and says "a colleague
    will follow up" (no peer transfer possible)
- Transfers log a `context_cache_config` warning — each transfer swaps
  instruction+tools, breaking the cache prefix (Module 10). Set `context_cache_config`
  on the `App` for transfer-heavy trees.

## Imports

```python
from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool          # agent_tool.AgentTool(agent=...)
# LlmAgent kwargs: sub_agents=[], disallow_transfer_to_parent=bool, disallow_transfer_to_peers=bool
```
