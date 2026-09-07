# Module 00 — Official documentation cross-reference

Read these pages alongside the module. ADK docs live at **https://adk.dev/**
(the old `google.github.io/adk-docs` URLs 301-redirect there).

| Topic in this module | Official page |
|---|---|
| What ADK is / overview | https://adk.dev/ |
| Installation, venv, pip | https://adk.dev/get-started/installation/ |
| Quickstart (folder layout, `.env`, first run) | https://adk.dev/get-started/quickstart/ |
| Python-specific get-started | https://adk.dev/get-started/python/ |
| Google Cloud / Vertex setup | https://adk.dev/get-started/ (Google Cloud section) |
| CLI subcommands & flags | https://adk.dev/api-reference/cli/ |
| Python API reference (root) | https://adk.dev/api-reference/python/ |
| Submodule list | https://adk.dev/api-reference/python/google-adk.html |
| Source, `pyproject.toml`, extras | https://github.com/google/adk-python |
| Sample agents | https://github.com/google/adk-samples |
| Release notes / changelog | https://github.com/google/adk-python/releases |

## Key API objects introduced later, first named here

- `google.adk.agents.Agent` (alias of `LlmAgent`) — the agent you define as `root_agent`.
- `google.adk.runners.Runner` / `InMemoryRunner` — drives an agent programmatically.
- `google.adk.sessions.InMemorySessionService` — ephemeral session store (dev default).
- `google.genai.types.Content` / `types.Part` — the message format ADK passes to models.

## Environment variables ADK reads

| Variable | Values | Meaning |
|---|---|---|
| `GOOGLE_GENAI_USE_VERTEXAI` | `1`/`true`/`TRUE` = on, `0`/`FALSE` = off | Route model calls via Vertex AI (on) or AI Studio (off). |
| `GOOGLE_API_KEY` | string | Gemini API key (AI Studio path). Empty on the Vertex path. |
| `GOOGLE_CLOUD_PROJECT` | project id | GCP project (Vertex path). |
| `GOOGLE_CLOUD_LOCATION` | e.g. `us-central1` | GCP region (Vertex path). |
| `GOOGLE_APPLICATION_CREDENTIALS` | path | Optional explicit service-account key file (prefer ADC / attached SA). |
| `MODEL` | e.g. `gemini-2.5-flash` | **Course convention, not ADK.** `agent.py` reads it via `os.environ`. |

On the Vertex path, auth = **Application Default Credentials**: `gcloud auth
application-default login` writes `%APPDATA%\gcloud\application_default_credentials.json`
(type `authorized_user`, with a `quota_project_id`). ADK / google-genai picks this up
automatically — no key in code or `.env`.

## Version notes

- Course targets **ADK 2.x** (`pip install "google-adk>=2,<3"`). Latest at time of writing: 2.8.0.
- ADK 1.x → 2.x introduced API renames (e.g. `CallbackContext` usage, context classes,
  graph workflows, managed agents). Where a topic changed, the module's README flags it.
- Always confirm command flags with `adk <cmd> --help` for your installed version.

## This machine (recorded 2026-09-05)

- Python installs on PATH: 3.9, 3.12, 3.13, 3.14 (×2). **Use 3.13** — `py -3.13`.
- A global `google-adk 1.24.0` exists on Python 3.14 without a working `adk` script.
  The project `.venv` supersedes it; ignore the global install.
- `.venv` built and verified: Python **3.13.7**, `google-adk` **2.8.0**, `adk` CLI OK.
- **Auth path: Vertex AI.** gcloud SDK 534.0.0, ADC configured
  (account `you@example.com`), project **your-gcp-project-id**,
  region **us-central1**, `aiplatform.googleapis.com` enabled. Model `gemini-2.5-flash`.
- `examples/ex01_hello_agent` ran end-to-end on Vertex (tool call + multi-turn memory OK).
- Example folders are prefixed `exNN_` because ADK 2.x rejects app/folder names that
  don't start with a letter.
