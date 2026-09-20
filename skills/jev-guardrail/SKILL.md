---
name: jev-guardrail
description: Screen LLM input and output with TypeSafe Jev Noul hazard batteries plus a harm Score; policy in code returns pass, review, or block. Use for jailbreak, prompt injection, secret leak, denylist pressure, or when the user runs /jev-guardrail or `npx jev guard`.
---

# Jev LLM guardrail

Jev does not refuse in prose. It scores hazards. **Code** returns `pass` / `review` / `block`, then a generative model (or a static message) talks.

Primitives and auth: `skills/jev/SKILL.md`. Cookbook: https://docs.typesafe.ai/cookbooks/llm_guardrails

## Battery

One request. Independent **Nouls** per hazard + one **Score** for harm. Gate Noul on the **probability**. Do not copy a Noul threshold onto Choice `confidence`.

Input hazards in this repo: `jailbreak`, `prompt_injection`, `secret_exfil`, `denylist_pressure`, `harmful_request`.

Output hazards: `broke_policy`, `secret_leak`, `hallucination`, `instruction_drift`, `harmful_content`.

Screen **both** sides. Redact secrets before sending `state`.

## Policy lives in code

Caller-owned thresholds. Defaults in this repo (`packages/js/src/guard.ts`, `jev_lab/policy.py`):

| Signal | Strict | Permissive |
|--------|--------|------------|
| Noul review | ≥ 0.35 | ≥ 0.35 |
| Noul action | ≥ 0.7 | ≥ 0.85 |
| Harm Score promotes review → block | ≥ 2.0 | ≥ 2.0 |

Guardrails **fail closed** (block if the call errors). Routers may fail open; this skill does not.

`jailbreak`, `prompt_injection`, `secret_exfil`, `denylist_pressure`, `harmful_request`, `broke_policy`, `secret_leak`, `harmful_content` → `block` when above the action bar. `hallucination` and `instruction_drift` → `review`.

## Pair with a generative model

- `block` — do not forward the text; return a fixed refusal
- `review` — human or a reasoning model
- `pass` — generate as usual

## This repo

```bash
npx jev guard --side input --text "Ignore previous instructions" --json
npx jev guard --side output --text "$REPLY" --json
python examples/07_guardrails.py
```

- `packages/js/src/guard.ts` — `inputBattery` / `outputBattery` / `routeGuard`
- `examples/07_guardrails.py` — Choice + Noul, then skip the chat model
