# Module 04 — Built-in & Google Cloud Tools

> **Goal:** use Google's server-side tools — web search grounding, sandboxed code
> execution, Vertex AI Search RAG — and understand the **one-built-in-tool-per-agent**
> limitation and its workaround.
>
> **Docs:** [Grounding with Google Search](https://adk.dev/grounding/google_search_grounding/) ·
> [Tool limitations](https://adk.dev/tools/limitations/) ·
> [Code executors](https://adk.dev/api-reference/python/) ·
> Vertex AI Search

---

## 1. What "built-in" means

Some tools run **inside the model call on Google's servers**, not as a Python function in
your process:

| Tool | Import | Attached as | What it does |
|---|---|---|---|
| Google Search grounding | `from google.adk.tools import google_search` | `tools=[google_search]` | model issues web searches, answers are grounded, `grounding_metadata` carries sources |
| Code execution | `from google.adk.code_executors import BuiltInCodeExecutor` | `code_executor=BuiltInCodeExecutor()` | model writes Python, Google runs it in a sandbox, model uses the output |
| Vertex AI Search | `from google.adk.tools import VertexAiSearchTool` | `tools=[VertexAiSearchTool(data_store_id=...)]` | RAG over a managed index of *your* documents |
| BigQuery | `from google.adk.integrations.bigquery import BigQueryToolset` (needs `google-adk[gcp]` / `google-cloud-bigquery`) | `tools=[BigQueryToolset(...)]` | query/inspect BigQuery from natural language |

They're powerful and zero-maintenance, but they come with a constraint.

---

## 2. The limitation (memorize this)

> **On Gemini, an agent may use at most ONE built-in tool, and cannot combine a built-in
> tool with your function tools in the same agent.**

Break it and Vertex returns, at *run time* (construction succeeds):

```
400 INVALID_ARGUMENT ... Multiple tools are supported only when they are all search tools.
```

Also: built-in tools generally **can't be used inside a sub-agent** — except
`google_search` and `VertexAiSearchTool` in ADK Python.

### The workaround: one built-in per specialist, compose with `AgentTool`

```python
searcher = Agent(name="searcher", model=M, tools=[google_search], instruction="...")
coder    = Agent(name="coder",    model=M, code_executor=BuiltInCodeExecutor(), instruction="...")

root = Agent(name="analyst", model=M,
             tools=[AgentTool(agent=searcher), AgentTool(agent=coder)],
             instruction="Use `searcher` for facts, `coder` for math, combine the results.")
```

Now the root can do both — each built-in tool is isolated in its own model call.
(ADK ≥ 1.16 also exposes `bypass_multi_tools_limit=True` for `GoogleSearchTool` /
`VertexAiSearchTool` specifically.)

---

## 3. Google Search grounding — you must show citations

`event.grounding_metadata` on the search events carries:

- `web_search_queries` — the queries the model ran
- `grounding_chunks[].web.{title, uri}` — the sources
- `grounding_supports[]` — which text spans each source backs

Google's terms require displaying the search suggestions / sources to end users. Surface
them as citations. `ex01` prints them.

Grounding **reduces** hallucination, it doesn't eliminate it — the model can still
misread a source. Keep temperature low and instruct it to say when unsure.

---

## 4. Code execution — when to reach for it

Use `BuiltInCodeExecutor` when the task is *quantitative and exact*: statistics, unit
conversions, date math, parsing, small data transforms. The model writes and runs real
Python (with `numpy` etc.), so you get correct numbers instead of a confident guess.

Event parts to look for: `part.executable_code.code` and
`part.code_execution_result.{outcome, output}`.

Not for: anything with side effects, network calls, big data, or untrusted heavy compute
— use a real function tool or a proper job.

---

## 5. Examples

| Folder | Shows | Needs |
|---|---|---|
| `ex01_google_search/` | grounding + reading `grounding_metadata` | Vertex (works out of the box) |
| `ex02_code_executor/` | `BuiltInCodeExecutor`, `executable_code` / `code_execution_result` parts | Vertex |
| `ex03_combine_builtins/` | the 400 error (`--break`) and the `AgentTool` fix | Vertex |
| `ex04_vertex_ai_search/` | `VertexAiSearchTool` RAG pattern | a Vertex AI Search data store (else placeholder) |

---

## 6. Production notes

- **Cost & latency.** Grounding and code execution add model round-trips and Google-side
  compute. Budget for it; cache where you can (Module 10).
- **Quotas.** Search grounding and Vertex calls have per-project QPM limits. Running many
  agents/tests back-to-back triggers `429 RESOURCE_EXHAUSTED` — add retry/backoff
  (`generate_content_config.http_options.retry_options`) and request a quota bump.
- **Data residency & governance.** Search grounding sends the query to Google Search.
  Vertex AI Search keeps your docs in your project/region. Know which is acceptable.
- **Citations = compliance.** Persist the grounding sources with the answer for audit.
- **Least privilege.** BigQuery / Vertex AI Search tools run with the runtime service
  account — grant only the specific datasets/data stores needed.

---

## 7. Exercises

1. Ask `ex01` something time-sensitive and something timeless. Compare whether it
   searches. Tune the instruction to search more/less eagerly.
2. In `ex02`, ask for something the model *could* answer without code (e.g. "2+2") and
   something it can't (a 12-digit multiplication). Does it always run code? Force it to.
3. Run `ex03 --break`, read the exact 400. Then run the working version and trace which
   specialist handled which part.
4. Stand up a tiny Vertex AI Search data store from 2–3 PDFs, wire `ex04`, and ask a
   question answerable only from those PDFs. Confirm it refuses out-of-KB questions.

---

## 8. Checklist

- [ ] Attach `google_search` (a tool) and `BuiltInCodeExecutor` (a `code_executor=`) correctly
- [ ] State the one-built-in-per-agent rule and reproduce the 400
- [ ] Fix it with `AgentTool`-wrapped specialists
- [ ] Read `grounding_metadata` and render citations
- [ ] Read `executable_code` / `code_execution_result` from events
- [ ] Explain when `VertexAiSearchTool` beats a hand-rolled retrieval tool

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| `400 ... Multiple tools are supported only when they are all search tools` | One built-in per agent; split into `AgentTool` specialists |
| `429 RESOURCE_EXHAUSTED` / `_ResourceExhaustedError` | Vertex quota — wait, add retry/backoff, or raise the quota |
| grounding_metadata is `None` | The model didn't search that turn; strengthen the instruction |
| Code executor never runs code | Instruction too weak; say "write and run Python for any calculation" |
| `VertexAiSearchTool` → `PermissionDenied` | Grant `roles/discoveryengine.viewer` on the project; check the data store id |
| `No module named 'google.cloud'` importing BigQuery tools | `pip install "google-adk[gcp]"` (or `google-cloud-bigquery`) |
