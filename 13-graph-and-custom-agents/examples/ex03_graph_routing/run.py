"""Workflow graph — conditional routing (a triage switchboard).

    python run.py

Graph:
    START -> classify (LLM) -> router (fn, emits a route) -> { BUG | BILLING | OTHER }
The router emits Event(actions=EventActions(route=...)); the dict edge picks the branch.
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk import Event, Workflow  
from google.adk.agents import LlmAgent  
from google.adk.events import EventActions  
from google.adk.runners import InMemoryRunner  
from google.genai import types  

M = os.environ["MODEL"]

classify = LlmAgent(
    name="classify", model=M,
    instruction="Classify the user's message as exactly one word: BUG, BILLING, or OTHER.",
)


def router(node_input) -> Event:
    """Turn the classifier's word into a graph route."""
    label = str(node_input).strip().upper()
    route = label if label in {"BUG", "BILLING"} else "OTHER"
    return Event(output=route, actions=EventActions(route=route))


def bug_handler(node_input) -> Event:
    return Event(output="Filed a bug ticket. Engineering will investigate; you'll get an update in 2 business days.")


def billing_handler(node_input) -> Event:
    return Event(output="Routed to billing. They'll review your account and reply within 24 hours.")


def other_handler(node_input) -> Event:
    return Event(output="Thanks for reaching out — a support generalist will follow up shortly.")


workflow = Workflow(
    name="triage",
    edges=[
        ("START", classify, router),
        (router, {"BUG": bug_handler, "BILLING": billing_handler, "OTHER": other_handler}),
    ],
)


async def run_once(msg: str) -> None:
    runner = InMemoryRunner(agent=workflow, app_name="triage")
    s = await runner.session_service.create_session(app_name="triage", user_id="u1")
    print(f"\nuser> {msg}")
    async for ev in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=msg)]),
    ):
        out = getattr(ev, "output", None)
        if out is not None:
            print(f"  -> {out!r}")


async def main() -> None:
    await run_once("The export button throws a 500 error every time.")
    await run_once("You charged my card twice this month.")
    await run_once("Do you have a mobile app?")


if __name__ == "__main__":
    asyncio.run(main())
