"""Module 01 · Example 2 — an agent to drive from your own `Runner`.

One small tool (`word_count`) so the event stream contains a function call + response
for `inspect_events.py` to dissect. Otherwise it's a plain conversational agent whose
memory comes entirely from session history.
"""

from __future__ import annotations

import os
import re

from google.adk.agents import Agent

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")


def word_count(text: str) -> dict:
    """Count the words in a piece of text.

    Args:
        text: The text to analyse.

    Returns:
        dict: {"status": "success", "words": <int>, "characters": <int>}
    """
    words = re.findall(r"\b\w+\b", text)
    return {"status": "success", "words": len(words), "characters": len(text)}


root_agent = Agent(
    name="assistant",
    model=MODEL,
    description="A general assistant that can also count words in text.",
    instruction=(
        "You are a helpful, concise assistant.\n"
        "- If the user asks how many words/characters are in some text, call `word_count`.\n"
        "- Otherwise just answer normally, using the conversation so far for context.\n"
        "- Keep answers short."
    ),
    tools=[word_count],
)
