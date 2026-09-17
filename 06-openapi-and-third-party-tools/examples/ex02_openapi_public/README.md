# Example 02 — `OpenAPIToolset` from a hand-written spec

The [Frankfurter](https://frankfurter.dev) FX API has no published OpenAPI doc, so
`agent.py` contains a ~30-line YAML spec. Two operations → two tools.

```powershell
python run.py
```

## Captured output

```
user> How many euros is 250 US dollars right now?
  [api call] get_latest_rates({'base': 'USD', 'symbols': 'EUR'})
  [api resp] {'amount': 1.0, 'base': 'USD', 'date': '2026-09-04', 'rates': {'EUR': 0.86044}}
agent> 250 US dollars converts to 215.11 Euros at a rate of 1 USD = 0.86044 EUR.

user> What was the USD to INR rate on 2024-01-02?
  [api call] get_historical_rates({'base': 'USD', 'symbols': 'INR', 'date': '2024-01-02'})
  [api resp] {'amount': 1.0, 'base': 'USD', 'date': '2024-01-02', 'rates': {'INR': 83.32}}
agent> On 2024-01-02, 1 USD = 83.32 INR.
```

## Takeaways

- You don't need a *published* spec — a minimal one you write is enough. Just the
  operations you care about, with `operationId`, `summary`, params, and a `servers:` URL.
- Path params (`/{date}`) and query params (`base`, `symbols`) both map through.
- The model does the final multiplication itself (the instruction tells it to) and shows
  the rate — good practice for auditability.
- Earlier draft used `api.frankfurter.app` with `from`/`to` params → 301 redirect +
  reserved-word rename (`from` → `param_from`). The fix: current URL + current param names.
