# Example 02 — `ToolContext`

```powershell
python run.py
```

## Captured output

```
user> Call me Rav.
  [call] set_nickname({'nickname': 'Rav'})           # writes state["user:nickname"]
agent> Hello Rav. I will call you Rav from now on.

user> What's my cart total?
  [call] load_cart({})                                # writes state["temp:cart"]
  [call] cart_total({})                               # reads state["temp:cart"]
agent> Rav, your cart total is 158 USD.

user> Show me the receipt.
  [call] load_cart({})
  [call] raw_receipt({})                              # sets actions.skip_summarization
agent> (verbatim tool result) RECEIPT
 1 x keyboard      89.00
 2 x hub           69.00

user> Hi again!                                       # NEW session, same user_id
agent> Hi Rav! How can I help you today?              # {user:nickname?} still resolved

session-1 state keys: ['user:nickname']
```

## Takeaways

| Feature | What you saw |
|---|---|
| `state["user:nickname"] = ...` | survived into a **new session** for the same `user_id` |
| `{user:nickname?}` in the instruction | reads `user:`-scoped state (prefix included in the placeholder) |
| `state["temp:cart"]` | written by `load_cart`, read by `cart_total`, **gone** after the turn — not in `session.state` |
| `tool_context.actions.skip_summarization = True` | the model did **not** reword the receipt; the raw tool result became the answer |

State prefixes: `(none)` = this session · `user:` = all of this user's sessions ·
`app:` = every user · `temp:` = this invocation only. Persistence depends on the
`SessionService` (Module 08) — `InMemory` here means everything is lost on restart.
