# Module 00 — Environment & Tooling Setup

> **Goal:** end this module with a clean, reproducible ADK 2.x environment, the `adk`
> CLI working, credentials configured, and a "hello agent" that responds.
>
> **Official docs:** [Installation](https://adk.dev/get-started/installation/) ·
> [Quickstart](https://adk.dev/get-started/quickstart/) ·
> [Python get-started](https://adk.dev/get-started/python/) ·
> [Google Cloud setup](https://adk.dev/get-started/) ·
> [CLI reference](https://adk.dev/api-reference/cli/)

---

## 1. What ADK is (the mental model)

**Agent Development Kit (ADK)** is an open-source, **code-first** framework for building,
testing, evaluating, and deploying LLM agents. Key properties:

| Property | What it means for you |
|---|---|
| **Code-first** | Agents are plain Python objects, not YAML/GUI config. Everything is version-controlled, testable, debuggable. |
| **Model-agnostic** | Works with Gemini natively, and with Claude / OpenAI / Llama / local models via `LiteLlm`. |
| **Deployment-agnostic** | Same agent runs locally (`adk run`), as a container (Cloud Run), on Kubernetes (GKE), or fully managed (Vertex AI Agent Engine). |
| **Rich primitives** | Tools, sessions, memory, artifacts, callbacks, plugins, multi-agent orchestration, evaluation, streaming/voice — all first-class. |

### Where ADK sits in the Google agent stack

```
Your Python code
   └── ADK  (agents, tools, orchestration, sessions, eval)
        ├── Model layer      → Gemini API (AI Studio)  OR  Vertex AI  OR  LiteLLM (other providers)
        ├── Runtime          → adk run / adk web / adk api_server / your FastAPI app
        └── Deploy targets    → Cloud Run · GKE · Vertex AI Agent Engine (Agent Runtime)
```

- **AI Studio path** — a single `GOOGLE_API_KEY`. Fastest to start, no Google Cloud project.
- **Vertex AI path** — uses your Google Cloud project + Application Default Credentials
  (ADC, from `gcloud auth application-default login`). No API key. Gives you IAM,
  VPC-SC, Agent Engine, managed sessions/memory, and one consistent auth story from
  laptop to production.

**This course uses the Vertex AI path throughout** (project `your-gcp-project-id`,
region `us-central1`, model `gemini-2.5-flash`). The AI Studio path is shown as an
alternative in each `.env.example` if you ever want it.

---

## 2. Prerequisites

| Requirement | Notes |
|---|---|
| **Python 3.10–3.13** | ADK requires `>=3.10`. **Avoid 3.14** for now — many ADK/GCP dependencies don't ship wheels for it yet. This machine has 3.12 and 3.13; we use **3.13** (confirmed working: `.venv` is Python 3.13.7). |
| `pip` + `venv` | Bundled with Python. |
| **`gcloud` CLI** + a GCP project | Needed now (Vertex path). This machine has SDK 534.0.0, project `your-gcp-project-id`, ADC configured. |
| **Vertex AI API enabled** | `gcloud services enable aiplatform.googleapis.com` (already enabled on this project). |
| `git` | For version control of your course repo. |
| (later) Docker/Podman | Only from Module 13 / 22. Not needed now. |

> Prefer the AI Studio path instead? Get a free key at
> [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) and set
> `GOOGLE_GENAI_USE_VERTEXAI=FALSE` + `GOOGLE_API_KEY=...` in each `.env`. Everything
> else in the course is identical.

---

## 3. Why a per-project virtual environment (and why yours is currently broken)

Your machine has **five** Python installations on `PATH` (3.9, 3.12, 3.13, 3.14 ×2).
`google-adk 1.24.0` is installed into the 3.14 site-packages, but its `adk.exe` console
script isn't on `PATH` — so `adk` "is not recognized". This is the single most common
Windows ADK setup problem.

**The fix is not to debug the global mess — it's to stop using global installs.**
A virtual environment gives you:

- One known Python version per project
- `adk` on `PATH` **automatically** while the venv is active (it lives in `.venv\Scripts\`)
- Reproducible installs via `requirements.txt` — your machine and a Cloud Run container get the *same* packages
- No version conflicts between projects

---

## 4. Step-by-step setup (Windows PowerShell)

Run these from the repo root: `D:\Learning\code\ADK learning\adk-tutorials`

```powershell
# 4.1 Create a virtual environment with Python 3.13
py -3.13 -m venv .venv

# 4.2 Activate it (you must do this in every new terminal)
.\.venv\Scripts\Activate.ps1
#   If you get "running scripts is disabled on this system":
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#   then re-run the activate line.

# 4.3 Upgrade pip, then install ADK 2.x
python -m pip install --upgrade pip
python -m pip install "google-adk>=2,<3"

# 4.4 Verify
adk --version
python -c "import google.adk, sys; print('adk', google.adk.__version__, '| py', sys.version.split()[0])"

# 4.5 Vertex auth — one-time per machine
gcloud auth application-default login
gcloud config set project your-gcp-project-id
gcloud services enable aiplatform.googleapis.com
gcloud auth application-default print-access-token   # should print a long token
```

Expected: `adk` prints `2.8.0` (or newer 2.x), Python is `3.13.7`.
This machine is already set up — running `00-environment-setup/verify_setup.py` with the
venv active prints **"All checks passed"**.

> **Activation check:** when the venv is active your prompt is prefixed with `(.venv)`.
> `Get-Command python` should point inside `...\adk-tutorials\.venv\Scripts\python.exe`.

### macOS/Linux equivalent

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "google-adk>=2,<3"
adk --version
```

---

## 5. ADK optional extras (`pip install "google-adk[...]"`)

Core `google-adk` covers Modules 00–19. Install extras when a module needs them:

| Extra | Installs support for | Needed in module |
|---|---|---|
| `eval` | Evaluation framework (`AgentEvaluator`, `adk eval`) | 18 |
| `a2a` | Agent-to-Agent protocol SDK | 26 |
| `mcp` | Model Context Protocol client/server | 05 |
| `db` | SQLAlchemy / Spanner session backends | 08 |
| `gcp` | Google Cloud service integrations | 22–24 |
| `otel-gcp` | OpenTelemetry → Cloud Trace exporters | 17 |
| `redis` | Redis-backed services | 08 (optional) |
| `extensions` | Extended tool/integration modules | various |
| `all` | Everything above | — |

For this course a good middle ground once you reach Part VI:

```powershell
python -m pip install "google-adk[eval,mcp,a2a,db]>=2,<3"
```

Full list: `pyproject.toml` in [github.com/google/adk-python](https://github.com/google/adk-python).

---

## 6. The `adk` CLI tour

| Command | Purpose | You'll use it in |
|---|---|---|
| `adk create <name>` | Scaffold a new agent folder (`agent.py`, `__init__.py`, `.env`). Flags: `--model`, `--api_key`, `--project`, `--region`. | 01+ |
| `adk run <folder>` | Interactive terminal chat with the agent. Flags: `--session_service_uri`, `--artifact_service_uri`, `--log_level`. | 01+ |
| `adk web` | Launch the **dev UI** (chat, event/trace inspector, eval tab) at `http://localhost:8000`. **Dev only.** Flags: `--port`, `--host`, `--reload_agents`. | 01+ |
| `adk api_server` | Start the FastAPI server (same one used in production). Flags: `--port`, `--with_ui`, `--session_service_uri`. | 21 |
| `adk eval` | Run an eval set against an agent. Flags: `--config_file_path`, `--print_detailed_results`. | 18 |
| `adk test` | Run `pytest` on agent test JSON files. | 18, 25 |
| `adk deploy {cloud_run\|agent_engine\|gke}` | Deploy to a hosted target. | 22–24 |
| `adk eval_set {create\|add_eval_case\|generate_eval_cases}` | Manage eval sets. | 18 |
| `adk optimize` | Auto-optimize root-agent instructions (GEPA optimizer). | 18 |
| `adk migrate session` | Migrate a session DB to the latest schema. | 08 (ops) |
| `adk telemetry {enable\|disable\|status}` | Control ADK's anonymous usage telemetry. | now (see §9) |

Run `adk --help` and `adk <command> --help` for the authoritative, version-specific list.

---

## 7. Credentials & the `.env` file

ADK auto-loads a `.env` file **from the agent's folder** (the directory containing
`agent.py`). Never commit secrets — this repo's `.gitignore` excludes `.env`.

### Vertex AI path (this course)

`.env`:
```dotenv
MODEL=gemini-2.5-flash

GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_API_KEY=
```

Notes:
- `GOOGLE_GENAI_USE_VERTEXAI` accepts `1` / `true` / `TRUE` (all equivalent) for on,
  `0` / `FALSE` for off.
- `GOOGLE_API_KEY` is deliberately empty — Vertex authenticates with **ADC**, the
  credentials from `gcloud auth application-default login` (stored at
  `~/AppData/Roaming/gcloud/application_default_credentials.json` on Windows).
- `MODEL` is **not** an ADK variable — it's our own convention. `agent.py` reads it via
  `os.environ["MODEL"]` so the model id is configurable per environment.
- No credential lives in the file itself, so committing this exact `.env` would be
  harmless — but we still git-ignore it out of habit and because other `.env`s won't be.

### AI Studio path (alternative)

```dotenv
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=key-from-aistudio.google.com/app/apikey
```

### Precedence & security

- Explicit shell environment variables > `.env` file values.
- `.env` is per-agent-folder — keeps experiments isolated.
- **Production:** no `.env`. Cloud Run uses the attached service account (+ Secret
  Manager for any real secrets); GKE uses Workload Identity; Agent Engine handles it.
  Covered in Modules 07, 22–24. The Vertex path you're using now is the same auth model,
  just backed by your user ADC instead of a service account.

---

## 8. Project layout ADK expects

```
adk-tutorials/                    <- repo root, your CWD when running adk
├── .venv/                        <- virtual environment (git-ignored)
├── .gitignore
├── requirements.txt              <- pinned deps for the whole course
├── my_agent/                     <- an "agent folder" = a package (name starts with a letter!)
│   ├── __init__.py               <- must contain:  from . import agent
│   ├── agent.py                  <- must define:   root_agent = Agent(...)
│   └── .env                      <- config for this agent (git-ignored)
└── 00-environment-setup/
    └── examples/
        └── ex01_hello_agent/     <- this module's example (same shape)
            ├── __init__.py
            ├── agent.py
            ├── .env  /  .env.example
            ├── run_programmatic.py
            └── requirements.txt
```

Rules ADK enforces:
- `__init__.py` must import the agent module: `from . import agent`
- `agent.py` must expose a module-level variable named **`root_agent`**
- You run `adk run <folder>` / `adk web` from the **parent** of the agent folder
- **The folder name becomes the "app name" and must start with a letter**, then only
  letters/digits/`_`/`-`. `01_hello_agent` fails with a Pydantic `ValidationError`;
  `ex01_hello_agent` is fine. That's why every example folder in this course is prefixed
  `exNN_`.

---

## 9. Telemetry (decide now)

ADK collects anonymous CLI usage telemetry by default. Check and set your preference:

```powershell
adk telemetry status
adk telemetry disable   # optional
```

This is unrelated to *your agent's* observability (traces/metrics you configure in Module 17).

---

## 10. Do the example

Go to [`examples/ex01_hello_agent/`](examples/ex01_hello_agent/) and follow its `README.md`.
It has you:

1. Copy `.env.example` → `.env` (or use the committed one) and set your project id.
2. Run `adk run ex01_hello_agent` from the `examples/` folder.
3. Run `adk web` and inspect the event trace.
4. Run the programmatic version, `python run_programmatic.py`, to see the `Runner` API.

This example is **verified working on the Vertex path** — see its README for the actual
captured output.

A helper script, [`verify_setup.py`](verify_setup.py), checks Python version, ADK version,
venv activation, `adk` on PATH, and credentials. Run it with the venv active:

```powershell
python 00-environment-setup\verify_setup.py
```

---

## 11. Exercises

1. **Break and fix PATH.** Deactivate the venv (`deactivate`), run `adk --version` (fails),
   reactivate, run it again (works). Explain in one sentence why.
2. **Two agents, one repo.** `adk create weather_agent` and `adk create joke_agent` with
   different `--model` values. Confirm `adk web` lists both in its dropdown.
   (Note `adk create` uses a letter-first name — good.)
3. **Version pin.** Freeze your environment: `pip freeze > requirements.lock.txt`.
   Diff it against `requirements.txt` and note which transitive deps ADK pulled in.
4. **Prove ADC is what's authenticating.** Run the example (works). Then in the same
   shell: `gcloud auth application-default revoke`, run it again (fails with
   `DefaultCredentialsError`), then `gcloud auth application-default login` and confirm
   it works again. No API key was ever involved.
5. **Region swap.** Change `GOOGLE_CLOUD_LOCATION` to `europe-west1` in the example's
   `.env` and re-run. Observe it still works (Gemini is multi-region) — note any latency
   difference.

---

## 12. Checklist — you can move to Module 01 when you can:

- [ ] Explain code-first / model-agnostic / deployment-agnostic in your own words
- [ ] Create and activate a `.venv`, and say why `adk` only works when it's active
- [ ] `adk --version` prints `2.x`
- [ ] State the difference between the AI Studio path and the Vertex AI path
- [ ] Write a correct `__init__.py` + `agent.py` + `.env` trio from memory
- [ ] Run an agent three ways: `adk run`, `adk web`, and programmatically with `Runner`
- [ ] Name what each `adk` subcommand does at a high level

---

## 13. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `adk : The term 'adk' is not recognized` | venv not activated, or ADK installed in a different Python | Activate `.venv`; reinstall with `python -m pip install "google-adk>=2,<3"` |
| `running scripts is disabled on this system` | PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `pip` install fails building a wheel on Python 3.14 | No 3.14 wheels yet for a GCP/grpc dep | Recreate venv with `py -3.13` |
| `ValidationError ... Invalid app name '01_x': must start with a letter` | Agent folder name starts with a digit | Rename the folder so it starts with a letter (`ex01_x`) |
| `google.auth.exceptions.DefaultCredentialsError` | ADC not set up | `gcloud auth application-default login` |
| `PermissionDenied` / `403` on `aiplatform` | Vertex AI API disabled, or wrong project | `gcloud services enable aiplatform.googleapis.com`; check `GOOGLE_CLOUD_PROJECT` in `.env` |
| `404 ... model gemini-... not found` | Model not served in that region | Use `us-central1`, or a `-latest` alias |
| `PermissionDenied: ... does not have permission ... aiplatform.endpoints.predict` | Your account lacks the role | Grant `roles/aiplatform.user` on the project |
| Lots of red `UserWarning: [EXPERIMENTAL] ...` from `adk run` | ADK 2.x flags experimental internals; PowerShell paints stderr red | Harmless — the run still completes. Ignore. |
| `adk web` shows no agents | Running from the wrong directory, or missing `__init__.py` | Run from the folder that *contains* the agent package; ensure `from . import agent` |
| `ModuleNotFoundError: google.adk` | Wrong interpreter | `python -c "import sys; print(sys.executable)"` — must be inside `.venv` |
| Multiple Python versions confuse `py` | — | `py --list` to see installed versions; use `py -3.13` explicitly |
