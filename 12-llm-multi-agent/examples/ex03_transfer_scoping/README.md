# Example 03 — Scoping transfers

```powershell
python run.py            # specialists can bounce to peers / parent
python run.py --locked   # disallow_transfer_to_parent / _peers = True
```

## Captured output

```
=== open transfers ===
user> I was double-charged $20, and also my package hasn't shipped after a week.
  --> transfer_to_agent: billing_expert   (by coordinator)
  --> transfer_to_agent: shipping_expert  (by billing_expert)   # <-- peer hop
[shipping_expert]> I can help you with the shipping status of your package.

=== LOCKED ===
user> I was double-charged $20, and also my package hasn't shipped after a week.
  --> transfer_to_agent: billing_expert   (by coordinator)
[billing_expert]> I will investigate the $20 double-charge immediately, and a colleague
                  will follow up regarding your unshipped package.        # no peer hop
```

## Takeaways

- **Open (default):** a sub-agent can `transfer_to_agent` to a peer or back to its
  parent. Here `billing_expert` punted the shipping half to `shipping_expert`.
- **`disallow_transfer_to_parent=True` + `disallow_transfer_to_peers=True`:** the
  specialist has no `transfer_to_agent` for those targets — it must finish its part (or
  `escalate`). No ping-pong.
- Typical setup: coordinator leaves transfers open; **leaf specialists disallow both** so
  a request can't loop between them.
