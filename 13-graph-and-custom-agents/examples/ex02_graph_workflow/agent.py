"""Module 13 · Example 2 — Workflow sequential graph, packaged for `adk web` / `adk run`.

Graph:  START -> normalize (fn) -> extract_amount (LLM) -> apply_policy (fn)
A `Workflow` is accepted as `root_agent` by the ADK 2.x loader.

Run (from …/13-graph-and-custom-agents/examples):
    adk web            # pick "ex02_graph_workflow", type e.g.: Taxi from the airport, $37.50
    adk run ex02_graph_workflow
"""

from __future__ import annotations

import os
import re

from google.adk import Event, Workflow
from google.adk.agents import LlmAgent
from google.genai import types

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")


def normalize(node_input) -> Event:
    """Pull the user's text out of the incoming Content."""
    text = node_input
    if hasattr(node_input, "parts"):
        text = " ".join(p.text or "" for p in node_input.parts)
    return Event(output=str(text).strip())


# the only AI node: turn free text into just a number
extract_amount = LlmAgent(
    name="extract_amount", model=MODEL,
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
    # content= makes the decision show up as a chat message in adk web
    return Event(
        output=decision,
        content=types.Content(role="model", parts=[types.Part(text=decision)]),
    )


root_agent = Workflow(
    name="expense_flow",
    description="Extracts the amount from an expense and applies a $500 approval policy.",
    edges=[("START", normalize, extract_amount, apply_policy)],
)
