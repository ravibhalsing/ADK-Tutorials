"""Module 05 · Example 2 — a custom MCP server, built with FastMCP.

This is the decorator-based way to write an MCP server (contrast with
`ex03`'s low-level `Server` API, which is more verbose but gives full
control). `FastMCP` turns each decorated function into an MCP tool
automatically — name, docstring, and type hints become the tool's schema.

Runs over stdio by default (`mcp.run()`), so `ex02`'s `agent.py` can launch
it as a subprocess via `StdioServerParameters(command=sys.executable, ...)`
— no Node.js, no npx, none of `ex01`'s Windows subprocess-spawn concerns:
this is a plain Python process the venv's own interpreter starts directly.

Run standalone to sanity-check it (it waits on stdio for a client, so this
just proves the server has no import/syntax errors — Ctrl-C to stop):
    python mcp_server.py
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("company-facts")

_EMPLOYEES = {
    "e1": {"name": "Priya Sharma", "role": "Engineering Manager", "office": "Bengaluru"},
    "e2": {"name": "Marcus Lee", "role": "Product Designer", "office": "Singapore"},
    "e3": {"name": "Fatima Khan", "role": "Backend Engineer", "office": "Bengaluru"},
}

_OFFICE_HEADCOUNT = {"Bengaluru": 2, "Singapore": 1}


@mcp.tool()
def get_employee(employee_id: str) -> dict:
    """Look up an employee by ID (e.g. "e1"). Returns their name, role, and office."""
    employee = _EMPLOYEES.get(employee_id)
    if employee is None:
        return {"error": f"No employee with id {employee_id!r}"}
    return employee


@mcp.tool()
def office_headcount(office: str) -> dict:
    """Return the number of employees in the given office (e.g. "Bengaluru")."""
    if office not in _OFFICE_HEADCOUNT:
        return {"error": f"Unknown office {office!r}. Known offices: {sorted(_OFFICE_HEADCOUNT)}"}
    return {"office": office, "headcount": _OFFICE_HEADCOUNT[office]}


if __name__ == "__main__":
    mcp.run()
