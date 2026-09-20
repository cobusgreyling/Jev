---
name: jev
description: Use TypeSafe Jev for typed judgments (Choice, Score, Noul) instead of asking a chat model to classify. Pair with a generative model for prose. Use when classifying, routing, scoring, guardrailing, or the user runs /jev.
---

# Jev — System One judgments

Jev is TypeSafe's System One model. It does **not** generate text. Send `state` + typed `questions`, get calibrated probabilities back.

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer $TYPESAFE_API_KEY
```

Key from the environment or `~/.typesafe/api_key`. Never commit it. Never print it.

## When to call Jev

- Classify, route, score, guardrail, re-rank, verify a citation or tool trace
- You need a value software can `if` on, with a probability
- You would otherwise prompt an LLM to "return JSON"

## When not to

- Writing, explaining, coding, chatting
- Counting, arithmetic, date math (do that in code)
- Open-ended extraction (candidate-generate, then Choice)

## Three primitives

| Type | Returns | Use |
|------|---------|-----|
| `choice` | `choice`, `probabilities`, `confidence` | One of a closed set (≤255) |
| `score` | `score`, `legend`, `probabilities`, `confidence` | Ordered rubric; can land between levels |
| `noul` | `noul` (0–1) | P(yes). No separate confidence field |

Question IDs are for your code. They are **not** sent to the model. Put the whole question in `instructions`.

## Rules

1. Ask every independent question in **one** request (speculative fan-out).
2. Keep control flow, weights, and side effects in **code**.
3. Gate on **confidence** for Choice/Score; gate on the **probability** for Noul.
4. Do not reuse a Noul threshold on a Choice.
5. Send only the state the questions need. Point at fields with `` `ticket.messages[0].text` ``.
6. A second HTTP call is only for true dependencies (next options or next state cannot be built yet).
7. Pin `jev-1.13.0` if thresholds were tuned against that version; `jev-latest` moves.

## Minimal request

```json
{
  "state": "I was charged twice. Please refund the duplicate today.",
  "model": "jev-latest",
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which team should handle this?",
      "criteria": {
        "billing": "Payments and refunds",
        "technical": "Bugs or integrations",
        "other": "Neither fits"
      }
    },
    "refund_requested": {
      "type": "noul",
      "instructions": "Does the message request a refund?"
    },
    "urgency": {
      "type": "score",
      "instructions": "How time-sensitive is this?",
      "criteria": ["No deadline", "Within a week", "Today or sooner"]
    }
  }
}
```

Official skill and cookbooks: https://docs.typesafe.ai/agent-skill

Sibling skills in this repo: `skills/jev-fanout`, `skills/jev-guardrail`, `skills/jev-route`.
