# Example 03 — `adk api_server` over HTTP

The same agent (`ex01_multi_tool_agent`), driven through the **production HTTP surface**
instead of the CLI or a Python `Runner`. This is what you deploy in Module 22.

There is no agent package in this folder — `adk api_server` serves the agent folders it
finds in the directory you launch it from.

## 1. Start the server

```powershell
# from …\01-adk-fundamentals\examples   (it contains ex01_multi_tool_agent/)
adk api_server
```
- FastAPI on `http://localhost:8000`
- Interactive API docs (Swagger): `http://localhost:8000/docs`
- Leave it running; use a second terminal for the client.

## 2. Talk to it — Python client

```powershell
# second terminal, venv active
cd "D:\Learning\code\ADK learning\adk-tutorials\01-adk-fundamentals\examples\ex03_api_server"
python client.py
```
`client.py` (stdlib only) does the full flow:
1. `GET /list-apps`
2. `POST /apps/ex01_multi_tool_agent/users/u1/sessions/s1`  (create session)
3. `POST /run`       — get the whole event list back at once
4. `POST /run_sse`   — stream events as Server-Sent Events

## 3. Talk to it — raw curl

See `curl_examples.sh` (run under Git Bash, or paste line by line). Same four calls.

## What to notice

- **Wire JSON is camelCase**: `appName`, `userId`, `sessionId`, `newMessage`.
- Sessions are addressed by the triple **`app_name / user_id / session_id`**. Create the
  session before `/run`, or you get `Session not found`.
- `/run` returns a JSON **array of events** — the same `Event` objects you iterated in
  `ex02`, serialized. `/run_sse` returns `data: {…}` lines, one per event.
- The server is stateless per request; all continuity lives in the session store
  (in-memory here — restart the server and `s1` is gone). Module 08 makes it persistent;
  Module 21 covers auth, CORS, and embedding this in your own FastAPI app.

## Captured output (abridged)

```
GET /list-apps -> ['ex01_multi_tool_agent', 'ex02_runner_basics']
create session -> 200 {'id': 's1', 'appName': 'ex01_multi_tool_agent', ...}

/run -> 3 events
  [multi_tool_agent] functionCall  get_weather({'city': 'Paris'})
  [multi_tool_agent] functionResp  get_weather -> {'status': 'success', 'temperature': '18°C', ...}
  [multi_tool_agent] text          It's currently 18°C with light rain in Paris.

/run_sse -> streaming
  data: {"content": {"parts": [{"functionCall": ...}]}, ...}
  data: {"content": {"parts": [{"functionResponse": ...}]}, ...}
  data: {"content": {"parts": [{"text": "It's currently 18°C ..."}]}, ...}
```
