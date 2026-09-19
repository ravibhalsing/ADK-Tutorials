# Module 03 — Function Tools (the core skill)

> **Goal:** write Python functions that an LLM can call reliably — correct schemas,
> model-readable docstrings, graceful errors — and use `ToolContext`,
> `LongRunningFunctionTool`, and `AgentTool`.
>
> **Docs:** [Function tools](https://adk.dev/tools-custom/function-tools/) ·
> [Tools overview](https://adk.dev/tools-custom/) ·
> [Tool context](https://adk.dev/context/)

---

## 1. A function becomes a tool

Put a function in `tools=[...]` and ADK wraps it in a `FunctionTool`, building a JSON
schema the model sees from:

- **function name** → the tool name
- **docstring** → the tool description + per-argument descriptions
- **type hints** → argument types
- **defaults** → which arguments are optional

```python
def get_weather(city: str, unit: str = "celsius") -> dict:
    """Get the current weather for a city.

    Args:
        city: City name, e.g. "Paris".
        unit: "celsius" or "fahrenheit". Defaults to celsius.

    Returns:
        dict: {"status": "success", "temperature": "18", "unit": "celsius"}
              or {"status": "error", "error_message": "..."}.
    """
    ...
```

### Type hints that work

| Use | Avoid |
|---|---|
| `str`, `int`, `float`, `bool` | bare `list` / `dict` without params (be explicit) |
| `list[str]`, `dict[str, int]` | custom classes as parameters (use primitives) |
| `Optional[str] = None` / `X \| None = None` | `*args`, `**kwargs` — **ignored** by the schema builder |
| Pydantic model *return* values (serialized) | non-JSON-serializable returns |

Everything the model passes in and everything you return must be JSON-serializable.

### The docstring **is** the spec

The model decides whether and how to call your tool from the **name + docstring**, not
the body. Write it for the model: say what it does, when to use it, what each arg means,
and what comes back. Google-style `Args:` blocks are parsed per-argument.

### Return a `dict` with `status`

```python
return {"status": "success", "data": {...}}
return {"status": "error", "error_message": "City 'Atlantis' not found. Try a real city."}
```

Why: the **model**, not your code, has to understand the outcome and decide what to do
next. A human-readable `error_message` lets it recover ("that city isn't supported, try
another") instead of crashing or hallucinating. Never `raise` for expected failures —
return an error dict. (Unexpected exceptions do propagate; see §6.)

### `FunctionTool` explicitly

`tools=[get_weather]` is shorthand for `tools=[FunctionTool(get_weather)]`. Use the
explicit form when you need to subclass or configure wrapping.

---

## 2. `ToolContext` — reach into the run

Add a parameter annotated `ToolContext` (any name) and ADK injects it — it does **not**
appear in the schema the model sees:

```python
from google.adk.tools import ToolContext

def save_preference(key: str, value: str, tool_context: ToolContext) -> dict:
    """Remember a user preference."""
    tool_context.state[f"user:{key}"] = value      # persists on the user
    return {"status": "success"}
```

`ToolContext` gives you:

| Member | Use |
|---|---|
| `.state` | read/write session state. Prefixes: none = session, `user:` = per-user, `app:` = per-app, `temp:` = this invocation only |
| `.actions.skip_summarization = True` | return the tool result to the user **verbatim**, skip the model's rewrite |
| `.actions.transfer_to_agent = "name"` | hand the turn to another agent (multi-agent, Module 12) |
| `.actions.escalate = True` | bubble up / end a `LoopAgent` (Module 11) |
| `.function_call_id` | correlate with the triggering `functionCall` event |
| `.load_artifact()` / `.save_artifact()` / `.list_artifacts()` | files (Module 10) |
| `.request_credential()` / auth helpers | tool auth (Module 07) |
| `.search_memory(query)` | long-term memory (Module 09) |

### Passing data between tools in one turn

Use `temp:` state — visible to later tools in the same invocation, discarded after:

```python
def fetch(url: str, tool_context: ToolContext) -> dict:
    tool_context.state["temp:doc"] = download(url)
    return {"status": "success"}

def summarize(tool_context: ToolContext) -> dict:
    return {"status": "success", "summary": shorten(tool_context.state["temp:doc"])}
```

Remember the event-loop rule (Module 01): a `state` write is committed after the tool's
event is processed by the Runner — fine across tool calls, don't assume mid-call.

---

## 3. `LongRunningFunctionTool` — human-in-the-loop & async jobs

For work that can't finish in one call: approvals, multi-minute jobs, waiting on an
external system. The tool returns a **pending** result; the agent pauses; your client
decides when to resume with the real result.

```python
from google.adk.tools import LongRunningFunctionTool

def ask_for_approval(purpose: str, amount: float) -> dict:
    """Request manager approval for a reimbursement. Returns a pending ticket."""
    ticket = create_ticket(purpose, amount)
    return {"status": "pending", "ticket_id": ticket.id, "approver": ticket.approver}

approval_tool = LongRunningFunctionTool(ask_for_approval)
```

Flow:
1. Model calls `ask_for_approval`. The event has the call id in
   `event.long_running_tool_ids`.
2. Your client sees `status: "pending"`, shows a UI, and **stops consuming events**.
3. Later (approval granted) the client sends a `types.FunctionResponse` with the same
   call id and the final result (`{"status": "approved"}`) as the next `new_message`.
4. The agent resumes and finishes.

`ex03` implements this end to end.

---

## 4. `AgentTool` — an agent as a callable tool

```python
from google.adk.tools import AgentTool

translator = Agent(name="translator", model=MODEL,
                   instruction="Translate the given text to French. Output only the translation.")

root = Agent(name="root", model=MODEL, tools=[AgentTool(agent=translator)])
```

`AgentTool` vs `sub_agents` (delegation):

| | `AgentTool` | `sub_agents` + transfer |
|---|---|---|
| Control after | returns to the caller, which continues | fully handed over; caller is done |
| Mental model | "call a function that happens to be an agent" | "route this conversation elsewhere" |
| Result | tool result, then caller's model summarizes (unless `skip_summarization=True`) | sub-agent talks to the user directly |
| Use for | a bounded sub-task (translate, summarize, classify) | specialist takes over the dialogue |

Useful `AgentTool` options: `skip_summarization=True` (return child output as-is),
`propagate_grounding_metadata=True` (keep search citations), `include_plugins=False`
(run the child isolated from parent plugins).

---

## 5. Examples

| Folder | Shows |
|---|---|
| `ex01_function_tools/` | schema from signature+docstring, optional args, `status` dict, error branch, `--schema` dump |
| `ex02_tool_context/` | `state` (session / `user:` / `temp:`), `skip_summarization`, tool→tool data pass |
| `ex03_long_running/` | `LongRunningFunctionTool` approval flow, pause + resume with a `FunctionResponse` |
| `ex04_agent_as_tool/` | `AgentTool` vs `sub_agents` side by side |

---

## 6. Production notes

- **Idempotency & side effects.** The model may retry a tool. Make writes idempotent or
  guard with an idempotency key.
- **Timeouts.** A slow sync tool blocks the turn. Wrap network calls with a timeout;
  push genuinely long work to `LongRunningFunctionTool` or a queue.
- **Validate model-supplied args.** The `city` string comes from an LLM. Range-check,
  allow-list, and sanitize before using it in a query/path/shell.
- **Unexpected exceptions** propagate out of `run_async` and abort the turn. Catch what
  you can inside the tool and return an error dict; let truly exceptional cases raise and
  be handled by a callback (Module 15) or the caller.
- **Logging.** Log tool name + args + outcome (redact secrets/PII). `event.usage_metadata`
  + tool error rate are your core agent metrics (Module 17).
- **Least privilege.** The tool runs with the service's credentials. Scope them per tool.

---

## 7. Exercises

1. **Docstring ablation.** Remove the `Args:` block from a tool. Does the model still
   call it correctly? Remove the docstring entirely — what happens?
2. **Bad args.** Make a tool that does `int(user_supplied)` with no guard; get the model
   to pass `"twelve"`. Fix it to return an error dict.
3. **`skip_summarization`.** Toggle it on a tool that returns a formatted table. Compare
   the user-facing output.
4. **Resume timing.** In `ex03`, resume the approval with `"status": "denied"`. Confirm
   the agent handles rejection.
5. **Tool vs sub-agent.** Convert `ex04`'s `AgentTool` translator to a `sub_agent`.
   Observe who replies to the user and whether the root agent gets control back.

---

## 8. Checklist

- [ ] Explain how ADK builds a tool schema and why the docstring matters most
- [ ] List JSON-safe parameter types; know that `*args/**kwargs` are ignored
- [ ] Return `status`/`error_message` dicts instead of raising for expected failures
- [ ] Use `ToolContext.state` with the right prefix (`user:` / `temp:` / none)
- [ ] Use `skip_summarization` and know when you want it
- [ ] Implement a `LongRunningFunctionTool` pause/resume cycle
- [ ] Choose `AgentTool` vs `sub_agents` for a given design

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| Model never calls the tool | Weak docstring/name; make the description say *when* to use it |
| `tool_context` shows up as a model argument | It's detected by the `ToolContext` annotation — check the type hint is exactly `ToolContext` |
| Args arrive as strings when you expected ints | Add precise type hints; still validate — models can send `"3"` |
| Tool raises, whole turn dies | Wrap expected failures, return `{"status":"error",...}` |
| `temp:` value missing in the next tool | You read it in the *same* tool call before the event boundary, or a different invocation |
| Long-running tool never resumes | Client must send a `FunctionResponse` with the **same** `function_call_id` |
