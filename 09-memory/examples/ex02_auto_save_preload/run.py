"""Hands-off memory: auto-save via callback + preload_memory (auto-inject).

    python run.py

- `after_agent_callback` calls `callback_context.add_session_to_memory()` after every
  turn -> the conversation is continuously archived.
- `preload_memory` runs BEFORE the model each turn, searches memory with the user's
  message, and injects the hits into the prompt -> no explicit tool call needed.

Two separate sessions; the second one already "knows" the first.
"""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.memory import InMemoryMemoryService  
from google.adk.runners import Runner  
from google.adk.sessions import InMemorySessionService  
from google.adk.tools import preload_memory  
from google.genai import types  

APP, USER, MODEL = "auto_memory", "u1", "gemini-2.5-flash"


async def auto_save(callback_context) -> None:
    await callback_context.add_session_to_memory()


agent = Agent(
    name="assistant",
    model=MODEL,
    instruction="You are a helpful personal assistant. Use anything you remember about the user.",
    tools=[preload_memory],
    after_agent_callback=auto_save,
)

session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()
runner = Runner(agent=agent, app_name=APP, session_service=session_service,
                memory_service=memory_service)


async def turn(session_id: str, text: str) -> None:
    print(f"user> {text}")
    async for ev in runner.run_async(
        user_id=USER, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=text)]),
    ):
        if ev.is_final_response() and ev.content:
            print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())


async def main() -> None:
    print("--- Session 1 ---")
    s1 = await session_service.create_session(app_name=APP, user_id=USER)
    await turn(s1.id, "I take my coffee black, no sugar. And I have a dog named Biscuit.")

    print("\n--- Session 2 (new session, no manual memory calls) ---")
    s2 = await session_service.create_session(app_name=APP, user_id=USER)
    await turn(s2.id, "How do I take my coffee, and what's my dog's name?")


if __name__ == "__main__":
    asyncio.run(main())
