# Example 01 — `SequentialAgent` pipeline

spec → **writer** (`draft`) → **reviewer** (`review`) → **refactor** (`final`)

```powershell
python run.py
```

## Captured output (abridged)

```
===== writer =====
def parse_hhmm_to_minutes(hhmm_str: str) -> int:
    ...
    time_pattern = re.compile(r"^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$")
    match = time_pattern.match(hhmm_str)
    ...

===== reviewer =====
*  Redundant Regex Compilation: re.compile runs on every call; compile once at module level.

===== refactor =====
# Compile the regular expression once at the module level for efficiency.
_TIME_PATTERN = re.compile(r"^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$")
def parse_hhmm_to_minutes(hhmm_str: str) -> int:
    ...

state keys after pipeline: ['spec', 'draft', 'review', 'final']
```

## Takeaways

- `SequentialAgent(sub_agents=[writer, reviewer, refactor])` runs them in that exact order.
- Data threading is just state: `writer` sets `output_key="draft"`, `reviewer`'s
  instruction contains `{draft}`, `refactor`'s contains `{draft}` and `{review}`.
- The initial `spec` was seeded via `create_session(state={"spec": ...})`.
- Deprecation notice suppressed in `run.py` — see module README (`Workflow` is the successor).
