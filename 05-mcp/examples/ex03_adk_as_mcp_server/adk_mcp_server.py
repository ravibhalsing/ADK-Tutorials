"""Expose ADK FunctionTools as an MCP server (the reverse direction).

Any MCP client — Claude Desktop, another agent framework, ADK's own MCPToolset —
can now call these tools. We wrap ADK `FunctionTool`s and advertise them via the
MCP low-level `Server` API.

Run standalone (it waits on stdio):
    python adk_mcp_server.py
"""

from __future__ import annotations

import asyncio
import json

import mcp.server.stdio
import mcp.types as mcp_types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type


# --- the ADK tools we want to share ---------------------------------------------

def celsius_to_fahrenheit(celsius: float) -> dict:
    """Convert a temperature from Celsius to Fahrenheit."""
    return {"fahrenheit": round(celsius * 9 / 5 + 32, 2)}


def slugify(text: str) -> dict:
    """Turn a string into a URL slug (lowercase, hyphens, alphanumeric only)."""
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return {"slug": slug}


ADK_TOOLS = {t.name: t for t in (FunctionTool(celsius_to_fahrenheit), FunctionTool(slugify))}

# --- MCP server plumbing -------------------------------------------------------

app = Server("adk-tools-over-mcp")


@app.list_tools()
async def list_tools() -> list[mcp_types.Tool]:
    return [adk_to_mcp_tool_type(t) for t in ADK_TOOLS.values()]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[mcp_types.Content]:
    tool = ADK_TOOLS.get(name)
    if not tool:
        return [mcp_types.TextContent(type="text", text=json.dumps({"error": f"no tool {name!r}"}))]
    result = await tool.run_async(args=arguments, tool_context=None)
    return [mcp_types.TextContent(type="text", text=json.dumps(result))]


async def main() -> None:
    async with mcp.server.stdio.stdio_server() as (read, write):
        await app.run(
            read, write,
            InitializationOptions(
                server_name=app.name,
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
