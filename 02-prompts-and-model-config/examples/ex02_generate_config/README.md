# Example 02 — `generate_content_config`

```powershell
python run.py
```

## Captured output

```
=== 1. temperature 0.0 (x4) — near-identical ===
  1: Olympus Perk
  2: Olympus Perk
  3: Olympus Perk
  4: Olympus Perk

=== 1. temperature 1.0 (x4) — variety ===
  1: Crimson Cup
  2: The Red Eye
  3: Olympus Brew
  4: Ares Brew

=== 2. max_output_tokens=40 — truncated mid-sentence ===
  Nuclear reactors are devices that initiate and control a sustained nuclear chain
  reaction. They are primarily used for generating electricity... Here's a breakdown of

=== 3. stop_sequences=['5'] — halts before emitting '5' ===
  '1\n2\n3\n4'
```

## Takeaways

- **`temperature=0.0`** makes output *stable* (not guaranteed byte-identical, but here it
  was). Use it for extraction, routing, classification, tests.
- **`temperature=1.0`** gives you variety — naming, brainstorming, drafting.
- **`max_output_tokens`** is a hard stop. The response just ends. Always set it in
  production to bound latency and cost.
- ⚠️ On Gemini **2.5 thinking models**, `max_output_tokens` also has to cover the
  *thinking* tokens. Too small a cap → the model spends the whole budget thinking and
  returns **empty text**. This example passes `ThinkingConfig(thinking_budget=0)` to the
  capped/stopper agents to get a clean demo. (More on thinking in `../ex04_planner_thinking`.)
- **`stop_sequences`** halt generation the moment the model would produce that literal.
  Handy with custom output delimiters.
