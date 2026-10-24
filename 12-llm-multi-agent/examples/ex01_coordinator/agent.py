"""Module 12 · Example 1 — coordinator / dispatcher.

The `frontdesk` model reads each sub-agent's `description` and issues
transfer_to_agent(...). After a transfer, that specialist owns the conversation.

    adk run ex01_coordinator
    python run.py
"""

from __future__ import annotations

import os

from google.adk.agents import LlmAgent

M = os.environ.get("MODEL", "gemini-2.5-flash")

billing = LlmAgent(
    name="billing", model=M,
    description="Invoices, refunds, payment methods, plan upgrades/downgrades, receipts.",
    instruction="You are Billing Support. Resolve the user's billing question directly "
                "and concisely. Do not discuss technical problems.",
)

tech = LlmAgent(
    name="tech", model=M,
    description="Error messages, outages, setup/configuration, how-to, bug reports.",
    instruction="You are Technical Support. Help the user fix their technical problem "
                "with concrete steps. Do not discuss billing.",
)

root_agent = LlmAgent(
    name="frontdesk", model=M,
    description="Customer support front desk / router.",
    instruction=(
        "You are the support front desk. Briefly greet the user, identify whether their "
        "issue is BILLING or TECHNICAL, and transfer:\n"
        "- billing/payment/refund/plan -> transfer to `billing`\n"
        "- errors/setup/how-to/bugs -> transfer to `tech`\n"
        "Do NOT attempt to answer billing or technical questions yourself."
    ),
    sub_agents=[billing, tech],
)
