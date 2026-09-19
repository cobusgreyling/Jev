#!/usr/bin/env python3
"""04 — Speculative fan-out: mix Choice, Score, and Noul in one request."""

from lib import judge
from jev_lab.cost import fanout_comparison

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
    },
    "frustration": {
        "type": "score",
        "instructions": "How frustrated does the author appear?",
        "criteria": [
            "Calm, just stating facts",
            "Frustrated but civil",
            "Very angry, strong language",
        ],
    },
    "is_urgent": {
        "type": "noul",
        "instructions": "Does the message convey urgency or time-sensitivity?",
    },
}

if __name__ == "__main__":
    resp = judge(STATE, QUESTIONS)
    answers = resp["answers"]
    print("department :", answers["department"]["choice"])
    print("frustration:", answers["frustration"]["score"])
    print("is_urgent  :", answers["is_urgent"]["noul"])
    cmp_ = fanout_comparison(state_tokens=80, question_tokens=40, n_questions=3)
    print(f"fan-out vs serial (toy tokens): {cmp_['cheaper_factor']}× cheaper batched")
