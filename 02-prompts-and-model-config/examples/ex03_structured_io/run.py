"""Structured output (output_schema + output_key) and structured input (input_schema).

    python run.py

Shows:
  1. output_schema forces typed JSON; output_key stores it in session.state
  2. the parsed object is a dict matching the Pydantic model
  3. input_schema requires the incoming message to be conforming JSON
  4. output_schema + tools on the same agent => ValueError (run with --break)
"""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.runners import Runner  
from google.adk.sessions import InMemorySessionService  
from google.genai import types  
from pydantic import BaseModel, Field  

MODEL = os.environ["MODEL"]
APP = "structured_io"


class Invoice(BaseModel):
    vendor: str = Field(description="Company that issued the invoice")
    total: float = Field(description="Grand total including tax")
    currency: str = Field(description="ISO currency code, e.g. USD")
    line_items: int = Field(description="Number of line items")


parser = Agent(
    name="invoice_parser",
    model=MODEL,
    instruction=(
        "Extract the invoice fields from the user's text. "
        "Respond ONLY with the JSON object — no prose, no markdown fences."
    ),
    output_schema=Invoice,
    output_key="invoice",
)


class GreetRequest(BaseModel):
    name: str
    language: str = Field(description="e.g. 'French', 'Japanese'")


greeter = Agent(
    name="greeter",
    model=MODEL,
    input_schema=GreetRequest,
    instruction="Produce a one-line greeting for the given name in the given language.",
)


async def run(agent: Agent, message: str, state: dict | None = None):
    svc = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP, session_service=svc)
    s = await svc.create_session(app_name=APP, user_id="u1", state=state or {})
    final = ""
    async for ev in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=message)]),
    ):
        if ev.is_final_response() and ev.content and ev.content.parts:
            final = "".join(p.text or "" for p in ev.content.parts).strip()
    stored = await svc.get_session(app_name=APP, user_id="u1", session_id=s.id)
    return final, dict(stored.state)


async def main() -> None:
    if "--break" in sys.argv:
        print("output_schema + tools + sub-agent transfer on one agent — what happens?")

        def noop(x: str) -> str:
            """A dummy tool."""
            return x

        try:
            bad = Agent(
                name="bad", model=MODEL, output_schema=Invoice,
                tools=[noop],
                instruction="Extract the invoice. Respond ONLY with JSON.",
            )
            print(f"  construction: OK ({bad.name})")
            final, _ = await run(bad, "INVOICE Foo Inc, 1 item, total 5 USD")
            print(f"  run: OK -> {final[:80]}")
        except Exception as e:  # noqa: BLE001
            print(f"  {type(e).__name__}: {e}")
        print(
            "\n  Lesson: behaviour depends on ADK version + model. Do NOT rely on it — "
            "split 'gather with tools' and 'format to schema' into two agents."
        )
        return

    invoice_text = (
        "INVOICE from Acme Cloud Ltd. 3 items. Subtotal 900 EUR, tax 90 EUR, "
        "total due 990 EUR."
    )
    print("=== 1. output_schema + output_key ===")
    final, state = await run(parser, invoice_text)
    print("  final response text :", final)
    print("  session.state['invoice'] :", json.dumps(state.get("invoice"), indent=2))
    print("  type in state :", type(state.get("invoice")).__name__)

    print("\n=== 2. input_schema (message must be conforming JSON) ===")
    good = json.dumps({"name": "Ravindra", "language": "Marathi"})
    final, _ = await run(greeter, good)
    print(f"  input  {good}")
    print(f"  output {final}")


if __name__ == "__main__":
    asyncio.run(main())
