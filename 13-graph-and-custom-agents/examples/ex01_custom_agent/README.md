# Example 01 — Custom `BaseAgent`

`StoryFlow`: generate → (critic + reviser)×2 → tone-check → **regenerate from scratch if
the tone check is NEGATIVE**. That conditional restart is what plain workflow agents
can't do.

```powershell
python run.py
```

## Captured output (abridged)

```
[generator]  Perched on a rocky cliff stood a lighthouse named Beacon, who felt lonely...
[critic]     The story resolves the loneliness too quickly, lacking emotional depth.
[reviser]    ...
[critic]     It's a descriptive vignette rather than a story with a plot.
[reviser]    ...
[tone_checker] NEGATIVE
  [custom logic] tone check NEGATIVE -> regenerating from scratch
[generator]  Perched high on a rocky cliff stood Beacon, a tall lighthouse who felt very lonely...

tone verdict: NEGATIVE
final story: ...knowing his light kept everyone safe made Beacon's steady heart feel a little less alone.
```

## Takeaways

```python
class StoryFlow(BaseAgent):
    _refine: LoopAgent = PrivateAttr()          # non-field attr -> PrivateAttr

    def __init__(self, **kw):
        super().__init__(name="story_flow", sub_agents=[generator, tone_checker], **kw)
        self._refine = LoopAgent(name="refine", max_iterations=2, sub_agents=[critic, reviser])

    async def _run_async_impl(self, ctx):
        async for e in generator.run_async(ctx): yield e
        async for e in self._refine.run_async(ctx): yield e
        async for e in tone_checker.run_async(ctx): yield e
        if (ctx.session.state.get("tone") or "").upper().startswith("NEGATIVE"):
            async for e in generator.run_async(ctx): yield e
```

- Sub-agents are called with `.run_async(ctx)` and their events re-`yield`ed.
- The `if` on `ctx.session.state["tone"]` is ordinary Python — that's the whole point.
- `BaseAgent` is Pydantic: `_refine` is a `PrivateAttr`, and `generator`/`tone_checker`
  go through `super().__init__(sub_agents=...)`.
