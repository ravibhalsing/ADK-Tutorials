"""Prove the ADK-as-MCP server works — with a raw MCP client (no LLM, no quota).

    python test_client.py

Spawns adk_mcp_server.py over stdio, lists its tools, and calls each one.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = str(pathlib.Path(__file__).parent / "adk_mcp_server.py")


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=[SERVER])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("tools advertised:", [t.name for t in tools.tools])

            r1 = await session.call_tool("celsius_to_fahrenheit", {"celsius": 100})
            print("celsius_to_fahrenheit(100) ->", r1.content[0].text)

            r2 = await session.call_tool("slugify", {"text": "Hello, ADK World!"})
            print("slugify('Hello, ADK World!') ->", r2.content[0].text)



if __name__ == "__main__":
    asyncio.run(main())
