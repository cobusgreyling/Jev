#!/usr/bin/env python3
"""02 — Choice: one option from a closed set, plus the full distribution."""

from lib import judge

STATE = "Hi, I've been trying to connect my Stripe account for 3 days and it keeps failing. I'm losing sales. Please help ASAP."
QUESTIONS = {
    "department": {
        "type": "choice",
        "instructions": "Which team should handle this message?",
        "criteria": {
            "billing": "Payments, invoicing, refunds, subscriptions",
            "technical": "Bugs, outages, integrations, API failures",
            "sales": "Pricing, upgrades, new accounts",
            "security": "Credential theft, jailbreaks, prompt injection, abuse",
        },
    }
}

if __name__ == "__main__":
    ans = judge(STATE, QUESTIONS)["answers"]["department"]
    print(f"choice = {ans['choice']}")
    print(f"confidence = {ans['confidence']}")
    for option, p in ans["probabilities"].items():
        print(f"  {option:12} {p:.3f}")
