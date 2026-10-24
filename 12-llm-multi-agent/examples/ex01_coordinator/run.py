"""python run.py — two users, two different routes."""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.runners import InMemoryRunner  
from google.genai import types  

from agent import root_agent  

APP = "support"


async def conversation(runner, sid, msgs):
    for m in msgs:
        print(f"\nuser> {m}")
        async for ev in runner.run_async(
            user_id="u1", session_id=sid,
            new_message=types.Content(role="user", parts=[types.Part(text=m)]),
        ):
            if ev.actions and ev.actions.transfer_to_agent:
                print(f"  --> transfer_to_agent: {ev.actions.transfer_to_agent}")
            if ev.is_final_response() and ev.author != "user" and ev.content:
                t = "".join(p.text or "" for p in ev.content.parts).strip()
                if t:
                    print(f"[{ev.author}]> {t}")


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)

    s1 = await runner.session_service.create_session(app_name=APP, user_id="u1")
    await conversation(runner, s1.id, [
        "Hi, I was charged twice for my subscription this month.",
        "Can you refund the duplicate?",
    ])

    s2 = await runner.session_service.create_session(app_name=APP, user_id="u1")
    await conversation(runner, s2.id, [
        "The app shows 'ERR_CONN_REFUSED' when I try to sync.",
    ])


if __name__ == "__main__":
    asyncio.run(main())
