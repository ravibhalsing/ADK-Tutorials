"""Custom memory tool: search conversation memory AND a separate 'docs' corpus.

    python run.py

- `tool_context.search_memory(query)` searches the Runner's memory_service
  (this user's past conversations).
- We also keep a second InMemoryMemoryService seeded with product docs, and
  search it directly for `app_name="docs"`.
"""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.events import Event  
from google.adk.memory import InMemoryMemoryService  
from google.adk.runners import Runner  
from google.adk.sessions import InMemorySessionService  
from google.adk.tools import ToolContext  
from google.genai import types  

APP, USER, MODEL = "kb_agent", "u1", "gemini-2.5-flash"

# --- a standalone 'docs' knowledge base -------------------------------------
docs_memory = InMemoryMemoryService()

DOCS = [
    "The Free plan allows 3 projects and 1 GB storage.",
    "The Pro plan is $12/user/month: unlimited projects, 100 GB storage, priority support.",
    "Data is retained for 30 days on Free and 365 days on Pro.",
    "SSO (SAML) is available on the Enterprise plan only.",
]


async def _seed_docs() -> None:
    # InMemoryMemoryService takes events, not direct memories. One event per doc snippet.
    events = [
        Event(author="docs", content=types.Content(role="model", parts=[types.Part(text=d)]))
        for d in DOCS
    ]
    await docs_memory.add_events_to_memory(app_name="docs", user_id="shared", events=events)


def _texts(resp) -> list[str]:
    return [p.text for e in resp.memories for p in (e.content.parts or []) if p.text]


async def knowledge_search(query: str, tool_context: ToolContext) -> dict:
    """Search product docs AND the user's past conversations for `query`."""
    convo = await tool_context.search_memory(query)
    docs = await docs_memory.search_memory(app_name="docs", user_id="shared", query=query)
    return {"from_docs": _texts(docs), "from_conversations": _texts(convo)}


agent = Agent(
    name="support",
    model=MODEL,
    instruction=(
        "Answer support questions. Call `knowledge_search` and answer ONLY from what it "
        "returns (docs + this user's history). If it's not there, say you don't know."
    ),
    tools=[knowledge_search],
)


async def main() -> None:
    await _seed_docs()
    ss = InMemorySessionService()
    ms = InMemoryMemoryService()
    runner = Runner(agent=agent, app_name=APP, session_service=ss, memory_service=ms)

    # seed a bit of "conversation history" for this user
    s0 = await ss.create_session(app_name=APP, user_id=USER)
    async for _ in runner.run_async(
        user_id=USER, session_id=s0.id,
        new_message=types.Content(role="user", parts=[types.Part(text="Note: we are on the Pro plan.")]),
    ):
        pass
    await ms.add_session_to_memory(await ss.get_session(app_name=APP, user_id=USER, session_id=s0.id))

    s1 = await ss.create_session(app_name=APP, user_id=USER)
    for q in [
        "How long is our data retained?",
        "Can we use SAML single sign-on?",
    ]:
        print(f"\nuser> {q}")
        async for ev in runner.run_async(
            user_id=USER, session_id=s1.id,
            new_message=types.Content(role="user", parts=[types.Part(text=q)]),
        ):
            for c in ev.get_function_calls():
                print(f"  [tool] {c.name}({dict(c.args)})")
            for r in ev.get_function_responses():
                print(f"  [result] {r.response}")
            if ev.is_final_response() and ev.content:
                print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())


if __name__ == "__main__":
    asyncio.run(main())
