# Example 01 — Consume a public MCP server (filesystem)

ADK as an MCP *client*, connecting to the official
`@modelcontextprotocol/server-filesystem` over stdio.

## Setup

```powershell
npm install                 # installs the server locally into node_modules
adk run ex01_consume_filesystem
```

`sandbox/` is the only directory the server is allowed to touch — it
contains `report.txt` and `team.csv` for the agent to find.

## Try it

```
hi
What files are in my folder?
Read report.txt and summarize it in one line.
```

## How it works

```python
McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(command="node", args=[...entry, SANDBOX]),
    ),
    tool_filter=["list_directory", "read_file", "get_file_info", "search_files"],
)
```

`tool_filter` is an allow-list — the server also exposes `write_file`,
`move_file`, `create_directory`; omitting them means the model can't call
them no matter what it's asked to do.

## Windows reliability notes

See the comment block at the top of `agent.py` for why this example spawns
`node` directly (instead of the docs' plain `npx`) and retries tool
discovery/calls with backoff. Short version: `adk`'s dev server tears down
and respawns the stdio connection often, and on Windows that respawn can
lose a race against process-creation overhead (antivirus scanning a fresh
binary, OS servicing activity). None of this is needed on Linux/macOS.

If you still see a `Connection closed` error surface to the user after all
retries are exhausted, it means something on the machine stalled process
creation for longer than ~20 seconds — check Task Manager / the Windows
Event Log for what else was running at that exact timestamp before assuming
it's a code bug.

## Exercise

Add `write_file` to `tool_filter` and ask the agent to create a file. Then
remove it again and confirm the agent reports it can't.
