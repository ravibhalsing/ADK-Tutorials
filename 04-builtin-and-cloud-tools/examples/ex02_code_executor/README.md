# Example 02 — `BuiltInCodeExecutor`

```powershell
adk run ex02_code_executor
python run.py
```

## Captured output

```
user> A dataset has values 4, 8, 15, 16, 23, 42. Give me the mean, population standard
      deviation, and the compound growth rate ... assuming 5 equal periods.

  [code]
    import numpy as np
    data = np.array([4, 8, 15, 16, 23, 42])
    print(f'{np.mean(data)=}')
  [result] outcome=Outcome.OUTCOME_OK output='np.mean(data)=np.float64(18.0)\n'
  [code]
    print(np.std(data, ddof=0))
  [result] outcome=Outcome.OUTCOME_OK output='std_dev_pop=np.float64(12.315302134607444)\n'
  [code]
    cagr = (42 / 4)**(1 / 5) - 1
  [result] outcome=Outcome.OUTCOME_OK output='cagr=0.6004343344404715\n'

agent> Mean = 18.0; population std dev ≈ 12.32; compound growth rate ≈ 60.04%.
```

## Takeaways

- `code_executor=BuiltInCodeExecutor()` is a **constructor argument, not a tool**.
- The model wrote real `numpy` code; Google ran it in a sandbox; the model used the exact
  outputs. No arithmetic guessing.
- Event parts: `part.executable_code.code` and
  `part.code_execution_result.{outcome, output}` (on non-final events).
- Like `google_search`, this counts as *the* built-in tool for that agent — it can't also
  carry function tools (see `../ex03_combine_builtins`).
- Keep it for exact/quantitative work. No side effects, no network, no big data.
