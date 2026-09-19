#!/usr/bin/env python3
"""03 — Score: position on an ordered rubric. Can land between levels."""

from lib import judge

STATE = "Hi, I've been trying to connect my Stripe account for 3 days and it keeps failing. I'm losing sales. Please help ASAP."
QUESTIONS = {
    "frustration": {
        "type": "score",
        "instructions": "How frustrated does the author appear?",
        "criteria": [
            "Calm, just stating facts",
            "Frustrated but civil",
            "Very angry, strong language",
        ],
    }
}

if __name__ == "__main__":
    ans = judge(STATE, QUESTIONS)["answers"]["frustration"]
    print(f"score = {ans['score']}")
    print(f"confidence = {ans['confidence']}")
    print("legend:", ans.get("legend"))
