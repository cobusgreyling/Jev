#!/usr/bin/env python3
"""05 — Confidence-gated routing. The label is what; confidence is whether."""

from lib import judge
from jev_lab.policy import confidence_route, ticket_policy

STATE = "How do I rotate an API key in the dashboard? No rush — I can wait until Monday."
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
    answers = judge(STATE, QUESTIONS, fixture="calm-question")["answers"]
    conf = answers["department"]["confidence"]
    print("choice     :", answers["department"]["choice"])
    print("confidence :", conf)
    print("lane       :", confidence_route(conf))
    print("policy     :", ticket_policy(answers)["action"])
