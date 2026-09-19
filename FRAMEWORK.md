# Framework for an ultimate Jev showcase

A model showcase is not a wrapper around Hello World. It is a **lab that teaches the operator layer** — the facts that change how you build — while staying clone-and-run honest.

This repo is built on eight layers. Use the same skeleton for any System One (or decision-model) showcase.

## 1. Thesis in one line

> Unstructured state in, typed probabilistic decisions out. Code owns the workflow.

If the visitor cannot repeat that after thirty seconds, the README failed.

## 2. Offline-first lab

Clone, `./run.sh`, browser. No key required.

| Surface | Offline? | Job |
|---------|----------|-----|
| What people miss | Yes | Ranked operator cards from official docs |
| Playground | Yes (fixtures) | Choice + Score + Noul over one state |
| Cost lab | Yes | Input-only billing, fan-out vs serial |
| Patterns | Yes | Fan-out, confidence routing, composite, intent |
| Jaggedness | Yes | What Jev 1.13 cannot do |
| Scenarios | Yes | Where it belongs vs a chat model |
| Live judge | Needs key | Real `POST /v1/systemone` |
| Model card | Yes | Specs, aliases, gotchas |

Live is a **tab**, not a gate.

## 3. Policy lives in code

The model returns distributions. `jev_lab/policy.py` decides:

- Noul → yes / no / review
- Confidence → act / confirm / human
- Weights → composite score
- Ticket policy → route, priority, escalate

Changing a threshold re-scores for free. That is the product.

```text
state + questions  →  Jev  →  typed answers
                                ↓
                         policy.py (your code)
                                ↓
                         side effects
```

## 4. Progressive examples (01 → 07)

1. Noul
2. Choice
3. Score
4. Parallel fan-out
5. Confidence routing
6. Composite scoring
7. Guardrail in front of a generative model

Each script runs against a recorded fixture. `--live` is opt-in.

## 5. Honesty layer

An ultimate showcase includes the jagged edges:

- Literal reading
- No counting / arithmetic / date math
- No generation
- No fine-tune
- Noul ≠ Choice; invariants are not guaranteed
- English-first, text-only

Tracked vendor claims sit in `data/claims.json` with nuance, not as slogans.

## 6. Secret hygiene

Public repo. World-readable history.

- `.env` gitignored; `.env.example` empty
- Key may live in `~/.typesafe/api_key` (mode 600)
- `/api/health` reports `live: true/false`, never the key
- `scripts/secret_scan.py` + CI fail on `apikey_…`

## 7. Repro

`pytest` for cost, policy, fixtures, secret scan. Docker for the lab. Makefile for demo / examples / test. Fixtures are JSON in `data/fixtures/` so the playground stays real when the key is absent.

## 8. Pairing, not replacement

Jev decides. A generative model writes. The scenarios tab is explicit about that split: triage, guardrails, RAG filters, citation checks, tool-trace verification — not chat.

---

That is the framework. The rest of this repository is that framework instantiated for TypeSafe Jev 1.13.
