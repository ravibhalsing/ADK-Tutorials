# Module 07 — official documentation cross-reference

| Topic | Page |
|---|---|
| Authentication (schemes, credentials, OAuth handshake, function-tool auth) | https://adk.dev/tools-custom/authentication/ |
| OpenAPI tools (auth_scheme / auth_credential args) | https://adk.dev/tools-custom/openapi-tools/ |
| Deployment secret handling | https://adk.dev/deploy/ (Modules 22–24) |

## Confirmed on this machine (ADK 2.8.0, Vertex, 2026-09-05)

- **API key**: `from google.adk.tools.openapi_tool.auth.auth_helpers import
  token_to_scheme_credential`. `token_to_scheme_credential("apikey", "query", "api_key",
  value)` → pass as `auth_scheme=`, `auth_credential=` to `OpenAPIToolset`. Verified with
  NASA APOD (`DEMO_KEY`): 403 without key, 200 with; the model's tool-call args contain
  **no** `api_key`.
- **Function-tool secret pattern** (ex02): resolve inside the tool from
  `tool_context.state["user:..."]` → Secret Manager → env; return error dict if none;
  mask the secret in the return value. `user:`-scoped token verified to persist and to
  take precedence.
- **OAuth2** classes: `from google.adk.auth import AuthConfig, AuthCredential,
  AuthCredentialTypes, OAuth2Auth`. Scheme via
  `fastapi.openapi.models.OAuth2 / OAuthFlows / OAuthFlowAuthorizationCode`.
  Handshake: tool calls `tool_context.request_credential(AuthConfig(...))` and returns
  pending → ADK emits a long-running `adk_request_credential` function call →
  client opens `auth_config.exchanged_auth_credential.oauth2.auth_uri` (+ `&redirect_uri=`)
  → sends back `types.FunctionResponse(id=<call id>, name="adk_request_credential",
  response=auth_config.model_dump())` with `auth_response_uri` set →
  `tool_context.get_auth_response(AuthConfig(...))` returns the exchanged credential.
  `adk web` automates the client half. ex03 not run end-to-end (needs OAuth client).
- **Service account helpers**: `service_account_dict_to_scheme_credential(config, scopes)`
  and `service_account_scheme_credential(ServiceAccount(use_default_credential=True,
  use_id_token=True, audience=...))` from the same `auth_helpers` module.

## Dependency note

Installing `google-api-python-client` + `google-auth-oauthlib` (for ex03) pulled
`opentelemetry-api 1.44` and `google-api-core 2.36`, conflicting with `google-adk 2.8`
(`opentelemetry-{api,sdk} <= 1.42.1`). Resolved by pinning
`opentelemetry-api==1.42.1`, `opentelemetry-sdk==1.42.1`,
`opentelemetry-semantic-conventions==0.63b1`, `google-api-core<2.36`. `pip check` clean after.

## Imports

```python
from google.adk.auth import AuthConfig, AuthCredential, AuthCredentialTypes, OAuth2Auth
from google.adk.tools.openapi_tool.auth.auth_helpers import (
    token_to_scheme_credential,
    service_account_dict_to_scheme_credential,
    service_account_scheme_credential,
)
from fastapi.openapi.models import OAuth2, OAuthFlows, OAuthFlowAuthorizationCode
```
