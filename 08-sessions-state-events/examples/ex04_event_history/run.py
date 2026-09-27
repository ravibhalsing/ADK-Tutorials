"""Dump the full Event history of a stored session.

    # first create some history:
    python ../ex03_database_persistence/run.py     (run it once or twice)
    # then:
    python run.py

No LLM calls — it just reads the SQLite DB from ex03.
"""

from __future__ import annotations

import asyncio
import pathlib

from google.adk.sessions import DatabaseSessionService

EX03_DB = pathlib.Path(__file__).parent.parent / "ex03_database_persistence" / "ex03.db"
DB = f"sqlite+aiosqlite:///{EX03_DB}"
APP, USER = "persist_demo", "learner"


def kinds(event) -> list[str]:
    out = []
    for p in (event.content.parts if event.content and event.content.parts else []):
        if getattr(p, "text", None):
            out.append(f"text[{len(p.text)}]")
        if getattr(p, "function_call", None):
            out.append(f"call:{p.function_call.name}")
        if getattr(p, "function_response", None):
            out.append(f"resp:{p.function_response.name}")
    return out or ["(no content)"]


async def main() -> None:
    if not EX03_DB.exists():
        print(f"No history yet. Run  ../ex03_database_persistence/run.py  first.")
        return

    svc = DatabaseSessionService(db_url=DB)
    r = await svc.list_sessions(app_name=APP, user_id=USER)
    if not r.sessions:
        print("No sessions in the DB.")
        return

    s = await svc.get_session(app_name=APP, user_id=USER, session_id=r.sessions[0].id)
    print(f"session {s.id}")
    print(f"  app={s.app_name} user={s.user_id} last_update={s.last_update_time}")
    print(f"  final state = {dict(s.state)}")
    print(f"  {len(s.events)} events:\n")

    for i, ev in enumerate(s.events, 1):
        delta = dict(ev.actions.state_delta) if (ev.actions and ev.actions.state_delta) else {}
        u = ev.usage_metadata
        usage = f" tok={u.total_token_count}" if u else ""
        print(f"  #{i:2}  author={ev.author:<10} {', '.join(kinds(ev)):<22}"
              f" final={ev.is_final_response()!s:<5}{usage}")
        if delta:
            print(f"       state_delta = {delta}")


if __name__ == "__main__":
    asyncio.run(main())
