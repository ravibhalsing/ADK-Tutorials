# Example 01 — Artifacts: save / load / list / version

```powershell
python run.py
```

## Captured output

```
user> Save a note called meeting.txt that says 'sync at 3pm Tuesday'.
  [call] save_note({'name': 'meeting.txt', 'text': 'sync at 3pm Tuesday'})
agent> Saved meeting.txt. Version 0.

user> Update meeting.txt to say 'sync moved to 4pm Tuesday'.
  [call] save_note({'name': 'meeting.txt', 'text': 'sync moved to 4pm Tuesday'})
agent> Updated meeting.txt. New version 1.

user> Save a permanent note called prefs that says 'dark mode, metric units'.
  [call] save_note({'name': 'user:prefs', 'text': 'dark mode, metric units'})
agent> Saved user:prefs. Version 0.

user> What notes do I have?
  [call] list_notes({})
agent> meeting.txt and user:prefs.

--- artifact store ---
  meeting.txt      versions=[0, 1]  latest='sync moved to 4pm Tuesday'
  user:prefs       versions=[0]     latest='dark mode, metric units'
```

## Takeaways

- `save_artifact` **auto-versions**: same filename → 0, then 1, then 2. It returns the
  new version number.
- `load_artifact(filename)` = latest; `load_artifact(filename, version=0)` = a specific one.
- `"user:prefs"` is **user-scoped** — it would be visible from any of this user's
  sessions; `meeting.txt` is only in this session.
- The agent decided to use the `user:` prefix because the user said "permanent".
- Needs `Runner(..., artifact_service=InMemoryArtifactService())` — no service → `ValueError`.
