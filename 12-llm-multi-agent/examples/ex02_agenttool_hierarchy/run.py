"""Hierarchical decomposition with AgentTool: writer -> research -> (facts, summarize).

    python run.py

Each level calls the level below as a *tool* and gets a result back — control
always returns to the caller (unlike sub_agent transfer).
"""

from __future__ import annotations

import asyncio
import os
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import LlmAgent  
from google.adk.runners import InMemoryRunner  
from google.adk.tools import agent_tool  
from google.genai import types  

M = os.environ["MODEL"]

# a stand-in for a real search tool (would be google_search in production)
_FACTS = {
    "great barrier reef": [
        "It stretches ~2,300 km along Australia's northeast coast.",
        "It is the world's largest coral reef system, visible from space.",
        "Roughly half its shallow-water coral was lost between 1995 and 2017.",
    ],
}


def fact_lookup(topic: str) -> dict:
    """Return a few known facts about a topic."""
    return {"facts": _FACTS.get(topic.strip().lower(), [])}


facts_agent = LlmAgent(
    name="facts_agent", model=M,
    description="Retrieves raw facts about a topic.",
    instruction="Call fact_lookup and return the raw facts as a bullet list.",
    tools=[fact_lookup],
)
summarizer = LlmAgent(
    name="summarizer", model=M,
    description="Condenses text into 1-2 sentences.",
    instruction="Summarize the provided text in at most 2 sentences.",
)

research = LlmAgent(
    name="research", model=M,
    description="Researches a topic: gathers facts then summarizes them into a brief.",
    instruction="Use `facts_agent` to gather facts about the topic, then `summarizer` "
                "to turn them into a 2-sentence brief. Return the brief.",
    tools=[agent_tool.AgentTool(agent=facts_agent),
           agent_tool.AgentTool(agent=summarizer)],
)

writer = LlmAgent(
    name="writer", model=M,
    instruction="Write a 3-sentence encyclopedia-style paragraph on the user's topic. "
                "First call `research` to get a factual brief, then expand it.",
    tools=[agent_tool.AgentTool(agent=research)],
)


async def main() -> None:
    runner = InMemoryRunner(agent=writer, app_name="hierarchy")
    s = await runner.session_service.create_session(app_name="hierarchy", user_id="u1")
    print("user> Write about the Great Barrier Reef.\n")
    async for ev in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text="Write about the Great Barrier Reef.")]),
    ):
        for c in ev.get_function_calls():
            print(f"  [{ev.author}] calls {c.name}")
        if ev.is_final_response() and ev.author != "user" and ev.content:
            t = "".join(p.text or "" for p in ev.content.parts).strip()
            if t:
                print(f"\n[{ev.author}]>\n{t}")


if __name__ == "__main__":
    asyncio.run(main())
