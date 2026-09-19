# Security

This is a public showcase. Treat every commit as world-readable.

## API keys

- Store `TYPESAFE_API_KEY` in `.env` (gitignored) or `~/.typesafe/api_key` (mode `600`).
- `.env.example` is the only committed env file, and it is empty.
- The lab never returns the key from `/api/health` or any other endpoint.
- Examples print answers, usage, and latency — never the Authorization header.

Mint and rotate keys at [console.typesafe.ai/keys](https://console.typesafe.ai/keys).

## Before you push

```bash
make secret-scan
```

The scanner fails if it finds TypeSafe-shaped keys (`apikey_…`), `.env` contents, or common cloud key prefixes.
