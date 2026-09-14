# Module 05 — MCP (Model Context Protocol)

> **Goal:** connect ADK agents to **MCP servers** (ADK as client), and expose ADK tools
> **as** an MCP server (ADK as server).
>
> **Docs:** [MCP tools](https://adk.dev/tools-custom/mcp-tools/) ·
> [MCP overview](https://adk.dev/mcp/)
>
> **Setup:** `pip install "google-adk[mcp]"` (pins a compatible `mcp` 1.x — the
> standalone `mcp` package's latest 2.x is **not** compatible with ADK 2.8). Node.js /
> `npx` needed for `ex01`.

---

## 1. What MCP is

**Model Context Protocol** is an open standard for how LLM apps talk to external
tools/data. A **client** (your ADK agent) connects to a **server** (filesystem, GitHub,
a database, Google Maps, your own) and the server advertises tools the client can call.

Why it matters: one integration standard instead of N bespoke ones. Thousands of MCP
servers already exist; ADK can use any of them, and can *be* one.

```
ADK agent ──(MCP client)──►  MCP server  ──►  files / APIs / DBs
   │                          list_tools → [tool schemas]
   │                          call_tool(name, args) → result
```

Transports:
| Transport | Class | Use |
|---|---|---|
| **stdio** | `StdioConnectionParams(server_params=StdioServerParameters(command=..., args=[...]))` | local server as a subprocess |
| **Streamable HTTP** | `StreamableHTTPConnectionParams(url=..., headers=...)` | remote server (the current standard) |
| **SSE** | `SseConnectionParams(url=..., headers=...)` | older remote servers |

---

## 2. ADK as MCP client — `McpToolset`

```python
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/safe/dir"],
        ),
        timeout=30,
    ),
    tool_filter=["list_directory", "read_file"],   # expose ONLY these
)

agent = Agent(name="fs", model=MODEL, tools=[toolset])
```

- `McpToolset` goes straight in `tools=[...]`. On first use it launches/connects the
  server, calls `list_tools`, and converts each MCP tool to an ADK tool.
- **`tool_filter`** is your allow-list. The filesystem server also has `write_file`,
  `move_file`, `create_directory` — omit them and the model can't call them.
- **`tool_list_cache_ttl_seconds`** (current versions) caches the discovered tool list
  for N seconds instead of re-listing on every turn — worth setting on any stdio server
  where re-listing means respawning the subprocess (see `ex01`).
- Remote: swap in `StreamableHTTPConnectionParams(url=..., headers={"Authorization": ...})`.
- **Cleanup:** call `await toolset.close()` when done (the `adk` CLI does this for you;
  a script must — see the examples). Serialized/deployed agents reconnect on demand.

The class is **`McpToolset`** (lowercase-cp). `MCPToolset` (all-caps) still works as a
deprecated alias in current `google-adk` — it logs a `DeprecationWarning` on
construction. Import the current name: `from google.adk.tools.mcp_tool import
McpToolset`. (Class names in this SDK have shifted before; if a fresh `pip install`
breaks an import here, check `python -c "from google.adk.tools.mcp_tool import
McpToolset"` first before assuming the code is wrong.)

---

## 3. ADK as MCP server

Two ways to expose ADK tools so *other* clients (Claude Desktop, another framework) can
use them:

**a) Low-level `Server`** — full control (`ex03`):
```python
from mcp.server.lowlevel import Server
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

app = Server("my-adk-tools")

@app.list_tools()
async def list_tools():
    return [adk_to_mcp_tool_type(t) for t in MY_TOOLS]

@app.call_tool()
async def call_tool(name, arguments):
    result = await MY_TOOLS[name].run_async(args=arguments, tool_context=None)
    return [mcp_types.TextContent(type="text", text=json.dumps(result))]
```

**b) `FastMCP`** — quick, decorator-based (`ex02`'s server):
```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("company-facts")

@mcp.tool()
def get_employee(employee_id: str) -> dict:
    """Look up an employee."""
    ...

mcp.run()   # stdio
```

For remote hosting, wrap it in Starlette + `StreamableHTTPSessionManager` and deploy to
Cloud Run (Module 22); or run it as a **Kubernetes sidecar** next to the agent (Module 24).

---

## 4. Examples

| Folder | Direction | Shows |
|---|---|---|
| `ex01_consume_filesystem/` | ADK → public MCP server | `MCPToolset` + npx filesystem server, `tool_filter` for read-only, sandboxed dir |
| `ex02_custom_mcp_server/` | ADK → your MCP server | `FastMCP` server + agent consuming it over stdio |
| `ex03_adk_as_mcp_server/` | your MCP client → ADK tools | expose ADK `FunctionTool`s via low-level `Server`; raw MCP client test (no LLM) |

---

## 5. Production notes

- **Trust boundary.** An MCP server is code you're giving tool access to. Vet it like a
  dependency (supply chain). Prefer pinned versions, not `npx -y latest`.
- **Least privilege via `tool_filter`** and via what the server itself can reach (scope
  the filesystem dir, the API token, the DB user).
- **Lifecycle.** stdio servers are child processes — they leak if you don't `close()`.
  Remote servers need connection pooling / retry. On deploy, connections are *not*
  restored automatically; the toolset reconnects lazily.
- **Latency.** Every `call_tool` is an IPC/HTTP round-trip on top of the model call.
- **Schema drift.** If the server updates its tool schemas, your agent's behaviour can
  change silently. Pin server versions; test after upgrades.
- **Sidecar pattern** (K8s): agent container + MCP server container in one pod, talking
  over `localhost` — isolation without network exposure.

---

## 6. Exercises

1. Add `write_file` to `ex01`'s `tool_filter` and have the agent create a file. Then
   remove it and confirm the agent reports it can't.
2. Add a third tool to `ex02`'s `FastMCP` server (e.g. `list_teams`). Restart, ask a
   question that needs it — no agent code change required.
3. Point `ex03`'s server at Claude Desktop (add it to `claude_desktop_config.json` as an
   `mcp` stdio server) and call `slugify` from a Claude chat.
4. Convert `ex02`'s server to Streamable HTTP and run it on `localhost:9000`; switch the
   agent to `StreamableHTTPConnectionParams`.

---

## 7. Checklist

- [ ] Install the right MCP support (`google-adk[mcp]`, not bare `mcp` 2.x)
- [ ] Wire an `MCPToolset` (stdio and HTTP) into an agent
- [ ] Use `tool_filter` as an allow-list and explain why
- [ ] `close()` an `MCPToolset` and know why it matters
- [ ] Expose ADK tools with `FastMCP` and with the low-level `Server`
- [ ] Describe the sidecar deployment pattern and the supply-chain risk

---

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: mcp.shared.session` | `mcp` 2.x installed; `pip install "google-adk[mcp]"` to get the compatible 1.x |
| `cannot import name 'MCPToolset'` | Current name is `McpToolset`: `from google.adk.tools.mcp_tool import McpToolset` (the all-caps name is a deprecated alias, not the other way around) |
| `npx` not found / ENOENT | Install Node.js; ensure `npx` is on PATH |
| First `ex01` run is slow | `npm install` (run once, see `ex01`'s README) is downloading `@modelcontextprotocol/server-filesystem` |
| server process lingers after script | You didn't `await toolset.close()` |
| `Client does not support MCP Roots` (info log) | Harmless — the filesystem server falls back to the allowed dir from its args |
| model calls fail `429 RESOURCE_EXHAUSTED` | Not MCP — Vertex quota (see Module 04 §6) |
| `ex01`: `mcp.shared.exceptions.McpError: Connection closed` (Windows only) | ADK's `MCPSessionManager` tears down and respawns the stdio child on nearly every turn; on Windows that respawn races process-creation overhead and occasionally loses. `ex01/agent.py` already retries discovery and calls with backoff — if you still see this surface to the user after all retries, something on the machine (antivirus scan, Windows Update servicing) stalled process creation for longer than ~20s at that exact moment. Check Task Manager / Event Viewer for what was running at that timestamp before assuming it's a code bug. `adk run` is more reliable than `adk web` here since it keeps one connection for the whole session instead of reconnecting every turn. |
