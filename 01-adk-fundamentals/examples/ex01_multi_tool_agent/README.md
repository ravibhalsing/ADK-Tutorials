# Example 01 — Multi-tool agent

The classic ADK starter: one agent, two tools (`get_weather`, `get_current_time`).
Purpose here is to **watch the event loop** in `adk web`, not the tools themselves.

## Run

```powershell
# from …\01-adk-fundamentals\examples  (parent of this folder)
adk run ex01_multi_tool_agent
```
Try:
- `weather in Paris?` → one tool call, one answer
- `what time is it in Tokyo and how's the weather there?` → **two** tool calls, one answer
- `weather on the Moon?` → tool returns `status: error`, agent reports it without inventing

## See the loop

```powershell
adk web        # http://localhost:8000  → pick ex01_multi_tool_agent
```
Ask the two-part question, then open the **Events** (or **Trace**) panel. You should see,
in order:

| # | Event | `is_final_response()` |
|---|---|---|
| 1 | user message | – |
| 2 | model → `functionCall get_weather(city="Tokyo")` (+ maybe `get_current_time` in the same event) | no |
| 3 | `functionResponse get_weather` | no |
| 4 | `functionResponse get_current_time` | no |
| 5 | model → final text | **yes** |

Exact event count varies with how the model batches the two calls — that's the point of
looking.

## Expected output (`adk run`, captured)

```
Running agent multi_tool_agent, type exit to exit.
[user]: what time is it in Tokyo and hows the weather there
[multi_tool_agent]: In Tokyo, the local time is 23:27:29 JST and the weather is
clear with a temperature of 24°C.
```

(If `°C` shows as `┬░C` in your PowerShell window, that's a console-encoding quirk, not a
bug — run `chcp 65001` once to switch the console to UTF-8. The data is correct.)

## Notes

- The tools return `dict` with a `status` key — the ADK-recommended shape. The `error`
  branch is what lets the agent fail gracefully.
- Supported cities: Paris, Tokyo, New York, Cairo (see `agent.py`).
- `MODEL` comes from `.env`. The committed `.env` points at project `gcp-learning-469104`.
- This same agent is reused by `../ex03_api_server/`.
