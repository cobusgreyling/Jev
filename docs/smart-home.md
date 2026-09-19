# Smart home demo

Interactive recreation of TypeSafe’s [smart home assistant demo](https://docs.typesafe.ai/demos/smart-home) (see the [Loom walkthrough](https://www.loom.com/share/18c4dbcf8db546dfb2d7f2ef018e78e4)).

Run the lab, then open **http://127.0.0.1:7872/home**.

## What you see

| Pane | Role |
|------|------|
| Command bar | Natural-language request + optional “talking to” device |
| Example chips | The same prompts as the official video |
| Smart Home | Rooms and devices. Mint = on / locked / climate running |
| Decision Trace | All ~13 questions from one call. Used answers are bright; speculative ones stay dim |

## Patterns

**Speculative fan-out.** “Turn off all of the lights” still asks what should happen to the *locks*, *fans*, *speakers*… Code reads only `category`, `scope`, `device_type`, and `action.light`.

**Confidence gating.** A plan’s confidence is the minimum over the Choice answers it consumed. Below 0.5 the UI asks before acting. Unlocking a door needs 0.85.

**LLM pairing (heuristic here).** `is_compound > 0.5` splits the utterance into atomic commands (regex, no extra key). `category == general` gets a short canned reply — in TypeSafe’s original, that call is a generative model.

## Offline vs live

No key: a keyword mock returns the same answer *shape*, so the house still moves.

`TYPESAFE_API_KEY` set: each Send is `POST /v1/systemone` with the real questions. The key never reaches the browser.

## Homes

- **1BR** — 10 devices (matches the video’s default)
- **Family home** — 19 devices, including Maya’s room and a patio (needed for “kid’s light” and “outside music”)
