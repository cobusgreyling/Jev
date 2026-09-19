# What people miss about Jev

Grounded in official TypeSafe docs and the 15 Sep 2026 announcement. Operator layer — not the homepage Pareto chart.

## 1. Jev is a function call, not a chatbot

It does not write. It judges. If you need a paragraph, call a generative model. If you find yourself chaining Choices to spell words, you are in the wrong interface.

## 2. Three primitives. That is the whole API

`choice` · `score` · `noul`. Mix them in one request. Question **IDs are not sent to the model** — put the full question in `instructions`.

A Noul of 0.5 is uncertainty, not a medium Score. Use Score when you need a spectrum.

## 3. Fan-out is the cost model

State is ingested once. Questions evaluate in parallel. TypeSafe’s parallel-questions cookbook: **12.2× cheaper, 10× faster** for 13 questions vs 13 calls, same answers.

Coding agents default to one question per HTTP call. Fight that.

## 4. Output is free. $0.042 / MTok input

$42 per billion input tokens. No 200k-style price cliff on Jev 1.13. The constraint is a **64k** request budget (32k for state + longest question). Rate limits can move during early access.

## 5. Confidence is a second axis. Noul does not have one

Choice and Score return `confidence` derived from how peaked the distribution is. Noul’s only signal is `noul`.

Do **not**:

- copy a Noul threshold onto a Choice
- assume `P(yes) + P(not yes) = 1` across two Nouls
- treat a yes/no Choice as interchangeable with a Noul

Do: act / confirm / human, with a higher bar for irreversible actions.

## 6. Code owns the workflow

TypeSafe’s own framing: AI-powered **software**, not agents that pick the next tool. Arithmetic, retrieval, side effects, and weights stay in code. When the team disagrees with a combined score, change the weights and re-run — the judgments are already stored.

## 7. You cannot fine-tune Jev

Same RLCD weights for every account. Customize with `state`, `instructions`, and `criteria`. Pin `jev-1.13.0` if you have tuned thresholds; `jev-latest` moves.

## 8. Jev 1.13 is literal and cannot count

Official jaggedness: math, counting, dates, multi-hop indirection, distractor-heavy state, adversarial content, contradictory criteria, generation. Extraction is a judgment. Arithmetic is not.

## 9. 0% schema errors is by construction, not a benchmark

The model cannot return a label off the schema. It can still be **wrong**, over-literal, or steered. “Can’t hallucinate” means can’t invent a type. Read the claims file before repeating homepage multipliers (~194× / ~445×) without the eval nuance.

## 10. English-first, text-only, small state wins

No image / audio / video. Point at nested fields with backticked paths: `` `ticket.messages[0].text` ``. Filter in code first — unrelated context costs accuracy.

---

Sources: [docs/sources.md](sources.md)
