"""Module 06 · Example 1 — OpenAPIToolset from a live spec.

Every operation in the Bookstore API's OpenAPI doc becomes a tool automatically:
  list_books, get_book, add_book  (from the operation_id of each route).

Start api_server.py first, then:
    adk run ex01_openapi_local
    python run.py                 # starts the API for you
"""

from __future__ import annotations

import os
import urllib.request

from google.adk.agents import Agent
from google.adk.tools.openapi_tool import OpenAPIToolset

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
BASE_URL = os.environ.get("BOOKSTORE_URL", "http://localhost:8001")


def _load_spec() -> str:
    with urllib.request.urlopen(f"{BASE_URL}/openapi.json", timeout=5) as r:
        return r.read().decode()


try:
    _spec = _load_spec()
    bookstore_tools = OpenAPIToolset(spec_str=_spec, spec_str_type="json")
    _tools = [bookstore_tools]
    _note = ""
except Exception as e:  # noqa: BLE001 — server not running yet
    _tools = []
    _note = f"\n\n(The Bookstore API is not reachable at {BASE_URL}: {e}. Start api_server.py.)"


root_agent = Agent(
    name="bookstore_agent",
    model=MODEL,
    description="Manages a bookstore catalog through its REST API.",
    instruction=(
        "You manage a bookstore via its API tools.\n"
        "- `list_books` returns every book with its `in_stock` count; it takes an optional "
        "`author` filter. Use it for any 'what books / how many / in stock' question.\n"
        "- `get_book` fetches one book by id (404 if missing — just say it doesn't exist).\n"
        "- `add_book` adds a book. Do it when the user asks; report the new id.\n"
        "- Always call a tool; never answer catalog questions from memory." + _note
    ),
    tools=_tools,
)
