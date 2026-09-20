"""Run the search agent and print the grounding metadata (citations).

    python run.py
"""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.runners import InMemoryRunner  
from google.genai import types  

from agent import root_agent  

APP = "search_demo"


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")

    q = "Who won the most recent FIFA World Cup and what was the final score?"
    print(f"user> {q}\n")

    async for ev in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=q)]),
    ):
        for c in ev.get_function_calls():
            print(f"  [call] {c.name}({dict(c.args)})")

        gm = ev.grounding_metadata
        if gm:
            if gm.web_search_queries:
                print(f"  [grounding] queries: {list(gm.web_search_queries)}")
            for chunk in (gm.grounding_chunks or []):
                if chunk.web:
                    print(f"  [source] {chunk.web.title} — {chunk.web.uri}")

        if ev.is_final_response() and ev.content:
            print("\nagent>", "".join(p.text or "" for p in ev.content.parts).strip())


if __name__ == "__main__":
    asyncio.run(main())
