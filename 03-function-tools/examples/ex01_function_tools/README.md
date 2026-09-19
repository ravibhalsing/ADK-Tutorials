# Example 01 — Function tools: schema, optional args, errors

```powershell
adk run ex01_function_tools          # from …/03-function-tools/examples
python run.py                        # scripted 3-turn demo
python run.py --schema               # print the JSON schema ADK generates
```

## `--schema` output (excerpt)

```jsonc
# estimate_shipping
{
  "name": "estimate_shipping",
  "description": "Estimate a shipping cost.\n\nArgs:\n    sku: Product SKU...",
  "parameters_json_schema": {
    "properties": {
      "sku":      { "type": "string" },
      "quantity": { "type": "integer" },
      "express":  { "type": "boolean", "default": false },
      "country":  { "anyOf": [{"type": "string"}, {"type": "null"}], "default": null }
    },
    "required": ["sku", "quantity"]           // no default => required
  }
}
```

Note: the whole docstring becomes `description`; `express`/`country` are **optional**
(they have defaults); `Optional[str] = None` becomes `anyOf [string, null]`.

## Chat output (captured)

```
user> How much is the USB-C hub and is it in stock?
  [call] lookup_product({'query': 'USB-C hub'})
  [resp] {'status': 'success', 'sku': 'SKU-2', 'name': 'USB-C hub', 'price': 34.5, 'stock': 0}
agent> The USB-C hub is $34.50 but currently out of stock.

user> What's express shipping for 3 laptop stands to Germany?
  [call] lookup_product({'query': 'laptop stand'})        # step 1: name -> SKU
  [call] estimate_shipping({'sku':'SKU-3','quantity':3,'express':True,'country':'Germany'})
  [resp] {'status': 'success', 'cost': 40.9, 'currency': 'USD', 'eta_days': 2}
agent> Express shipping for 3 laptop stands to Germany will cost 40.90 USD, arriving in 2 days.

user> Price of SKU-9?
  [resp] {'status': 'error', 'error_message': "No product matches 'SKU-9'. Catalog: ..."}
agent> There is no product with SKU-9. Valid SKUs are SKU-1 (Mechanical keyboard)...
```

## Takeaways

- The model **chained** two tools in turn 2 (lookup → shipping) with no extra prompting —
  because each docstring says clearly what it's for.
- The `status: "error"` dict with a helpful `error_message` let the model recover in
  turn 3 instead of guessing or crashing.
- `lookup_product` accepts SKU *or* partial name — designing tool inputs around how users
  actually phrase things reduces "please give me the SKU" dead-ends.
