"""Module 04 · Example 2 — BuiltInCodeExecutor.

    adk run ex02_code_executor
    python run.py

The model writes Python, Gemini runs it in a sandbox, and the model uses the
result. Great for exact arithmetic, data crunching, and unit conversions where
an LLM would otherwise guess.

Note: `code_executor=` is a constructor arg, NOT a tool. It also counts as a
"built-in tool" for the one-per-agent limitation (see ../ex03_combine_builtins).
"""

from __future__ import annotations

import os

from google.adk.agents import Agent
from google.adk.code_executors import BuiltInCodeExecutor

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

root_agent = Agent(
    name="calc_agent",
    model=MODEL,
    description="Solves quantitative problems by writing and running Python.",
    instruction=(
        "For any calculation, statistics, or data manipulation, write Python code and "
        "run it rather than computing in your head. Then explain the result briefly."
    ),
    code_executor=BuiltInCodeExecutor(),
)
