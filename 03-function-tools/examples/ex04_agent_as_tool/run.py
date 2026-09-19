"""AgentTool vs sub_agents — same specialist, two integration styles.

    python run.py            # AgentTool: specialist returns control to the root
    python run.py --subagent # sub_agent: specialist takes over the turn

Watch `event.author` to see WHO is answering the user.
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import sys

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.runners import InMemoryRunner  
from google.adk.tools import AgentTool  
from google.genai import types  

MODEL = os.environ["MODEL"]
APP = "agent_as_tool"

poet = Agent(
    name="poet",
    model=MODEL,
    description="Writes a short 4-line poem about a given topic.",
    instruction="Write exactly 4 lines of verse about the user's topic. Output only the poem.",
)


def build_root(use_subagent: bool) -> Agent:
    if use_subagent:
        return Agent(
            name="concierge",
            model=MODEL,
            instruction=(
                "You are a concierge. For normal questions, answer directly. "
                "If the user wants a poem, transfer to the `poet` agent."
            ),
            sub_agents=[poet],
        )
    return Agent(
        name="concierge",
        model=MODEL,
        instruction=(
            "You are a concierge. For normal questions, answer directly. "
            "If the user wants a poem, call the `poet` tool, then present the poem to "
            "the user with a one-line intro."
        ),
        tools=[AgentTool(agent=poet)],
    )


async def main() -> None:
    use_sub = "--subagent" in sys.argv
    root = build_root(use_sub)
    print(f"mode: {'sub_agent (transfer)' if use_sub else 'AgentTool (call)'}\n")

    runner = InMemoryRunner(agent=root, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")

    async for ev in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(
            role="user", parts=[types.Part(text="Write me a poem about the monsoon.")]
        ),
    ):
        for c in ev.get_function_calls():
            print(f"  [{ev.author}] call {c.name}({dict(c.args)})")
        if ev.actions and ev.actions.transfer_to_agent:
            print(f"  [{ev.author}] --> transfer_to_agent: {ev.actions.transfer_to_agent}")
        if ev.is_final_response() and ev.content:
            t = "".join(p.text or "" for p in ev.content.parts).strip()
            if t:
                print(f"\n[final answer authored by: {ev.author}]\n{t}")


if __name__ == "__main__":
    asyncio.run(main())
