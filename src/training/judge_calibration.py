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
) -> CalibrationResult:
    """Score one case and check it, isolating any scorer fault."""
    bands = case["expected"].get(scorer_kind, {})
    try:
        score = scorer.score(case["generated"], case["reference"])
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
) -> CalibrationReport:
    """Run ``scorer`` over ``cases`` and check the per-kind expected bands.

    Args:
        scorer: Any ``ContentScorer`` implementation.
        scorer_kind: Selects which band set applies (currently "overlap"). A kind
            with no declared bands for a case leaves that case unchecked.
        cases: Calibration cases to run.

    Returns:
        A ``CalibrationReport``. ``passed`` is True only when every case passed;
        a raising scorer counts as both a failure and an error.
    """
    results = [_run_case(scorer, scorer_kind, case) for case in cases]
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


def _format_band(band: Band) -> str:
    """Render an inclusive band as ``[lo-hi]`` with open bounds as infinities."""
    low, high = band
    lo = "-inf" if low is None else f"{low:.2f}"
    hi = "+inf" if high is None else f"{high:.2f}"
    return f"[{lo}-{hi}]"


def _format_result(result: CalibrationResult) -> str:
    """Render one case's outcome for one scorer as a single line."""
    if result["error"] is not None:
        return f"ERROR ({result['error']})"
    if not result["checks"]:
        return "no bands declared - not checked"
    parts = []
    for check in result["checks"]:
        actual = "None" if check["actual"] is None else f"{check['actual']:.3f}"
        verdict = "PASS" if check["passed"] else "FAIL"
        parts.append(f"{check['metric']} {actual} {_format_band(check['band'])} {verdict}")
    return " | ".join(parts)


def format_report(reports: Sequence[CalibrationReport]) -> str:
    """Render one or more calibration reports as a side-by-side scorecard.

    Args:
        reports: One report per scorer kind. All reports must have been run over
            the same cases in the same order.

    Returns:
        A printable scorecard ending in a ``RESULT: PASS``/``RESULT: FAIL`` line,
        where any failing scorer fails the whole scorecard.
    """
    lines = ["", "Judge Calibration Scorecard", "=" * 72]
    if not reports:
        lines += ["(no scorers run)", ""]
        return "\n".join(lines)

    width = max(len(report["scorer_kind"]) for report in reports)
    for index, first_case in enumerate(reports[0]["results"]):
        lines.append("")
        lines.append(f"{first_case['name']} - {first_case['description']}")
        for report in reports:
            result = report["results"][index]
            lines.append(f"  {report['scorer_kind']:<{width}} : {_format_result(result)}")

    lines += ["", "-" * 72]
    for report in reports:
        passed_count = report["total"] - report["failed"]
        lines.append(
            f"  {report['scorer_kind']:<{width}} : {passed_count}/{report['total']} passed "
            f"({report['failed']} failed, {report['errors']} errors)"
        )
    overall = all(report["passed"] for report in reports)
    lines += [f"RESULT: {'PASS' if overall else 'FAIL'}", ""]
    return "\n".join(lines)
