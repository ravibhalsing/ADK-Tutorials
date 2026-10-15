"""Drive ex01's SequentialAgent pipeline with a spec typed by the user.

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

APP = "pipe"


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")
    spec = input("Describe the function to write: ").strip() or (
        "parse a 'HH:MM' string into total minutes since midnight; reject invalid input")
    async for ev in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=spec)]),
    ):
        if ev.is_final_response() and ev.author != "user" and ev.content:
            print(f"\n===== {ev.author} =====")
            print("".join(p.text or "" for p in ev.content.parts).strip())

    final = await runner.session_service.get_session(app_name=APP, user_id="u1", session_id=s.id)
    print("\nstate keys after pipeline:", list(final.state.keys()))


if __name__ == "__main__":
    asyncio.run(main())
