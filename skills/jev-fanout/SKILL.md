---
name: jev-fanout
description: Ask every independent TypeSafe Jev question in one POST /v1/systemone (speculative fan-out). Use for parallel questions, smart-home or compound commands, one-call turn assessment, or when the user runs /jev-fanout. Do not fire one HTTP call per question.
---

# Jev speculative fan-out

Ask every independent judgment over the **same state in one** `POST /v1/systemone`. Questions run in parallel and **cannot see each other's answers**. Code consumes the ones that apply.

Primitives and auth: `skills/jev/SKILL.md`. Official pattern: https://docs.typesafe.ai/patterns/fan-out

## Do this

1. List the judgments the workflow might need, including speculative ones (category, compound, room, device, availability, action per device type).
2. Put each in `questions` with complete `instructions`. Write the speculative premise into the question (`If this is a light command, …`). Question IDs are not sent to the model.
3. Mix `choice`, `score`, and `noul` in that one request. Pin `jev-1.13.0` once thresholds are tuned; `jev-latest` moves.
4. In code, branch on the answers that apply; leave the rest unused.
5. Make a second HTTP call only when the next options or next state cannot be built yet.

## Do not

- One question per HTTP call
- Hide five judgments in one Choice
- Assume later questions saw earlier answers

## Shape

```json
{
  "state": "I've been trying to connect Stripe for 3 days. I'm losing sales. Help ASAP.",
  "model": "jev-latest",
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which team should handle this message?",
      "criteria": {
        "billing": "Payments, invoicing, refunds",
        "technical": "Bugs, outages, integrations",
        "other": "Neither fits"
      }
    },
    "frustration": {
      "type": "score",
      "instructions": "How frustrated does the author appear?",
      "criteria": ["Calm, just stating facts", "Frustrated but civil", "Very angry, strong language"]
    },
    "is_urgent": {
      "type": "noul",
      "instructions": "Does the message convey urgency or time-sensitivity?"
    }
  }
}
```

## This repo

- `examples/04_parallel_fanout.py` — Choice + Score + Noul in one call
- `jev_lab/home.py` and `/home` — ~13 speculative questions, then the dispatcher acts
- `packages/js/src/turn.ts` — `npx jev turn` (route + input guard, one call)
- `docs/smart-home.md`
