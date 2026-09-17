"""Module 06 · Example 3 — wrap third-party tools.

ADK wraps tools from other ecosystems:
  - LangchainTool(tool=<a LangChain BaseTool>)
  - CrewaiTool(tool=<a CrewAI tool>, name=..., description=...)

Here we wrap a LangChain tool built with `Tool.from_function` (the canonical
LangChain custom-tool primitive). ANY LangChain `BaseTool` plugs in the same way —
the community integration tools (search, DBs, APIs, …) included, though their
upstream maintenance varies. The CrewAI pattern is in crewai_pattern.py.

Import path in ADK 2.x: `google.adk.integrations.langchain`
(`google.adk.tools.langchain_tool` still works but is deprecated).

    adk run ex03_langchain_crewai
    python run.py
"""

from __future__ import annotations

import ast
import operator
import os

from google.adk.agents import Agent

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

try:
    from google.adk.integrations.langchain import LangchainTool
except ImportError:
    from google.adk.tools.langchain_tool import LangchainTool

from langchain_core.tools import tool as lc_tool

# --- a safe arithmetic evaluator, exposed as a LangChain tool ------------------

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported expression")


@lc_tool
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression like '(3+4)*2 ** 3'. Input: the expression string."""
    try:
        return str(_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:  # noqa: BLE001
        return f"error: {e}"


calculator_tool = LangchainTool(tool=calculator)

root_agent = Agent(
    name="mathy_agent",
    model=MODEL,
    description="Answers questions, using a LangChain calculator tool for exact arithmetic.",
    instruction=(
        "For any arithmetic, call the `calculator` tool with a single expression string "
        "rather than computing yourself. Then state the answer in a sentence."
    ),
    tools=[calculator_tool],
)
