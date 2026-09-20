"""Show the executable-code and code-result parts in the event stream.

    python run.py
"""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.runners import InMemoryRunner  
from google.genai import types  

from agent import root_agent  

APP = "calc_demo"
Q = (
    "A dataset has values 4, 8, 15, 16, 23, 42. "
    "Give me the mean, population standard deviation, and the compound growth rate "
    "from the first to the last value assuming 5 equal periods."
)


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")
    print(f"user> {Q}\n")

    async for ev in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=Q)]),
    ):
        for p in (ev.content.parts if ev.content and ev.content.parts else []):
            if getattr(p, "executable_code", None):
                print("  [code]\n" + "\n".join("    " + ln for ln in p.executable_code.code.splitlines()))
            if getattr(p, "code_execution_result", None):
                r = p.code_execution_result
                print(f"  [result] outcome={r.outcome} output={r.output!r}")
        if ev.is_final_response() and ev.content:
            print("\nagent>", "".join(p.text or "" for p in ev.content.parts).strip())


if __name__ == "__main__":
    asyncio.run(main())
