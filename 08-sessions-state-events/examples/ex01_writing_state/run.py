"""The three correct ways to write state, and the one wrong way.

    python run.py

Uses one model turn (an agent with output_key + a state-writing tool), then an
out-of-band append_event, then demonstrates why direct mutation fails.
"""

from __future__ import annotations

import asyncio
import pathlib
import time

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.events import Event, EventActions  
from google.adk.runners import Runner  
from google.adk.sessions import DatabaseSessionService  
from google.adk.tools import ToolContext  
from google.genai import types  

DB = f"sqlite+aiosqlite:///{pathlib.Path(__file__).parent / 'ex01.db'}"
APP, USER = "writing_state", "u1"


def note_topic(topic: str, tool_context: ToolContext) -> dict:
    """Record the topic the user wants to discuss."""
    tool_context.state["current_topic"] = topic          # method b: context.state
    tool_context.state["temp:noted_at"] = time.time()
    return {"status": "success", "topic": topic}


agent = Agent(
    name="notetaker",
    model="gemini-2.5-flash",
    instruction="When the user names a topic, call note_topic. Then reply in one sentence.",
    tools=[note_topic],
    output_key="last_reply",                              # method a: output_key
)


async def main() -> None:
    svc = DatabaseSessionService(db_url=DB)
    runner = Runner(agent=agent, app_name=APP, session_service=svc)
    session = await svc.create_session(app_name=APP, user_id=USER, state={"turn": 0})

    # --- methods a + b via one agent turn ---
    async for _ in runner.run_async(
        user_id=USER, session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text="Let's talk about black holes.")]),
    ):
        pass

    s = await svc.get_session(app_name=APP, user_id=USER, session_id=session.id)
    print("after agent turn:")
    print("  state['current_topic'] =", s.state.get("current_topic"), "   (method b: tool context.state)")
    print("  state['last_reply']    =", (s.state.get("last_reply") or "")[:60], "...   (method a: output_key)")
    print("  'temp:noted_at' present?", "temp:noted_at" in s.state, "  (temp: dropped after the invocation)")

    # --- method c: EventActions.state_delta + append_event (out of band) ---
    evt = Event(author="system", actions=EventActions(state_delta={
        "turn": s.state.get("turn", 0) + 1,
        "user:visit_count": s.state.get("user:visit_count", 0) + 1,
    }))
    await svc.append_event(s, evt)
    s = await svc.get_session(app_name=APP, user_id=USER, session_id=session.id)
    print("\nafter append_event (method c):")
    print("  state['turn'] =", s.state.get("turn"), "  state['user:visit_count'] =", s.state.get("user:visit_count"))

    # --- the WRONG way ---
    s.state["hacked"] = "nope"        # mutate the fetched object directly
    s2 = await svc.get_session(app_name=APP, user_id=USER, session_id=session.id)
    print("\nwrong way (direct mutation of get_session().state):")
    print("  'hacked' in a freshly fetched session?", "hacked" in s2.state, "  <- change did NOT persist")

    print(f"\n(db: {pathlib.Path(DB.split('///')[1]).name} — delete it to reset)")


if __name__ == "__main__":
    asyncio.run(main())
