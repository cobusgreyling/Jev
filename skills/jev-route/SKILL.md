---
name: jev-route
description: Route with TypeSafe Jev — map Choice plus confidence to act/confirm/human, or pick a coding-agent model tier. Use for confidence routing, model routing, cheap vs frontier, loop-jev, or when the user runs /jev-route or `npx jev route`.
---

# Jev routing

Jev returns a distribution. **Code** picks the lane. Fan-out extra questions in the same call (`skills/jev-fanout/SKILL.md`). Primitives and auth: `skills/jev/SKILL.md`.

## 1. Confidence-gated action

Choice is **what**. Confidence is **whether** to trust it.

Defaults in `jev_lab/policy.py`:

| Confidence | Lane |
|------------|------|
| ≥ 0.8 | `act` |
| ≥ 0.5 | `confirm` |
| else | `human` |

Raise the bar for irreversible actions (unlock, spend, delete). Compose Noul urgency and Score frustration **after** the Choice, in code (`ticket_policy`). Do not reuse a Noul 0.7 threshold as Choice `confidence`.

`examples/05_confidence_routing.py`

## 2. Model-tier routing

Choice criteria = cheapest tier that can still do the job. Labels in `packages/js/src/route.ts`:

| Tier | When |
|------|------|
| `nano` | Typo, format, list, one-line edit |
| `fast` | L1 triage, classify, changelog |
| `balanced` | Focused patch, PR comment |
| `frontier` | Ambiguous multi-file, CI root-cause |
| `reasoning` | Verifier, security, maker/checker |

If `confidence < 0.55` and the pick is not `nano`, this repo falls back to `balanced` — an uncertain call must not overspend or underpower.

Ask in the **same** request: `difficulty` (Score), `needs_tools` / `needs_long_context` / `needs_maker_checker` (Noul). Map the Choice label to a concrete model id in code; do not ask Jev to generate the id as text.

```bash
npx jev route --goal "CI has been red for 3 days" --level L2 --json
npx jev turn --goal "Draft daily triage" --level L1 --json
```

`packages/js/src/route.ts` · `packages/js/src/turn.ts` (route + input guard, one call)
