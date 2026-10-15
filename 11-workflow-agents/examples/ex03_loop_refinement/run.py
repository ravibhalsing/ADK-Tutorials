"""Drive ex03's LoopAgent refinement loop.

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

APP = "loop"


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")
    brief = input("What should be written, and what are the rules? ").strip()
    async for _ in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=brief)]),
    ):
        pass

    final = await runner.session_service.get_session(app_name=APP, user_id="u1", session_id=s.id)
    print("\nfinal draft:", final.state.get("draft"))
    print("critic verdict:", final.state.get("feedback"))


if __name__ == "__main__":
    asyncio.run(main())
