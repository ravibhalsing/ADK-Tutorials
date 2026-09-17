"""A tiny local REST API (FastAPI) for the OpenAPI-tools example.

Start it in its own terminal:
    python api_server.py            # http://localhost:8001  (docs at /docs)

`agent.py` reads http://localhost:8001/openapi.json and turns every operation
into a tool automatically.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# `servers` MUST be in the spec — OpenAPIToolset reads the base URL from here.
app = FastAPI(
    title="Bookstore API",
    version="1.0.0",
    servers=[{"url": "http://localhost:8001", "description": "local"}],
)

_BOOKS: dict[int, dict] = {
    1: {"id": 1, "title": "The Pragmatic Programmer", "author": "Hunt & Thomas", "year": 1999, "in_stock": 3},
    2: {"id": 2, "title": "Designing Data-Intensive Applications", "author": "Kleppmann", "year": 2017, "in_stock": 0},
    3: {"id": 3, "title": "A Philosophy of Software Design", "author": "Ousterhout", "year": 2018, "in_stock": 7},
}
_next_id = 4


class BookIn(BaseModel):
    title: str
    author: str
    year: int


@app.get("/books", operation_id="list_books", summary="List all books, optionally filtered by author")
def list_books(author: str | None = Query(default=None, description="Filter by (partial) author name")):
    items = list(_BOOKS.values())
    if author:
        items = [b for b in items if author.lower() in b["author"].lower()]
    return {"count": len(items), "books": items}


@app.get("/books/{book_id}", operation_id="get_book", summary="Get a single book by id")
def get_book(book_id: int):
    if book_id not in _BOOKS:
        raise HTTPException(status_code=404, detail=f"No book with id {book_id}")
    return _BOOKS[book_id]


@app.post("/books", operation_id="add_book", summary="Add a new book to the catalog")
def add_book(book: BookIn):
    global _next_id
    rec = {"id": _next_id, **book.model_dump(), "in_stock": 0}
    _BOOKS[_next_id] = rec
    _next_id += 1
    return rec


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
