"""The canonical memory flow: capture in one session, recall in another.

    python run.py

Turn 1 (session A): user states a fact; agent acknowledges.
    -> add_session_to_memory(session A)
Turn 2 (session B, fresh): user asks about it; agent calls `load_memory`.
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
from google.adk.tools import load_memory  
from google.genai import types  

APP, USER, MODEL = "memory_demo", "u1", "gemini-2.5-flash"

capture_agent = Agent(
    name="capture", model=MODEL,
    instruction="Briefly acknowledge what the user tells you. One sentence.",
)
recall_agent = Agent(
    name="recall", model=MODEL,
    instruction=(
        "Answer the user's question. If the answer might be in a past conversation, "
        "call `load_memory` with a search query first, then answer from what it returns."
    ),
    tools=[load_memory],
)


async def ask(agent, session_service, memory_service, session_id, text):
    runner = Runner(agent=agent, app_name=APP, session_service=session_service,
                    memory_service=memory_service)
    out = ""
    async for ev in runner.run_async(
        user_id=USER, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=text)]),
    ):
        for c in ev.get_function_calls():
            print(f"  [tool] {c.name}({dict(c.args)})")
        if ev.is_final_response() and ev.content:
            out = "".join(p.text or "" for p in ev.content.parts).strip()
    return out


async def main() -> None:
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

    print("--- Turn 1 (session A): capture ---")
    a = await session_service.create_session(app_name=APP, user_id=USER)
    print("user> I'm allergic to shellfish and my project deadline is March 14.")
    print("agent>", await ask(capture_agent, session_service, memory_service, a.id,
                              "I'm allergic to shellfish and my project deadline is March 14."))

    completed = await session_service.get_session(app_name=APP, user_id=USER, session_id=a.id)
    await memory_service.add_session_to_memory(completed)
    print("\n(session A saved to memory)\n")

    print("--- Turn 2 (session B, brand new): recall ---")
    b = await session_service.create_session(app_name=APP, user_id=USER)
    print("user> When is my deadline, and is there anything I can't eat?")
    print("agent>", await ask(recall_agent, session_service, memory_service, b.id,
                              "When is my deadline, and is there anything I can't eat?"))


if __name__ == "__main__":
    asyncio.run(main())
