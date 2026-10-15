"""Module 11 · Example 1 — SequentialAgent: spec -> write -> review -> refactor.

Data flows through session state: each step's output_key is read by the next
step's {placeholder}.

    adk web
    adk run ex01_sequential_pipeline
    python run.py
"""

from __future__ import annotations

import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)  # SequentialAgent -> Workflow (Module 13)

from google.adk.agents import LlmAgent, SequentialAgent

M = os.environ.get("MODEL", "gemini-2.5-flash")

writer = LlmAgent(
    name="writer", model=M, output_key="draft",
    instruction="Write a single Python function for this spec. Code only, no prose:\n{spec}",
)
reviewer = LlmAgent(
    name="reviewer", model=M, output_key="review",
    instruction="List concrete problems with this code as bullet points (bugs, edge "
                "cases, style). Be terse.\n\n{draft}",
)
refactor = LlmAgent(
    name="refactor", model=M, output_key="final",
    instruction="Rewrite the function fixing every point in the review. Code only.\n\n"
                "CODE:\n{draft}\n\nREVIEW:\n{review}",
)


def _seed_spec(callback_context):
    """Copy the user's chat message into state['spec'] at the start of every
    run, so each new message in `adk web` / `adk run` is a fresh spec."""
    content = callback_context.user_content
    text = "".join(p.text or "" for p in content.parts).strip() if content and content.parts else ""
    if text:
        callback_context.state["spec"] = text
    return None


root_agent = SequentialAgent(
    name="code_pipeline",
    sub_agents=[writer, reviewer, refactor],
    before_agent_callback=_seed_spec,
)
