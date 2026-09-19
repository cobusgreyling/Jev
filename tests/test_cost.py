from jev_lab.cost import estimate_cost, fanout_comparison


def test_output_is_free():
    est = estimate_cost(1_000_000, 1_000_000, questions=1)
    assert est["jev"]["output_usd"] == 0.0
    assert est["jev"]["input_usd"] == 0.042


def test_more_questions_on_llm_stand_in_not_jev_input():
    one = estimate_cost(1000, questions=1)
    ten = estimate_cost(1000, questions=10)
    assert one["jev"]["total_usd"] == ten["jev"]["total_usd"]
    assert ten["llm_stand_in"]["total_usd"] > one["llm_stand_in"]["total_usd"]


def test_fanout_cheaper_than_serial():
    cmp_ = fanout_comparison(3000, 80, 13)
    assert cmp_["batched_input_tokens"] < cmp_["serial_input_tokens"]
    assert cmp_["cheaper_factor"] > 1
