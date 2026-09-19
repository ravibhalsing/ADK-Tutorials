"""ToolContext: state prefixes (session / user: / temp:), skip_summarization,
tool-to-tool data passing.

    python run.py
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
from google.adk.tools import ToolContext  
from google.genai import types  

MODEL = os.environ["MODEL"]
APP = "tool_context"


# --- tools -------------------------------------------------------------------

def set_nickname(nickname: str, tool_context: ToolContext) -> dict:
    """Save what the user wants to be called (persists across all their sessions)."""
    tool_context.state["user:nickname"] = nickname
    return {"status": "success", "saved": nickname}


def load_cart(tool_context: ToolContext) -> dict:
    """Load the current shopping cart into working memory for other tools to use."""
    # pretend this came from a database
    cart = [{"item": "keyboard", "qty": 1, "price": 89.0},
            {"item": "hub", "qty": 2, "price": 34.5}]
    tool_context.state["temp:cart"] = cart          # temp: -> this turn only
    return {"status": "success", "items": len(cart)}


def cart_total(tool_context: ToolContext) -> dict:
    """Compute the total of the cart previously loaded by load_cart."""
    cart = tool_context.state.get("temp:cart")
    if not cart:
        return {"status": "error", "error_message": "Call load_cart first."}
    total = sum(i["qty"] * i["price"] for i in cart)
    return {"status": "success", "total": round(total, 2), "currency": "USD"}


def raw_receipt(tool_context: ToolContext) -> dict:
    """Return a preformatted receipt that must be shown to the user VERBATIM."""
    cart = tool_context.state.get("temp:cart") or []
    lines = [f"{i['qty']:>2} x {i['item']:<10} {i['qty']*i['price']:>8.2f}" for i in cart]
    receipt = "RECEIPT\n" + "\n".join(lines)
    tool_context.actions.skip_summarization = True   # <-- don't let the model reword it
    return {"status": "success", "receipt": receipt}


agent = Agent(
    name="cart_agent",
    model=MODEL,
    instruction=(
        "You help with a shopping cart.\n"
        "The user's saved nickname is: {user:nickname?}\n"
        "- If that nickname is present, greet/address the user by it.\n"
        "- If the user gives a (new) nickname, call set_nickname.\n"
        "- For totals: call load_cart, then cart_total.\n"
        "- For a receipt: call load_cart, then raw_receipt, and show its 'receipt' text."
    ),
    tools=[set_nickname, load_cart, cart_total, raw_receipt],
)


async def turn(runner: Runner, sid: str, text: str) -> None:
    print(f"\nuser> {text}")
    async for ev in runner.run_async(
        user_id="u1", session_id=sid,
        new_message=types.Content(role="user", parts=[types.Part(text=text)]),
    ):
        for c in ev.get_function_calls():
            print(f"  [call] {c.name}({dict(c.args)})")
        if ev.is_final_response() and ev.content:
            text = "".join(p.text or "" for p in ev.content.parts).strip()
            if text:
                print("agent>", text)
            else:
                # skip_summarization: the tool response IS the final answer
                for r in ev.get_function_responses():
                    print(f"agent> (verbatim tool result) {r.response.get('receipt', r.response)}")


async def main() -> None:
    svc = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP, session_service=svc)

    s1 = await svc.create_session(app_name=APP, user_id="u1")
    await turn(runner, s1.id, "Call me Ravi.")
    await turn(runner, s1.id, "What's my cart total?")
    await turn(runner, s1.id, "Show me the receipt.")

    # New session, SAME user — user: state carries over, temp: and session state do not.
    s2 = await svc.create_session(app_name=APP, user_id="u1")
    await turn(runner, s2.id, "Hi again!")

    stored1 = await svc.get_session(app_name=APP, user_id="u1", session_id=s1.id)
    print("\nsession-1 state keys:", list(stored1.state.keys()))
    print("  ('user:nickname' is user-scoped; 'temp:cart' was dropped after each turn)")


if __name__ == "__main__":
    asyncio.run(main())
