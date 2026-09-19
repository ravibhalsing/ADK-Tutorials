# Examples, Explained (No Code — Just the Concepts)

> Companion to `../WHY-FUNCTION-TOOLS.md`. Each section below matches one example
> folder and explains, in plain language: what it's actually showing, why that
> capability exists, its advantages, and where you'd use it in a real product.

---

## `ex01_function_tools/` — Turning a plain function into something the agent can use

**The scenario in the example:** a small online store assistant. It can look up a
product (by SKU or by typing part of the name, like "hub") and estimate shipping cost.

**What it's really demonstrating:** the most basic and most important idea in this
whole module — the agent doesn't "know" prices or stock. It has to *ask* by calling a
tool, read the real answer, and only then talk to the user. When the user asked for
shipping on "3 laptop stands," the agent figured out on its own that it first needed
the SKU (called the lookup tool), then used that SKU to get the shipping estimate — two
tool calls, chained, with no extra hand-holding from the developer. When the user asked
about a SKU that doesn't exist, the tool didn't crash — it handed back a polite "not
found" explanation, and the agent relayed that instead of making something up.

### Why we use it
This is the foundation everything else in the module builds on. Without this, the
"agent" is just a chatbot reciting facts it memorized during training — which for a
store means wrong prices, wrong stock, and confidently wrong answers.

### Advantages
- **Grounded, current answers** — price and stock come from the real catalog, not a guess.
- **The agent chains steps on its own** — if you describe each tool well, the model
  figures out the order (look up the product → then price shipping) without you writing
  that logic yourself.
- **Clean failure recovery** — a "not found" case becomes a helpful message instead of a
  crash or a hallucinated product.
- **Handles messy real input** — the lookup accepts a SKU *or* a rough product name,
  because that's how people actually ask.

### Real-time use cases
- E-commerce assistants (price/stock/shipping lookups — exactly this example, at scale).
- Airline/travel bots checking real fares and seat availability.
- Banking assistants reading a real account balance or transaction list.
- Any "ask a question, get a real fact back" bot: internal HR bot answering "how many
  leave days do I have left," IT bot answering "what's my ticket status," etc.

---

## `ex02_tool_context/` — Giving tools memory and control over the conversation

**The scenario in the example:** a shopping-cart assistant that (1) remembers a
nickname you tell it, even in a brand-new conversation later, (2) loads your cart and
computes the total across two tool calls in the *same* turn, and (3) can show a receipt
exactly as formatted, without letting the model "helpfully" rewrite it.

**What it's really demonstrating:** three different memory/control problems that come
up constantly in real agents:
1. **Long-term memory** — "remember my nickname forever" (`user:` prefix) — this
   survived into a completely new session for the same person.
2. **Short-term, same-turn memory** — "the cart I just loaded, so the *next* tool call
   in this same turn can use it" (`temp:` prefix) — gone the moment the turn ends.
3. **Bypassing the model's rewriting** — for the receipt, the tool's exact formatted
   output was shown to the user untouched, instead of the model paraphrasing it (which
   could subtly change numbers or formatting).

### Why we use it
A tool that can't remember anything is stuck re-fetching or re-asking every single time,
even within one request. And some outputs (receipts, legal text, exact prices,
generated code) must never be "creatively rephrased" by the model — they need to reach
the user byte-for-byte.

### Advantages
- **Personalization that survives across sessions** — the user doesn't have to
  re-introduce themselves every conversation.
- **Efficient multi-step tool use within one turn** — one tool fetches data, a second
  tool uses it, without you passing that data back and forth through the model's text.
- **Guaranteed-exact output** — no risk of the model silently altering a number, a
  formatted table, or a legal disclaimer when it "summarizes" the tool's result.
- **Clear boundaries on what's remembered and for how long** — you (the developer)
  explicitly choose per-piece-of-data whether it's session-only, user-forever, or
  just-this-instant, instead of everything being either "remembered forever" or
  "forgotten immediately."

### Real-time use cases
- Any assistant that should recognize a returning user ("Welcome back, Rav") —
  loyalty/CRM bots, support bots, personal assistants.
- Multi-step checkout or booking flows where one tool result (cart, itinerary) feeds the
  next tool in the same request.
- Anything that must show an exact, unaltered artifact to the user: invoices, receipts,
  contracts, generated reports, formatted tables, code snippets.
- Multi-tenant apps where some memory should be per-user (`user:`), some per-app-wide
  (`app:` — e.g. a shared promo code), and some just scratch space for right now
  (`temp:`).

---

## `ex03_long_running/` — Handling things that can't finish immediately

**The scenario in the example:** an employee asks for a $1200 reimbursement. The agent
doesn't (and can't) approve it itself — it creates a ticket, tells the user "awaiting
your manager Priya," and then **stops**. Sometime later — could be minutes, could be
days, and the whole process could even be shut down in between — the manager's real
decision comes in from the outside, and the agent picks the conversation back up exactly
where it left off to tell the user "approved" or "denied and why."

**What it's really demonstrating:** not every real-world action is instant. Some things
need a human's sign-off, some things take a long time to compute, some things depend on
another system replying later (an email response, a payment gateway callback, a
background job finishing). The agent needs a way to say "I've started this, I'll tell
you when it's done" instead of freezing the whole conversation waiting.

### Why we use it
If every tool had to return an answer immediately, you simply couldn't build anything
that needs human approval, waits on an external service, or runs for a long time — the
user (and your server) would just hang. This pattern lets the conversation "pause"
indefinitely and resume later without losing context.

### Advantages
- **Nothing blocks** — the app/process can even be restarted while waiting; the
  conversation state isn't lost.
- **Enables human-in-the-loop safety** — high-risk or high-value actions (payments,
  refunds, account changes, deployments) can require a real person's approval before the
  agent finishes the job, without you building a separate approval system from scratch.
- **Handles real-world delays honestly** — the user is told "this is pending," not left
  wondering if the bot is broken.
- **Same conversational agent handles both instant and slow actions** — the user
  experience stays consistent whether the answer comes back in one second or three days.

### Real-time use cases
- Expense/reimbursement approval (the exact example) — or purchase orders, discount
  approvals, refund approvals.
- IT access requests ("grant me admin access") pending a manager's or security team's
  approval.
- Anything waiting on a human reply: "email the customer and wait for their response,"
  "wait for the vendor to confirm the quote."
- Long background jobs: generating a large report, processing a large file, running a
  model training job, waiting for a payment provider's webhook.
- On-call/DevOps bots that propose a risky action (restart a production service, roll
  back a deploy) and wait for a human to confirm before actually doing it.

---

## `ex04_agent_as_tool/` — Letting one agent borrow another agent as a tool

**The scenario in the example:** a "concierge" agent handles general questions itself,
but for poems it hands the job to a specialist "poet" agent. The example runs it two
ways to show the difference:
- **As a tool (`AgentTool`)**: the concierge calls the poet like a function, gets the
  poem back, and the concierge is the one who presents it to the user (with its own
  intro line). The concierge stays in charge and can keep helping afterward.
- **As a hand-off (`sub_agents` + transfer)**: the concierge *transfers the whole
  conversation* to the poet, and the poet itself now replies directly to the user. The
  concierge is out of the picture for that turn.

**What it's really demonstrating:** two very different ways to combine specialist
agents, and they produce genuinely different behavior — who ends up "talking" to the
user, and who's in control afterward. Watching `event.author` (who authored the final
message) is literally how you can see the difference happen.

### Why we use it
As agents grow more capable, you don't want one giant agent trying to be an expert at
everything (translation, poetry, legal review, scheduling, support). It's easier to
build, test, and reason about small specialist agents and then combine them — the same
way you'd write focused functions instead of one enormous one. But you need *both*
combination styles because sometimes you want the specialist's answer folded back into a
bigger response (`AgentTool`), and sometimes you genuinely want the specialist to just
take over the conversation (`sub_agents`).

### Advantages
- **Reuse specialist agents across many "root" agents** — write the poet once, use it
  from any concierge-style agent.
- **Keeps the root agent in control (`AgentTool`)** — good when the specialist's output
  is just one ingredient in a larger answer the root is assembling.
- **Clean hand-off when appropriate (`sub_agents`)** — good when a specialist should
  genuinely own the rest of the conversation (e.g. a dedicated billing agent taking over
  a billing dispute).
- **Easier to build and maintain** — small, focused agents with narrow instructions are
  simpler to prompt-engineer and debug than one agent trying to do everything.
- **Composability** — specialist agents can themselves have their own tools, be swapped
  out, or be improved independently without touching the root agent's logic.

### Real-time use cases
- **`AgentTool` (bounded sub-task, caller stays in charge):** a customer-support agent
  that calls a "summarizer" agent to condense a long ticket history before replying; a
  writing assistant that calls a "translator" agent for one paragraph; a research agent
  that calls a "fact-checker" agent to verify one claim before including it in its
  answer.
- **`sub_agents` (full hand-off, specialist takes over):** a general support bot that
  transfers a billing dispute to a dedicated "billing agent"; a triage bot that routes a
  technical issue to a "tier-2 engineering agent"; a multi-department company bot
  ("HR," "IT," "Finance") where the right department's agent takes over once the topic
  is identified.

---

## Quick-reference: which one do I reach for?

| If you need to... | Use |
|---|---|
| Give the agent a real fact or a real action | `FunctionTool` (`ex01`) |
| Remember something across turns/sessions, pass data tool-to-tool, or show an exact unaltered result | `ToolContext` (`ex02`) |
| Handle something that needs a human's OK or takes a long time | `LongRunningFunctionTool` (`ex03`) |
| Reuse another agent for a bounded sub-task, keeping control | `AgentTool` (`ex04`) |
| Hand the whole conversation to a specialist | `sub_agents` + transfer (`ex04`, contrasted) |
