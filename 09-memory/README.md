# Module 09 — Memory (long-term recall)



An AI agent, by default, has amnesia between conversations. A "session" = one conversation window. The moment it ends and a new one starts, the agent has zero memory of you — even if you talked five minutes ago.

Real-world analogy: Think of calling a company's support lin- Session = the phone call happening right now.
- Memory = the notes a support rep writes into the CRM after the call, which the next rep reads before picking up your next call.           
Without memory, every call starts from scratch ("Who are you? What's your issue?"). With memory, the rep already knows your plan, your past complaints, your preferences. That's what all 4 examples arels of sophistication.

---

ex01 — load_memory (manual save, manual recall)

- What happens: Session A ends → code explicitly says "save  Session B starts fresh → the agent is given a load_memorytool (like a "search my notes" button) and has to decide to use it when it thinks the answer might be in the past.
- Analogy: A rep who has to remember to write notes after the to search the CRM before answering you.
- Real use case: Any system where you want fine control — e.g., only save memory after the user confirms something important, and let the model reason
  about whether it needs to look something up.

ex02 — preload_memory + auto-save callback (hands-off)

- What happens: after_agent_callback auto-saves every turn wemory auto-searches memory before the model even responds and silently stuffs relevant facts into the prompt.
- Analogy: Like a smart CRM that logs the call automaticallyen with your history the second you call — the rep doesn'tlift a finger.
- Real use case: Personal assistant apps (like the "memory" s) — you mention once "I take my coffee black," and it justknows next time, with zero explicit "remember this" instruction from you.

ex03 — custom tool combining two memory sources

- What happens: One tool (knowledge_search) queries two different pools: (1) this user's own conversation history, and (2) a separate shared "docs"
  knowledge base (pricing plans, policies) that's the same f
- Analogy: Exactly like a real support bot: it checks the official help-center FAQ and your account notes together, then answers using both — "You're
  on the Pro plan (from your notes), and Pro includes 365-dacs)."
- Real use case: This is the actual pattern behind tools like Intercom/Zendesk AI bots — merge company knowledge with personal/account context in one
  answer.

ex04 — Vertex AI Memory Bank (production-grade)

- What happens: Same auto-save pattern as ex02 (that's the a you highlighted), but instead of InMemoryMemoryService(which lives only in RAM and vanishes the second the script ends), it uses VertexAiMemoryBankService — a real Google Cloud service that permanently
  stores memories, does meaning-based (semantic) search, anddates repeated facts instead of hoarding raw transcriptsforever.
- Analogy: ex01–ex03 are like keeping notes on a sticky pad u close the office for the day. ex04 is the actual permanentfiling cabinet (cloud database) a real company would use — it survives server restarts, works across multiple servers, and scales to millions of
  users.
- Real use case: Any production AI assistant that needs to remember users across days/weeks/months and run reliably at scale — e.g., a company's
  internal AI assistant that remembers each employee's prefe

---

The progression, in one line each

1. ex01 – see the raw mechanics (explicit save, explicit sea
2. ex02 – make it automatic (no manual calls)
3. ex03 – combine personal memory + shared knowledge base (r
4. ex04 – swap the toy in-RAM storage for real persistent cloud storage (production-ready)  

> **Goal:** give an agent knowledge that outlives a single conversation — past chats and
> external corpora — via `MemoryService`, `load_memory` / `preload_memory`, and
> `search_memory`.
>
> **Docs:** [Memory](https://adk.dev/sessions/memory/)

---

## 1. Session vs Memory

| | Session / State (Module 08) | Memory (this module) |
|---|---|---|
| Scope | one conversation thread | across all of a user's conversations, or a shared corpus |
| Shape | key/value + event log | a searchable archive of past content |
| Access | automatic (history replayed every turn) | **on demand** — the agent searches it |
| Analogy | working memory | a library you consult |

You still need sessions for the current chat. Memory is what lets turn 1 of *tomorrow's*
chat know what you said today.

---

## 2. `MemoryService` implementations

| Service | Search | Persistence | Install / needs |
|---|---|---|---|
| `InMemoryMemoryService()` | keyword | none | — (dev) |
| `VertexAiMemoryBankService(project, location, agent_engine_id)` | **semantic**, auto-consolidated ("the user likes X") | managed | `google-adk[gcp]` + an Agent Engine |
| `VertexAiRagMemoryService(rag_corpus, similarity_top_k, vector_distance_threshold)` | vector similarity | RAG Engine corpus | a RAG corpus |

Wire it into the `Runner` (or CLI):
```python
runner = Runner(agent=..., app_name=..., session_service=..., memory_service=memory_service)
```
```bash
adk web agents/ --memory_service_uri "agentengine://1234567890"
```

### Interface

```python
# ingest
await memory_service.add_session_to_memory(session)                  # after a chat ends
await memory_service.add_events_to_memory(app_name=, user_id=, events=, session_id=?)  # incremental
await memory_service.add_memory(app_name=, user_id=, memories=[MemoryEntry(...)])      # Vertex Bank ONLY
                                                                     # (InMemory raises NotImplementedError)
# retrieve
resp = await memory_service.search_memory(app_name=, user_id=, query=)   # -> resp.memories
```

---

## 3. Three ways an agent uses memory

### a) `load_memory` tool — the agent decides when to look

```python
from google.adk.tools import load_memory
Agent(..., tools=[load_memory],
      instruction="Call load_memory if the answer might be in a past conversation.")
```
The model emits a `load_memory(query=...)` call; ADK searches and feeds results back.

### b) `preload_memory` tool — automatic injection every turn

```python
from google.adk.tools import preload_memory
Agent(..., tools=[preload_memory], instruction="Use what you remember about the user.")
```
Runs **before** the model each turn, searches with the user's message, injects hits into
the prompt. No explicit tool call. Best for "assistant that just knows you".

### c) `tool_context.search_memory(query)` — inside your own tool

```python
async def knowledge_search(query: str, tool_context: ToolContext) -> dict:
    resp = await tool_context.search_memory(query)
    return {"hits": [p.text for e in resp.memories for p in (e.content.parts or []) if p.text]}
```
Full control — combine sources, re-rank, filter, search a *second* memory service.

---

## 4. Saving conversations to memory

- **Manual:** `await memory_service.add_session_to_memory(completed_session)` when a chat ends.
- **Automatic:** an `after_agent_callback`:
  ```python
  async def auto_save(callback_context):
      await callback_context.add_session_to_memory()
  Agent(..., after_agent_callback=auto_save)
  ```
- **Design what to save.** Raw transcripts bloat the store and retrieve noisily.
  `VertexAiMemoryBankService` consolidates automatically (turns chatter into durable
  facts). With `InMemory`/RAG, consider summarizing before ingest, or storing only
  user-stated facts / preferences.

---

## 5. Examples

| Folder | Shows | Needs |
|---|---|---|
| `ex01_load_memory/` | capture in session A → `add_session_to_memory` → recall in session B via `load_memory` | — ✅ |
| `ex02_auto_save_preload/` | `after_agent_callback` auto-save + `preload_memory` — fully hands-off | — ✅ |
| `ex03_custom_memory_tool/` | `tool_context.search_memory` **+** a separate "docs" `MemoryService`; combines both | — ✅ |
| `ex04_vertex_memory_bank/` | `VertexAiMemoryBankService` + `VertexAiSessionService`, semantic + consolidated | an Agent Engine |

---

## 6. Production notes

- **Store cost & index freshness.** Memory Bank / RAG corpora cost money and have
  ingestion latency. Don't save every turn synchronously in the request path — queue it.
- **User-scoped isolation.** Memory is keyed by `(app_name, user_id)`. Never let one
  user's `user_id` retrieve another's. Shared corpora use a sentinel user (`"shared"`).
- **Right to be forgotten.** You must be able to purge a user's memories (DSAR/GDPR).
  Memory Bank supports deletion APIs; for RAG, delete the corpus docs.
- **Staleness & contradiction.** "I moved to Berlin" after "I live in Pune" — Memory Bank
  consolidation helps; hand-rolled stores need recency weighting or explicit updates.
- **Retrieval quality.** Keyword (`InMemory`) is a toy. Use semantic (Bank) or vector
  (RAG) in prod; tune `similarity_top_k` / `vector_distance_threshold`.
- **Prompt-injection surface.** Retrieved memory text enters the prompt. If memory can
  contain attacker-controlled content, treat it as untrusted (Module 16).

---

## 7. Exercises

1. In `ex01`, ask a question whose answer is **not** in memory — confirm the agent says
   so rather than hallucinating.
2. In `ex02`, add a contradicting fact in session 2 ("actually I take one sugar"); in
   session 3, which does the agent believe? Try it with keyword vs (if you have it) Bank.
3. In `ex03`, add a `recency` sort to `knowledge_search` and prefer conversation hits
   over doc hits for personal questions.
4. Stand up an Agent Engine, wire `ex04`, and watch Memory Bank consolidate "I'm
   vegetarian and live in Pune" into a durable preference used for a lunch suggestion.

---

## 8. Checklist

- [ ] State the session-vs-memory distinction
- [ ] Pick a `MemoryService` for dev vs prod
- [ ] Use `load_memory`, `preload_memory`, and `tool_context.search_memory`
- [ ] Save a session to memory manually and via `after_agent_callback`
- [ ] Know `InMemory.add_memory` is unsupported (use `add_events_/add_session_to_memory`)
- [ ] Name the prod concerns: cost, isolation, deletion, staleness, injection

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| `NotImplementedError: does not support direct memory writes` | `InMemoryMemoryService` — use `add_session_to_memory` / `add_events_to_memory` |
| Agent never searches memory | weak instruction; with `load_memory` tell it *when*; or switch to `preload_memory` |
| `search_memory` returns nothing for an obvious match | keyword service — phrase the query with words that appear in the stored text, or use a semantic backend |
| memory not shared across sessions | you didn't `add_session_to_memory` (or the callback isn't firing) |
| `UnicodeEncodeError` printing setup text on Windows | non-ASCII in the string; `chcp 65001` or keep it ASCII |
