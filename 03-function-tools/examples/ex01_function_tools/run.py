"""Drive ex01, and (with --schema) print the JSON schema ADK builds for each tool.

    python run.py
    python run.py --schema
"""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.runners import InMemoryRunner  
from google.adk.tools import FunctionTool  
from google.genai import types  

from agent import estimate_shipping, lookup_product, root_agent  

APP = "store"


def dump_schemas() -> None:
    for fn in (lookup_product, estimate_shipping):
        decl = FunctionTool(fn)._get_declaration()
        print(f"\n# {fn.__name__}")
        print(json.dumps(decl.model_dump(exclude_none=True), indent=2, default=str))


async def chat() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")
    for turn in [
        "How much is the USB-C hub and is it in stock?",
        "What's express shipping for 3 laptop stands to Germany?",
        "Price of SKU-9?",
    ]:
        print(f"\nuser> {turn}")
        async for ev in runner.run_async(
            user_id="u1", session_id=s.id,
            new_message=types.Content(role="user", parts=[types.Part(text=turn)]),
        ):
            for c in ev.get_function_calls():
                print(f"  [call] {c.name}({dict(c.args)})")
            for r in ev.get_function_responses():
                print(f"  [resp] {r.response}")
            if ev.is_final_response() and ev.content:
                print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())


if __name__ == "__main__":
    if "--schema" in sys.argv:
        dump_schemas()
    else:
        asyncio.run(chat())
