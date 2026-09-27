"""State scopes: (none) / user: / app: / temp: across two users and two sessions.

    python run.py

No LLM calls — pure SessionService + append_event, so it's fast and quota-free.
"""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.events import Event, EventActions  
from google.adk.sessions import DatabaseSessionService  

DB = f"sqlite+aiosqlite:///{pathlib.Path(__file__).parent / 'ex02.db'}"
APP = "scopes_demo"


async def set_state(svc, app, user, sid, delta):
    s = await svc.get_session(app_name=app, user_id=user, session_id=sid)
    await svc.append_event(s, Event(author="system", actions=EventActions(state_delta=delta)))


async def show(svc, app, user, sid, label):
    s = await svc.get_session(app_name=app, user_id=user, session_id=sid)
    print(f"  {label}: {dict(sorted(s.state.items()))}")


async def main() -> None:
    svc = DatabaseSessionService(db_url=DB)

    # alice: session A1 and A2 ; bob: session B1
    a1 = await svc.create_session(app_name=APP, user_id="alice")
    a2 = await svc.create_session(app_name=APP, user_id="alice")
    b1 = await svc.create_session(app_name=APP, user_id="bob")

    # write different scopes from alice's session A1
    await set_state(svc, APP, "alice", a1.id, {
        "step": "A1-only",                 # session scope
        "user:theme": "dark",              # all of alice's sessions
        "app:banner": "Welcome!",          # every user
        "temp:scratch": "gone soon",       # this invocation only (append_event = its own invocation)
    })

    print("alice A1 (where we wrote):")
    await show(svc, APP, "alice", a1.id, "A1")
    print("\nalice A2 (same user, different session):")
    await show(svc, APP, "alice", a2.id, "A2")   # sees user: + app:, NOT step, NOT temp:
    print("\nbob B1 (different user):")
    await show(svc, APP, "bob", b1.id, "B1")     # sees app: only

    print("\n--- observations ---")
    print("  'step' (session)   -> only in A1")
    print("  'user:theme'       -> in A1 and A2 (alice), not B1 (bob)")
    print("  'app:banner'       -> in all three")
    print("  'temp:scratch'     -> in none (discarded after its invocation)")

    print(f"\n(db: {pathlib.Path(DB.split('///')[1]).name})")


if __name__ == "__main__":
    asyncio.run(main())
