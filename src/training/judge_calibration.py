"""Calibration harness for content scorers (Phase 3c).

Runs a ``ContentScorer`` over cases whose correct scores are known by
construction and checks each declared metric against an inclusive tolerance
band. No generation model runs here — fixtures feed the scorer directly, so the
result measures the scorer in isolation rather than the scorer plus a model.

Bands are keyed per scorer kind ("overlap" / "llm"), which lets a case encode a
known limitation of one scorer as expected behaviour while holding another to a
higher bar (see ``judge_calibration_cases.DEFAULT_CALIBRATION_CASES``).
"""

from collections.abc import Sequence  # noqa: TC003 -- must resolve at runtime for get_type_hints()
from typing import Any, TypedDict

# ContentScore/ContentScorer must resolve at runtime for get_type_hints() to work
from src.training.content_scorer import ContentScore, ContentScorer  # noqa: TC001

# Inclusive (min, max); either bound may be None to leave that side open.
Band = tuple[float | None, float | None]


class CalibrationCase(TypedDict):
    """One gold-by-construction case with per-scorer expected bands."""

    name: str
    description: str
    generated: list[dict]
    reference: list[dict]
    expected: dict[str, dict[str, Band]]


class MetricCheck(TypedDict):
    """Outcome of checking one metric against its declared band."""

    metric: str
    band: Band
    actual: float | None
    passed: bool


class CalibrationResult(TypedDict):
    """Per-case outcome: the actual score, each band check, and any fault."""

    name: str
    description: str
    score: ContentScore | None
    checks: list[MetricCheck]
    error: str | None
    passed: bool


class CalibrationReport(TypedDict):
    """Aggregate outcome for one scorer over all cases."""

    scorer_kind: str
    results: list[CalibrationResult]
    total: int
    failed: int
    errors: int
    passed: bool


def _within(value: float | None, band: Band) -> bool:
    """Return True when ``value`` falls inside the inclusive ``band``.

    Args:
        value: The measured metric, or None when the scorer left it undefined.
        band: Inclusive ``(min, max)``; either bound may be None.

    Returns:
        False when ``value`` is None — a metric that declared a band but was
        never produced is a breach, not a pass.
    """
    if value is None:
        return False
    low, high = band
    if low is not None and value < low:
        return False
    return not (high is not None and value > high)


def _check_metrics(score: ContentScore | None, bands: dict[str, Band]) -> list[MetricCheck]:
    """Check every declared metric of ``score`` against its band."""
    checks: list[MetricCheck] = []
    # A TypedDict is a plain dict at runtime; copy it so the metric name can be
    # a variable key without tripping TypedDict's literal-key typing.
    actuals: dict[str, Any] = dict(score) if score is not None else {}
    for metric, band in bands.items():
        actual = actuals.get(metric)
        checks.append(
            {
                "metric": metric,
                "band": band,
                "actual": actual,
                "passed": _within(actual, band),
            }
        )
    return checks


def _run_case(
    scorer: ContentScorer,
    scorer_kind: str,
    case: CalibrationCase,
    client: Any,
    judge_model: str | None,
) -> CalibrationResult:
    """Score one case and check it, isolating any scorer fault."""
    bands = case["expected"].get(scorer_kind, {})
    try:
        score = scorer.score(
            case["generated"], case["reference"], client=client, judge_model=judge_model
        )
    except Exception as exc:  # noqa: BLE001 - a scorer fault must not abort the run
        return {
            "name": case["name"],
            "description": case["description"],
            "score": None,
            "checks": [],
            "error": f"{type(exc).__name__}: {exc}",
            "passed": False,
        }

    checks = _check_metrics(score, bands)
    return {
        "name": case["name"],
        "description": case["description"],
        "score": score,
        "checks": checks,
        "error": None,
        "passed": all(check["passed"] for check in checks),
    }


def run_calibration(
    scorer: ContentScorer,
    scorer_kind: str,
    cases: Sequence[CalibrationCase],
    *,
    client: Any = None,
    judge_model: str | None = None,
) -> CalibrationReport:
    """Run ``scorer`` over ``cases`` and check the per-kind expected bands.

    Args:
        scorer: Any ``ContentScorer`` implementation.
        scorer_kind: Selects which band set applies ("overlap" or "llm"). A kind
            with no declared bands for a case leaves that case unchecked.
        cases: Calibration cases to run.
        client: Optional model client, threaded to scorers that call an LLM.
        judge_model: Optional judge model name, threaded to LLM scorers.

    Returns:
        A ``CalibrationReport``. ``passed`` is True only when every case passed;
        a raising scorer counts as both a failure and an error.
    """
    results = [_run_case(scorer, scorer_kind, case, client, judge_model) for case in cases]
    failed = sum(1 for result in results if not result["passed"])
    errors = sum(1 for result in results if result["error"] is not None)
    return {
        "scorer_kind": scorer_kind,
        "results": results,
        "total": len(results),
        "failed": failed,
        "errors": errors,
        "passed": failed == 0,
    }
