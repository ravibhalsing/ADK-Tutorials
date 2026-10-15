# Module 11 — Workflow Agents (deterministic orchestration)

> **Goal:** compose agents with **code-guaranteed** control flow — in order
> (`SequentialAgent`), at the same time (`ParallelAgent`), or repeatedly
> (`LoopAgent`) — passing data through session state.
>
> **Docs:** [Workflow agents](https://adk.dev/agents/workflow-agents/) ·
> [Sequential](https://adk.dev/agents/workflow-agents/sequential-agents/) ·
> [Parallel](https://adk.dev/agents/workflow-agents/parallel-agents/) ·
> [Loop](https://adk.dev/agents/workflow-agents/loop-agents/) ·
> [Patterns](https://adk.dev/workflows/patterns/)

> ### ⚠️ ADK 2.x status
> `SequentialAgent` / `ParallelAgent` / `LoopAgent` are **deprecated** in ADK 2.8 in
> favour of the `Workflow` graph API (**Module 13**):
> *"…is deprecated in favor of Workflow and will be removed in a future version.
> Workflow cannot yet be used as an LlmAgent sub-agent."*
>
> They still **work** and you'll meet them everywhere in existing ADK code, and
> `Workflow` can't yet be nested inside an `LlmAgent`, so they're not gone. **Learn the
> patterns here** — order / parallel / loop, data-through-state — they transfer 1:1 to
> `Workflow`. Use `Workflow` for new deterministic flows once you've done Module 13.
> The examples pass `warnings.filterwarnings("ignore")` for the deprecation notice.

---

## 1. Workflow agents vs LLM delegation

| | Workflow agent (this module) | LLM-driven `sub_agents` (Module 12) |
|---|---|---|
| Who decides the flow | **your code** — fixed | the model — `transfer_to_agent` |
| Determinism | total | none |
| Use when | the steps and their order are known | the routing depends on understanding the request |

A workflow agent is itself a `BaseAgent` — it has a `name`, goes in `sub_agents`, and
can be nested inside other workflow agents.

They pass data through **shared session state**: step 1 writes `output_key="x"`, step 2's
instruction reads `{x}`.

---

## 2. `SequentialAgent` — pipeline

```python
from google.adk.agents import SequentialAgent, LlmAgent

writer   = LlmAgent(name="writer",   model=M, output_key="draft",
                    instruction="Write a 3-line function for: {spec}")
reviewer = LlmAgent(name="reviewer", model=M, output_key="review",
                    instruction="Review this code, list issues:\n{draft}")
refactor = LlmAgent(name="refactor", model=M, output_key="final",
                    instruction="Rewrite the code fixing the review.\nCode:\n{draft}\nReview:\n{review}")

pipeline = SequentialAgent(name="code_pipeline", sub_agents=[writer, reviewer, refactor])
```

Runs `writer → reviewer → refactor`, same `InvocationContext` throughout, each step sees
the state the previous ones wrote. `session.state` ends with `draft`, `review`, `final`.

---

## 3. `ParallelAgent` — fan-out / fan-in

```python
from google.adk.agents import ParallelAgent, SequentialAgent

r1 = LlmAgent(name="solar", model=M, output_key="solar",
              instruction="Two facts about solar power costs.")
r2 = LlmAgent(name="wind",  model=M, output_key="wind",
              instruction="Two facts about wind power costs.")
r3 = LlmAgent(name="hydro", model=M, output_key="hydro",
              instruction="Two facts about hydro power costs.")

fan_out   = ParallelAgent(name="research", sub_agents=[r1, r2, r3])
synth     = LlmAgent(name="synth", model=M,
                     instruction="Compare these:\nSolar: {solar}\nWind: {wind}\nHydro: {hydro}")

workflow  = SequentialAgent(name="research_then_synth", sub_agents=[fan_out, synth])
```

- All branches start together → wall-clock ≈ the slowest branch, not the sum.
- Branches are **isolated** — no shared conversation history between them; they only meet
  through the `output_key`s they each write.
- Merge in a **following `SequentialAgent` step** that reads every `output_key`.
- Don't make one branch depend on another's output — that's a `SequentialAgent`.

---

## 4. `LoopAgent` — iterate until good enough

```python
from google.adk.agents import LoopAgent, BaseAgent
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext

class StopWhenApproved(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        if ctx.session.state.get("verdict") == "APPROVED":
            yield Event(author=self.name, actions=EventActions(escalate=True))  # <-- break the loop
        else:
            yield Event(author=self.name)   # no-op, keep looping

writer = LlmAgent(name="writer", model=M, output_key="draft",
                  instruction="Improve state['draft'] to meet: {rubric}. If empty, write a first draft.")
critic = LlmAgent(name="critic", model=M, output_key="verdict",
                  instruction="Reply exactly APPROVED or REVISE for state['draft'] vs {rubric}. "
                              "If REVISE, add one sentence why.")

loop = LoopAgent(name="refine", max_iterations=4, sub_agents=[writer, critic, StopWhenApproved(name="stopper")])
```

- **`LoopAgent` never stops itself.** You must provide a stop: `max_iterations`, and/or a
  sub-agent that sets `actions.escalate = True`.
- State carries across iterations — `writer` reads the `draft` it wrote last round.
- `escalate=True` bubbles out of the loop (also used to bubble out of a parent, Module 12).

---

## 5. Examples

| Folder | Pattern |
|---|---|
| `ex01_sequential_pipeline/` | `SequentialAgent`: spec → write → review → refactor |
| `ex02_parallel_gather/` | `ParallelAgent` (3 researchers) inside `SequentialAgent` (+ synthesizer) |
| `ex03_loop_refinement/` | `LoopAgent`: writer + critic + escalating stop-checker, `max_iterations` |

---

## 6. Production notes

- **Cost multiplies.** A 3-step pipeline = 3 model calls; a 4-iteration loop of 2 agents
  = up to 8. `ParallelAgent` runs them at once (faster) but you pay for all. Budget with
  `RunConfig(max_llm_calls=...)` as a circuit-breaker.
- **Parallel concurrency.** Many branches → many simultaneous model calls → rate limits.
  Throttle branch count; add retry/backoff.
- **Partial failure.** If one `ParallelAgent` branch errors, decide: fail the whole
  workflow, or synthesize from the branches that succeeded (guard `{key?}` in the
  synthesizer, check for missing keys).
- **Loop runaway.** Always set `max_iterations`. Log the iteration count; alert if loops
  routinely hit the cap (the critic never approves → prompt bug).
- **Determinism for tests.** Workflow structure is fixed, so eval (Module 18) is easier —
  assert the trajectory of agent names.
- **State hygiene.** Use clear `output_key` names; `temp:` for values only the next step
  needs; don't leave large intermediate blobs in persisted state.

---

## 7. Exercises

1. Add a 4th step to `ex01` that scores the final code 1-10 into `output_key="score"`;
   print `session.state["score"]`.
2. In `ex02`, make one researcher raise; adjust the synthesizer to handle the missing
   `output_key` gracefully.
3. In `ex03`, tighten the rubric so the critic keeps saying REVISE — watch it stop at
   `max_iterations`. Print how many iterations ran.
4. Nest: put `ex03`'s loop as the middle step of a `SequentialAgent` (setup → loop →
   publish).
5. Time `ex02` with `ParallelAgent` vs a `SequentialAgent` of the same 3 researchers.

---

## 8. Checklist

- [ ] Build a `SequentialAgent` and pass data via `output_key` → `{key}`
- [ ] Build `ParallelAgent` + a merge step; explain branch isolation
- [ ] Build a `LoopAgent` with `max_iterations` **and** an `escalate` stop-checker
- [ ] Nest workflow agents
- [ ] Reason about cost, concurrency limits, and partial failure

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| `{key}` → `KeyError` in a later step | the earlier step didn't run / didn't set `output_key`; or use `{key?}` |
| `LoopAgent` runs forever (to the cap every time) | no `escalate` path, or the critic's output never matches your stop condition — print it |
| `ParallelAgent` branch reads another branch's key | it's `None` — parallel branches don't see each other; use `SequentialAgent` |
| all branches serialized, not parallel | you nested them in a `SequentialAgent`, or a branch is `await`ing a shared lock |
| stop-checker doesn't break the loop | it must `yield Event(actions=EventActions(escalate=True))`, not return a value |
