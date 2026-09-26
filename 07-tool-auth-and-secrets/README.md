# Module 07 — Tool Authentication & Secrets

> **Goal:** give tools credentials safely — API keys, service accounts, and the
> interactive OAuth2 flow — without leaking secrets to the model or into logs.
>
> **Docs:** [Authentication](https://adk.dev/tools-custom/authentication/)

---

## 1. The landscape

| Auth type | ADK support | Interactive? | Example |
|---|---|---|---|
| **API key** (query / header / cookie) | `token_to_scheme_credential("apikey", "query", "api_key", value)` | no | `ex01` |
| **HTTP Bearer** (static token) | `token_to_scheme_credential("oauth2Token", ...)` / raw header | no | — |
| **Service Account** (call Google APIs) | `service_account_dict_to_scheme_credential(config, scopes)` | no | §4 |
| **Service Account ID token** (call *your* IAM-protected service) | `service_account_scheme_credential(ServiceAccount(use_default_credential=True, use_id_token=True, audience=...))` | no | §4 |
| **OAuth2 / OIDC** (act as the end user) | `AuthScheme` + `AuthCredential(OAUTH2, OAuth2Auth(client_id, client_secret))` + the handshake | **yes** | `ex03` |

Two ADK classes underpin all of it:
- **`AuthScheme`** — *how* the API wants credentials (from OpenAPI 3 security schemes).
- **`AuthCredential`** — the *starting* material (`auth_type` + the key / client id+secret / SA json).

---

## 2. API key (non-interactive) — `ex01`

```python
from google.adk.tools.openapi_tool.auth.auth_helpers import token_to_scheme_credential

auth_scheme, auth_credential = token_to_scheme_credential(
    "apikey", "query", "api_key", os.environ["NASA_API_KEY"]
)
toolset = OpenAPIToolset(spec_str=SPEC, spec_str_type="yaml",
                         auth_scheme=auth_scheme, auth_credential=auth_credential)
```

The key is applied to every request the toolset makes. The **model never sees it** —
the tool-call args have no `api_key`. Same idea for a header key: `"header", "X-Api-Key"`.

---

## 3. Function tool + a secret you resolve yourself — `ex02`

For a plain `FunctionTool`, resolve the secret inside the tool, in priority order:

```python
def _resolve_token(tool_context: ToolContext) -> str | None:
    return (tool_context.state.get("user:chat_token")     # 1. per-user (multi-tenant)
            or _from_secret_manager("chat-bot-token")      # 2. production
            or os.environ.get("CHAT_BOT_TOKEN"))           # 3. local dev
```

Rules:
- **Never** return the secret or log it. Mask it (`tok[:3] + "…" + tok[-2:]`).
- **Per-user tokens** live in `state["user:..."]` so each caller uses their own
  credential — essential for multi-tenant deployments.
- Missing secret → return `{"status": "error", "error_message": "...connect your token"}`,
  not an exception.

### Secret Manager (production)

```python
from google.cloud import secretmanager   # pip install google-cloud-secret-manager

client = secretmanager.SecretManagerServiceClient()
path = f"projects/{PROJECT}/secrets/{name}/versions/latest"
secret = client.access_secret_version(name=path).payload.data.decode()
```
Grant the runtime service account `roles/secretmanager.secretAccessor` on that secret
only. On Cloud Run you can also mount secrets as env vars (Module 22).

---

## 4. Service Account (call Google APIs as the app)

```python
from google.adk.tools.openapi_tool.auth.auth_helpers import service_account_dict_to_scheme_credential

scheme, cred = service_account_dict_to_scheme_credential(
    config=json.loads(sa_json), scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
```

**Access token** (default) → call Google APIs. **ID token**
(`use_id_token=True, audience=<url>`) → call your own Cloud Run / IAP-protected service.
Prefer `use_default_credential=True` (the attached SA / ADC) over shipping an SA JSON.

---

## 5. Interactive OAuth2 (act as the user) — `ex03`

The tool can't get the credential on its own — the user must sign in. The handshake:

```
tool: check cache -> check get_auth_response() -> neither?
      tool_context.request_credential(AuthConfig(scheme, cred)); return {"status":"pending"}
        ↓  (ADK emits a long-running `adk_request_credential` call)
client: open auth_config...oauth2.auth_uri (+ &redirect_uri=...)
        user consents -> browser hits your redirect_uri with ?code=...
        client sends a FunctionResponse(id=<call id>, name="adk_request_credential",
                                        response=auth_config-with-auth_response_uri)
        ↓
tool: get_auth_response() now returns the exchanged credential -> build Credentials,
      cache in state["user:..._token"], call the API, return the data
```

- **`adk web` does the whole client half for you** — it pops the consent screen and
  handles the callback. `ex03/run.py` shows the manual version (local callback server).
- Cache the token (`state["user:...token"]`, or better a secret store) and **refresh**
  it (`creds.refresh(Request())`) so the user signs in once.
- `ex03` needs a Google OAuth **Web** client id/secret and the Calendar API enabled.

---

## 6. Examples

| Folder | Auth | Testable now? |
|---|---|---|
| `ex01_api_key/` | API key in query string (NASA APOD, `DEMO_KEY`) | ✅ yes |
| `ex02_function_tool_secret/` | secret resolution: `user:` state → Secret Manager → env; per-user tokens | ✅ yes |
| `ex03_oauth_interactive/` | full OAuth2 code flow (Google Calendar) | needs an OAuth client id/secret |

---

## 7. Production notes

- **Storing tokens in session state is a risk** (the docs say so). `state` may be
  persisted to a DB in plaintext. For refresh tokens especially, prefer a secret
  manager or an auth-broker service; encrypt at rest if you must use state.
- **Per-user isolation.** In multi-tenant apps every user's credential must be scoped to
  them (`user:` prefix, or a per-user row keyed by `user_id`). Never a shared token.
- **Least privilege / minimal scopes.** Request the narrowest OAuth scopes; grant the SA
  only the specific secrets/resources it needs.
- **Rotation.** Handle refresh-token expiry and client-secret rotation without redeploy.
- **Audit.** Log *that* a credential was used (tool, user, time) — never the value.
- **Workload Identity Federation** (GKE, GitHub Actions) removes long-lived keys
  entirely — Module 24 / 25.

---

## 8. Exercises

1. Switch `ex01` to send the key as a **header** (`token_to_scheme_credential("apikey",
   "header", "X-Api-Key", ...)`) against an API that wants a header.
2. In `ex02`, set `CHAT_BOT_TOKEN` in `.env` and confirm the first post now succeeds
   with the shared token; then add a `user:` token and confirm it takes precedence.
3. Stand up a real Secret Manager secret, grant your ADC access, and make `ex02` pull
   from it.
4. Do `ex03` end to end with your own Google account and a throwaway OAuth client.
5. Run `ex03` under `adk web` instead of `run.py` — note that you write **zero**
   callback-handling code.

---

## 9. Checklist

- [ ] Inject an API key into an OpenAPI toolset without the model seeing it
- [ ] Resolve a secret in a function tool with a dev→prod fallback chain, masked in output
- [ ] Store and use a **per-user** credential
- [ ] Explain access token vs ID token for service accounts
- [ ] Walk the interactive OAuth2 handshake (`request_credential` → client → `get_auth_response`)
- [ ] State why refresh tokens shouldn't sit in plaintext session state

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| API returns 401/403 despite config | wrong `in` location (query vs header) or param name in `token_to_scheme_credential` |
| Model asks the user for the API key | you put the key in the tool signature — inject it via the toolset instead |
| `bytes can only contain ASCII` | non-ASCII char in a `b"..."` literal (e.g. an em-dash) |
| OAuth loop never completes | `redirect_uri` must exactly match the one registered on the OAuth client |
| token works once then fails | not refreshing — call `creds.refresh(Request())` when expired |
| `opentelemetry` / `google-api-core` version conflict after installing google-api-python-client | pin `opentelemetry-{api,sdk}==1.42.1` and `google-api-core<2.36` (ADK 2.8 caps otel) |
