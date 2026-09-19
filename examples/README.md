# Examples

Offline fixtures by default. Add `--live` to call `POST /v1/systemone` when `TYPESAFE_API_KEY` is set.

| Script | Primitive / pattern |
|--------|---------------------|
| `01_noul.py` | P(yes) |
| `02_choice.py` | Closed set + distribution |
| `03_score.py` | Ordered rubric |
| `04_parallel_fanout.py` | All three in one request |
| `05_confidence_routing.py` | act / confirm / human |
| `06_composite_scoring.py` | Weights in code, no model call |
| `07_guardrails.py` | Block before a generative model |
