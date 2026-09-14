# Example 04 — `VertexAiSearchTool` (managed RAG)

**Needs a Vertex AI Search data store** — a managed index over your documents. Without
one, `agent.py` loads a placeholder agent that just explains this.

## The pattern

```python
from google.adk.tools import VertexAiSearchTool

search_tool = VertexAiSearchTool(data_store_id=
    "projects/123/locations/global/collections/default_collection/dataStores/my-kb")

kb_agent = Agent(
    name="kb_agent", model=MODEL,
    instruction="Answer ONLY from the search tool's passages. Cite document titles. "
                "Say 'I don't know' if it's not there.",
    tools=[search_tool],
)
```

## Set it up

1. Google Cloud Console → **AI Applications** → **Data Stores** → **Create data store**.
2. Source: upload PDFs, point at a website, or connect BigQuery / Cloud Storage.
3. Wait for indexing. Copy the full data store resource id.
4. Put it in `.env`:
   ```
   DATASTORE_ID=projects/<num>/locations/<loc>/collections/default_collection/dataStores/<id>
   ```
5. `adk run ex04_vertex_ai_search`

## Why managed RAG vs a hand-rolled tool

| | `VertexAiSearchTool` | your own `search_docs()` function tool |
|---|---|---|
| Indexing, chunking, embeddings | managed by Google | you build + maintain it |
| Freshness | scheduled re-crawl / re-import | your job |
| Grounding metadata / citations | provided | you assemble |
| Control over retrieval | limited | total |
| When | company KB, docs site, support content | custom stores, hybrid search, niche ranking |

`VertexAiSearchTool` is one of the two built-in tools (with `google_search`) that ADK
Python *can* use inside a sub-agent, and it supports `bypass_multi_tools_limit=True`.

Deeper RAG (Vertex RAG Engine, custom retrievers) is covered alongside Memory in
Module 09.
