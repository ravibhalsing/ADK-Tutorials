"""python run.py — currency agent over a hand-written OpenAPI spec."""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.runners import InMemoryRunner  
from google.genai import types  

from agent import root_agent  

APP = "fx"


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")
    for q in [
        "How many euros is 250 US dollars right now?",
        "What was the USD to INR rate on 2024-01-02?",
    ]:
        print(f"\nuser> {q}")
        async for ev in runner.run_async(
            user_id="u1", session_id=s.id,
            new_message=types.Content(role="user", parts=[types.Part(text=q)]),
        ):
            for c in ev.get_function_calls():
                print(f"  [api call] {c.name}({dict(c.args)})")
            for r in ev.get_function_responses():
                print(f"  [api resp] {str(r.response)[:200]}")
            if ev.is_final_response() and ev.content:
                print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())


if __name__ == "__main__":
    asyncio.run(main())
