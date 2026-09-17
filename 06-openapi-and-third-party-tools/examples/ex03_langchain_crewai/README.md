# Example 03 — Wrap LangChain / CrewAI tools

```powershell
python run.py                # LangchainTool wrapping a @tool calculator
```

## Captured output

```
user> What is (128 * 47) + (2 ** 16)?
  [tool call] calculator({'expression': '(128 * 47) + (2 ** 16)'})
agent> The answer is 71,552.

user> If a loan of 5000 grows at 7% for 3 years compounded annually, what's the balance?
  [tool call] calculator({'expression': '5000 * (1.07) ** 3'})
agent> The balance after 3 years will be 6125.215.
```

## Takeaways

- `LangchainTool(tool=<any LangChain BaseTool>)` — drops into `tools=[...]`.
- Build the LangChain tool with the **`@tool` decorator** (or `StructuredTool` +
  `args_schema`). `Tool.from_function` leaks a `config` kwarg through the bridge and
  raises `TypeError` at call time.
- Import path: `google.adk.integrations.langchain` (the old `google.adk.tools.langchain_tool`
  still works but warns).
- The same pattern covers `langchain_community`'s hundreds of integration tools — but
  many are lightly maintained (Wikipedia's tool now 403s on Wikimedia's user-agent
  policy; the `arxiv` tool broke on an upstream API change). Pin versions, test first.

## CrewAI

See `crewai_pattern.py`. `CrewaiTool(tool=..., name=..., description=...)` — name and
description are **required** (ADK can't infer them). Needs `google-adk[extensions]` or
`crewai-tools` (heavy).
