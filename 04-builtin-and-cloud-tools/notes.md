# Module 04 — official documentation cross-reference

| Topic | Page |
|---|---|
| Google Search grounding | https://adk.dev/grounding/google_search_grounding/ |
| Grounding with Vertex AI Search | https://adk.dev/grounding/ |
| Tool limitations (one-built-in-per-agent, sub-agent rules) | https://adk.dev/tools/limitations/ |
| Code executors (`BuiltInCodeExecutor`) | https://adk.dev/api-reference/python/ (google.adk.code_executors) |
| Vertex AI Search tool | https://adk.dev/api-reference/python/ (google.adk.tools) |
| BigQuery integration | https://adk.dev/api-reference/python/ (google.adk.integrations.bigquery) |

## Confirmed on this machine (ADK 2.8.0, Vertex us-central1, 2026-09-05)

- `from google.adk.tools import google_search` → a `GoogleSearchTool` instance. Attach as
  `tools=[google_search]`. Grounding **works on Vertex**; `event.grounding_metadata` has
  `web_search_queries` and `grounding_chunks[].web.{title, uri}` (uris are
  `vertexaisearch.cloud.google.com/grounding-api-redirect/...`).
- `from google.adk.code_executors import BuiltInCodeExecutor` → pass as
  `code_executor=BuiltInCodeExecutor()`. Model emits `part.executable_code.code`,
  sandbox returns `part.code_execution_result.{outcome, output}`. Verified: numpy
  available in the sandbox.
- **Limitation is real and enforced at run time** (construction succeeds):
  `google_search` + a function tool in one agent →
  `400 INVALID_ARGUMENT: Multiple tools are supported only when they are all search tools.`
- Workaround: `tools=[AgentTool(agent=searcher), AgentTool(agent=coder)]` where each
  specialist holds exactly one built-in. `bypass_multi_tools_limit=True` exists for
  `GoogleSearchTool` / `VertexAiSearchTool` (ADK ≥ 1.16).
- `VertexAiSearchTool(data_store_id=...)` imports fine; needs a real data store to run.
- `google.adk.tools.bigquery` is **deprecated** → `google.adk.integrations.bigquery`,
  and needs `google-cloud-*` (install `google-adk[gcp]`).
- ⚠️ **Grounding / search quota on a fresh project is low** — back-to-back runs hit
  `_ResourceExhaustedError` (429). `ex03`'s search sub-call is quota-sensitive; the
  `--break` 400 demo is the reliable teaching artifact.

## Imports

```python
from google.adk.tools import google_search, VertexAiSearchTool, AgentTool
from google.adk.code_executors import BuiltInCodeExecutor
# from google.adk.integrations.bigquery import BigQueryToolset   # needs google-adk[gcp]
```
