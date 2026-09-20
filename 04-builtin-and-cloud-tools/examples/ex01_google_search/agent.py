"""Module 04 · Example 1 — Google Search grounding.

    adk run ex01_google_search
    adk web
    python run.py

`google_search` grounds answers in live web results. On Vertex this is
"Grounding with Google Search". The event stream carries grounding_metadata
(sources + the spans they support) which you MUST surface as citations.
"""

from __future__ import annotations

import os

from google.adk.agents import Agent
from google.adk.tools import google_search

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

root_agent = Agent(
    name="research_agent",
    model=MODEL,
    description="Answers factual questions using live Google Search results.",
    instruction=(
        "You answer questions using the `google_search` tool for anything that could be "
        "recent, changing, or that you're unsure about. "
        "Summarize concisely and mention that the info comes from a web search."
    ),
    tools=[google_search],
)
