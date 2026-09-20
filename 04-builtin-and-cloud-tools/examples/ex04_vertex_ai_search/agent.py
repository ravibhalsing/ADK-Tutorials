"""Module 04 · Example 4 — VertexAiSearchTool (managed RAG).

⚠️ This needs a Vertex AI Search *data store* you own. Create one:
   Console → AI Applications → Data Stores → Create (import PDFs / a website / BigQuery),
   then copy its full resource id into .env as DATASTORE_ID:
   projects/<num>/locations/<loc>/collections/default_collection/dataStores/<id>

Then:  adk run ex04_vertex_ai_search

If DATASTORE_ID is unset, this module falls back to explaining the pattern only.
"""

from __future__ import annotations

import os

from google.adk.agents import Agent

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
DATASTORE_ID = os.environ.get("DATASTORE_ID", "").strip()

if DATASTORE_ID:
    from google.adk.tools import VertexAiSearchTool

    search_tool = VertexAiSearchTool(data_store_id=DATASTORE_ID)
    root_agent = Agent(
        name="kb_agent",
        model=MODEL,
        description="Answers questions from the company knowledge base.",
        instruction=(
            "Answer ONLY from the knowledge base via the search tool. "
            "If the answer isn't in the retrieved passages, say you don't know. "
            "Cite the document titles you used."
        ),
        tools=[search_tool],
    )
else:
    # Placeholder so `adk run` still loads the package with a clear message.
    root_agent = Agent(
        name="kb_agent_unconfigured",
        model=MODEL,
        instruction=(
            "Tell the user: this example needs a Vertex AI Search data store. "
            "Set DATASTORE_ID in .env (see agent.py header) to enable real RAG."
        ),
    )
