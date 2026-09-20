"""Built-in tools can't share an agent — wrap them as AgentTools instead.

    python run.py            # coder-only route (reliable): AgentTool composition works
    python run.py --search   # adds the google_search route (needs grounding quota)
    python run.py --break    # google_search + a function tool in ONE agent -> 400

Vertex error when you break the rule:
    400 INVALID_ARGUMENT ... Multiple tools are supported only when they are all
    search tools.

Note: on a fresh GCP project the Google Search grounding quota is tiny; the
--search route may return 429 (_ResourceExhaustedError). The --break 400 and the
coder route both work regardless.
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import sys

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.code_executors import BuiltInCodeExecutor  
from google.adk.runners import InMemoryRunner  
from google.adk.tools import AgentTool, google_search  
from google.genai import types  

MODEL = os.environ["MODEL"]
APP = "combine"

# Each built-in tool lives ALONE in its own specialist agent...
searcher = Agent(
    name="searcher", model=MODEL,
    description="Finds current facts on the web.",
    instruction="Use google_search to answer the query. Return the facts plainly.",
    tools=[google_search],
)
coder = Agent(
    name="coder", model=MODEL,
    description="Does exact calculations by running Python.",
    instruction="Write and run Python to compute the answer. Return just the result.",
    code_executor=BuiltInCodeExecutor(),
)

# ...and the root uses them as tools (AgentTool), so it can combine both.
root = Agent(
    name="analyst", model=MODEL,
    instruction=(
        "You answer questions that may need both a web lookup and a calculation.\n"
        "- Call `searcher` for facts you don't reliably know.\n"
        "- Call `coder` for any arithmetic.\n"
        "- Combine the results into one clear answer."
    ),
    tools=[AgentTool(agent=searcher), AgentTool(agent=coder)],
)


def broken_agent() -> Agent:
    def word_len(word: str) -> dict:
        """Return the length of a word."""
        return {"length": len(word)}

    return Agent(name="broken", model=MODEL, instruction="help",
                 tools=[google_search, word_len])


async def ask(agent: Agent, q: str) -> None:
    runner = InMemoryRunner(agent=agent, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")
    print(f"user> {q}")
    try:
        async for ev in runner.run_async(
            user_id="u1", session_id=s.id,
            new_message=types.Content(role="user", parts=[types.Part(text=q)]),
        ):
            for c in ev.get_function_calls():
                print(f"  [{ev.author}] call {c.name}")
            if ev.is_final_response() and ev.content:
                t = "".join(p.text or "" for p in ev.content.parts).strip()
                if t:
                    print("agent>", t)
    except Exception as e:  # noqa: BLE001
        print(f"  !! {type(e).__name__}: {str(e)[:200]}")


async def main() -> None:
    if "--break" in sys.argv:
        await ask(broken_agent(), "How long is the word 'python'?")
        return
    if "--search" in sys.argv:
        await ask(
            root,
            "Find the population of Canada, then tell me what it becomes after "
            "10 years of 1.2% annual growth.",
        )
        return
    # coder-only route — exercises AgentTool composition without touching search quota
    await ask(
        root,
        "Assume a population of 40,000,000. What is it after 10 years of 1.2% "
        "annual compound growth? Use the coder.",
    )


if __name__ == "__main__":
    asyncio.run(main())
