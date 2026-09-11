"""Build a Runner by hand; run a multi-turn conversation; prove session isolation.

Run from THIS folder:
    python run_multiturn.py

What it shows:
  * Runner + InMemorySessionService wired explicitly (the production shape)
  * one session, three turns — turn 3 depends on turns 1–2 (history works)
  * two sessions with different user_ids — state does NOT leak between them
"""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")  # before importing agent.py

from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from agent import root_agent  # noqa: E402

APP_NAME = "runner_basics"


def user_text(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text)])


async def say(runner: Runner, user_id: str, session_id: str, text: str) -> str:
    """Send one message; return the final answer text."""
    final = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=user_text(text)
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final = "".join(p.text or "" for p in event.content.parts).strip()
    print(f"  [{user_id}] you: {text}")
    print(f"  [{user_id}] bot: {final}")
    return final


async def main() -> None:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    print("=== One session, three turns (history must carry) ===")
    s = await session_service.create_session(app_name=APP_NAME, user_id="alice")
    await say(runner, "alice", s.id, "My favourite colour is teal. Remember that.")
    await say(runner, "alice", s.id, "How many words were in my previous message?")
    await say(runner, "alice", s.id, "What's my favourite colour?")

    print("\n=== Two sessions, no leakage ===")
    sa = await session_service.create_session(app_name=APP_NAME, user_id="bob")
    sb = await session_service.create_session(app_name=APP_NAME, user_id="carol")
    await say(runner, "bob", sa.id, "The secret word is 'volcano'. Keep it.")
    await say(runner, "carol", sb.id, "What is the secret word?")  # must NOT know it
    await say(runner, "bob", sa.id, "What is the secret word?")     # must know it

    print("\n=== Inspect stored session state / history ===")
    stored = await session_service.get_session(
        app_name=APP_NAME, user_id="alice", session_id=s.id
    )
    print(f"  alice session has {len(stored.events)} events, state={dict(stored.state)}")


if __name__ == "__main__":
    asyncio.run(main())
