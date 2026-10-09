# Module 10 — Context Engineering: Compaction, Caching & Artifacts

The big picture

This whole tutorial folder is about "what happens to a chatbot's memory when conversations get long". Google's ADK (Agent Development Kit) gives you 3 separate tools to deal with that: Artifacts (files), Compaction (summarizing old chat), and Caching (reusing prompts to save money). Each example isolates one concept.

---

Example 01 — Artifacts basics: "Save this as a file, not as chat text"

Real-life analogy: Instead of an assistant repeating "your meeting is at 3pm" in every reply forever, they write it on a sticky note (a file) that anyone can look up later.

- save_note / list_notes are just tools the LLM can call — like giving the AI a filing cabinet instead of relying on it remembering things in its head.
- Versioning: saving meeting.txt twice doesn't overwrite it — it keeps version 0 and version 1, like "Document (1).docx", "Document (2).docx" but automatic.
- Scope (user: prefix): a normal file only exists in this conversation. A user:-prefixed file follows you across all your chats — like the difference between a note stuck to one desk vs. a note in your phone's cloud notes app that syncs everywhere.

Real use case: an AI travel agent that remembers your seat preference (user:prefs) across every future trip you book, but keeps this specific itinerary (meeting.txt) only for this conversation.

---

Example 02 — Files in/out: "Look at this image, remember what you saw"

Real-life analogy: You show a coworker a photo, they jot down a one-line description on a sticky note, then walk away. Later you ask "what was in that photo again?" — they don't need the photo back, they just read their sticky note.

- Sending an image to the model is just adding an extra Part to the message — same as adding an attachment to an email.
- The agent describes the image, then saves the description as an artifact (not the raw image — that'd be wasteful to keep re-sending).
- LoadArtifactsTool lets the agent, in a later turn (when the image is no longer in the conversation), fetch that saved caption back.

Real use case: a customer-support bot where a user uploads a screenshot of an error. The bot analyzes it once, stores the finding, and can reference it 10 messages later without needing the image resent or kept in the active context (which would cost tokens every single turn).

---

Example 03 — Context compaction: "Summarize old chat so it doesn't get too long/expensive"

Real-life analogy: Think of a long group chat. Instead of scrolling back 500 messages every time someone joins, someone posts a "TL;DR of everything so far" pinned message. New replies only need to reference the pinned summary, not the whole history.

- Every LLM call re-sends the entire conversation so far (that's how these models work — no persistent memory between calls). The longer the chat, the more tokens (=money and slower responses) every single turn costs.
- EventsCompactionConfig(compaction_interval=3) says: "after every 3 messages, auto-summarize the older ones into a condensed version."
- The original messages are not deleted (still in session.events for your records/audit), but the model only sees the summary going forward — so cost/context size stays flat instead of growing forever.
- Proof it works: the bot correctly recalled "Priya, 5-day Kyoto trip" even after that raw message got compacted away — because the summary preserved the key facts.

Real use case: a long customer support chat or a coding agent session that runs for hours — without compaction, each new message would cost more than the last and eventually hit the model's context limit. This is literally how Claude Code itself keeps working in long sessions (you even saw that behavior mentioned in your system prompt: "the conversation is summarized when it grows long").

---

Example 04 — Context caching: "Don't pay full price to re-read the same instructions every time"

Real-life analogy: If you're a lawyer answering many client questions about the same 50-page contract, you don't re-read the whole contract fresh every single time — you keep it open on your desk (cached in your head) and just check the new question against it. First read = full time cost, every read after = nearly free/instant.

- Here the agent has a giant static system instruction (a fake ~7,000-token "company travel policy"). That text never changes between turns.
- ContextCacheConfig tells Gemini: "cache this stable prefix, and reuse it instead of reprocessing it every call."
- Turn 1: pays full price, cache gets built (cached=6119 out of prompt=6861 — note even turn 1 shows caching kicking in as it forms).
- Turn 2: prompt=6888, cached=6880 — almost the entire prompt was served from cache, meaning you're billed at a steep discount for those tokens instead of full price.
- This is different from compaction — compaction shrinks conversation history; caching avoids re-billing/re-processing unchanging content (system prompt, tool definitions, big reference docs).
- What breaks it: if any part of that "stable" content changes turn-to-turn (e.g., a {username} template inside the instruction), the cache is invalidated and you're back to full price.

Real use case: a customer support bot for one product with a long product manual baked into its instructions — caching means you pay full price for that manual once, then near-free reuse for every customer question afterward, instead of re-paying for those same 7,000 tokens on every single message.

---

How the four connect

┌────────────────────────────────────────────────────────────────┬───────────────────────┬──────────────────────────────────────────────────────────────┐
│                            Problem                             │         Tool          │                        What it solves                        │
├────────────────────────────────────────────────────────────────┼───────────────────────┼──────────────────────────────────────────────────────────────┤
│ "I need to remember a fact/file across turns or across all     │ Artifacts (ex01,      │ Persistent storage, not re-sent every turn                   │
│ chats"                                                         │ ex02)                 │                                                              │
├────────────────────────────────────────────────────────────────┼───────────────────────┼──────────────────────────────────────────────────────────────┤
│ "The conversation is getting too long/expensive"               │ Compaction (ex03)     │ Shrinks history by summarizing old turns                     │
├────────────────────────────────────────────────────────────────┼───────────────────────┼──────────────────────────────────────────────────────────────┤
│ "My instructions/docs are huge but never change"               │ Caching (ex04)        │ Avoids re-paying to reprocess the unchanging part of the     │
│                                                                │                       │ prompt                                                       │
└────────────────────────────────────────────────────────────────┴───────────────────────┴──────────────────────────────────────────────────────────────┘

Artifacts = external filing cabinet. Compaction = compressing old conversation. Caching = not re-billing for stuff that hasn't changed. All three exist because LLMs have no built-in memory — every call is stateless and re-sends everything, so ADK gives you ways to keep that "everything" small and cheap.

Regarding the line you highlighted, LoadArtifactsTool (ex02 line 56) is the specific tool that lets the model say "let me go check the sticky note I wrote earlier" instead of needing that information handed to it again in the current message.


> **Goal:** keep the prompt small and cheap as conversations grow (**compaction**),
> avoid re-sending a large stable prefix every turn (**context caching**), and handle
> **files** (images, PDFs, generated reports) as versioned **artifacts**.
>
> **Docs:** [Compaction](https://adk.dev/context/compaction/) ·
> [Caching](https://adk.dev/context/caching/) ·
> [Artifacts](https://adk.dev/artifacts/)
>
> Compaction & caching are configured on the **`App`** object, not the agent:
> `Runner(app=App(name=, root_agent=, events_compaction_config=, context_cache_config=), session_service=...)`

---

## 1. Context compaction — summarize old history

Every turn, ADK sends the conversation history to the model. Long chats → big prompts →
slow + expensive. **Compaction** replaces stretches of old events with an LLM-written
summary.

```python
from google.adk.apps.app import App, EventsCompactionConfig

# sliding window: summarize after every N events, keep some overlap
App(name=..., root_agent=agent,
    events_compaction_config=EventsCompactionConfig(compaction_interval=3, overlap_size=1))

# token-based (takes priority if both set): summarize when the window exceeds a threshold
EventsCompactionConfig(token_threshold=4000, event_retention_size=5)
```

| Param | Strategy | Meaning |
|---|---|---|
| `compaction_interval` | sliding window | summarize after this many completed events |
| `overlap_size` | sliding window | already-summarized events kept for continuity |
| `token_threshold` | token-based | summarize once the context exceeds this |
| `event_retention_size` | token-based | recent events left untouched |
| `summarizer` | both | custom `LlmEventSummarizer` (model + prompt) |

The summary lands in the event log as an event whose `actions.compaction` holds
`start_timestamp`, `end_timestamp`, `compacted_content` (see `ex03`). Old events aren't
deleted — the *model* just sees the summary instead.

**Interacts with memory (Module 09):** compaction shrinks the *current* window; memory is
cross-session recall. Use both for long-running assistants.

---

## 2. Model context caching — don't re-send the stable prefix

If your agent has a huge system instruction / tool set / document prefix that's identical
every turn, caching stores it on Gemini's side and you pay a fraction for the reused
tokens.

```python
from google.adk.agents.context_cache_config import ContextCacheConfig

App(name=..., root_agent=agent,
    context_cache_config=ContextCacheConfig(
        min_tokens=2048,     # only cache requests at least this big (default 0)
        ttl_seconds=600,     # cache lifetime (default 1800)
        cache_intervals=5,   # reuse the same cache at most N times (default 10)
    ))
```

- Works on **Gemini 2.0+**. The stable prefix = system instruction + tools + the
  unchanging head of the conversation.
- `ex04` output (real): turn 1 `prompt=6861 cached=6119` (cache being created,
  `cache_metadata: Fingerprint-only`); turn 2 `prompt=6888 cached=6880` — **~99% of the
  prompt served from cache**, `cache_metadata: Cache <id>: used 1 invocations, cached 2
  contents, expires in 9.7min`.
- Read cache activity from `event.usage_metadata.cached_content_token_count` and
  `event.cache_metadata`.
- Invalidation: TTL expiry, `cache_intervals` exhausted, or the prefix changing (a
  different instruction / tool set — e.g. an agent transfer, Module 03).

**Keep the cacheable part actually stable.** Templated `{state}` in the instruction, or
per-user text, breaks the prefix. Put dynamic bits in the turn message, not the system
instruction.

---

## 3. Artifacts — files, versioned

Text goes in `state`. **Binary / files** (images, PDFs, audio, CSVs, generated docs) go
in artifacts: named, versioned blobs tied to a session or a user.

```python
from google.adk.artifacts import InMemoryArtifactService, GcsArtifactService
from google.genai import types

runner = Runner(agent=..., app_name=..., session_service=...,
                artifact_service=InMemoryArtifactService())          # dev
#               artifact_service=GcsArtifactService(bucket_name="my-adk-artifacts")   # prod

# in a tool / callback (needs ToolContext / CallbackContext):
part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
version = await tool_context.save_artifact(filename="report.pdf", artifact=part)   # -> 0, then 1, 2…
latest  = await tool_context.load_artifact(filename="report.pdf")                  # newest
v0      = await tool_context.load_artifact(filename="report.pdf", version=0)
names   = await tool_context.list_artifacts()
```

| Feature | Detail |
|---|---|
| **Versioning** | automatic; `save_artifact` returns the new version (0-indexed); `load_artifact()` = latest |
| **Session scope** | `"report.pdf"` — tied to `app/user/session` |
| **User scope** | `"user:settings.json"` — tied to `app/user`, visible from any session; keeps the `user:` prefix when listed |
| **Format** | `types.Part` with `inline_data` (`Blob(data=bytes, mime_type=...)`). Always set a correct MIME type |
| **Model access** | `LoadArtifactsTool()` lets the model choose which artifacts to load before answering |
| **Backends** | `InMemoryArtifactService` (dev, RAM), `GcsArtifactService(bucket_name=)` (prod, ADC) |

Files uploaded by the user arrive as extra `types.Part`s in the message (see `ex02`);
`RunConfig(save_input_blobs_as_artifacts=True)` auto-saves them.

---

## 4. Examples

| Folder | Shows |
|---|---|
| `ex01_artifacts_basics/` | `save/load/list` via `ToolContext`; versioning (v0→v1); session vs `user:` scope |
| `ex02_artifacts_files/` | upload an image → multimodal describe → `save_artifact` → `LoadArtifactsTool` recall |
| `ex03_context_compaction/` | `EventsCompactionConfig` sliding window; the compaction-summary events in history |
| `ex04_context_caching/` | `ContextCacheConfig` + a big static instruction; ~99% cache hit on turn 2 |

---

## 5. Production notes

- **GCS lifecycle.** `GcsArtifactService` writes one object per version — set a bucket
  lifecycle rule to expire old versions, or `delete_artifact` explicitly. Use signed URLs
  to hand files to clients (Module 21); the `adk web` sandbox blocks direct downloads.
- **Artifact size.** `InMemoryArtifactService` holds everything in RAM. Big files →
  `GcsArtifactService` always; consider a size cap in your save tool.
- **Cache economics.** Caching has its own (small) storage cost and a creation call.
  Worth it when the stable prefix is large and reused often; not for short prompts. Watch
  the hit rate (`cached_content_token_count / prompt_token_count`) in your metrics.
- **Compaction cost.** Each compaction is an extra LLM call (the summarizer). Tune the
  interval so you're not summarizing every turn; use a cheap model for the summarizer.
- **PII.** Summaries and artifacts can contain personal data — same retention/deletion
  rules as sessions (Module 08).
- **Transfers defeat caching.** In multi-agent trees, each transfer swaps the
  instruction+tools, so the cache prefix changes. Set `context_cache_config` on the App
  and keep agent instructions as stable as you can.

---

## 6. Exercises

1. In `ex03`, switch to `token_threshold=1500` and feed a long paste; confirm token-based
   compaction fires instead of the interval.
2. In `ex04`, make the instruction templated (`{topic}` from state) and re-run — does the
   cache still hit? Explain.
3. In `ex01`, save `report.pdf` five times, then `load_artifact(version=2)` and diff
   against latest.
4. Wire `GcsArtifactService(bucket_name=...)` (create a bucket, grant your ADC
   `roles/storage.objectAdmin`) and confirm artifacts survive a restart.
5. Add `RunConfig(save_input_blobs_as_artifacts=True)` to `ex02` and check the uploaded
   PNG shows up in `list_artifacts()` automatically.

---

## 7. Checklist

- [ ] Configure compaction (sliding-window and token-based) on an `App`
- [ ] Find the compaction summary in the event log (`actions.compaction`)
- [ ] Configure `ContextCacheConfig` and read `cached_content_token_count` / `cache_metadata`
- [ ] Explain what breaks the cache prefix
- [ ] `save`/`load`/`list` artifacts and reason about versioning
- [ ] Choose session vs `user:` artifact scope; `InMemory` vs `Gcs` backend
- [ ] Accept an uploaded file and let the model load artifacts on demand

---

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `ValueError: artifact_service ... not configured` | pass `artifact_service=` to the `Runner` |
| `load_artifact` returns `None` | that filename/version doesn't exist — check `list_artifacts()` / `list_versions()` |
| cache never hits (`cached=0`) | prompt below `min_tokens`, or the prefix changes each turn (templated instruction, tool changes, transfer), or model < Gemini 2.0 |
| compaction never fires | `compaction_interval` higher than your turn count; or you set only `token_threshold` and never exceed it |
| `cache_metadata` shows "Fingerprint-only" forever | still within the first use / creating the cache; check again next turn |
| big artifacts slow / OOM | move to `GcsArtifactService`; cap sizes in your save tool |
