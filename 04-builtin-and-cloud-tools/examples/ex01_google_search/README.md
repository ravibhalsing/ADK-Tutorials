# Example 01 — Google Search grounding

```powershell
adk run ex01_google_search      # from …/04-builtin-and-cloud-tools/examples
python run.py                   # prints grounding metadata
```

## Captured output

```
user> Who won the most recent FIFA World Cup and what was the final score?

  [grounding] queries: ['most recent FIFA World Cup winner and final score']
  [source] topendsports.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZ...
  [source] britannica.com   — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZ...
  [source] fifa.com         — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZ...
  [source] wikipedia.org    — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZ...

agent> ... won by ... , who defeated ... in the final. ...
```

## Takeaways

- `tools=[google_search]` — nothing else needed. The model decides when to search.
- `event.grounding_metadata` gives you `web_search_queries` and
  `grounding_chunks[].web.{title, uri}`. **Render these as citations** — Google's terms
  require showing sources/search suggestions to end users.
- The source URIs are `vertexaisearch.cloud.google.com/grounding-api-redirect/...`
  redirects, not direct links — that's expected.
- Grounding lowers hallucination but doesn't kill it. Low temperature + "say if unsure".
- `google_search` is a **built-in** tool: it can't share an agent with other tools
  (see `../ex03_combine_builtins`).
