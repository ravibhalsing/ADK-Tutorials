# Example 02 — Consume your own MCP server

`mcp_server.py` is a small server built with `FastMCP` (decorator-based —
contrast with `ex03`'s low-level `Server` API). `agent.py` connects to it
over stdio, the same pattern as `ex01`, just pointed at a server we wrote
ourselves instead of an npm package.

## Setup

```powershell
adk run ex02_custom_mcp_server
```

No Node.js involved — the server is `python mcp_server.py`, launched via
`sys.executable`, so none of `ex01`'s Windows subprocess-spawn concerns
apply here. A plain Python child process starts fast and reliably.

## Try it

```
Who is e1?
How many people are in the Bengaluru office?
Who is e9?
```

The last one should come back as a plain "no employee with that id" — the
server returns `{"error": ...}` for unknown IDs, and the agent's
instruction says to relay that instead of guessing.

## How it works

```python
# mcp_server.py
mcp = FastMCP("company-facts")

@mcp.tool()
def get_employee(employee_id: str) -> dict:
    """Look up an employee by ID."""
    ...

mcp.run()   # stdio by default
```

```python
# agent.py
McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(command=sys.executable, args=[SERVER]),
    ),
)
```

No `tool_filter` here — every tool the server exposes is meant to be
callable.

## Exercise

Add a third tool to `mcp_server.py` (e.g. `list_teams`). Restart, ask a
question that needs it — no change to `agent.py` required, since
`McpToolset` discovers tools by calling the server, not by declaring them
upfront.
