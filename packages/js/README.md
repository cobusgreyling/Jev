# `@cobusgreyling/jev`

TypeScript client + CLI for TypeSafe Jev, aimed at **agent harnesses**.

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

Auth: `TYPESAFE_API_KEY`, `~/.config/typesafe/api_key`, or `~/.typesafe/api_key` (mode 600). Never commit the key. Without a key, a heuristic fallback runs.

See the [repo README](../../README.md) and [Loop Engineering Jev guide](https://github.com/cobusgreyling/loop-engineering/blob/main/docs/jev.md).
