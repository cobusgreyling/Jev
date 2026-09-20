# Agent skills

Unofficial Jev skills for Claude Code, Codex, Cursor, Grok, and `npx skills add`. They encode this repo’s thesis: **Jev decides, code owns the workflow.**

The official TypeSafe skill (API, primitives, cookbooks) lives at [typesafe-ai/skills](https://github.com/typesafe-ai/skills). Install that too. Do not treat these as a replacement.

| Skill | Purpose |
|-------|---------|
| [jev](jev/SKILL.md) | When to call Jev; Choice / Score / Noul; request shape |
| [jev-fanout](jev-fanout/SKILL.md) | Every independent question in one `POST /v1/systemone` |
| [jev-guardrail](jev-guardrail/SKILL.md) | Input/output hazard screen → pass / review / block |
| [jev-route](jev-route/SKILL.md) | Confidence lanes (`act` / `confirm` / `human`) and model-tier routing |

```bash
npx skills add cobusgreyling/Jev --skill jev
npx skills add cobusgreyling/Jev --skill jev-fanout
npx skills add cobusgreyling/Jev --skill jev-guardrail
npx skills add cobusgreyling/Jev --skill jev-route
```

Grok loads `.grok/skills/` (symlinks to this directory). Slash: `/jev`, `/jev-fanout`, `/jev-guardrail`, `/jev-route`.
