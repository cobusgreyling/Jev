# Anti-patterns

| Don’t | Do |
|-------|----|
| Prompt Jev to “explain its reasoning” | Log the distribution; explain in your UI or a chat model |
| One question per HTTP call | Fan out every independent question |
| Hide five judgments in “is this a good ticket?” | Atomic questions, combine in code |
| Count items / compare dates in a Noul | Extract, then arithmetic in code |
| Interpolate an exact dollar amount from a Score | Threshold the Score; compute money in code |
| Chain Choices to generate a sentence | Use a generative model |
| Fine-tune / LoRA | Better `state` + `criteria` |
| Dump the whole CRM into `state` | Retrieve, filter, send what the question needs |
| Reuse a Noul 0.7 threshold on Choice.confidence | Separate gates; plot on your data |
| Treat low confidence as a yes | `confirm` or `human` |
| Put side effects inside the model call | Policy module, then act |
| Commit `TYPESAFE_API_KEY` | `.env` or `~/.typesafe/api_key` |
