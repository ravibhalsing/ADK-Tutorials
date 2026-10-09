# Example 03 — Context compaction

`App(events_compaction_config=EventsCompactionConfig(compaction_interval=3, overlap_size=1))`
— after every 3 events, older turns get summarized.

```powershell
python run.py
```

## Captured output (abridged)

```
user> My name is Priya and I'm planning a trip to Kyoto.       agent> ...
user> I'll be there for 5 days in April.                        agent> ...
user> I'm mostly interested in temples and gardens.             agent> ...
user> I don't eat meat.                                         agent> ...
user> What's my name and how long is my trip?
agent> Your name is Priya and your trip is 5 days long.         <-- still correct after compaction
user> Suggest one thing to do that fits my interests and diet.
agent> Visit Ryoan-ji Zen temple and its rock garden; I can suggest vegetarian dining nearby.

--- stored session: 14 events ---
  # 7 user  ''  <-- COMPACTION SUMMARY
       compacted_content: "...Priya will be visiting Kyoto for 5 days in April. Her
                           primary interests ... are temples and gardens..."
  #14 user  ''  <-- COMPACTION SUMMARY
       compacted_content: "...The user is planning a trip to Kyoto, is interested in
                           temples and gardens, and follows a vegetarian diet. Their
                           name is Priya and their trip is 5 days long..."
```

## Takeaways

- Compaction produces **new events** in the log (`author=user`, empty content) carrying
  `event.actions.compaction` = `{start_timestamp, end_timestamp, compacted_content}`.
- Original events stay in `session.events`; the **model** is fed the summary instead of
  the raw turns, so the window stops growing.
- The summary preserved the salient facts — the agent answered a question about turn 1
  correctly at turn 5.
- Each compaction = one extra LLM call. Tune `compaction_interval` (or use
  `token_threshold`) so it's not every turn; set a cheap `summarizer` model for prod.
