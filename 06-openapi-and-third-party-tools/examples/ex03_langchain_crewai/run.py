"""python run.py — agent using a LangChain Wikipedia tool through LangchainTool."""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.runners import InMemoryRunner  
from google.genai import types  

from agent import root_agent  

APP = "reference"


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")
    for q in [
        "What is (128 * 47) + (2 ** 16)?",
        "If a loan of 5000 grows at 7% for 3 years compounded annually, what's the balance?",
    ]:
        print(f"\nuser> {q}")
        async for ev in runner.run_async(
            user_id="u1", session_id=s.id,
            new_message=types.Content(role="user", parts=[types.Part(text=q)]),
        ):
            for c in ev.get_function_calls():
                print(f"  [tool call] {c.name}({dict(c.args)})")
            if ev.is_final_response() and ev.content:
                print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())


if __name__ == "__main__":
    asyncio.run(main())
