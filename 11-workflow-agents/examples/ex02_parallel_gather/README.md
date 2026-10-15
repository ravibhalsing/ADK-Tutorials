# Example 02 — `ParallelAgent` fan-out + gather

```powershell
python run.py
```

## Captured output (abridged)

```
===== solar_researcher (6.9s) =====   * solar costs down >90% in a decade ...
===== wind_researcher (7.7s) =====    * wind costs down >70% ...
===== hydro_researcher (8.8s) =====   * high upfront capex, very low opex ...
===== synthesizer (16.0s) =====
Both solar and wind have seen dramatic cost reductions... Hydro presents a different
cost profile: high upfront capital, among the lowest operational costs once built.

total wall time: 16.0s  (3 researchers ran concurrently)
```

## Takeaways

- The 3 researchers finished at **6.9 / 7.7 / 8.8s** — concurrent, not 6.9+7.7+8.8.
- Structure: `SequentialAgent([ ParallelAgent([r1, r2, r3]), synthesizer ])`.
- Branches are isolated: `wind_researcher` can't see `solar`'s output. They only meet
  through the `output_key`s (`solar`, `wind`, `hydro`) that the synthesizer's instruction
  reads.
- If a branch might fail, guard the synthesizer with `{solar?}` and handle the gap.
