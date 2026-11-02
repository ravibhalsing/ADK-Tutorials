"""Module 13 · Example 1 — custom BaseAgent, packaged for `adk web` / `adk run`.

Same StoryFlow as run.py: generate -> (critique+revise) x2 -> tone check ->
regenerate from scratch if the tone check is NEGATIVE.

Difference for the web UI: there is no pre-seeded state, so the agent takes the
story topic from your chat message and saves it to state["topic"] first.

Run (from …/13-graph-and-custom-agents/examples):
    adk web            # pick "ex01_custom_agent", type e.g.: a lonely lighthouse
    adk run ex01_custom_agent
"""

from __future__ import annotations

import os
from typing import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types
from pydantic import PrivateAttr

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

generator = LlmAgent(
    name="generator", model=MODEL, output_key="story",
    instruction="Write a 4-sentence children's story about {topic}. Keep it gentle.",
)
critic = LlmAgent(
    name="critic", model=MODEL, output_key="critique",
    instruction="One sentence: what's the biggest weakness of this story?\n{story}",
)
reviser = LlmAgent(
    name="reviser", model=MODEL, output_key="story",
    instruction="Rewrite the story fixing this critique. 4 sentences.\n\n"
                "STORY:\n{story}\n\nCRITIQUE:\n{critique}",
)
tone_checker = LlmAgent(
    name="tone_checker", model=MODEL, output_key="tone",
    instruction="Reply exactly POSITIVE or NEGATIVE: is the overall tone of this story "
                "upbeat and reassuring for a small child?\n\n{story}",
)


class StoryFlow(BaseAgent):
    """generate -> (critique+revise) x2 -> tone check -> regenerate if NEGATIVE."""

    _refine: LoopAgent = PrivateAttr()

    def __init__(self, **kw):
        super().__init__(
            name="story_flow",
            description="Writes a gentle children's story, refines it, and re-writes it "
                        "if the tone check fails.",
            sub_agents=[generator, tone_checker],
            **kw,
        )
        self._refine = LoopAgent(name="refine", max_iterations=2,
                                 sub_agents=[critic, reviser])

    def _say(self, ctx: InvocationContext, text: str, state_delta: dict | None = None) -> Event:
        """A visible chat message from this agent (optionally carrying a state change)."""
        return Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(role="model", parts=[types.Part(text=text)]),
            actions=EventActions(state_delta=state_delta or {}),
        )

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # 1. topic comes from the user's message (state writes go through state_delta)
        topic = ""
        if ctx.user_content and ctx.user_content.parts:
            topic = " ".join(p.text or "" for p in ctx.user_content.parts).strip()
        topic = topic or ctx.session.state.get("topic") or "a lonely lighthouse"
        yield self._say(ctx, f"[custom logic] topic = {topic!r}", {"topic": topic})

        # 2. generate -> refine loop -> tone check
        async for e in generator.run_async(ctx):
            yield e
        async for e in self._refine.run_async(ctx):
            yield e
        async for e in tone_checker.run_async(ctx):
            yield e

        # 3. the conditional restart plain workflow agents can't express
        if (ctx.session.state.get("tone") or "").upper().startswith("NEGATIVE"):
            yield self._say(ctx, "[custom logic] tone check NEGATIVE -> regenerating from scratch")
            async for e in generator.run_async(ctx):
                yield e
        else:
            yield self._say(ctx, "[custom logic] tone check POSITIVE -> keeping the refined story")

        yield self._say(ctx, f"Final story:\n\n{ctx.session.state.get('story', '')}")


root_agent = StoryFlow()
