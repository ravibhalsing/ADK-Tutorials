"""LongRunningFunctionTool — a human-approval pause/resume cycle.

    python run.py            # approve the request
    python run.py --deny     # deny it

Flow:
  1. user asks for a $1200 reimbursement
  2. model calls ask_for_approval -> returns {"status": "pending", ...}
     (the event carries the call id in event.long_running_tool_ids)
  3. we STOP consuming events and simulate a manager decision
  4. we send a FunctionResponse with the SAME call id and the final decision
  5. the agent resumes and tells the user the outcome
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
from google.adk.tools import LongRunningFunctionTool  
from google.genai import types  

MODEL = os.environ["MODEL"]
APP = "approvals"


def ask_for_approval(purpose: str, amount: float) -> dict:
    """Request manager approval for a reimbursement.

    Args:
        purpose: What the money is for.
        amount: Amount in USD.

    Returns:
        dict: a PENDING ticket — the real decision arrives later, out of band.
    """
    return {
        "status": "pending",
        "ticket_id": "RB-4471",
        "approver": "Priya (manager)",
        "purpose": purpose,
        "amount": amount,
    }


agent = Agent(
    name="reimbursement_agent",
    model=MODEL,
    instruction=(
        "You process reimbursement requests.\n"
        "- Call `ask_for_approval` with the purpose and amount.\n"
        "- While it is pending, tell the user it's awaiting their manager.\n"
        "- When the approval result arrives, inform the user of the final decision "
        "clearly (approved or denied) and the ticket id."
    ),
    tools=[LongRunningFunctionTool(ask_for_approval)],
)


async def main() -> None:
    approve = "--deny" not in sys.argv
    runner = InMemoryRunner(agent=agent, app_name=APP)
    session = await runner.session_service.create_session(app_name=APP, user_id="u1")

    # ---- phase 1: initial request; capture the long-running call id ----
    print("user> I need to be reimbursed $1200 for a conference ticket.")
    pending_call = None
    async for ev in runner.run_async(
        user_id="u1", session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text="I need reimbursement of $1200 for a conference ticket.")],
        ),
    ):
        for c in ev.get_function_calls():
            print(f"  [call] {c.name}({dict(c.args)})")
            if ev.long_running_tool_ids and c.id in ev.long_running_tool_ids:
                pending_call = c
        for r in ev.get_function_responses():
            print(f"  [resp] {r.response}")
        if ev.is_final_response() and ev.content:
            t = "".join(p.text or "" for p in ev.content.parts).strip()
            if t:
                print("agent>", t)

    assert pending_call, "expected a long-running call"
    print(f"\n...ticket {('approved' if approve else 'DENIED')} by manager out of band...\n")

    # ---- phase 2: resume with the real decision ----
    decision = (
        {"status": "approved", "ticket_id": "RB-4471"}
        if approve else
        {"status": "denied", "ticket_id": "RB-4471", "reason": "over $1000 needs director sign-off"}
    )
    resume_msg = types.Content(
        role="user",
        parts=[types.Part(function_response=types.FunctionResponse(
            id=pending_call.id, name=pending_call.name, response=decision,
        ))],
    )
    async for ev in runner.run_async(
        user_id="u1", session_id=session.id, new_message=resume_msg
    ):
        if ev.is_final_response() and ev.content:
            print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())


if __name__ == "__main__":
    asyncio.run(main())
