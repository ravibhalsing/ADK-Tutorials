# Example 01 — Instruction styles

One question ("Why is the sky blue?"), three ways to write the instruction.

```powershell
python run.py
```

## What it does

| Agent | `instruction` | State it reads |
|---|---|---|
| `static` | fixed string | — |
| `templated` | `"You are {persona}. ... connect it to {topic?} ..."` | `persona` (required), `topic` (optional) |
| `provider` | callable branching on `state["level"]` | `level` = child / expert / adult |

State is set per call via `create_session(state=...)`.

## Captured output (abridged)

```
static (no state):
  The sky is blue because sunlight is scattered by molecules in the atmosphere,
  with shorter blue wavelengths scattered more than longer red ones.

templated (persona="a poetic science writer", topic="the colour of sunsets"):
  Tiny air molecules scatter the sun's blue light most... At sunset, this blue
  light has scattered away, letting fiery reds and oranges blaze forth.

templated (persona="a blunt engineer", topic absent -> {topic?} omitted):
  Rayleigh scattering. Blue light's shorter wavelength scatters more across the
  atmosphere...

provider (state.level = child):
  Imagine sunlight is like a crayon box with all colors! The tiny air bits ...
  bounce just the blue crayon color everywhere.

provider (state.level = expert):
  ...predominantly governed by ... Rayleigh scattering ...
```

## Notes

- `{topic?}` with `topic` missing → the placeholder is dropped, no error. Try `{topic}`
  (no `?`) with `topic` absent and you'll get a `KeyError` when the request is built.
- The provider is just Python — put branching, list formatting, or date math there.
- The `AsyncModels ... AFC ... not recommended` line is a harmless `google-genai` nag
  (no tools here); ignore it.
