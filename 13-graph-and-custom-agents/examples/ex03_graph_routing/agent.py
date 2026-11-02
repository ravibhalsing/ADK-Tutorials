"""Module 13 · Example 3 — Workflow conditional routing, packaged for `adk web` / `adk run`.

Graph:
    START -> classify (LLM) -> router (fn, emits a route) -> { BUG | BILLING | OTHER }

Run (from …/13-graph-and-custom-agents/examples):
    adk web            # pick "ex03_graph_routing", type e.g.: You charged my card twice
    adk run ex03_graph_routing
"""

from __future__ import annotations

import os

from google.adk import Event, Workflow
from google.adk.agents import LlmAgent
from google.adk.events import EventActions
from google.genai import types

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

classify = LlmAgent(
    name="classify", model=MODEL,
    instruction="Classify the user's message as exactly one word: BUG, BILLING, or OTHER.",
)


def router(node_input) -> Event:
    """Turn the classifier's word into a graph route."""
    label = str(node_input).strip().upper()
    route = label if label in {"BUG", "BILLING"} else "OTHER"
    return Event(output=route, actions=EventActions(route=route))


def _reply(text: str) -> Event:
    # content= makes the reply show up as a chat message in adk web
    return Event(output=text, content=types.Content(role="model", parts=[types.Part(text=text)]))


def bug_handler(node_input) -> Event:
    return _reply("Filed a bug ticket. Engineering will investigate; you'll get an update in 2 business days.")


def billing_handler(node_input) -> Event:
    return _reply("Routed to billing. They'll review your account and reply within 24 hours.")


def other_handler(node_input) -> Event:
    return _reply("Thanks for reaching out — a support generalist will follow up shortly.")


root_agent = Workflow(
    name="triage",
    description="Classifies a support message and routes it to BUG, BILLING or OTHER.",
    edges=[
        ("START", classify, router),
        (router, {"BUG": bug_handler, "BILLING": billing_handler, "OTHER": other_handler}),
    ],
)
