"""DatabaseSessionService — the conversation survives a process restart.

    python run.py            # run 1: introduce yourself
    python run.py            # run 2+: it remembers (state + history from SQLite)
    python run.py --list     # list stored sessions for the user
    python run.py --reset    # delete the stored session

One model turn per run.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.runners import Runner  
from google.adk.sessions import DatabaseSessionService  
from google.adk.tools import ToolContext  
from google.genai import types  

DB = f"sqlite+aiosqlite:///{pathlib.Path(__file__).parent / 'ex03.db'}"
APP, USER = "persist_demo", "learner"


def remember_name(name: str, tool_context: ToolContext) -> dict:
    """Save the user's name so future conversations can greet them."""
    tool_context.state["user:name"] = name
    return {"status": "success"}


agent = Agent(
    name="host",
    model="gemini-2.5-flash",
    instruction=(
        "The user's saved name is: {user:name?}\n"
        "- If a name is saved, greet them by it and mention this is a continued chat.\n"
        "- If not, ask their name; when they give it, call remember_name.\n"
        "Keep replies to one or two sentences."
    ),
    tools=[remember_name],
)


async def get_or_create(svc):
    existing = await svc.list_sessions(app_name=APP, user_id=USER)
    if existing.sessions:
        sid = existing.sessions[0].id
        print(f"(resuming session {sid[:8]}… from the database)")
        return await svc.get_session(app_name=APP, user_id=USER, session_id=sid)
    print("(no stored session — starting fresh)")
    return await svc.create_session(app_name=APP, user_id=USER)


async def main() -> None:
    svc = DatabaseSessionService(db_url=DB)

    if "--list" in sys.argv:
        r = await svc.list_sessions(app_name=APP, user_id=USER)
        for s in r.sessions:
            full = await svc.get_session(app_name=APP, user_id=USER, session_id=s.id)
            print(f"  {s.id}  events={len(full.events)}  state={dict(full.state)}")
        return

    if "--reset" in sys.argv:
        r = await svc.list_sessions(app_name=APP, user_id=USER)
        for s in r.sessions:
            await svc.delete_session(app_name=APP, user_id=USER, session_id=s.id)
        print(f"deleted {len(r.sessions)} session(s)")
        return

    session = await get_or_create(svc)
    runner = Runner(agent=agent, app_name=APP, session_service=svc)

    turn = "Hi!" if session.state.get("user:name") else "Hello, I'm Ravindra."
    print(f"\nuser> {turn}")
    async for ev in runner.run_async(
        user_id=USER, session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=turn)]),
    ):
        if ev.is_final_response() and ev.content:
            print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())

    final = await svc.get_session(app_name=APP, user_id=USER, session_id=session.id)
    print(f"\nstored: {len(final.events)} events, state={dict(final.state)}")


if __name__ == "__main__":
    asyncio.run(main())
