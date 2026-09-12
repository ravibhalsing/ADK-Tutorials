"""generate_content_config — temperature, max_output_tokens, stop_sequences.

    python run.py

Shows:
  1. temperature 0.0 vs 1.0 — run the same creative prompt 4x each, compare variety
  2. max_output_tokens — a hard cap truncates the answer
  3. stop_sequences — generation halts at a literal
"""

from __future__ import annotations

import asyncio
import os
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.runners import Runner  
from google.adk.sessions import InMemorySessionService  
from google.genai import types  

MODEL = os.environ["MODEL"]
APP = "gen_config"


def make_agent(name: str, cfg: types.GenerateContentConfig, instruction: str) -> Agent:
    return Agent(name=name, model=MODEL, instruction=instruction, generate_content_config=cfg)


async def ask(agent: Agent, prompt: str) -> str:
    svc = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP, session_service=svc)
    s = await svc.create_session(app_name=APP, user_id="u1")
    out = ""
    async for ev in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
    ):
        if ev.is_final_response() and ev.content and ev.content.parts:
            out = "".join(p.text or "" for p in ev.content.parts).strip()
    return out


async def main() -> None:
    creative = "Invent a name for a coffee shop on Mars. Reply with ONLY the name."

    print("=== 1. temperature 0.0 (x4) — expect near-identical ===")
    cold = make_agent("cold", types.GenerateContentConfig(temperature=0.0), "You are creative.")
    for i in range(4):
        print(f"  {i+1}: {await ask(cold, creative)}")

    print("\n=== 1. temperature 1.0 (x4) — expect variety ===")
    hot = make_agent("hot", types.GenerateContentConfig(temperature=1.0), "You are creative.")
    for i in range(4):
        print(f"  {i+1}: {await ask(hot, creative)}")

    print("\n=== 2. max_output_tokens=40 — answer gets truncated mid-sentence ===")
    # NOTE: on Gemini 2.5 'thinking' models, max_output_tokens must ALSO cover thinking
    # tokens. Too small a cap => the whole budget is spent thinking => empty text.
    # So we disable thinking here to get a clean truncation demo.
    capped = make_agent(
        "capped",
        types.GenerateContentConfig(
            max_output_tokens=40,
            temperature=0.2,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
        "You are a helpful encyclopedia.",
    )
    print(" ", await ask(capped, "Explain how a nuclear reactor works.") or "(empty!)")

    print("\n=== 3. stop_sequences=['5'] — generation halts when it would emit '5' ===")
    stopper = make_agent(
        "stopper",
        types.GenerateContentConfig(
            stop_sequences=["5"],
            temperature=0.0,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
        "Follow the instruction exactly.",
    )
    print(repr(await ask(stopper, "Count from 1 to 10, one number per line.")))


if __name__ == "__main__":
    asyncio.run(main())
