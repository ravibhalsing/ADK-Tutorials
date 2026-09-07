# Example 01 — Hello Agent

The smallest useful ADK agent: four required fields + one tool.
Runs on the **Vertex AI path** (gcloud ADC, no API key).

> **Folder name rule:** an ADK agent folder becomes the "app name", which in ADK 2.x
> **must start with a letter** and contain only letters/digits/`_`/`-`. That's why this
> folder is `ex01_hello_agent`, not `01_hello_agent`.

## Files

| File | Role |
|---|---|
| `agent.py` | Defines `root_agent` (an `Agent` / `LlmAgent`) and one function tool. Reads `MODEL` from `.env`. |
| `__init__.py` | `from . import agent` — lets ADK discover the agent. |
| `.env.example` | Template for credentials. Copy to `.env`. |
| `run_programmatic.py` | Runs the same agent via the `Runner` API (no CLI). |
| `requirements.txt` | Per-example dependencies. |

## Setup

One-time, machine-wide (if not already done):

```powershell
gcloud auth application-default login
gcloud config set project <your-project-id>
```

Per-example:

```powershell
cd "D:\Learning\code\ADK learning\adk-tutorials"
.\.venv\Scripts\Activate.ps1

cd "00-environment-setup\examples\ex01_hello_agent"
Copy-Item .env.example .env
notepad .env        # set GOOGLE_CLOUD_PROJECT / LOCATION / MODEL, save, close
cd ..               # back to …\examples  (the parent of the agent folder)
```

The committed `.env` in this folder is already filled in for project
`your-gcp-project-id` / `us-central1` / `gemini-2.5-flash`. Change it to your own project.

## Run it — 3 ways

### A. Terminal chat

```powershell
# from …\00-environment-setup\examples
adk run ex01_hello_agent
```
Type `hi`, then `what time is it?`, then `exit`. Expected: a greeting, then a sentence
with the current UTC time (the model called `get_utc_time`).

### B. Dev UI (see the trace)

```powershell
adk web
```
Open http://localhost:8000, pick `ex01_hello_agent`, send "what time is it?".
Then open the **Events** / **Trace** panel and find:
`user message → llm request → functionCall get_utc_time → functionResponse → llm request → final text`.
This event view is your primary debugging tool for the rest of the course.

### C. Programmatic (the Runner API)

```powershell
# from THIS folder (…\ex01_hello_agent)
cd ex01_hello_agent
python run_programmatic.py
```
Actual output from a test run (time will differ):
```
(model: gemini-2.5-flash)

user> Hi there!
agent> Hello! I'm Gemini, a large language model here to help you learn about Google ADK. How can I assist you today?

user> What's the time right now?
  [tool call] get_utc_time({})
  [tool result] {'status': 'success', 'utc_time': '2026-09-05T13:53:08+00:00'}
agent> The current UTC time is 2026-09-05 13:53:08. Is there anything else I can help you with?

user> Thanks — remind me what you just told me.
agent> I just told you that the current UTC time is 2026-09-05 13:53:08. Can I help with anything else?
```
The third turn proves session memory: the agent recalls the earlier turn because all
three messages share one session.

## What to notice

- **No `main()` in `agent.py`.** ADK imports the module and reads `root_agent`.
- **The docstring is the tool spec.** The model decides to call `get_utc_time` based on
  the function name + docstring — not the code body. Write docstrings for the model.
- **`MODEL` comes from `.env`.** `run_programmatic.py` calls `load_dotenv()` *before*
  importing `agent.py`; the `adk` CLI does that for you.
- **`gemini-2.5-flash`** keeps iteration cheap. Swap to `gemini-2.5-pro` for harder
  reasoning (Module 02 / 14).

## Expected noise (not errors)

ADK 2.x prints `UserWarning: [EXPERIMENTAL] ...` lines for `InMemoryCredentialService`,
`BaseCredentialService`, and `JSON_SCHEMA_FOR_FUNC_DECL`. These are informational — the
run still succeeds. PowerShell renders stderr in red, which makes them look worse than
they are.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Invalid app name '01_...': must start with a letter` | Rename the agent folder to start with a letter (`ex01_...`). |
| `google.auth.exceptions.DefaultCredentialsError` | Run `gcloud auth application-default login`. |
| `PermissionDenied` / `403` on Vertex | Enable the API: `gcloud services enable aiplatform.googleapis.com`; check the project id in `.env`. |
| `404 ... model ... not found` | The model id/region combo isn't available; try `us-central1` or a `-latest` alias. |
| `adk` not recognized | Activate the venv (`.\.venv\Scripts\Activate.ps1`). |
| `adk web` shows no agents | Run it from `…\examples` (the folder that *contains* `ex01_hello_agent`). |

See Module 00 README §13 for the full table.
