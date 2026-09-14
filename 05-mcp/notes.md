# Module 05 — official documentation cross-reference

| Topic | Page |
|---|---|
| MCP tools (client + server, transports, deployment patterns) | https://adk.dev/tools-custom/mcp-tools/ |
| MCP overview | https://adk.dev/mcp/ |
| MCP standard | https://modelcontextprotocol.io |

## Confirmed on this machine (ADK 2.8.0, mcp 1.29.1, Node 24, 2026-09-05)

- **Install:** `pip install "google-adk[mcp]"` → pins `mcp==1.29.1`. Installing bare
  `mcp` gets **2.1.1**, whose restructure (`httpx2`, `mcp-types`, moved
  `mcp.shared.session.ProgressFnT`) breaks `google.adk.tools.mcp_tool.mcp_toolset`.
- **Class name is `MCPToolset`** (not `McpToolset` as some docs show):
  `from google.adk.tools.mcp_tool import MCPToolset`.
  Connection params: `from google.adk.tools.mcp_tool.mcp_session_manager import
  StdioConnectionParams, SseConnectionParams, StreamableHTTPConnectionParams`.
  `from mcp import StdioServerParameters`.
- **ex01** (client → npx `@modelcontextprotocol/server-filesystem`): works. Logs
  `Secure MCP Filesystem Server running on stdio` and
  `Client does not support MCP Roots, using allowed directories set from server args`.
  MCP tool calls (`list_directory`, `read_file`) appear as normal `event.get_function_calls()`.
  `tool_filter` is an allow-list. `await toolset.close()` required in scripts.
- **ex02** (client → our `FastMCP` server via `sys.executable mcp_server.py`): MCP layer
  verified (server logs `ListToolsRequest`, `CallToolRequest`); full run pending Gemini
  quota.
- **ex03** (ADK tools → MCP server): **fully verified without an LLM**.
  `adk_to_mcp_tool_type` (from `google.adk.tools.mcp_tool.conversion_utils`) converts an
  ADK `FunctionTool` to `mcp_types.Tool`. `FunctionTool.run_async(args=..., tool_context=None)`
  executes it. Raw `mcp.ClientSession` lists + calls the tools.
- `FastMCP` is available: `from mcp.server.fastmcp import FastMCP`; `@mcp.tool()`; `mcp.run()`.

## Imports

```python
# client
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams, SseConnectionParams, StreamableHTTPConnectionParams,
)
from mcp import StdioServerParameters

# server (ADK tools over MCP)
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio, mcp.types as mcp_types
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

# server (quick)
from mcp.server.fastmcp import FastMCP
```
