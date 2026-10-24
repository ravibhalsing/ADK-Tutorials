# Module 12 — LLM-Driven Multi-Agent Systems

> **Goal:** let the **model** decide which agent handles what — delegation via
> `sub_agents` + `transfer_to_agent`, composition via `AgentTool`, and the classic
> patterns (coordinator, hierarchy, generator-critic) with shared state as the bus.
>
> **Docs:** [Multi-agent patterns](https://adk.dev/workflows/patterns/) ·
> [Collaboration](https://adk.dev/workflows/collaboration/) ·
> [Agent routing](https://adk.dev/agents/routing/)

---

## 1. Two ways to connect agents

| | `sub_agents=[...]` + transfer | `tools=[AgentTool(agent=X)]` |
|---|---|---|
| Model action | `transfer_to_agent("X")` | `X(request=...)` like a function |
| Who answers the user after | **X** — it owns the conversation now | the **caller** — X returns a result, caller continues |
| Analogy | "let me put you through to billing" | "let me go ask billing and come back" |
| Good for | a specialist should run the dialogue | a bounded sub-task whose answer you need |

(You saw the `event.author` difference in Module 03 · ex04.)

`description` matters here: a coordinator's model reads each sub-agent's `description` to
choose. Write them as routing hints.

### Delegation is automatic

Give an `LlmAgent` `sub_agents=[...]` and ADK adds `transfer_to_agent` to its toolset.
The parent's model calls it when its instruction says to route. No manual wiring.

---

## 2. Pattern: Coordinator / Dispatcher

```python
billing = LlmAgent(name="billing", model=M,
                   description="Handles invoices, refunds, payment methods, plan changes.",
                   instruction="You are billing support. Resolve the user's billing issue.")
tech    = LlmAgent(name="tech", model=M,
                   description="Handles errors, outages, how-to, configuration, bugs.",
                   instruction="You are technical support. Help the user fix the problem.")

coordinator = LlmAgent(
    name="frontdesk", model=M,
    instruction="Greet, then transfer: billing questions -> `billing`, technical "
                "questions -> `tech`. Don't try to answer specialist questions yourself.",
    sub_agents=[billing, tech],
)
```

The coordinator's model emits `transfer_to_agent("billing")`; from then on `billing`
answers the user directly (its events have `author="billing"`).

---

## 3. Pattern: Hierarchical decomposition (`AgentTool`)

```python
from google.adk.tools import agent_tool

web_search = LlmAgent(name="web_search", model=M, tools=[google_search],
                      description="Finds current facts on the web.")
summarize  = LlmAgent(name="summarize", model=M,
                      description="Condenses text to key points.")

research = LlmAgent(name="research", model=M,
                    description="Researches a topic and returns a short brief.",
                    tools=[agent_tool.AgentTool(agent=web_search),
                           agent_tool.AgentTool(agent=summarize)])

writer = LlmAgent(name="writer", model=M,
                  instruction="Write a 1-paragraph report on the user's topic. "
                              "Call `research` to gather facts first.",
                  tools=[agent_tool.AgentTool(agent=research)])
```

`writer → research → (web_search, summarize)`. Each level calls down and gets a result
back — control always returns to the caller. Deep trees get expensive; keep them shallow.

---

## 4. Pattern: Generator ↔ Critic

Two forms:
- **One pass** — a `SequentialAgent([generator, critic])` (critic just labels the output).
- **Iterate** — a `LoopAgent([generator, critic, stopper])` (Module 11 · ex03).

The bus is state: `generator` writes `output_key="draft"`, `critic` reads `{draft}` and
writes `output_key="verdict"`.

---

## 5. Scoping transfers

By default a sub-agent can transfer **back to its parent** and **to its peers**. Lock it
down:

```python
specialist = LlmAgent(
    name="specialist", model=M, instruction="...",
    disallow_transfer_to_parent=True,   # can't bounce back up
    disallow_transfer_to_peers=True,    # can't hand off sideways
)
```

Use it to force a specialist to either finish the task or `escalate`, not ping-pong. A
coordinator usually leaves transfers open; leaf specialists usually disallow both.

---

## 6. Examples

| Folder | Pattern |
|---|---|
| `ex01_coordinator/` | coordinator + `billing` / `tech` specialists; watch `transfer_to_agent` and `event.author` |
| `ex02_agenttool_hierarchy/` | `writer → research → (web_search, summarize)` via `AgentTool` |
| `ex03_transfer_scoping/` | `disallow_transfer_to_parent` / `disallow_transfer_to_peers` — with vs without |

---

## 7. Production notes

- **Runaway delegation.** A → B → A → B… Set `disallow_transfer_*` on leaves; cap with
  `RunConfig(max_llm_calls=...)`; log the transfer chain and alert on cycles.
- **Cost & latency blow-up.** Every transfer / `AgentTool` call is ≥1 model call, often
  with a fresh (uncached) prompt prefix (Module 10). Prefer flat where you can.
- **Per-agent models.** Use a cheap model for the coordinator/router, a stronger one for
  the specialist that does the hard work.
- **Tracing across agents.** One invocation spans many agents — you need cross-agent
  traces (Module 17) to debug. `event.author` + `invocation_id` are the thread.
- **Instruction discipline.** Tell the coordinator *not* to answer specialist questions
  itself, and tell specialists to stay in their lane. Ambiguous descriptions → mis-routing.
- **State namespacing.** Many agents writing state → collisions. Prefix keys per agent or
  use `temp:` for hand-offs.

---

## 8. Exercises

1. In `ex01`, add a `general` agent for everything else and a rule: transfer only if
   clearly billing or tech, else answer directly.
2. Make `ex01`'s `billing` agent try to `transfer_to_agent("tech")` mid-conversation;
   then add `disallow_transfer_to_peers=True` and see the difference.
3. Convert `ex02`'s `research` from an `AgentTool` on `writer` to a `sub_agent` — who
   replies to the user now?
4. Add `max_llm_calls=6` via `RunConfig` to `ex02` and trigger the limit.
5. Trace `ex02`: print `event.author` for every event and draw the call tree.

---

## 9. Checklist

- [ ] Explain `sub_agents`+transfer vs `AgentTool` and predict who answers the user
- [ ] Build a coordinator that routes by `description`
- [ ] Build a 3-level `AgentTool` hierarchy
- [ ] Apply `disallow_transfer_to_parent` / `_peers` and say why
- [ ] Use shared state as the generator↔critic bus
- [ ] Name the failure modes: cycles, cost, mis-routing

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| Coordinator answers instead of transferring | instruction too permissive; add "do NOT answer X yourself, transfer to `x`" |
| Wrong specialist chosen | sharpen each sub-agent's `description` (it's the routing signal) |
| Agents ping-pong forever | `disallow_transfer_to_parent`/`_peers` on leaves; `max_llm_calls` cap |
| `AgentTool` child can't see conversation | by design — pass what it needs in the tool args / a `{state}` value |
| specialist replies but root "takes over" again | that's `AgentTool` semantics; use `sub_agents` if the specialist should own the dialogue |
