"""disallow_transfer_to_parent / disallow_transfer_to_peers.

    python run.py            # specialists CAN bounce around
    python run.py --locked   # specialists must finish or escalate

Scenario: user asks triage a question that tempts the first specialist to hand
off to a peer.
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import sys

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import LlmAgent  
from google.adk.runners import InMemoryRunner  
from google.genai import types  

M = os.environ["MODEL"]
LOCKED = "--locked" in sys.argv


def specialist(name: str, topic: str, other: str) -> LlmAgent:
    return LlmAgent(
        name=name, model=M,
        description=f"Handles {topic} questions.",
        instruction=(
            f"You handle {topic}. Answer the {topic} part of the user's question in one "
            f"sentence. If the question also has a {other} part, "
            + ("do NOT transfer; just note that a colleague will follow up on it."
               if LOCKED else f"transfer to the `{other}_expert` for that part.")
        ),
        disallow_transfer_to_parent=LOCKED,
        disallow_transfer_to_peers=LOCKED,
    )


billing_expert = specialist("billing_expert", "billing", "shipping")
shipping_expert = specialist("shipping_expert", "shipping", "billing")

coordinator = LlmAgent(
    name="coordinator", model=M,
    instruction="Route the user to `billing_expert` or `shipping_expert` based on the "
                "first topic mentioned.",
    sub_agents=[billing_expert, shipping_expert],
)


async def main() -> None:
    print(f"mode: {'LOCKED (no peer/parent transfer)' if LOCKED else 'open transfers'}\n")
    runner = InMemoryRunner(agent=coordinator, app_name="scoping")
    s = await runner.session_service.create_session(app_name="scoping", user_id="u1")
    q = "I was double-charged $20, and also my package hasn't shipped after a week."
    print(f"user> {q}")
    async for ev in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=q)]),
    ):
        if ev.actions and ev.actions.transfer_to_agent:
            print(f"  --> transfer_to_agent: {ev.actions.transfer_to_agent}  (by {ev.author})")
        if ev.is_final_response() and ev.author != "user" and ev.content:
            t = "".join(p.text or "" for p in ev.content.parts).strip()
            if t:
                print(f"[{ev.author}]> {t}")


if __name__ == "__main__":
    asyncio.run(main())
