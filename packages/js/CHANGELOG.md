# Changelog

## 0.1.0

Not published. Install from this repository. Issues belong on [cobusgreyling/Jev](https://github.com/cobusgreyling/Jev/issues), not on loop-engineering. The lab version is the repo `VERSION` file.

- Initial `jev` CLI and `@cobusgreyling/jev` library: `route`, `retrieve`, `guard`, `classify`, `turn`, `doctor`
- TypeSafe System One client with retries, secret redaction, and file/env key resolution
- Heuristic fallback when no API key is configured so CI stays green
- Same queries as Loop Engineering `tools/loop-jev`
- Default model is `jev-1.13.0`. `TYPESAFE_MODEL=jev-latest` opts into the moving alias.
- `describeKeySource()` returns `none` when no key file exists.
