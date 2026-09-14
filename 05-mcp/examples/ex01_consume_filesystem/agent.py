"""Module 05 · Example 1 — consume a public MCP server (filesystem).

ADK is the MCP *client* here. `McpToolset` launches the official Node-based
`@modelcontextprotocol/server-filesystem` over stdio, discovers its tools,
converts them to ADK tools, and proxies calls. This is the canonical pattern
from the ADK docs (https://adk.dev/tools-custom/mcp-tools/):

    McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(command="npx", args=[...]),
        ),
        tool_filter=[...],   # allow-list — the server also has write_file etc.
    )

Setup: run `npm install` in this directory once (installs
`@modelcontextprotocol/server-filesystem` locally). Requires Node.js.

Windows note: the official docs themselves flag stdio-transport subprocess
spawning as flaky on Windows (`_make_subprocess_transport NotImplementedError`,
their fix: `adk web --no-reload`). In practice the deeper issue is that ADK's
MCPSessionManager tears down and respawns the child process on every
"different loop or disconnected" check, so any given connection attempt is a
race against Windows process-creation latency (antivirus scanning a freshly
spawned/installed binary, OS servicing activity, etc.). This file adds three
defenses on top of the bare docs example, in increasing order of importance:

  1. Launch `node` directly on the locally-installed package instead of going
     through `npx` (which on Windows means `cmd.exe` + an npm registry-verify
     step first) — one less subprocess hop to race. Falls back to `npx -y` if
     `npm install` hasn't been run yet.
  2. `tool_list_cache_ttl_seconds` caches the discovered tool list, so the
     risky respawn only has to succeed once per TTL window, not every turn.
  3. `_RetryingMcpToolset` retries both tool discovery and individual tool
     *calls* with backoff before giving up. Safe to retry calls blindly here
     because `tool_filter` only exposes read-only tools.

None of this is required by the MCP or ADK spec — it's Windows-specific
transport-reliability engineering. On Linux/macOS the bare docs example
(stdio + npx, no retries) is reliable as-is.

    adk run ex01_consume_filesystem
    adk web --no-reload
"""

from __future__ import annotations

import asyncio
import logging
import os
import pathlib

from google.adk.agents import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_tool import McpTool
from mcp import StdioServerParameters

logger = logging.getLogger(__name__)

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

HERE = pathlib.Path(__file__).parent

# The only directory the MCP server is allowed to touch.
SANDBOX = str(HERE / "sandbox")

_LOCAL_SERVER_ENTRY = (
    HERE / "node_modules" / "@modelcontextprotocol" / "server-filesystem" / "dist" / "index.js"
)

if _LOCAL_SERVER_ENTRY.exists():
    COMMAND = "node"
    ARGS = [str(_LOCAL_SERVER_ENTRY), SANDBOX]
else:
    # On Windows, `npx` is a shell script — only `npx.cmd` can be spawned
    # directly by subprocess without a shell.
    COMMAND = "npx.cmd" if os.name == "nt" else "npx"
    ARGS = ["-y", "@modelcontextprotocol/server-filesystem", SANDBOX]


# Capped exponential backoff: several seconds of retry budget for a cold
# subprocess spawn, without any single wait growing unboundedly long.
_BACKOFF_INITIAL_SECONDS = 1.0
_BACKOFF_FACTOR = 1.8
_BACKOFF_MAX_SECONDS = 6.0
_DISCOVERY_ATTEMPTS = 6
_CALL_ATTEMPTS = 6

# Substring ADK's graceful-error-handling path puts in a failed call's
# {"error": ...} dict when the stdio session died mid-request — as opposed to
# a legitimate application-level error (bad path, file not found), which
# retrying would never fix.
_TRANSIENT_ERROR_MARKER = "connection closed"


def _retry_delays(attempts: int):
    """Yields `attempts - 1` backoff delays (none after the last attempt)."""
    delay = _BACKOFF_INITIAL_SECONDS
    for _ in range(attempts - 1):
        yield delay
        delay = min(delay * _BACKOFF_FACTOR, _BACKOFF_MAX_SECONDS)


def _wrap_with_call_retry(tool: McpTool) -> None:
    """Monkey-patches `tool.run_async` to retry transient connection errors."""
    original_run_async = tool.run_async

    async def run_async(*, args, tool_context):
        delays = _retry_delays(_CALL_ATTEMPTS)
        result = None
        for attempt in range(1, _CALL_ATTEMPTS + 1):
            result = await original_run_async(args=args, tool_context=tool_context)
            error = result.get("error") if isinstance(result, dict) else None
            if not error or _TRANSIENT_ERROR_MARKER not in str(error).lower():
                return result
            delay = next(delays, None)
            if delay is None:
                break
            logger.info(
                "MCP call to %s attempt %d/%d hit a transient connection error,"
                " retrying in %.2fs",
                tool.name,
                attempt,
                _CALL_ATTEMPTS,
                delay,
            )
            await asyncio.sleep(delay)
        return result

    tool.run_async = run_async


class _RetryingMcpToolset(McpToolset):
    """McpToolset that retries both tool discovery and tool calls on the
    transient cold-start / reconnect race (see module docstring).
    """

    async def get_tools(self, readonly_context: ReadonlyContext | None = None):
        delays = _retry_delays(_DISCOVERY_ATTEMPTS)
        tools = None
        for attempt in range(1, _DISCOVERY_ATTEMPTS + 1):
            try:
                tools = await super().get_tools(readonly_context)
                break
            except ConnectionError:
                delay = next(delays, None)
                if delay is None:
                    raise
                logger.info(
                    "MCP tool discovery attempt %d/%d failed, retrying in %.2fs",
                    attempt,
                    _DISCOVERY_ATTEMPTS,
                    delay,
                )
                await asyncio.sleep(delay)

        for tool in tools:
            if isinstance(tool, McpTool):
                _wrap_with_call_retry(tool)
        return tools


root_agent = Agent(
    name="fs_agent",
    model=MODEL,
    description="Reads and lists files inside a sandboxed folder via an MCP server.",
    instruction=(
        "You can inspect files in the user's project folder using the filesystem tools. "
        "Use `list_directory` to see what's there and `read_file` to read a file. "
        "Answer questions about the file contents. Never claim a file exists without listing. "
        "Only report results that came back from an actual tool call. If `list_directory` or "
        "`read_file` is not available to you as a callable tool, say so plainly — do not write "
        "out a fake tool call or invent file names or contents."
    ),
    tools=[
        _RetryingMcpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=COMMAND,
                    args=ARGS,
                    # Pin the child process's cwd to the sandbox. Without this,
                    # a relative path like "." resolves against whatever
                    # directory `adk web`/`adk run` happened to be launched
                    # from, not the sandbox.
                    cwd=SANDBOX,
                ),
                timeout=120,
            ),
            # Cache the discovered tool list so the risky first connection
            # only has to succeed once per 5 minutes, not on every turn.
            tool_list_cache_ttl_seconds=300,
            # Allow-list: the filesystem server also has write_file, move_file,
            # create_directory — omit them so the model can't call them.
            tool_filter=["list_directory", "read_file", "get_file_info", "search_files"],
        )
    ],
)
