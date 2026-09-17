# Example 01 — `OpenAPIToolset` from a live spec

A local FastAPI "Bookstore API" — its `/openapi.json` becomes three tools
(`list_books`, `get_book`, `add_book`) with zero tool code.

```powershell
python run.py                        # starts the API for you
# or, in two terminals:
python api_server.py                 # terminal 1
adk run ex01_openapi_local           # terminal 2
```

## Captured output

```
Bookstore API up on :8001

user> List the books by Kleppmann and how many are in stock.
  [api call] list_books({'author': 'Kleppmann'})
  [api resp] {'count': 1, 'books': [{'id': 2, 'title': 'Designing Data-Intensive Applications', 'in_stock': 0, ...}]}
agent> There is 1 book by Kleppmann, "Designing Data-Intensive Applications" (2017). It is out of stock.

user> Please add 'The Mythical Man-Month' by Fred Brooks, published 1975. Yes, go ahead.
  [api call] add_book({'title': 'The Mythical Man-Month', 'author': 'Fred Brooks', 'year': 1975})
  [api resp] {'id': 4, 'title': 'The Mythical Man-Month', 'in_stock': 0, ...}
agent> Added with ID 4.

user> Show me book id 99.
  [api call] get_book({'book_id': 99})
  [api resp] {'error': 'Tool get_book execution failed ...'}   # API returned 404
agent> The book with ID 99 does not exist.
```

## Takeaways

- Tool **names = `operation_id`** on each FastAPI route. Set them explicitly.
- `FastAPI(servers=[{"url": "http://localhost:8001"}])` — **required**, or the tools have
  no base URL. FastAPI doesn't add it by default.
- A 404 comes back as an error string; the model relays it. Retries are capped at 3.
- Add/remove a route → the toolset regenerates on next load. No agent changes.
