# Module 02 — official documentation cross-reference

| Topic | Page |
|---|---|
| instruction / description / templating / output_schema / output_key / include_contents | https://adk.dev/agents/llm-agents/ |
| Planners (BuiltInPlanner, PlanReActPlanner, ThinkingConfig) | https://adk.dev/agents/llm-agents/ → "Planner" |
| Gemini models, model ids, regional-endpoint caveat | https://adk.dev/agents/models/google-gemini/ |
| `generate_content_config` fields (via google-genai) | https://ai.google.dev/api/generate-content#GenerationConfig |
| Global instructions → GlobalInstructionPlugin | https://adk.dev/apps/plugins/ |
| RunConfig / streaming | https://adk.dev/runtime/runconfig/ |

## Confirmed on this machine (ADK 2.8.0, gemini-2.5-flash / Vertex us-central1, 2026-09-05)

- **Instruction provider** signature: `Callable[[ReadonlyContext], str]`. Import
  `from google.adk.agents.readonly_context import ReadonlyContext`. `ctx.state` is
  read-only, plus `ctx.agent_name`, `ctx.invocation_id`.
- **`{key}`** missing in state → `KeyError` at request build. **`{key?}`** → omitted.
- **`create_session(..., state={...})`** seeds state before the first turn — how the
  examples inject values for templating/providers.
- **`temperature=0.0`** gave byte-identical output across 4 runs (not guaranteed, but
  stable). `temperature=1.0` gave 3–4 distinct answers per 4 runs.
- **`max_output_tokens`** truncates hard. ⚠️ On Gemini 2.5 thinking models the cap also
  covers thinking tokens — a tiny cap yields **empty text**. Pass
  `types.ThinkingConfig(thinking_budget=0)` for a clean truncation/stop demo.
- **`stop_sequences=["5"]`** on "count 1..10" → `'1\n2\n3\n4'`.
- **`output_schema`** → model returns JSON, ADK parses + Pydantic-coerces (`990` → `990.0`),
  stores the **dict** in `state[output_key]`. `output_schema` + `tools` on one agent:
  *worked* on ADK 2.8 + Gemini 2.5, but don't rely on it — split into two agents.
- **`input_schema`** → the user message must be a JSON string conforming to the model.
- **Thinking**: Gemini 2.5 thinks even with no planner (`thoughts_token_count` > 0).
  `BuiltInPlanner(ThinkingConfig(include_thoughts=True))` did NOT surface `part.thought`
  parts on this endpoint; `PlanReActPlanner` surfaced 1 and injected `/*PLANNING*/`
  structure into the visible output.

## Imports

```python
from google.adk.agents import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.planners import BuiltInPlanner, PlanReActPlanner
from google.genai import types      # GenerateContentConfig, ThinkingConfig, SafetySetting,
                                    # HarmCategory, HarmBlockThreshold
from pydantic import BaseModel, Field
```
