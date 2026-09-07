"""Module 00 example — the smallest useful ADK agent.

What this demonstrates:
  * the required `root_agent` module-level variable
  * the four fields every LLM agent needs: name, model, description, instruction
  * one function tool, so we can see tool-calling in the `adk web` trace view

Run it:
    # from the folder that CONTAINS this package (…/00-environment-setup/examples):
    adk run ex01_hello_agent        # terminal chat
    adk web                         # dev UI at http://localhost:8000

Credentials:
    Copy .env.example -> .env. This course uses the Vertex AI path (gcloud ADC):
        GOOGLE_GENAI_USE_VERTEXAI=1
        GOOGLE_CLOUD_PROJECT=<your-project>
        GOOGLE_CLOUD_LOCATION=us-central1
    plus a one-time `gcloud auth application-default login` on your machine.
    ADK auto-loads this .env from the agent folder.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

# `Agent` is an alias for `LlmAgent`. Both imports work; `Agent` is the common one.
from google.adk.agents import Agent

# Model id comes from the .env file (key: MODEL) so it's configurable per environment.
# On the Vertex path the same short id (e.g. "gemini-2.5-flash") resolves against Vertex.
MODEL = os.environ.get("MODEL", "gemini-2.5-flash")


def get_utc_time() -> dict:
    """Return the current UTC date and time.

    Use this whenever the user asks what time or date it is. Takes no arguments.

    Returns:
        dict: {"status": "success", "utc_time": "<ISO-8601 string>"}
    """
    return {
        "status": "success",
        "utc_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


# ADK discovers this exact name. It must be a module-level variable called `root_agent`.
root_agent = Agent(
    name="hello_agent",
    # gemini-2.5-flash = cheap + fast; ideal for learning and iteration.
    # (from .env; swap to gemini-2.5-pro for harder reasoning — see Module 02 / 14.)
    model=MODEL,
    description="A minimal greeting agent that can also report the current UTC time.",
    instruction=(
        "You are a friendly assistant for someone learning Google ADK.\n"
        "- Greet the user warmly on the first turn.\n"
        "- If they ask for the time or date, call the `get_utc_time` tool and report "
        "the result in a human-readable sentence.\n"
        "- Keep answers to two sentences or fewer."
    ),
    tools=[get_utc_time],
)
