#!/usr/bin/env python3
"""06 — Composite scoring: atomic signals, weights in code."""

from jev_lab.policy import composite_score

# Pretend three Nouls already came back from one fan-out call.
SIGNALS = {
    "requests_credentials": 0.92,
    "sender_identity_mismatch": 0.71,
    "unexpected_reward": 0.64,
}

WEIGHTS = {
    "requests_credentials": 0.45,
    "sender_identity_mismatch": 0.30,
    "unexpected_reward": 0.25,
}

if __name__ == "__main__":
    spam_risk = composite_score([(SIGNALS[k], WEIGHTS[k]) for k in SIGNALS])
    print(f"spam_risk = {spam_risk:.3f}")
    if 0.4 < spam_risk < 0.6:
        print("uncertain → human review")
    elif spam_risk >= 0.6:
        print("quarantine")
    else:
        print("pass")
    print("Change WEIGHTS and re-score — no model call.")
