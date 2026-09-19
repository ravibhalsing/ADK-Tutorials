# Example 03 — `LongRunningFunctionTool` (human-in-the-loop)

```powershell
python run.py          # manager approves
python run.py --deny   # manager denies
```

## Captured output (`python run.py`)

```
user> I need to be reimbursed $1200 for a conference ticket.
  [call] ask_for_approval({'purpose': 'conference ticket', 'amount': 1200})
  [resp] {'status': 'pending', 'ticket_id': 'RB-4471', 'approver': 'Priya (manager)', ...}
agent> Your reimbursement request ... is awaiting approval from your manager, Priya.
       Your ticket ID is RB-4471.

...ticket approved by manager out of band...

agent> Your reimbursement request for a conference ticket for $1200 has been approved.
       Your ticket ID is RB-4471.
```

`python run.py --deny` → final line: *"...has been denied. The reason ... is that over
$1000 needs director sign-off."*

## The mechanism

1. `ask_for_approval` is wrapped in `LongRunningFunctionTool`. It returns
   `{"status": "pending", ...}` — **not** the final answer.
2. The triggering event exposes the call id in `event.long_running_tool_ids`. The script
   grabs the matching `FunctionCall` and **stops** the first `run_async` loop.
3. Out of band (a real app: a Slack button, a ticket webhook, a cron job) the decision is
   made.
4. The script resumes by sending a new message whose part is a
   `types.FunctionResponse(id=<same call id>, name=<same name>, response=<final dict>)`.
5. The agent picks up where it left off and tells the user the outcome.

## Why this matters

The agent process doesn't block for minutes/hours/days. Between step 2 and step 4 you can
shut the process down entirely — the conversation lives in the session store. This is the
pattern for approvals, "email the customer and wait for a reply", long compute jobs, and
anything gated on an external system.
