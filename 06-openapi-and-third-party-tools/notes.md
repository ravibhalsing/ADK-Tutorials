# Module 06 — official documentation cross-reference

| Topic | Page |
|---|---|
| OpenAPI tools (`OpenAPIToolset`, `RestApiTool`) | https://adk.dev/tools-custom/openapi-tools/ |
| Tools overview / third-party | https://adk.dev/tools-custom/ |
| Authentication | https://adk.dev/tools-custom/authentication/ (Module 07) |

## Confirmed on this machine (ADK 2.8.0, Vertex, 2026-09-05)

- **Import:** `from google.adk.tools.openapi_tool import OpenAPIToolset` (short path works).
  Full: `...openapi_tool.openapi_spec_parser.openapi_toolset`.
- `OpenAPIToolset(spec_str=..., spec_str_type="json"|"yaml")` or `spec_dict=...`.
- `await toolset.get_tools()` lists the generated `RestApiTool`s. Names come from
  `operationId` (snake_case). Descriptions from `summary`.
- **`servers:` is mandatory** in the spec — without it the base URL is unknown and calls
  fail. FastAPI: `FastAPI(servers=[{"url": "http://localhost:8001"}])` (not added by default).
- **Reserved words**: a query param named `from` is exposed to the model as `param_from`.
  Verify it still hits the API's real param name (Frankfurter's new API uses
  `base`/`symbols`, avoiding the issue).
- **Redirects not followed**: `api.frankfurter.app` → 301; had to use
  `https://api.frankfurter.dev/v1`.
- API 4xx → tool returns an `{'error': 'Tool ... execution failed ... don't retry more
  than 3 times ...'}` string; the model relays it gracefully.
- **LangChain**: `from google.adk.integrations.langchain import LangchainTool`
  (`google.adk.tools.langchain_tool` deprecated). Wrap a `@langchain_core.tools.tool`
  function or a `StructuredTool`. `Tool.from_function` leaks a `config` kwarg → `TypeError`.
  `langchain-community` Wikipedia tool is broken (Wikimedia now requires a UA → 403);
  `arxiv` tool broken (Search.results() removed). Community tools rot — pin/replace.
- **CrewAI**: `from google.adk.integrations.crewai import CrewaiTool`, needs
  `google-adk[extensions]`. `CrewaiTool(tool=..., name=..., description=...)` — name +
  description required.

## Imports

```python
from google.adk.tools.openapi_tool import OpenAPIToolset
from google.adk.integrations.langchain import LangchainTool
from google.adk.integrations.crewai import CrewaiTool          # google-adk[extensions]
from langchain_core.tools import tool as lc_tool
```
