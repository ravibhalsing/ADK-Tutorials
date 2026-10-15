"""Module 11 · Example 3 — LoopAgent: writer -> critic -> stopper, repeated.

Your chat message is the brief (what to write + the rules). The loop stops when
the critic says APPROVED, or after 3 rounds.

    adk web
"""

import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent
from google.adk.events import Event, EventActions
from google.genai import types

M = os.environ.get("MODEL", "gemini-2.5-flash")


# 1. Save the user's message as the rubric and clear the previous attempt.
def start_fresh(callback_context):
    msg = callback_context.user_content
    callback_context.state["rubric"] = msg.parts[0].text
    callback_context.state["draft"] = ""
    callback_context.state["feedback"] = ""


# 2. Writer: improves the draft using the critic's feedback.
writer = LlmAgent(
    name="writer", model=M, output_key="draft",
    instruction="Rubric: {rubric}\n"
                "Previous attempt: {draft}\n"
                "Critic's feedback: {feedback}\n"
                "Write an improved version. Output ONLY the result.",
)

# 3. Critic: approves or asks for a revision.
critic = LlmAgent(
    name="critic", model=M, output_key="feedback",
    instruction="Rubric: {rubric}\n"
                "Draft: {draft}\n"
                "If the draft meets EVERY rule, reply exactly: APPROVED\n"
                "Otherwise reply: REVISE - <one short reason>",
)


# 4. Stopper: ends the loop (escalate=True) once the critic approves.
class Stopper(BaseAgent):
    async def _run_async_impl(self, ctx):
        approved = ctx.session.state["feedback"].strip().upper().startswith("APPROVED")
        text = f"Final: {ctx.session.state['draft']}" if approved else "Revising..."
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=text)]),
            actions=EventActions(escalate=approved),
        )


root_agent = LoopAgent(
    name="refine",
    max_iterations=3,
    sub_agents=[writer, critic, Stopper(name="stopper")],
    before_agent_callback=start_fresh,
)
