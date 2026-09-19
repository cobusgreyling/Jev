#!/usr/bin/env python3
"""01 — Noul: P(yes) for a closed statement. Pass --live to hit the API."""

from lib import judge

STATE = "Hi, I've been trying to connect my Stripe account for 3 days and it keeps failing. I'm losing sales. Please help ASAP."
QUESTIONS = {
    "is_urgent": {
        "type": "noul",
        "instructions": "Does the message convey urgency or time-sensitivity?",
        "criteria": {
            "true": "Explicit deadline, ongoing outage, or 'ASAP'",
            "false": "Can wait; no time pressure",
        },
    }
}

if __name__ == "__main__":
    answers = judge(STATE, QUESTIONS)["answers"]
    noul = answers["is_urgent"]["noul"]
    print(f"is_urgent noul = {noul:.3f}")
    print("Noul has no separate confidence field — the probability is the signal.")
