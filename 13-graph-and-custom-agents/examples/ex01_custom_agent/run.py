"""Custom agent: subclass BaseAgent for control flow the workflow agents can't do.

    python run.py

Pattern: generate a short story -> critique+revise loop -> tone check ->
if the tone check FAILS, regenerate from scratch (conditional restart).
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import warnings
from typing import AsyncGenerator

warnings.filterwarnings("ignore", category=DeprecationWarning)

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent  
from google.adk.agents.invocation_context import InvocationContext  
from google.adk.events import Event  
from google.adk.runners import InMemoryRunner  
from google.genai import types  
from pydantic import PrivateAttr  

M = os.environ["MODEL"]

generator = LlmAgent(
    name="generator", model=M, output_key="story",
    instruction="Write a 4-sentence children's story about {topic}. Keep it gentle.",
)
critic = LlmAgent(
    name="critic", model=M, output_key="critique",
    instruction="One sentence: what's the biggest weakness of this story?\n{story}",
)
reviser = LlmAgent(
    name="reviser", model=M, output_key="story",
    instruction="Rewrite the story fixing this critique. 4 sentences.\n\n"
                "STORY:\n{story}\n\nCRITIQUE:\n{critique}",
)
tone_checker = LlmAgent(
    name="tone_checker", model=M, output_key="tone",
    instruction="Reply exactly POSITIVE or NEGATIVE: is the overall tone of this story "
                "upbeat and reassuring for a small child?\n\n{story}",
)


class StoryFlow(BaseAgent):
    """generate -> (critique+revise) x2 -> tone check -> regenerate if NEGATIVE."""

    _refine: LoopAgent = PrivateAttr()

    def __init__(self, **kw):
        super().__init__(
            name="story_flow",
            sub_agents=[generator, tone_checker],
            **kw,
        )
        self._refine = LoopAgent(name="refine", max_iterations=2,
                                 sub_agents=[critic, reviser])

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        async for e in generator.run_async(ctx):
            yield e
        async for e in self._refine.run_async(ctx):
            yield e
        async for e in tone_checker.run_async(ctx):
            yield e

        if (ctx.session.state.get("tone") or "").upper().startswith("NEGATIVE"):
            print("  [custom logic] tone check NEGATIVE -> regenerating from scratch")
            async for e in generator.run_async(ctx):
                yield e
        else:
            print("  [custom logic] tone check POSITIVE -> keeping the refined story")


async def main() -> None:
    runner = InMemoryRunner(agent=StoryFlow(), app_name="story")
    s = await runner.session_service.create_session(
        app_name="story", user_id="u1", state={"topic": "a lonely lighthouse"})
    async for ev in runner.run_async(
        user_id="u1", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text="write it")]),
    ):
        if ev.is_final_response() and ev.author != "user" and ev.content:
            t = "".join(p.text or "" for p in ev.content.parts).strip()
            if t:
                print(f"[{ev.author}] {t[:200]}")

    final = await runner.session_service.get_session(app_name="story", user_id="u1", session_id=s.id)
    print("\ntone verdict:", final.state.get("tone"))
    print("final story:", final.state.get("story"))


if __name__ == "__main__":
    asyncio.run(main())
