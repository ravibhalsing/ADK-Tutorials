"""Workflow graph — deterministic code and an LLM node interleaved.

    python run.py

Graph:  START -> normalize (fn) -> extract_amount (LLM) -> apply_policy (fn) -> END
Only ONE node is an LLM call; the rest is plain, predictable Python.
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import re
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk import Event, Workflow  
from google.adk.agents import LlmAgent  
from google.adk.runners import InMemoryRunner  
from google.genai import types  

M = os.environ["MODEL"]


def normalize(node_input) -> Event:
    """Pull the user's text out of the incoming Content and lowercase it."""
    text = node_input
    if hasattr(node_input, "parts"):
        text = " ".join(p.text or "" for p in node_input.parts)
    return Event(output=str(text).strip())


# the only AI node: turn free text into just a number
extract_amount = LlmAgent(
    name="extract_amount", model=M,
    instruction="The input is an expense description. Output ONLY the dollar amount as a "
                "bare number (e.g. 249.99). If none, output 0.",
)


def apply_policy(node_input) -> Event:
    """Deterministic policy: >500 needs approval; >0 is a valid claim."""
    m = re.search(r"[-+]?\d*\.?\d+", str(node_input))
    amount = float(m.group()) if m else 0.0
    if amount <= 0:
        decision = "REJECTED: no amount found"
    elif amount > 500:
        decision = f"NEEDS APPROVAL: ${amount:.2f} exceeds the $500 auto-approve limit"
    else:
        decision = f"AUTO-APPROVED: ${amount:.2f}"
    return Event(output=decision)


workflow = Workflow(
    name="expense_flow",
    edges=[("START", normalize, extract_amount, apply_policy)],
)


async def run_once(msg: str) -> None:
    runner = InMemoryRunner(agent=workflow, app_name="expense")
    s = await runner.session_service.create_session(app_name="expense", user_id="u1")
    print(f"\nuser> {msg}")
    async for ev in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=msg)]),
    ):
        ni = getattr(ev, "node_info", None) or getattr(ev, "nodeInfo", None)
        out = getattr(ev, "output", None)
        if out is not None:
            node = ni.path.split("/")[-1] if ni and ni.path else "?"
            print(f"  [{node}] -> {out!r}")


async def main() -> None:
    await run_once("Taxi from the airport, $37.50")
    await run_once("New standing desk and chair, 749 dollars total")
    await run_once("Lunch with the team")


if __name__ == "__main__":
    asyncio.run(main())
