"""Module 03 · Example 1 — function tools: schema, optional args, errors.

    adk run ex01_function_tools
    adk web
    python run.py --schema      # print the JSON schema ADK generates
"""

from __future__ import annotations

import os
from typing import Optional

from google.adk.agents import Agent

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

_CATALOG = {
    "SKU-1": {"name": "Mechanical keyboard", "price": 89.0, "stock": 12},
    "SKU-2": {"name": "USB-C hub", "price": 34.5, "stock": 0},
    "SKU-3": {"name": "Laptop stand", "price": 45.0, "stock": 7},
}


def lookup_product(query: str) -> dict:
    """Look up a product by SKU or by (partial) name.

    Args:
        query: A SKU like "SKU-1", or part of a product name like "hub" or "keyboard".
            Case-insensitive.

    Returns:
        dict: {"status": "success", "sku", "name", "price", "stock"} on a single match,
              {"status": "error", "error_message"} if nothing or too much matches.
    """
    q = query.strip().lower()
    if q.upper() in _CATALOG:
        item = _CATALOG[q.upper()]
        return {"status": "success", "sku": q.upper(), **item}
    hits = [(sku, v) for sku, v in _CATALOG.items() if q in v["name"].lower()]
    if len(hits) == 1:
        sku, item = hits[0]
        return {"status": "success", "sku": sku, **item}
    if not hits:
        names = ", ".join(f"{s} ({v['name']})" for s, v in _CATALOG.items())
        return {"status": "error", "error_message": f"No product matches '{query}'. Catalog: {names}."}
    return {
        "status": "error",
        "error_message": f"'{query}' matches several products: {[s for s, _ in hits]}. Be more specific.",
    }


def estimate_shipping(sku: str, quantity: int, express: bool = False,
                      country: Optional[str] = None) -> dict:
    """Estimate a shipping cost.

    Args:
        sku: Product SKU.
        quantity: How many units (must be >= 1).
        express: Express shipping if True. Defaults to False (standard).
        country: Optional ISO country name. Defaults to domestic if omitted.

    Returns:
        dict: {"status": "success", "cost", "currency", "eta_days"} or an error dict.
    """
    if quantity < 1:
        return {"status": "error", "error_message": "quantity must be at least 1"}
    if sku.strip().upper() not in _CATALOG:
        return {"status": "error", "error_message": f"unknown SKU '{sku}'"}

    base = 5.0 + 1.5 * quantity
    if express:
        base *= 2.2
    if country and country.strip().lower() not in {"india", "in"}:
        base += 20.0
    eta = 2 if express else 6
    return {"status": "success", "cost": round(base, 2), "currency": "USD", "eta_days": eta}


root_agent = Agent(
    name="store_agent",
    model=MODEL,
    description="Answers product and shipping questions for a small online store.",
    instruction=(
        "You are a store assistant.\n"
        "- Use `lookup_product` for price/stock/name questions.\n"
        "- Use `estimate_shipping` for delivery cost/time. Ask for quantity if the user "
        "didn't give one.\n"
        "- If a tool returns status 'error', relay the error_message plainly and, if "
        "helpful, list valid SKUs. Never invent prices or stock.\n"
        "- Be concise."
    ),
    tools=[lookup_product, estimate_shipping],
)
