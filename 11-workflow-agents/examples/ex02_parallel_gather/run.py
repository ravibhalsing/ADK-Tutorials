"""Drive ex02's ParallelAgent fan-out + SequentialAgent gather.

    python run.py
"""

from __future__ import annotations

import asyncio
import pathlib
import time

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.runners import InMemoryRunner
from google.genai import types

from agent import root_agent

APP = "fanout"


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")

    topic = input("Topic to research: ").strip() or "solar power"

    t0 = time.time()
    async for ev in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=topic)]),
    ):
        if ev.is_final_response() and ev.author != "user" and ev.content:
            txt = "".join(p.text or "" for p in ev.content.parts).strip()
            print(f"\n===== {ev.author} ({time.time()-t0:.1f}s) =====\n{txt}")

    print(f"\ntotal wall time: {time.time()-t0:.1f}s  (3 researchers ran concurrently)")


if __name__ == "__main__":
    asyncio.run(main())
