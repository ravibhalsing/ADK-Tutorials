# Module 02 — Prompts, Instructions & Model Configuration

> **Goal:** control *what the model is told* (instructions — static, templated, dynamic)
> and *how it generates* (`generate_content_config`, planners, history control), plus get
> structured input/output.
>
> **Docs:** [LLM agents](https://adk.dev/agents/llm-agents/) ·
> [Gemini models](https://adk.dev/agents/models/google-gemini/) ·
> [Runtime config](https://adk.dev/runtime/runconfig/) ·
> [Plugins](https://adk.dev/apps/plugins/) (for `GlobalInstructionPlugin`)

---

## 1. `instruction` — three forms

### a) Static string

```python
Agent(
    name="tutor", model=MODEL,
    instruction=(
        "You are a patient maths tutor for 12-year-olds.\n"
        "- Explain each step. Never just give the final number.\n"
        "- If the question isn't maths, politely decline."
    ),
)
```
The `instruction` becomes the model's **system instruction** — sent every turn, separate
from the conversation. Put role, task, tone, constraints, tool-usage rules, and output
format here. `description` is *not* sent to this model — it's metadata for other agents.

### b) Templated string — inject session state

```python
instruction="You are helping {user_name}. Their goal today is: {daily_goal}."
```

| Placeholder | Resolves to | If missing |
|---|---|---|
| `{key}` | `session.state["key"]` | **raises** `KeyError` at request build |
| `{key?}` | `session.state["key"]` | silently omitted |
| `{artifact.name}` | text content of artifact `name` | error unless it exists |

State must be populated *before* the turn — via `create_session(state=…)`, a
`before_agent_callback`, `output_key` from a previous agent, or a tool writing to
`tool_context.state` (Module 03 / 08).

### c) Dynamic — an instruction provider (callable)

```python
from google.adk.agents.readonly_context import ReadonlyContext

def build_instruction(ctx: ReadonlyContext) -> str:
    tier = ctx.state.get("plan_tier", "free")
    extra = "You may use premium tools." if tier == "pro" else "Stick to basic answers."
    return f"You are support for a {tier}-tier user. {extra}"

Agent(name="support", model=MODEL, instruction=build_instruction)
```

Signature: `Callable[[ReadonlyContext], str | Awaitable[str]]`. Use it when the prompt
needs logic (branching, formatting a list from state, fetching a value, date math).
`ReadonlyContext` gives `state` (read-only), `agent_name`, `invocation_id` — no writes.

> **Templating vs provider:** `{key}` is a literal substitution done by ADK. A provider
> is your code. Note: with a provider, `{...}` in the *returned* string is still
> templated unless you disable it — keep returned text free of stray braces.

### d) Shared instructions across a multi-agent tree

`global_instruction` on the root agent is **deprecated**. Use the
`GlobalInstructionPlugin` (Module 15) registered on the `App` — it prepends a common
system instruction to *every* agent in the tree.

---

## 2. `generate_content_config` — how the model generates

```python
from google.genai import types

Agent(
    name="extractor", model=MODEL,
    instruction="Extract the invoice fields as asked.",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.0,           # 0 = as deterministic as possible
        top_p=0.95,
        max_output_tokens=512,     # hard cap on the response
        stop_sequences=["END"],    # stop when the model emits this
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
        ],
    ),
)
```

| Field | Effect | Typical |
|---|---|---|
| `temperature` | randomness. Low = focused/repeatable, high = creative | `0.0`–`0.3` for extraction/routing; `0.7`–`1.0` for ideation |
| `top_p` / `top_k` | nucleus / top-k sampling cutoffs | leave default unless tuning |
| `max_output_tokens` | truncates the response | set it — protects latency & cost |
| `stop_sequences` | early stop on a literal | useful with custom output formats |
| `safety_settings` | block thresholds per harm category | policy decision; see Module 16 |
| `response_mime_type` / `response_schema` | force JSON (see §4, usually via `output_schema`) | — |
| `http_options.retry_options` | client-side retry/backoff | `HttpRetryOptions(initial_delay=1, attempts=2)` |

For **reproducibility**: `temperature=0.0` plus a fixed model version (`gemini-2.5-flash`,
not `-latest`). Output is *more* stable, never byte-identical.

---

## 3. Planners & "thinking"

```python
from google.adk.planners import BuiltInPlanner, PlanReActPlanner
from google.genai import types

# a) Use the model's native thinking (Gemini 2.5)
planner = BuiltInPlanner(
    thinking_config=types.ThinkingConfig(
        include_thoughts=True,   # surface the reasoning as 'thought' parts
        thinking_budget=512,     # ~max thinking tokens; 0 disables
    ),
)

# b) Force an explicit Plan→Act→Reason text structure (models without thinking)
planner = PlanReActPlanner()

Agent(name="researcher", model=MODEL, planner=planner, tools=[...])
```

- `BuiltInPlanner` → configures Gemini's built-in reasoning. `include_thoughts=True`
  makes thought summaries visible as separate parts in the event stream.
- `PlanReActPlanner` → prompt-engineers a `/*PLANNING*/ … /*ACTION*/ … /*REASONING*/`
  structure. Model-agnostic; costs extra tokens.
- Default (no planner) is fine for most agents. Add one when tasks need multi-step
  decomposition before acting.

---

## 4. Structured input & output

### `output_key` — capture the answer into state

```python
Agent(name="summarizer", model=MODEL, output_key="summary",
      instruction="Summarize the user's text in 2 sentences.")
# after the turn: session.state["summary"] == "<the 2-sentence text>"
```
The next agent in a `SequentialAgent` can then read `{summary}`. This is the primary
data-passing mechanism between agents (Module 11).

### `output_schema` — force a typed JSON object

```python
from pydantic import BaseModel, Field

class Invoice(BaseModel):
    vendor: str
    total: float = Field(description="Grand total including tax")
    due_date: str

Agent(name="parser", model=MODEL, output_schema=Invoice, output_key="invoice",
      instruction="Extract the invoice. Respond ONLY with the JSON object.")
# session.state["invoice"] is now a dict matching Invoice
```

Constraints (important):
- Historically an `output_schema` agent could **not** also use `tools` or transfer to
  sub-agents. On **ADK 2.x + Gemini 2.5** it often works via a function-tool fallback
  (verified in `ex03 --break`), but support still varies by model and version.
- **Best practice regardless:** keep it a pure formatter. Split "gather with tools" and
  "format to schema" into two agents (a `SequentialAgent`, Module 11). Clearer, portable,
  testable.
- The model is instructed to emit JSON; ADK validates it against the schema and stores
  the parsed **dict** in `state[output_key]`.

### `input_schema` — require typed input

```python
Agent(name="calc", model=MODEL, input_schema=MyRequestModel, ...)
```
The incoming user message must be JSON conforming to `MyRequestModel`. Useful for
agent-to-agent calls and programmatic pipelines; awkward for free-text chat.

---

## 5. `include_contents` — how much history the model sees

```python
Agent(name="classifier", model=MODEL, include_contents="none",
      instruction="Classify the SINGLE input message as spam/ham. Reply one word.")
```

| Value | Behaviour | Use |
|---|---|---|
| `"default"` | full relevant conversation history is sent | chat, context-dependent tasks |
| `"none"` | only the current message (+ instruction) | stateless classifiers, formatters, map-style steps in a pipeline |

`"none"` cuts tokens and prevents earlier turns from contaminating a pure function.

---

## 6. Examples in this module

| Folder | Shows |
|---|---|
| `ex01_instruction_styles/` | static vs `{state}` templating vs callable provider — same question, 3 behaviours |
| `ex02_generate_config/` | `temperature` 0 vs 1 (repeat-run variance), `max_output_tokens`, `stop_sequences` |
| `ex03_structured_io/` | `output_schema` + `output_key`; inspect `session.state` after; the tools/schema constraint |
| `ex04_planner_thinking/` | `BuiltInPlanner` + `ThinkingConfig(include_thoughts=True)`; find thought parts in events |

Each has its own `.env`, `README.md` (captured output), and a `run.py`.

---

## 7. API surface

```python
from google.adk.agents import Agent
from google.adk.agents.readonly_context import ReadonlyContext   # instruction providers
from google.adk.planners import BuiltInPlanner, PlanReActPlanner
from google.genai import types                                    # GenerateContentConfig,
                                                                  # ThinkingConfig, SafetySetting
from pydantic import BaseModel, Field                             # schemas
```

---

## 8. Exercises

1. **Provider beats templating.** Rewrite `ex01`'s templated agent as a provider that
   also falls back to a default goal and uppercases the user's name. Confirm identical
   behaviour when state is present, better behaviour when it's absent.
2. **Determinism check.** Run `ex02` 5× at `temperature=0` and 5× at `temperature=1`
   with the same creative prompt. Quantify the difference (e.g. distinct first sentences).
3. **Schema break.** Give `ex03`'s parser a `tools=[...]` argument and run it. Observe the
   error / fallback. Then split into `gatherer` + `formatter`.
4. **Token budget.** Set `max_output_tokens=20` on a summarizer and feed a long article.
   Inspect `event.content` and `finish_reason` — what does a truncated response look like?
5. **Thinking visibility.** In `ex04`, toggle `include_thoughts` False→True and diff the
   event stream. Where do thought parts appear? Do they reach `is_final_response()`?

---

## 9. Checklist

- [ ] Explain instruction vs description vs turn content
- [ ] Use `{key}`, `{key?}`, and a callable provider, and say when each is right
- [ ] Set `temperature`, `max_output_tokens`, `stop_sequences`, `safety_settings`
- [ ] State why `output_schema` and `tools` don't mix, and the two-agent workaround
- [ ] Use `output_key` to pass a result into state
- [ ] Choose `include_contents="none"` vs `"default"` correctly
- [ ] Add a `BuiltInPlanner` and find thoughts in the event stream

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `KeyError: 'user_name'` building the request | Templated `{user_name}` but state has no such key — use `{user_name?}` or set state first |
| `output_schema` agent returns prose or ```json fences | Strengthen the instruction ("Respond ONLY with the JSON object, no prose, no markdown") |
| `output_schema`+`tools` works on Gemini 2.5 but breaks elsewhere | Expected — support varies. Split into two agents for portability |
| Thoughts never appear | Model must support thinking (Gemini 2.5); `thinking_budget` > 0; `include_thoughts=True` |
| `gemini-flash-latest` → 404 on Vertex `us-central1` | Regional endpoints need exact versions — use `gemini-2.5-flash` (this course already does) |
| Response cut off mid-sentence | `max_output_tokens` too low; raise it or ask for a shorter answer |
