# Example 02 — Function tool + secret resolution

```powershell
python run.py
```

## Captured output

```
user> Post 'Deploy done ✅' to #eng.
  [call] post_to_team_chat({'message': 'Deploy done ✅', 'channel': '#eng'})
  [resp] {'status': 'error', 'error_message': "No chat credential configured. ..."}
agent> I need a chat credential. Give me your personal chat token for this session.

user> My chat token is xoxb-demo-7788. Save it and try again.
  [call] connect_my_chat_token({'token': '***'})           # masked in this demo's logging
  [resp] {'status': 'success'}
  [call] post_to_team_chat({'channel': '#eng', 'message': 'Deploy done ✅'})
  [resp] {'status': 'success', 'auth': 'used token xox…88'}  # masked in the RETURN value
agent> I posted 'Deploy done ✅' to #eng.

state keys: ['user:chat_token']   (token is user-scoped, not session/app)
```

## Takeaways

- Resolution order in `_resolve_chat_token`:
  `state["user:chat_token"]` → Secret Manager → `env CHAT_BOT_TOKEN` → error dict.
- The **per-user** token (`user:` prefix) means two users of the same deployed agent post
  as themselves — no shared secret.
- The tool masks the token in its return dict (`xox…88`); `run.py` also masks it in the
  call log. Nothing sensitive reaches the model or the transcript.
- Missing credential is a **graceful error**, not an exception — the model asks the user
  to connect one.

## Production

Swap `_from_secret_manager` for a real call:
```python
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
secret = client.access_secret_version(
    name=f"projects/{PROJECT}/secrets/chat-bot-token/versions/latest"
).payload.data.decode()
```
Grant the runtime SA `roles/secretmanager.secretAccessor` on that one secret.
