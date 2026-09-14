# Example 03 — Expose ADK tools *as* an MCP server

The reverse direction: your ADK `FunctionTool`s become MCP tools any client can call
(Claude Desktop, another framework, ADK's own `MCPToolset`).

```powershell
python test_client.py       # raw MCP client — no LLM, no Vertex quota needed
python adk_mcp_server.py     # run the server standalone (waits on stdio; Ctrl-C to stop)
```

## Captured output (`test_client.py`)

```
tools advertised: ['celsius_to_fahrenheit', 'slugify']
celsius_to_fahrenheit(100) -> {"fahrenheit": 212.0}
slugify('Hello, ADK World!') -> {"slug": "hello-adk-world"}
```

## How it works

```python
app = Server("adk-tools-over-mcp")             # mcp low-level server

@app.list_tools()
async def list_tools():
    return [adk_to_mcp_tool_type(t) for t in ADK_TOOLS.values()]   # ADK schema -> MCP schema

@app.call_tool()
async def call_tool(name, arguments):
    result = await ADK_TOOLS[name].run_async(args=arguments, tool_context=None)
    return [mcp_types.TextContent(type="text", text=json.dumps(result))]
```

`adk_to_mcp_tool_type` (from `google.adk.tools.mcp_tool.conversion_utils`) does the
schema translation. `FunctionTool.run_async(..., tool_context=None)` executes the tool.

## Use it from Claude Desktop

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "adk-tools": {
      "command": "python",
      "args": ["D:/.../05-mcp/examples/ex03_adk_as_mcp_server/adk_mcp_server.py"]
    }
  }
}
```
Restart Claude Desktop; `celsius_to_fahrenheit` and `slugify` appear as tools.

## Hosting remotely

Wrap the server in Starlette + `StreamableHTTPSessionManager` (stateless for scale) and
deploy to Cloud Run — see Module 22. Or run it as a K8s sidecar — Module 24.
