# Example 03 — Custom memory tool (conversations + docs)

```powershell
python run.py
```

## Captured output

```
user> How long is our data retained?
  [tool] knowledge_search({'query': 'data retention period'})
  [result] {'from_docs': ['Data is retained for 30 days on Free and 365 days on Pro.'],
            'from_conversations': []}
agent> Data is retained for 30 days on the Free plan and 365 days on the Pro plan.

user> Can we use SAML single sign-on?
  [tool] knowledge_search({'query': 'SAML single sign-on'})
  [result] {'from_docs': ['SSO (SAML) is available on the Enterprise plan only.', ...],
            'from_conversations': ['Note: we are on the Pro plan.', ...]}
agent> SSO (SAML) is only available on the Enterprise plan. Based on our previous
       conversation, you are on the Pro plan, so you do not have SAML.
```

## Takeaways

```python
async def knowledge_search(query: str, tool_context: ToolContext) -> dict:
    convo = await tool_context.search_memory(query)                       # the Runner's memory
    docs  = await docs_memory.search_memory(app_name="docs", user_id="shared", query=query)
    return {"from_docs": _texts(docs), "from_conversations": _texts(convo)}
```

- `tool_context.search_memory` hits whatever `memory_service` the `Runner` has.
- A **second** `InMemoryMemoryService` holds product docs, searched directly with an
  explicit `app_name`/`user_id`.
- Second query shows the payoff: the agent fused a **doc fact** with a **memory of the
  conversation** to reach a conclusion neither source stated outright.
- Seeding the docs store: `InMemoryMemoryService` has no `add_memory`; use
  `add_events_to_memory(app_name=, user_id=, events=[Event(author="docs", content=...)])`.
