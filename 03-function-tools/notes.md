# Module 03 — official documentation cross-reference

| Topic | Page |
|---|---|
| Function tools, schema generation, docstrings, return dict | https://adk.dev/tools-custom/function-tools/ |
| Tools overview, tool categories | https://adk.dev/tools-custom/ |
| ToolContext, state, actions | https://adk.dev/context/ |
| LongRunningFunctionTool / human-in-the-loop | https://adk.dev/tools-custom/function-tools/ → "Long Running" + graph "Human input" |
| AgentTool | https://adk.dev/tools-custom/function-tools/ → "Agent-as-a-Tool" |
| Tool auth (deep) | https://adk.dev/tools-custom/authentication/ (Module 07) |

## Confirmed on this machine (ADK 2.8.0, gemini-2.5-flash / Vertex, 2026-09-05)

- `tools=[fn]` auto-wraps as `FunctionTool(fn)`. Inspect the generated schema with
  `FunctionTool(fn)._get_declaration().model_dump(exclude_none=True)`:
  - whole docstring → `description`
  - params with no default → `required`; with default → optional
  - `Optional[str] = None` → `anyOf: [{string}, {null}], default: null`
  - `*args` / `**kwargs` → omitted
- **`ToolContext`** is injected by type annotation (any parameter name), not in the model
  schema. `tool_context.state[...]` writes with prefixes:
  - `user:foo` → **persisted across sessions for the same `user_id`** (verified: a new
    session greeted the user by a nickname saved in a previous session)
  - `temp:foo` → visible to later tools in the same turn, **not** in `session.state` after
  - no prefix → this session
- **Instruction templating supports prefixed keys**: `{user:nickname?}` resolves against
  `user:`-scoped state.
- **`tool_context.actions.skip_summarization = True`** → the raw tool result becomes the
  final answer; the model does not reword it. The final event then has no text part —
  read `event.get_function_responses()`.
- **`LongRunningFunctionTool`**: returning `{"status": "pending", ...}` puts the call id
  in `event.long_running_tool_ids`. Resume by sending a new message whose part is
  `types.Part(function_response=types.FunctionResponse(id=<call_id>, name=<tool_name>,
  response=<final_dict>))`. Verified both approve and deny paths; the process can be
  stopped between pause and resume.
- **`AgentTool(agent=X)`** → root calls X like a tool, root authors the final answer.
  **`sub_agents=[X]`** + `transfer_to_agent` → X authors the final answer, root is out.
  (Check `event.author`.)
- Transfer-heavy apps log a `context_cache_config` warning — every transfer changes the
  prompt prefix and defeats caching. Set `context_cache_config` on the `App` (Module 10).

## Imports

```python
from google.adk.tools import ToolContext, FunctionTool, LongRunningFunctionTool, AgentTool
from google.genai import types   # types.FunctionResponse, types.Part
```
