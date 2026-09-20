# Example 03 — combining built-in tools

```powershell
python run.py            # coder route — AgentTool composition (reliable)
python run.py --search   # adds the google_search route (needs grounding quota)
python run.py --break    # google_search + a function tool in ONE agent
```

## `--break` — the rule, enforced

```
user> How long is the word 'python'?
  !! ClientError: 400 INVALID_ARGUMENT ...
     Unable to submit request because Multiple tools are supported only when they
     are all search tools.
```

Construction succeeds; the error is at **run time**, from Vertex. One built-in tool per
agent, and no mixing a built-in with function tools.

## The fix — `AgentTool`-wrapped specialists

```
user> Assume a population of 40,000,000. What is it after 10 years of 1.2% annual
      compound growth? Use the coder.
  [analyst] call coder                       # coder = its own agent w/ BuiltInCodeExecutor
agent> After 10 years ... approximately 45,067,671.
```

```
searcher = Agent(tools=[google_search], ...)             # exactly one built-in
coder    = Agent(code_executor=BuiltInCodeExecutor(), ...) # exactly one built-in
analyst  = Agent(tools=[AgentTool(agent=searcher), AgentTool(agent=coder)], ...)
```

Each built-in tool is isolated in its own model call; the root orchestrates.

## Note on quota

`--search` calls Google Search grounding through the `searcher` sub-agent. On a fresh
GCP project that quota is very low and back-to-back runs return
`_ResourceExhaustedError` (429). The `coder` route and the `--break` demo don't touch it.
For real use: add `generate_content_config.http_options.retry_options` and request a
quota increase.
