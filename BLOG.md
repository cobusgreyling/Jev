# Jev is not a faster chatbot

TypeSafe shipped **Jev** on 15 September 2026: the first **System One** model. The launch demo is latency. The useful part is the interface.

A chat model generates strings. Software then tries to recover a decision from those strings. Jev inverts that. You declare the decision *before* the call. The model fills a typed slot and a probability distribution. There is no JSON to scrape. There is no label it is allowed to invent.

That sounds like “structured output.” It is stricter than that:

- **Choice** — one option from a set you defined (up to 255), plus `probabilities` and `confidence`
- **Score** — a position on *your* rubric; it can land between levels
- **Noul** — P(yes) from 0 to 1, and **no separate confidence field**

Questions over the same `state` run **in parallel**. Adding a speculative question is almost free. TypeSafe’s own cookbook puts 13 questions over one article at ~12× cheaper and ~10× faster than 13 serial calls. Output tokens are free. Input is $0.042 per million tokens.

The architectural claim is the one most wrappers miss: **code owns the workflow.** Jev is a smart `if`, not an agent. You decompose a fuzzy judgment into atomic questions, combine the answers with weights you can change without a new prompt, and escalate when confidence is low.

Jev 1.13 is also jagged. It is literal. It cannot count. It should not do date arithmetic. You cannot fine-tune it. English is first. Adversarial state can steer it. TypeSafe published that list; an honest showcase repeats it.

The pairing is the product: **Jev decides, a generative model writes.** Guardrails, ticket routing, RAG filters, citation checks, tool-trace verification — those are System One jobs. Drafting the reply is not.

This repository is an unofficial lab for that split. Offline fixtures, a cost calculator, a policy module, and a live tab if you have a key. The key never belongs in git.

- Announcement: https://typesafe.ai/blog/introducing-system-one-models-and-jev
- Docs: https://docs.typesafe.ai/
- Jaggedness: https://docs.typesafe.ai/model-jaggedness/jev-1.13
