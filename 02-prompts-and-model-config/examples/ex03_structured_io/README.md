# Example 03 — Structured input & output

```powershell
python run.py           # output_schema + output_key, then input_schema
python run.py --break   # output_schema + tools on one agent — see what happens
```

## Captured output

```
=== 1. output_schema + output_key ===
  final response text : {"vendor": "Acme Cloud Ltd.", "total": 990, "currency": "EUR", "line_items": 3}
  session.state['invoice'] : {"vendor": "Acme Cloud Ltd.", "total": 990.0, "currency": "EUR", "line_items": 3}
  type in state : dict

=== 2. input_schema (message must be conforming JSON) ===
  input  {"name": "Ravindra", "language": "Marathi"}
  output नमस्कार, रवींद्र!

--- run.py --break ---
  construction: OK
  run: OK -> {"vendor": "Foo Inc", "total": 5, "currency": "USD", "line_items": 1}
  Lesson: don't rely on it — split gather-with-tools and format-to-schema.
```

## Takeaways

- `output_schema=Invoice` → the model must return JSON matching `Invoice`; ADK parses and
  **validates** it. Note `total` became `990.0` (float coercion by Pydantic).
- `output_key="invoice"` → the parsed **dict** lands in `session.state["invoice"]`, ready
  for the next agent in a pipeline (Module 11) or a downstream tool.
- `input_schema=GreetRequest` → the incoming user message must be JSON conforming to the
  model. Good for programmatic / agent-to-agent calls; not for free-text chat.
- `--break`: on ADK 2.8 + Gemini 2.5 this happens to work, but support is model/version
  dependent. Keep schema-formatting agents pure.
