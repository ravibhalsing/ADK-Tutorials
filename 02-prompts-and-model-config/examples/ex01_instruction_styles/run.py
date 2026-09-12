"""Three instruction styles, one question — see how behaviour changes.

    python run.py

Agents:
  static   — fixed string
  templated — "{persona}" / "{topic?}" filled from session state
  provider — a callable that branches on state["level"]
"""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

import os  

from google.adk.agents import Agent  
from google.adk.agents.readonly_context import ReadonlyContext  
from google.adk.runners import Runner  
from google.adk.sessions import InMemorySessionService  
from google.genai import types  

MODEL = os.environ["MODEL"]
QUESTION = "Why is the sky blue?"

static_agent = Agent(
    name="static",
    model=MODEL,
    instruction="You are a terse physics teacher. Answer in exactly one sentence.",
)

templated_agent = Agent(
    name="templated",
    model=MODEL,
    # {persona} is required; {topic?} is optional (omitted if absent from state)
    instruction=(
        "You are {persona}. Answer the user's question. "
        "If relevant, connect it to {topic?}. Keep it under 40 words."
    ),
)


def instruction_provider(ctx: ReadonlyContext) -> str:
    level = ctx.state.get("level", "adult")
    if level == "child":
        return "Explain to a 6-year-old using a simple analogy. Two sentences max."
    if level == "expert":
        return (
            "Answer at a graduate physics level in 3 sentences max. "
            "Use the term 'Rayleigh scattering'."
        )
    return "Explain clearly for a curious adult in 2-3 sentences."


provider_agent = Agent(
    name="provider",
    model=MODEL,
    instruction=instruction_provider,
)

APP = "instruction_styles"


async def ask(agent: Agent, state: dict) -> str:
    svc = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP, session_service=svc)
    session = await svc.create_session(app_name=APP, user_id="u1", state=state)
    out = ""
    async for ev in runner.run_async(
        user_id="u1",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=QUESTION)]),
    ):
        if ev.is_final_response() and ev.content and ev.content.parts:
            out = "".join(p.text or "" for p in ev.content.parts).strip()
    return out


async def main() -> None:
    print(f"Q: {QUESTION}\n")

    print("static (no state):")
    print(" ", await ask(static_agent, {}))

    print("\ntemplated (persona + topic in state):")
    print(" ", await ask(templated_agent, {
        "persona": "a poetic science writer",
        "topic": "the colour of sunsets",
    }))

    print("\ntemplated (persona only, topic absent -> {topic?} omitted):")
    print(" ", await ask(templated_agent, {"persona": "a blunt engineer"}))

    print("\nprovider (state.level = child):")
    print(" ", await ask(provider_agent, {"level": "child"}))

    print("\nprovider (state.level = expert):")
    print(" ", await ask(provider_agent, {"level": "expert"}))


if __name__ == "__main__":
    asyncio.run(main())
