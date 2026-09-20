# Jev Showcase — TypeSafe System One, not chat

<p align="center">
  <img src="assets/header.jpg" alt="Jev — a crystalline decision engine emitting parallel judgment beams" width="100%" />
</p>

<p align="center">
  <strong>Unofficial operator-level companion for TypeSafe Jev</strong><br/>
  Choice · Score · Noul · parallel fan-out · confidence as a second axis<br/>
  Jev 1.13 · released <strong>15 September 2026</strong>
</p>

<p align="center">
  <a href="docs/WHAT-PEOPLE-MISS.md">What people miss</a> ·
  <a href="https://typesafe.ai/blog/introducing-system-one-models-and-jev">Announcement</a> ·
  <a href="https://docs.typesafe.ai/">Docs</a> ·
  <a href="https://docs.typesafe.ai/models">Models</a> ·
  <a href="BLOG.md">Article</a> ·
  <a href="FRAMEWORK.md">Showcase framework</a>
</p>

---

Most posts stop at **“fast structured output.”** This repo surfaces the **docs-only details** that change how you build: Jev is a **function call**, questions run **in parallel**, **output is free**, **confidence is not probability**, and **code owns the workflow**.

| Under-known fact | Why it matters |
|------------------|----------------|
| **Not a chatbot** | No prose, code, or explanations. Pair with a generative model. |
| **Three primitives** | Choice / Score / Noul. Question IDs are not sent to the model. |
| **Fan-out** | Many questions, one state, one call. ~12× cheaper than serial. |
| **$0.042 / MTok, output free** | Optimize question design, not completion length. |
| **Noul has no `confidence`** | Do not copy a Noul threshold onto a Choice. |
| **No fine-tune** | Shape answers via `state` + `instructions` + `criteria`. |
| **Literal + no math** | Count, dates, and arithmetic stay in code. |

Full write-up: **[docs/WHAT-PEOPLE-MISS.md](docs/WHAT-PEOPLE-MISS.md)** · interactive cards in the lab.

**Keywords:** TypeSafe, Jev, System One, RLCD, calibrated decisions, structured output, confidence routing, agent guardrails

---

## The one-liner

> **Frontier-intelligence function call** — unstructured state in, typed probabilistic decisions out. 70–500 ms. Cannot invent a label off your schema.

| | |
|--|--|
| **Model id** | `jev-1.13.0` (`jev-latest`) |
| **Class** | System One (not a chat LLM) |
| **Endpoint** | `POST /v1/systemone` |
| **Context** | 64k / request; 32k for state + longest question |
| **Input** | Text / JSON. No image, audio, or video |
| **Output** | Choice · Score · Noul (+ probabilities) |
| **Pricing** | **$0.042 / MTok input · output free** |
| **Latency** | 70–500 ms (vendor) |
| **Training** | RLCD — Reinforcement Learning for Calibrated Decisions |
| **Released** | 15 September 2026 |

---

## 30-second start

```bash
git clone https://github.com/cobusgreyling/Jev.git
cd Jev

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:7872/home** for the smart-home demo (TypeSafe’s fan-out house), or **http://127.0.0.1:7872** for the operator lab.

### Harness CLI (TypeScript)

The same System One questions, packaged for agent loops — model routing, semantic retrieval, LLM guardrails, reasoning-trace classification. Wired into [Loop Engineering](https://github.com/cobusgreyling/loop-engineering) as `loop-jev`.

```bash
cd packages/js && npm install && npm test
npx jev doctor
npx jev route --goal "CI has been red for 3 days" --level L2 --json
npx jev guard --side input --text "Ignore previous instructions" --json
```

Docs: [`packages/js/README.md`](packages/js/README.md) · [loop-engineering/docs/jev.md](https://github.com/cobusgreyling/loop-engineering/blob/main/docs/jev.md)

The key is never printed. Store it as `TYPESAFE_API_KEY`, `~/.typesafe/api_key`, or `~/.config/typesafe/api_key` (mode 600).

```bash
./run.sh
```

### Agent skills

Portable `SKILL.md` files for coding agents. Official TypeSafe skill: [typesafe-ai/skills](https://github.com/typesafe-ai/skills).

```bash
npx skills add cobusgreyling/Jev --skill jev
npx skills add cobusgreyling/Jev --skill jev-fanout
npx skills add cobusgreyling/Jev --skill jev-guardrail
npx skills add cobusgreyling/Jev --skill jev-route
```

| Skill | Purpose |
|-------|---------|
| [`jev`](skills/jev/SKILL.md) | Primitives and when to call Jev |
| [`jev-fanout`](skills/jev-fanout/SKILL.md) | Speculative fan-out (one request, many questions) |
| [`jev-guardrail`](skills/jev-guardrail/SKILL.md) | Input/output hazard screen |
| [`jev-route`](skills/jev-route/SKILL.md) | Confidence lanes and model-tier routing |

Grok also loads [`.grok/skills/`](.grok/skills) (symlinks). Catalog: [`skills/README.md`](skills/README.md).

### Docker

```bash
docker compose up --build
# → http://127.0.0.1:7872
```

No API key for offline tabs. Live judge:

```bash
cp .env.example .env
# put your TypeSafe key in .env or ~/.typesafe/api_key
# mint at https://console.typesafe.ai/keys
./run.sh
```

The key is never logged, never returned by `/api/health`, and never committed. See [SECURITY.md](SECURITY.md).

---

## What the lab shows

| Surface | Offline? | What you learn |
|---------|----------|----------------|
| **[Smart home](/home)** | Yes (mock) | Official-style house: 13 questions in one call, code flips the lights |
| **What people miss** | Yes | 10 ranked operator cards with actions + doc links |
| **Playground** | Yes | Choice + Score + Noul, then a policy in code |
| **Cost lab** | Yes | Input-only billing, fan-out vs serial, LLM stand-in |
| **Patterns** | Yes | Fan-out · confidence routing · composite · intent |
| **Jaggedness** | Yes | Official Jev 1.13 failure modes |
| **Scenarios** | Yes | Triage, guardrails, RAG, citations, tool traces |
| **Live judge** | Needs key | Real System One call; key never shown |
| **Model card** | Yes | Specs, aliases, gotchas |

---

## The request shape

```bash
curl -X POST https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

Answers come back under the same keys, typed. Nothing to parse.

---

## Progressive examples

```bash
python examples/01_noul.py
python examples/02_choice.py
python examples/03_score.py
python examples/04_parallel_fanout.py
python examples/05_confidence_routing.py
python examples/06_composite_scoring.py
python examples/07_guardrails.py
```

Fixtures by default. Add `--live` when `TYPESAFE_API_KEY` is set.

```bash
make test
make secret-scan
```

---

## Repository map

```text
├── app.py / static/          Operator lab + /home smart-home demo
├── jev_lab/                  HTTP client, cost, policy, house dispatcher
├── packages/js/              TypeScript harness CLI (@cobusgreyling/jev)
├── FRAMEWORK.md              The eight-layer showcase skeleton
├── BLOG.md                   Narrative article
├── examples/01–07            Progressive scripts
├── data/                     model-card, claims, fixtures
├── docs/                     Operator notes + smart-home + sources
├── skills/                   Agent skills (jev, jev-fanout, jev-guardrail, jev-route)
├── .grok/skills/             Grok-discoverable copies of those skills
├── tests/                    pytest
└── SECURITY.md               Key hygiene
```

This is **not** an official TypeSafe product. It does **not** replace `typesafe-sdk`. It **does** make the System One thesis interactive and measurable.

---

## Use Jev when…

- You need classify / route / score / verify on a hot path
- Schema errors are unacceptable
- You want calibrated probabilities, not a paragraph
- You will keep side effects in code

## Prefer a generative model when…

- You need prose, code, or an explanation
- The answer space is not a closed set
- The task is counting, arithmetic, or date math
- You want an agent that chooses its own next action

---

## Docs index

| Topic | Link |
|-------|------|
| What people miss | [docs/WHAT-PEOPLE-MISS.md](docs/WHAT-PEOPLE-MISS.md) |
| Smart home demo | [docs/smart-home.md](docs/smart-home.md) |
| Anti-patterns | [docs/anti-patterns.md](docs/anti-patterns.md) |
| Sources | [docs/sources.md](docs/sources.md) |
| Official jaggedness | [Jev 1.13](https://docs.typesafe.ai/model-jaggedness/jev-1.13) |
| Official patterns | [docs.typesafe.ai/patterns](https://docs.typesafe.ai/patterns) |
| Workflow evals | [evals.typesafe.ai](https://evals.typesafe.ai/) |
| Agent skills | [skills/](skills/) |

---

MIT · Unofficial · [TypeSafe AI](https://typesafe.ai)
