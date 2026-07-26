"""Unit tests for the LLM-judge content scorer (Phase 3b)."""

from src.training.llm_judge_scorer import LLMJudgeScorer

CASE_A = {
    "summary_suffix": "door unlocks on valid keyfob",
    "preconditions": "ignition on; keyfob paired",
    "test_steps": "1. Press the unlock button.",
    "expected_result": "Door unlocks within 200 ms.",
    "test_type": "functional",
}
CASE_B = {
    "summary_suffix": "wipers follow rain intensity",
    "preconditions": "vehicle running; rain sensor enabled",
    "test_steps": "1. Simulate heavy rainfall.",
    "expected_result": "Wipers switch to maximum speed within 500 ms.",
    "test_type": "functional",
}


class _ScriptedClient:
    """Returns queued responses in call order; records the calls."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def generate_completion(
        self, model_name, prompt, is_json=False, return_full_response=True, format_schema=None
    ):
        self.calls.append({"model": model_name, "prompt": prompt})
        return self._responses.pop(0)


def test_perfect_match_and_quality():
    client = _ScriptedClient(['{"matches": [[0, 0], [1, 1]]}', '{"quality": 0.9}'])
    score = LLMJudgeScorer().score([CASE_A, CASE_B], [CASE_A, CASE_B], client=client)
    assert score == {"precision": 1.0, "recall": 1.0, "f1": 1.0, "quality": 0.9}


def test_partial_match():
    client = _ScriptedClient(['{"matches": [[0, 0]]}', '{"quality": 0.5}'])
    score = LLMJudgeScorer().score([CASE_A, CASE_B], [CASE_A], client=client)
    assert score["precision"] == 0.5
    assert score["recall"] == 1.0
    assert round(score["f1"], 3) == 0.667
    assert score["quality"] == 0.5


def test_one_to_one_enforced():
    # Both generated cases claim the single reference; only one counts.
    client = _ScriptedClient(['{"matches": [[0, 0], [1, 0]]}', '{"quality": 0.4}'])
    score = LLMJudgeScorer().score([CASE_A, CASE_B], [CASE_A], client=client)
    assert score["precision"] == 0.5
    assert score["recall"] == 1.0


def test_quality_clamped_high():
    client = _ScriptedClient(['{"matches": []}', '{"quality": 1.3}'])
    score = LLMJudgeScorer().score([CASE_A], [CASE_A], client=client)
    assert score["quality"] == 1.0


def test_quality_clamped_low():
    client = _ScriptedClient(['{"matches": []}', '{"quality": -0.2}'])
    score = LLMJudgeScorer().score([CASE_A], [CASE_A], client=client)
    assert score["quality"] == 0.0


def test_malformed_matching_nulls_prf_but_keeps_quality():
    client = _ScriptedClient(["not json at all", '{"quality": 0.7}'])
    score = LLMJudgeScorer().score([CASE_A], [CASE_A], client=client)
    assert score["precision"] is None
    assert score["recall"] is None
    assert score["f1"] is None
    assert score["quality"] == 0.7


def test_malformed_quality_nulls_quality_but_keeps_prf():
    client = _ScriptedClient(['{"matches": [[0, 0]]}', "not json"])
    score = LLMJudgeScorer().score([CASE_A], [CASE_A], client=client)
    assert score["precision"] == 1.0
    assert score["quality"] is None


def test_no_reference_returns_none():
    client = _ScriptedClient([])  # no calls expected
    assert LLMJudgeScorer().score([CASE_A], [], client=client) is None
    assert client.calls == []


def test_empty_generation_short_circuits():
    client = _ScriptedClient([])  # no calls expected
    score = LLMJudgeScorer().score([], [CASE_A], client=client)
    assert score == {"precision": None, "recall": 0.0, "f1": 0.0, "quality": None}
    assert client.calls == []
