# Module 06 — OpenAPI & Third-Party Tool Ecosystems

> **Goal:** turn a whole REST API into tools with one line (`OpenAPIToolset`), and reuse
> LangChain / CrewAI tools via `LangchainTool` / `CrewaiTool`.
>
> **Docs:** [OpenAPI tools](https://adk.dev/tools-custom/openapi-tools/) ·
> [Tools overview](https://adk.dev/tools-custom/) · third-party tools

---

## 1. `OpenAPIToolset` — a REST API becomes a toolset

```python
from google.adk.tools.openapi_tool import OpenAPIToolset

toolset = OpenAPIToolset(spec_str=open_api_json, spec_str_type="json")   # or "yaml", or spec_dict=
agent = Agent(name="api_agent", model=MODEL, tools=[toolset])
```

What it does:
- Parses an **OpenAPI 3.x** document.
- Creates one **`RestApiTool`** per operation (GET/POST/PUT/DELETE/…).
- Tool **name** ← `operationId` (snake_cased, ≤ 60 chars). Tool **description** ←
  `summary` / `description`. Parameters ← the operation's `parameters` + request body.
- At call time it builds and sends the HTTP request, returns the JSON.

### Gotchas (all hit while building this module)

| Gotcha | Fix |
|---|---|
| No `servers:` block → tool has no base URL → calls fail / hit `localhost` | Put `servers: [{url: https://...}]` in the spec (FastAPI: `FastAPI(servers=[...])`) |
| Reserved Python names (`from`, `class`, `id`) as parameters | ADK renames them (`from` → `param_from`) — check the wire name matches the API, or rename in the spec |
| API returns a 3xx redirect | `RestApiTool` doesn't follow redirects — use the final URL in `servers:` |
| API returns 4xx/5xx | surfaced to the model as an error string (it can relay or retry, capped at 3) |
| Give every operation an explicit `operationId` | otherwise tool names are auto-generated and ugly |

### Auth

```python
OpenAPIToolset(spec_dict=spec, auth_scheme=..., auth_credential=...)
```
API-key / bearer / OAuth2 schemes from the spec's `securitySchemes` are honoured;
credentials passed here apply to every generated tool. Full auth flows: Module 07.

---

## 2. `LangchainTool` — reuse LangChain's tool ecosystem

```python
from google.adk.integrations.langchain import LangchainTool   # 2.x path
# (google.adk.tools.langchain_tool still works, deprecated)
from langchain_core.tools import tool as lc_tool

@lc_tool
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression."""
    ...

agent = Agent(name="a", model=MODEL, tools=[LangchainTool(tool=calculator)])
```

Any LangChain `BaseTool` works — including the hundreds of `langchain_community`
integration tools (search, SQL, HTTP, cloud services). **Caveat:** many
`langchain_community` tools are lightly maintained and break against upstream API
changes (we hit this with Wikipedia's new user-agent policy and an `arxiv` version
mismatch). Pin versions; test before relying on one.

Use the **`@tool` decorator** or a `StructuredTool` with an explicit `args_schema` —
plain `Tool.from_function` leaks a `config` kwarg through the ADK bridge.

---

## 3. `CrewaiTool` — reuse CrewAI tools

```python
from google.adk.integrations.crewai import CrewaiTool   # needs google-adk[extensions]
from crewai_tools import SerperDevTool

search = CrewaiTool(
    tool=SerperDevTool(),
    name="web_search",                       # required — ADK can't infer it
    description="Search the web. Input: a query string.",   # required
)
```

CrewAI tools **require** an explicit `name` + `description`. See `ex03/crewai_pattern.py`.
`crewai-tools` is a heavy dependency — install it only if you need it.

---

## 4. When to use which

| You have | Use |
|---|---|
| An OpenAPI/Swagger spec for the API | `OpenAPIToolset` |
| An API with no spec | write a minimal spec (see `ex02`) or a plain function tool (Module 03) |
| A tool already implemented in LangChain/CrewAI | `LangchainTool` / `CrewaiTool` |
| Full control over retries, ranking, caching, shaping | a hand-written function tool |
| A whole *service* (files, DB, SaaS) | an MCP server (Module 05) |

---

## 5. Examples

| Folder | Shows |
|---|---|
| `ex01_openapi_local/` | `OpenAPIToolset` from a live FastAPI `/openapi.json`; GET/POST, path + query params, 404 handling |
| `ex02_openapi_public/` | a **hand-written** YAML spec for a real key-less public API (Frankfurter FX); path + query params |
| `ex03_langchain_crewai/` | `LangchainTool` wrapping a `@tool` function; CrewAI pattern in `crewai_pattern.py` |

---

## 6. Production notes

- **Spec drift.** The generated tools are only as correct as the spec. If the deployed
  API diverges from its spec, tools break at call time. Regenerate/test on API changes;
  pin the spec version you built against.
- **Partial failures & retries.** `RestApiTool` retries a failed call up to 3× on the
  model's judgement. Make sure the underlying operations are safe to retry (idempotent),
  or the model will double-POST.
- **Rate limits & timeouts.** Every tool call is a real HTTP request. Add upstream
  backoff; watch the API's quota.
- **Credential rotation.** Auth credentials are captured at toolset construction — plan
  for refresh (Module 07).
- **Third-party tool trust.** A `langchain_community`/`crewai` tool is third-party code
  with network access. Vet it, pin it, sandbox its credentials.

---

## 7. Exercises

1. Add a `DELETE /books/{id}` route to `ex01`'s API. Regenerate — the `delete_book` tool
   appears with no agent change. Then `tool_filter` it out.
2. Break `ex02` by removing the `servers:` line. Read the failure. Restore it.
3. In `ex03`, swap the calculator for `langchain_community.tools.DuckDuckGoSearchRun`
   (`pip install duckduckgo-search`). Note whether it works or hits a rate limit.
4. Give `ex01`'s API an API-key security scheme and pass `auth_credential` to the toolset.

---

## 8. Checklist

- [ ] Generate tools from a JSON and a YAML OpenAPI spec
- [ ] Explain why `servers:` and `operationId` matter
- [ ] Handle an API error surfaced through a generated tool
- [ ] Wrap a LangChain `@tool` with `LangchainTool`
- [ ] State why `CrewaiTool` needs explicit name/description
- [ ] Choose OpenAPI vs function tool vs MCP for a given integration

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| Tool calls hit `localhost` / no host | add `servers:` to the spec |
| `Status 301/302` | API redirected; use the canonical URL |
| param named `param_from` on the wire | ADK renamed reserved word `from`; align spec ↔ API |
| `calculator() missing 1 required positional argument` via LangchainTool | use `@tool` / `StructuredTool`, not `Tool.from_function` |
| `No module named 'langchain_core'` | `pip install langchain-core` (or `langchain-community`) |
| `Crewai Tools require pip install 'google-adk[extensions]'` | install that extra (heavy) |
| community tool raises `AttributeError`/`JSONDecodeError` | version drift in the community package; pin or replace |
