"""Unit tests for the Phase 3c judge calibration runner.

Uses scripted fake scorers so the runner's band-checking, error isolation, and
aggregation are pinned without needing Ollama.
"""

from typing import TYPE_CHECKING, Any

import pytest

from src.training.content_scorer import ReferenceOverlapScorer
from src.training.judge_calibration import CalibrationCase, run_calibration
from src.training.judge_calibration_cases import DEFAULT_CALIBRATION_CASES

if TYPE_CHECKING:
    from src.training.content_scorer import ContentScore


class _FixedScorer:
    """Returns a preset ContentScore for every case."""

    def __init__(self, score: ContentScore | None) -> None:
        self._score = score

    def score(
        self,
        generated_cases: list[dict],
        reference_cases: list[dict],
        *,
        client: Any = None,
        judge_model: str | None = None,
    ) -> ContentScore | None:
        return self._score


class _RaisingScorer:
    """Raises on the first call, then returns a perfect score."""

    def __init__(self) -> None:
        self.calls = 0

    def score(
        self,
        generated_cases: list[dict],
        reference_cases: list[dict],
        *,
        client: Any = None,
        judge_model: str | None = None,
    ) -> ContentScore | None:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("judge exploded")
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "quality": 1.0}


def _case(name: str, expected: dict) -> CalibrationCase:
    return {
        "name": name,
        "description": f"{name} description",
        "generated": [{"summary_suffix": "g"}],
        "reference": [{"summary_suffix": "r"}],
        "expected": expected,
    }


def test_all_bands_within_range_passes():
    cases = [_case("identity", {"overlap": {"f1": (0.9, 1.0)}})]
    scorer = _FixedScorer({"precision": 1.0, "recall": 1.0, "f1": 1.0, "quality": None})

    report = run_calibration(scorer, "overlap", cases)

    assert report["passed"] is True
    assert report["total"] == 1
    assert report["failed"] == 0
    assert report["errors"] == 0
    assert report["results"][0]["checks"][0]["passed"] is True


def test_breached_band_fails_the_report():
    cases = [_case("paraphrase", {"llm": {"f1": (0.7, 1.0)}})]
    scorer = _FixedScorer({"precision": 0.2, "recall": 0.2, "f1": 0.2, "quality": None})

    report = run_calibration(scorer, "llm", cases)

    assert report["passed"] is False
    assert report["failed"] == 1
    assert report["errors"] == 0
    assert report["results"][0]["checks"][0]["actual"] == 0.2


def test_none_metric_with_declared_band_is_a_breach_not_a_crash():
    cases = [_case("empty", {"llm": {"quality": (0.5, 1.0)}})]
    scorer = _FixedScorer({"precision": None, "recall": 0.0, "f1": 0.0, "quality": None})

    report = run_calibration(scorer, "llm", cases)

    assert report["passed"] is False
    assert report["results"][0]["checks"][0]["actual"] is None
    assert report["results"][0]["error"] is None


def test_scorer_returning_none_with_declared_band_is_a_breach():
    cases = [_case("no_reference", {"overlap": {"f1": (0.9, 1.0)}})]

    report = run_calibration(_FixedScorer(None), "overlap", cases)

    assert report["passed"] is False
    assert report["results"][0]["score"] is None


def test_scorer_exception_is_isolated_and_run_continues():
    cases = [
        _case("first", {"llm": {"f1": (0.9, 1.0)}}),
        _case("second", {"llm": {"f1": (0.9, 1.0)}}),
    ]
    scorer = _RaisingScorer()

    report = run_calibration(scorer, "llm", cases)

    assert scorer.calls == 2, "run must continue past a raising case"
    assert report["errors"] == 1
    assert report["failed"] == 1
    assert "judge exploded" in report["results"][0]["error"]
    assert report["results"][1]["passed"] is True


def test_bands_are_selected_by_scorer_kind():
    cases = [_case("paraphrase", {"overlap": {"f1": (0.0, 0.35)}, "llm": {"f1": (0.7, 1.0)}})]
    scorer = _FixedScorer({"precision": 0.0, "recall": 0.0, "f1": 0.0, "quality": None})

    assert run_calibration(scorer, "overlap", cases)["passed"] is True
    assert run_calibration(scorer, "llm", cases)["passed"] is False


def test_kind_with_no_declared_bands_is_not_checked():
    cases = [_case("identity", {"overlap": {"f1": (0.9, 1.0)}})]
    scorer = _FixedScorer({"precision": 0.0, "recall": 0.0, "f1": 0.0, "quality": None})

    report = run_calibration(scorer, "llm", cases)

    assert report["results"][0]["checks"] == []
    assert report["passed"] is True


def test_bands_are_inclusive_at_both_ends():
    cases = [_case("edge", {"overlap": {"f1": (0.5, 0.5)}})]
    scorer = _FixedScorer({"precision": 0.5, "recall": 0.5, "f1": 0.5, "quality": None})

    assert run_calibration(scorer, "overlap", cases)["passed"] is True


def test_open_ended_band_accepts_none_bound():
    cases = [_case("open", {"overlap": {"f1": (0.9, None)}})]
    scorer = _FixedScorer({"precision": 1.0, "recall": 1.0, "f1": 1.0, "quality": None})

    assert run_calibration(scorer, "overlap", cases)["passed"] is True


def test_client_and_judge_model_are_threaded_to_the_scorer():
    seen: dict[str, Any] = {}

    class _Recording:
        def score(self, generated_cases, reference_cases, *, client=None, judge_model=None):
            seen["client"] = client
            seen["judge_model"] = judge_model
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "quality": None}

    sentinel = object()
    run_calibration(
        _Recording(),
        "llm",
        [_case("identity", {"llm": {"f1": (0.9, 1.0)}})],
        client=sentinel,
        judge_model="llama3.1:8b",
    )

    assert seen["client"] is sentinel
    assert seen["judge_model"] == "llama3.1:8b"


def _overlap_report():
    return run_calibration(ReferenceOverlapScorer(0.85), "overlap", DEFAULT_CALIBRATION_CASES)


def test_default_cases_have_the_five_expected_names():
    names = [case["name"] for case in DEFAULT_CALIBRATION_CASES]
    assert names == ["identity", "disjoint", "subset", "paraphrase", "noise"]


def test_every_default_case_declares_bands_for_both_scorer_kinds():
    for case in DEFAULT_CALIBRATION_CASES:
        assert set(case["expected"]) == {"overlap", "llm"}, case["name"]


def test_overlap_column_passes_every_default_case():
    """The overlap scorer is deterministic, so this pins its real behavior."""
    report = _overlap_report()

    failures = [r["name"] for r in report["results"] if not r["passed"]]
    assert failures == [], f"overlap breached bands for: {failures}"
    assert report["errors"] == 0


def test_overlap_scores_identity_perfectly():
    result = _overlap_report()["results"][0]
    assert result["score"]["f1"] == pytest.approx(1.0)


def test_overlap_fails_to_match_paraphrases():
    """The known limitation this whole phase exists to measure."""
    result = next(r for r in _overlap_report()["results"] if r["name"] == "paraphrase")
    assert result["score"]["f1"] <= 0.35
    assert result["passed"] is True, "the low score IS the expected overlap behavior"


def test_overlap_subset_recall_is_one_half():
    result = next(r for r in _overlap_report()["results"] if r["name"] == "subset")
    assert result["score"]["recall"] == pytest.approx(0.5)
    assert result["score"]["precision"] == pytest.approx(1.0)


def test_overlap_noise_precision_penalises_padding():
    result = next(r for r in _overlap_report()["results"] if r["name"] == "noise")
    assert result["score"]["recall"] == pytest.approx(1.0)
    assert result["score"]["precision"] == pytest.approx(0.6)
