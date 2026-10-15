# `@cobusgreyling/jev`

**Not on npm.** Install from this directory (`npm install` here, or a git dependency on `packages/js`). This package version (`0.1.0`) is the harness. The lab showcase version is the repo root `VERSION` file and moves on its own.

TypeScript client + CLI for TypeSafe Jev, aimed at **agent harnesses**. Default model is `jev-1.13.0`. Set `TYPESAFE_MODEL=jev-latest` to track the alias.

Same queries Loop Engineering ships as [`tools/loop-jev`](https://github.com/cobusgreyling/loop-engineering/tree/main/tools/loop-jev).

| Command | Decision |
|---------|----------|
| `route` | Which model tier should handle this turn? |
| `retrieve` | Which passages belong in context? |
| `guard` | Pass, review, or block this message? |
| `classify` | What failed in this trace? |
| `turn` | Route **and** input-guard in **one** Jev call |

```bash
cd packages/js
npm install
npm test
npx jev doctor
npx jev route --goal "Draft daily triage" --level L1 --json
```

Auth: `TYPESAFE_API_KEY` or `JEV_API_KEY`, then `~/.config/typesafe/api_key` or `~/.typesafe/api_key` (mode 600). Never commit the key. Without a key, a heuristic fallback runs. `npx jev doctor` reports `none` when no key file is present.

See the [repo README](../../README.md) and [Loop Engineering Jev guide](https://github.com/cobusgreyling/loop-engineering/blob/main/docs/jev.md).
