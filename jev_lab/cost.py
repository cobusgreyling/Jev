"""Published TypeSafe pricing helpers.

Rates from docs.typesafe.ai/models (Jev 1.13, Sep 2026):
input $0.042 / MTok, output free.
"""

from __future__ import annotations

from typing import Any

JEV_INPUT_PER_MTOK = 0.042
JEV_OUTPUT_PER_MTOK = 0.0
# Representative frontier chat rates for the comparison chart only.
LLM_INPUT_PER_MTOK = 2.00
LLM_OUTPUT_PER_MTOK = 6.00


def estimate_cost(
    input_tokens: int,
    output_tokens: int = 0,
    *,
    questions: int = 1,
) -> dict[str, Any]:
    input_tokens = max(0, int(input_tokens))
    output_tokens = max(0, int(output_tokens))
    questions = max(1, int(questions))

    jev_in = (input_tokens / 1_000_000) * JEV_INPUT_PER_MTOK
    jev_out = (output_tokens / 1_000_000) * JEV_OUTPUT_PER_MTOK
    jev_total = jev_in + jev_out

    # Naive LLM stand-in: one structured-output call per question, ~80 output tokens each.
    llm_calls = questions
    llm_out_tokens = max(output_tokens, 80 * llm_calls)
    llm_in = (input_tokens / 1_000_000) * LLM_INPUT_PER_MTOK * llm_calls
    llm_out = (llm_out_tokens / 1_000_000) * LLM_OUTPUT_PER_MTOK
    llm_total = llm_in + llm_out

    savings = 0.0 if llm_total <= 0 else (llm_total - jev_total) / llm_total
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "questions": questions,
        "jev": {
            "input_usd": round(jev_in, 8),
            "output_usd": round(jev_out, 8),
            "total_usd": round(jev_total, 8),
            "rates": {
                "input_per_mtok": JEV_INPUT_PER_MTOK,
                "output_per_mtok": JEV_OUTPUT_PER_MTOK,
            },
        },
        "llm_stand_in": {
            "calls": llm_calls,
            "input_usd": round(llm_in, 8),
            "output_usd": round(llm_out, 8),
            "total_usd": round(llm_total, 8),
            "rates": {
                "input_per_mtok": LLM_INPUT_PER_MTOK,
                "output_per_mtok": LLM_OUTPUT_PER_MTOK,
            },
            "note": "Illustrative $2 / $6 chat model, one serial call per question.",
        },
        "savings_vs_llm": round(savings, 4),
        "notes": [
            "Jev bills input tokens only. Output is free.",
            "Questions in one request share the state and run in parallel.",
            "LLM stand-in is a comparison sketch, not a quote from any vendor.",
        ],
    }


def fanout_comparison(
    state_tokens: int,
    question_tokens: int,
    n_questions: int,
) -> dict[str, Any]:
    """One batched Jev call vs N serial Jev calls (state resent each time)."""
    n_questions = max(1, int(n_questions))
    batched_input = state_tokens + question_tokens * n_questions
    serial_input = n_questions * (state_tokens + question_tokens)
    batched = estimate_cost(batched_input, questions=n_questions)
    serial = estimate_cost(serial_input, questions=n_questions)
    factor = 0.0 if batched["jev"]["total_usd"] <= 0 else (
        serial["jev"]["total_usd"] / batched["jev"]["total_usd"]
    )
    return {
        "n_questions": n_questions,
        "state_tokens": state_tokens,
        "question_tokens": question_tokens,
        "batched_input_tokens": batched_input,
        "serial_input_tokens": serial_input,
        "batched_usd": batched["jev"]["total_usd"],
        "serial_usd": serial["jev"]["total_usd"],
        "cheaper_factor": round(factor, 2),
        "note": "TypeSafe's parallel-questions cookbook reports ~12× cheaper and ~10× faster for 13 questions over one article.",
    }
