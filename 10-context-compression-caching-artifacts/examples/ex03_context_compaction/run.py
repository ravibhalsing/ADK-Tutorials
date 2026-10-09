"""Context compaction — summarize old history to keep the window (and cost) small.

    python run.py

Configured on the App via EventsCompactionConfig (sliding window here). After
`compaction_interval` events, older turns are summarized. We run a multi-turn
chat and then inspect the stored events for the compaction summary.
"""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.apps.app import App, EventsCompactionConfig  
from google.adk.runners import Runner  
from google.adk.sessions import InMemorySessionService  
from google.genai import types  

APP, USER, MODEL = "compaction_demo", "u1", "gemini-2.5-flash"

agent = Agent(
    name="chatbot", model=MODEL,
    instruction="You are a concise assistant. Answer in one short sentence.",
)

app = App(
    name=APP,
    root_agent=agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,   # summarize after every 3 completed events
        overlap_size=1,          # keep 1 already-summarized event for continuity
    ),
)


async def main() -> None:
    session_service = InMemorySessionService()
    runner = Runner(app=app, session_service=session_service)
    s = await session_service.create_session(app_name=APP, user_id=USER)

    turns = [
        "My name is Priya and I'm planning a trip to Kyoto.",
        "I'll be there for 5 days in April.",
        "I'm mostly interested in temples and gardens.",
        "I don't eat meat.",
        "What's my name and how long is my trip?",     # needs early context
        "Suggest one thing to do that fits my interests and diet.",
    ]
    for t in turns:
        print(f"\nuser> {t}")
        async for ev in runner.run_async(
            user_id=USER, session_id=s.id,
            new_message=types.Content(role="user", parts=[types.Part(text=t)]),
        ):
            if ev.is_final_response() and ev.content:
                print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())

    final = await session_service.get_session(app_name=APP, user_id=USER, session_id=s.id)
    print(f"\n--- stored session: {len(final.events)} events ---")
    for i, ev in enumerate(final.events, 1):
        comp = getattr(ev.actions, "compaction", None) if ev.actions else None
        tag = "  <-- COMPACTION SUMMARY" if comp else ""
        txt = ""
        if ev.content and ev.content.parts:
            txt = (ev.content.parts[0].text or "")[:60].replace("\n", " ")
        print(f"  #{i:2} {ev.author:<8} {txt!r}{tag}")
        if comp:
            print(f"       {comp}")


if __name__ == "__main__":
    asyncio.run(main())
