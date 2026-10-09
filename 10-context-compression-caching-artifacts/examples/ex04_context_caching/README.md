# Example 04 — Model context caching

`App(context_cache_config=ContextCacheConfig(min_tokens=1024, ttl_seconds=600, cache_intervals=10))`
+ a ~7,000-token static instruction (a fake travel-policy manual).

```powershell
python run.py
```

## Captured output (real)

```
user> What's the domestic meal cap?
  usage: prompt=6861 cached=6119 output=18
  cache_metadata: Fingerprint-only: 0 contents, fingerprint=c0e4875b...      <-- cache being created
agent> Meals are capped at 60 USD/day domestic. (Section 1)

user> How long do I have to submit receipts?
  usage: prompt=6888 cached=6880 output=16                                    <-- ~99% from cache
  cache_metadata: Cache 4651164138041507840: used 1 invocations, cached 2 contents, expires in 9.7min
agent> Employees must submit receipts within 30 days. (Section 1)
```

(A 3rd turn hit Vertex `429 RESOURCE_EXHAUSTED` — quota, not a caching problem. The
script catches it.)

## Takeaways

- Turn 1: ADK creates the cache from the stable prefix (system instruction + tools).
  `cache_metadata` says "Fingerprint-only" while it's forming.
- Turn 2: `cached_content_token_count` ≈ `prompt_token_count` — nearly the entire prompt
  is served from cache. `cache_metadata` shows the live cache id, use count, and TTL.
- You pay full price for cached tokens **once**, then a large discount on reuse.
- **What breaks it:** prompt below `min_tokens`, the prefix changing (templated
  `{state}` in the instruction, tool-set changes, an agent transfer), TTL expiry, or
  `cache_intervals` used up. Keep dynamic content in the turn message, not the system
  instruction.
- Read it in your own code: `event.usage_metadata.cached_content_token_count` and
  `event.cache_metadata`.
