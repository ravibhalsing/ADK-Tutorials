"""python run.py — NASA APOD agent with an API key injected by the toolset."""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.runners import InMemoryRunner  
from google.genai import types  

from agent import root_agent  

APP = "apod"


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")
    for q in [
        "What's the astronomy picture of the day?",
        "What about on 2020-07-04?",
    ]:
        print(f"\nuser> {q}")
        async for ev in runner.run_async(
            user_id="u1", session_id=s.id,
            new_message=types.Content(role="user", parts=[types.Part(text=q)]),
        ):
            for c in ev.get_function_calls():
                # note: no api_key here — the toolset adds it after the model call
                print(f"  [api call] {c.name}({dict(c.args)})")
            if ev.is_final_response() and ev.content:
                print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())


if __name__ == "__main__":
    asyncio.run(main())
