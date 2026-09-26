# Example 03 — Interactive OAuth2 (Google Calendar)

The full authorization-code flow: the tool asks for a credential, the user signs in, the
tool gets an access token, caches it, and calls the API.

## Setup (required)

1. Cloud Console → **APIs & Services → Credentials → Create OAuth client ID →
   Web application**.
2. Authorized redirect URI: `http://localhost:8765/callback`
3. Enable the **Google Calendar API** on the project.
4. `.env`:
   ```
   OAUTH_CLIENT_ID=xxxx.apps.googleusercontent.com
   OAUTH_CLIENT_SECRET=xxxx
   ```
5. `pip install -r requirements.txt`

```powershell
python run.py     # opens a browser; consent; prints your next events
```

Without creds it prints: `Set OAUTH_CLIENT_ID / OAUTH_CLIENT_SECRET in .env first`.

## The handshake (in `agent.py` + `run.py`)

| Step | Where | What |
|---|---|---|
| 1 | `list_upcoming_events` | no cached creds, no auth response → `tool_context.request_credential(AuthConfig(scheme, cred))`, return `{"status":"pending"}` |
| 2 | ADK | emits a long-running `adk_request_credential` function call |
| 3 | `run.py` | detects it, reads `auth_config...oauth2.auth_uri`, appends `&redirect_uri=`, opens the browser |
| 4 | browser | user consents → Google redirects to `http://localhost:8765/callback?code=...` |
| 5 | `run.py` | tiny `HTTPServer` catches that URL; sends a `FunctionResponse(id=<call id>, name="adk_request_credential", response=auth_config.model_dump())` with `auth_response_uri` set |
| 6 | `list_upcoming_events` (re-run) | `tool_context.get_auth_response(...)` returns the exchanged credential → build `Credentials`, cache in `state["user:google_calendar_token"]`, call the Calendar API |

## `adk web` does steps 3–5 for you

Run `adk web`, pick `ex03_oauth_interactive`, ask "what's on my calendar?" — the dev UI
pops the Google consent screen and handles the callback. **Zero** client code.

## Notes

- The token is cached per-user (`user:` prefix) and **refreshed** when expired, so sign-in
  happens once.
- In production, don't leave refresh tokens in `state` — use a secret store (see module
  README §7).
