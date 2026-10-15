"""Module 11 · Example 2 — ParallelAgent fan-out + SequentialAgent gather.

The user's message is the topic. Three researchers run concurrently (each
writes its own output_key), then a synthesizer step reads all three.

    adk web
    adk run ex02_parallel_gather
    python run.py
"""

from __future__ import annotations

import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

M = os.environ.get("MODEL", "gemini-2.5-flash")


def researcher(key: str, angle: str) -> LlmAgent:
    # {topic} is a state placeholder filled at run time from the user's message.
    # Double braces because this is an f-string.
    return LlmAgent(
        name=f"{key}_researcher", model=M, output_key=key,
        instruction=f"State exactly two concise facts about the {angle} of: {{topic}}. "
                    f"Two bullet points, nothing else.",
    )


fan_out = ParallelAgent(name="research", sub_agents=[
    researcher("cost", "cost"),
    researcher("benefits", "main benefits"),
    researcher("risks", "main risks or drawbacks"),
])

synth = LlmAgent(
    name="synthesizer", model=M,
    instruction="In 3 sentences, give an overall picture of {topic} using these notes.\n\n"
                "COST:\n{cost}\n\nBENEFITS:\n{benefits}\n\nRISKS:\n{risks}",
)


def _seed_topic(callback_context):
    """Copy the user's chat message into state['topic'] at the start of every run."""
    content = callback_context.user_content
    text = "".join(p.text or "" for p in content.parts).strip() if content and content.parts else ""
    if text:
        callback_context.state["topic"] = text
    return None


root_agent = SequentialAgent(
    name="research_then_synth",
    sub_agents=[fan_out, synth],
    before_agent_callback=_seed_topic,
)
