# Example 02 — State scopes

No LLM calls — pure `SessionService`. Writes four scoped keys from **alice's session A1**,
then reads state from A1, alice's other session **A2**, and **bob's** session B1.

```powershell
python run.py
```

## Captured output

```
alice A1 (where we wrote):
  A1: {'app:banner': 'Welcome!', 'step': 'A1-only', 'user:theme': 'dark'}
alice A2 (same user, different session):
  A2: {'app:banner': 'Welcome!', 'user:theme': 'dark'}
bob B1 (different user):
  B1: {'app:banner': 'Welcome!'}
```

| Key | Scope | A1 | A2 (alice) | B1 (bob) |
|---|---|---|---|---|
| `step` | session | ✅ | — | — |
| `user:theme` | user (`user_id`) | ✅ | ✅ | — |
| `app:banner` | app (`app_name`) | ✅ | ✅ | ✅ |
| `temp:scratch` | invocation | — | — | — |

`temp:` never shows up on a later read — it's discarded when its invocation ends.
These distinctions **only exist with a persistent service**; `InMemorySessionService`
loses everything on restart regardless of prefix.
