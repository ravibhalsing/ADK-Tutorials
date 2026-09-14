"""Module 05 · Example 2 — consume your own MCP server.

`mcp_server.py` in this folder is a small FastMCP server exposing employee
lookup and office headcount tools. This agent connects to it over stdio,
the same way `ex01` connects to the public filesystem server — the only
difference is *whose* server it is.

    adk run ex02_custom_mcp_server
    adk web
"""

from __future__ import annotations

import os
import pathlib
import sys

from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
SERVER = str(pathlib.Path(__file__).parent / "mcp_server.py")

root_agent = Agent(
    name="hr_agent",
    model=MODEL,
    description="Answers questions about employees and office headcount using a custom MCP server.",
    instruction=(
        "Use the MCP tools to answer questions about employees and office headcount. "
        "Only report results that came back from an actual tool call — never invent an "
        "employee, role, office, or headcount. If a tool returns an 'error' field, relay "
        "it plainly instead of guessing."
    ),
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,  # the venv's own python — no subprocess-spawn
                    args=[SERVER],           # concerns like ex01's Node.js server has
                ),
                timeout=20,
            ),
        )
    ],
)
