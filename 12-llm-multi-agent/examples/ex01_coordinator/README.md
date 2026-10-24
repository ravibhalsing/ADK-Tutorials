# Example 01 — Coordinator / Dispatcher

`frontdesk` (router) + `billing` + `tech` (specialists). The router transfers by reading
each specialist's `description`.

```powershell
adk run ex01_coordinator      # from …/12-llm-multi-agent/examples
python run.py
```

## Captured output

```
user> Hi, I was charged twice for my subscription this month.
  --> transfer_to_agent: billing
[billing]> I understand you were charged twice ... Please provide your account details
          so I can investigate and issue a refund.

user> Can you refund the duplicate?
[billing]> To process the refund I need to verify your account ...     # still billing

user> The app shows 'ERR_CONN_REFUSED' when I try to sync.             # new session
  --> transfer_to_agent: tech
[tech]> "ERR_CONN_REFUSED" means the app can't reach the server. Try: 1. check
        internet ... 2. restart the app ... 5. check server status ...
```

## Takeaways

- `LlmAgent(sub_agents=[billing, tech])` gives the router a `transfer_to_agent` tool
  automatically. The instruction tells it *when* to use it and *not* to answer specialist
  questions itself.
- After the transfer, the specialist owns the conversation — the follow-up "can you
  refund" went straight to `billing` (`event.author == "billing"`), no re-routing.
- Routing quality = `description` quality. "Handles invoices, refunds, payment methods,
  plan changes" is a good routing signal; "billing stuff" is not.
