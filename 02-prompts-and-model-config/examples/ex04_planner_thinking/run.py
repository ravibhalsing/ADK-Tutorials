"""Planners: BuiltInPlanner (native thinking) and PlanReActPlanner (text structure).

    python run.py            # BuiltInPlanner, include_thoughts=True — show thought parts
    python run.py --noplan   # same agent, no planner — compare
    python run.py --react    # PlanReActPlanner

We print each event and flag parts where part.thought is True.
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import sys

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.planners import BuiltInPlanner, PlanReActPlanner  
from google.adk.runners import InMemoryRunner  
from google.genai import types  

MODEL = os.environ["MODEL"]
APP = "planner_demo"

PROMPT = (
    "A train leaves city A at 14:00 going 60 km/h. Another leaves city B (300 km away) "
    "at 14:30 going 90 km/h toward A. At what clock time do they meet?"
)


def build_agent() -> Agent:
    if "--react" in sys.argv:
        return Agent(name="planner", model=MODEL, planner=PlanReActPlanner(),
                     instruction="Solve the problem. Show your work.")
    if "--noplan" in sys.argv:
        return Agent(name="planner", model=MODEL,
                     instruction="Solve the problem. Show your work.")
    return Agent(
        name="planner", model=MODEL,
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(include_thoughts=True, thinking_budget=1024)
        ),
        instruction="Solve the problem. Show your work.",
    )


async def main() -> None:
    agent = build_agent()
    mode = "--react" if "--react" in sys.argv else "--noplan" if "--noplan" in sys.argv else "BuiltInPlanner"
    print(f"mode: {mode}\nprompt: {PROMPT}\n")

    runner = InMemoryRunner(agent=agent, app_name=APP)
    session = await runner.session_service.create_session(app_name=APP, user_id="u1")

    n_thought_parts = 0
    async for ev in runner.run_async(
        user_id="u1", session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=PROMPT)]),
    ):
        for p in (ev.content.parts if ev.content and ev.content.parts else []):
            if getattr(p, "thought", None):
                n_thought_parts += 1
                text = (p.text or "").strip().replace("\n", " ")
                print(f"  [THOUGHT] {text[:160]}")
            elif p.text:
                tag = "final" if ev.is_final_response() else "text"
                print(f"  [{tag}] {p.text.strip()[:300]}")

    print(f"\nthought parts seen: {n_thought_parts}")
    if ev.usage_metadata:
        u = ev.usage_metadata
        print(f"last event tokens: prompt={u.prompt_token_count} "
              f"thoughts={getattr(u, 'thoughts_token_count', None)} "
              f"total={u.total_token_count}")


if __name__ == "__main__":
    asyncio.run(main())
