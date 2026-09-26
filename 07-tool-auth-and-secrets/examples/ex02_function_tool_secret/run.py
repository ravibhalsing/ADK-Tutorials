"""python run.py — shows secret resolution + per-user override.

Run once with no CHAT_BOT_TOKEN in .env (auth error), then the user 'connects'
their own token and the post succeeds — without any shared secret.
"""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.runners import InMemoryRunner  
from google.genai import types  

from agent import root_agent  

APP = "chat"


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")
    for q in [
        "Post 'Deploy done ✅' to #eng.",
        "My chat token is xoxb-demo-7788. Save it and try again.",
    ]:
        print(f"\nuser> {q}")
        async for ev in runner.run_async(
            user_id="u1", session_id=s.id,
            new_message=types.Content(role="user", parts=[types.Part(text=q)]),
        ):
            for c in ev.get_function_calls():
                args = {k: ("***" if "token" in k else v) for k, v in c.args.items()}
                print(f"  [call] {c.name}({args})")
            for r in ev.get_function_responses():
                print(f"  [resp] {r.response}")
            if ev.is_final_response() and ev.content:
                print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())

    stored = await runner.session_service.get_session(app_name=APP, user_id="u1", session_id=s.id)
    print("\nstate keys:", list(stored.state.keys()), "(token is user-scoped)")


if __name__ == "__main__":
    asyncio.run(main())
