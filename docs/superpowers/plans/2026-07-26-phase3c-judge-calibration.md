# Phase 3c — Judge Calibration Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a calibration harness that measures whether the Phase 3b LLM judge is trustworthy, by scoring gold-by-construction fixtures through any `ContentScorer` and reporting pass/fail against declared tolerance bands.

**Architecture:** Two new modules (`judge_calibration.py` for types + runner + report, `judge_calibration_cases.py` for fixture data) plus a `--validate-judge` CLI mode on `utilities/train_vision_model.py`. The runner depends only on the `ContentScorer` protocol, so both scorers are validated through identical code. No generation model runs anywhere in this path — fixtures feed the scorer directly, which is what isolates the judge from model noise.

**Tech Stack:** Python 3.14.6+, `TypedDict` for data / `__slots__` classes for behaviour (existing `content_scorer.py` convention), pytest, ruff, mypy, local Ollama for the opt-in live test only.

**Spec:** `docs/superpowers/specs/2026-07-26-phase3c-judge-calibration-design.md`

## Global Constraints

- Python 3.14.6+; no backward compatibility shims.
- **No cloud API calls anywhere**, including eval and training paths (`CLAUDE.md` project principle, confirmed 2026-07-26 as a hard rule). The judge is local Ollama only.
- `ruff check src/ main.py utilities/` is the enforced gate and must pass before every commit.
- Do NOT mass-reformat or mass-fix pre-existing `ruff format` drift (~11 files) or pre-existing mypy errors (~310). Only format/type-clean files you actually touch.
- Google Python Style Guide docstrings on every module, class, and function.
- `CHANGELOG.md` updated for the feature (Task 5).
- Classes in this codebase declare `__slots__`; adding an instance attribute requires adding it to the slots tuple first.
- Canonical test-case schema is exactly: `summary_suffix`, `preconditions`, `test_steps`, `expected_result`, `test_type`. Never reintroduce `action`/`data`.
- A scorer fault must never abort a run — the established convention at `llm_judge_scorer.py:131` and `vision_raft_trainer.py:1145`.
- `evaluate_model` and `vision_raft_trainer.py` are **not modified by this plan**.
- Commit style: Conventional Commits, lowercase, imperative, no trailing period, subject < 72 chars. End commit messages with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- Work happens on branch `feat/phase3c-judge-calibration` (already created). Never commit to `main`.

## File Structure

| File | Responsibility |
|------|----------------|
| `src/training/judge_calibration.py` | Types (`Band`, `CalibrationCase`, `MetricCheck`, `CalibrationResult`, `CalibrationReport`), band checking, `run_calibration`, `format_report` |
| `src/training/judge_calibration_cases.py` | `DEFAULT_CALIBRATION_CASES` fixture data only — no logic |
| `utilities/train_vision_model.py` | `--validate-judge` mode, arg validation, exit codes |
| `tests/training/test_judge_calibration.py` | Unit tests (fake scorer) + deterministic overlap column over all fixtures |
| `tests/training/test_judge_calibration_integration.py` | Opt-in live-Ollama llm column |
| `docs/training/README.md` | Calibration section |
| `CHANGELOG.md` | Added entry |

---

### Task 1: Calibration types and runner

**Files:**
- Create: `src/training/judge_calibration.py`
- Test: `tests/training/test_judge_calibration.py`

**Interfaces:**
- Consumes: `ContentScore`, `ContentScorer` from `src/training/content_scorer.py`
- Produces:
  - `Band = tuple[float | None, float | None]`
  - `CalibrationCase` TypedDict: `name: str`, `description: str`, `generated: list[dict]`, `reference: list[dict]`, `expected: dict[str, dict[str, Band]]`
  - `MetricCheck` TypedDict: `metric: str`, `band: Band`, `actual: float | None`, `passed: bool`
  - `CalibrationResult` TypedDict: `name: str`, `description: str`, `score: ContentScore | None`, `checks: list[MetricCheck]`, `error: str | None`, `passed: bool`
  - `CalibrationReport` TypedDict: `scorer_kind: str`, `results: list[CalibrationResult]`, `total: int`, `failed: int`, `errors: int`, `passed: bool`
  - `run_calibration(scorer, scorer_kind, cases, *, client=None, judge_model=None) -> CalibrationReport`

**Deliberate deviation from the spec:** the spec sketched `cases` as defaulting to `DEFAULT_CALIBRATION_CASES`. It must NOT have that default — `judge_calibration_cases.py` imports `CalibrationCase` from `judge_calibration.py`, so a default referencing the fixtures would create a circular import. `cases` is a required parameter; callers pass `DEFAULT_CALIBRATION_CASES` explicitly (Task 4 does).

- [ ] **Step 1: Write the failing tests**

Create `tests/training/test_judge_calibration.py`:

```python
"""Unit tests for the Phase 3c judge calibration runner.

Uses scripted fake scorers so the runner's band-checking, error isolation, and
aggregation are pinned without needing Ollama.
"""

from typing import Any

import pytest

from src.training.content_scorer import ContentScore
from src.training.judge_calibration import CalibrationCase, run_calibration


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/training/test_judge_calibration.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.training.judge_calibration'`

- [ ] **Step 3: Write the implementation**

Create `src/training/judge_calibration.py`:

```python
"""Calibration harness for content scorers (Phase 3c).

Runs a ``ContentScorer`` over cases whose correct scores are known by
construction and checks each declared metric against an inclusive tolerance
band. No generation model runs here — fixtures feed the scorer directly, so the
result measures the scorer in isolation rather than the scorer plus a model.

Bands are keyed per scorer kind ("overlap" / "llm"), which lets a case encode a
known limitation of one scorer as expected behaviour while holding another to a
higher bar (see ``judge_calibration_cases.DEFAULT_CALIBRATION_CASES``).
"""

from collections.abc import Sequence
from typing import Any, TypedDict

from src.training.content_scorer import ContentScore, ContentScorer

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
    if high is not None and value > high:
        return False
    return True


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/training/test_judge_calibration.py -v`
Expected: PASS — 10 passed

- [ ] **Step 5: Lint, format, type-check**

```bash
ruff check src/training/judge_calibration.py tests/training/test_judge_calibration.py --fix
ruff format src/training/judge_calibration.py tests/training/test_judge_calibration.py
mypy src/training/judge_calibration.py --python-version 3.14
```
Expected: ruff "All checks passed!"; mypy reports no NEW errors in this file.

- [ ] **Step 6: Re-run tests after formatting**

Run: `python3 -m pytest tests/training/test_judge_calibration.py -v`
Expected: PASS — 10 passed

- [ ] **Step 7: Commit**

```bash
git add src/training/judge_calibration.py tests/training/test_judge_calibration.py
git commit -m "feat(training): add judge calibration runner and band checking

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Gold-by-construction fixture cases

**Files:**
- Create: `src/training/judge_calibration_cases.py`
- Modify: `tests/training/test_judge_calibration.py` (append the overlap-column tests)

**Interfaces:**
- Consumes: `CalibrationCase`, `Band`, `run_calibration` from Task 1; `ReferenceOverlapScorer` from `src/training/content_scorer.py`
- Produces: `DEFAULT_CALIBRATION_CASES: tuple[CalibrationCase, ...]` with exactly five cases named `identity`, `disjoint`, `subset`, `paraphrase`, `noise`

**Important:** the overlap scorer's actual behaviour on these specific strings is an empirical fact, not a guess. Step 4 verifies it and tells you what to do if reality disagrees.

- [ ] **Step 1: Write the fixture module**

Create `src/training/judge_calibration_cases.py`:

```python
"""Gold-by-construction calibration cases for content scorers (Phase 3c).

Each case pairs a generated set with a reference set whose correct score is
known by construction, plus the inclusive bands each scorer kind is expected to
land in. Cases use the canonical test-case schema.

``paraphrase`` is the discriminating case: the deterministic overlap scorer
matches on string similarity and is EXPECTED to fail it, while the LLM judge
must clear it to justify its cost. Paraphrases are hand-authored rather than
model-generated, so the ground truth never depends on a model's opinion.
"""

from src.training.judge_calibration import CalibrationCase

# --- Reference scenarios -----------------------------------------------------

_REF_DOOR_LOCK: dict = {
    "summary_suffix": "Door locks when vehicle exceeds 20 km/h",
    "preconditions": "Vehicle stationary, all doors closed and unlocked",
    "test_steps": (
        "1. Start the engine\n"
        "2. Accelerate the vehicle to 25 km/h\n"
        "3. Observe the door lock actuators"
    ),
    "expected_result": "All four doors lock automatically once speed exceeds 20 km/h",
    "test_type": "Functional",
}

_REF_ANTI_PINCH: dict = {
    "summary_suffix": "Driver window reverses on obstruction during auto-close",
    "preconditions": "Ignition on, driver window fully open",
    "test_steps": (
        "1. Trigger auto-close on the driver window\n"
        "2. Insert a test obstacle in the window path"
    ),
    "expected_result": "Window stops and reverses direction within 100 ms of contact",
    "test_type": "Safety",
}

_REF_MIRROR_FOLD: dict = {
    "summary_suffix": "Exterior mirrors fold when vehicle is locked",
    "preconditions": "Vehicle unlocked, mirrors unfolded, ignition off",
    "test_steps": (
        "1. Lock the vehicle with the remote key fob\n2. Observe both exterior mirrors"
    ),
    "expected_result": "Both exterior mirrors fold inward within 3 seconds of locking",
    "test_type": "Functional",
}

_REF_HAZARD: dict = {
    "summary_suffix": "Hazard lights activate on emergency braking",
    "preconditions": "Vehicle travelling at 80 km/h on a dry surface",
    "test_steps": "1. Apply full braking force\n2. Observe the hazard indicators",
    "expected_result": (
        "Hazard lights flash automatically while deceleration exceeds the threshold"
    ),
    "test_type": "Safety",
}

# --- Paraphrases: same scenarios, deliberately different wording -------------

_PARA_DOOR_LOCK: dict = {
    "summary_suffix": "Automatic central locking engages above 20 kph",
    "preconditions": "Car at rest, every door shut and in the unlocked state",
    "test_steps": (
        "1. Switch on the powertrain\n"
        "2. Drive until the speedometer reads 25 kph\n"
        "3. Listen for the latch motors"
    ),
    "expected_result": (
        "Every door latches by itself as soon as the threshold speed is passed"
    ),
    "test_type": "Functional",
}

_PARA_ANTI_PINCH: dict = {
    "summary_suffix": "Anti-pinch protection retracts the driver glass",
    "preconditions": "Power mode on, glass on the driver side lowered completely",
    "test_steps": (
        "1. Activate one-touch up on the driver side\n"
        "2. Place a blocking object into the glass travel path"
    ),
    "expected_result": (
        "Travel halts and the glass retreats no later than 100 ms after touching the object"
    ),
    "test_type": "Safety",
}

_PARA_MIRROR_FOLD: dict = {
    "summary_suffix": "Wing mirrors retract on central locking",
    "preconditions": "Doors in open state, mirrors extended, engine switched off",
    "test_steps": (
        "1. Press lock on the keyless remote\n2. Watch the wing mirrors on both sides"
    ),
    "expected_result": "Each wing mirror swings inward no more than 3 seconds after lock",
    "test_type": "Functional",
}

# --- Unrelated scenarios -----------------------------------------------------

_OTHER_AIR_FILTER: dict = {
    "summary_suffix": "Cabin air filter replacement interval warning",
    "preconditions": "Odometer at 14,900 km, filter service counter active",
    "test_steps": (
        "1. Drive until the odometer reads 15,000 km\n"
        "2. Read the driver information cluster"
    ),
    "expected_result": "Cluster shows the cabin air filter service reminder",
    "test_type": "Functional",
}

_OTHER_BLUETOOTH: dict = {
    "summary_suffix": "Infotainment Bluetooth pairing with two phones",
    "preconditions": "Infotainment on, no devices paired",
    "test_steps": (
        "1. Pair the first handset\n"
        "2. Pair the second handset\n"
        "3. Play audio from the second handset"
    ),
    "expected_result": "Both handsets remain paired and audio streams from the second",
    "test_type": "Functional",
}

_OTHER_TYRE_PRESSURE: dict = {
    "summary_suffix": "Tyre pressure warning at 1.8 bar",
    "preconditions": "All tyres inflated to 2.4 bar, ignition on",
    "test_steps": (
        "1. Deflate the front left tyre to 1.8 bar\n"
        "2. Drive above 25 km/h for two minutes"
    ),
    "expected_result": "Low tyre pressure telltale illuminates for the front left wheel",
    "test_type": "Functional",
}

_THREE_REFS = [_REF_DOOR_LOCK, _REF_ANTI_PINCH, _REF_MIRROR_FOLD]

DEFAULT_CALIBRATION_CASES: tuple[CalibrationCase, ...] = (
    {
        "name": "identity",
        "description": "generated == reference (3 cases)",
        "generated": list(_THREE_REFS),
        "reference": list(_THREE_REFS),
        "expected": {
            "overlap": {"precision": (0.9, 1.0), "recall": (0.9, 1.0), "f1": (0.9, 1.0)},
            "llm": {"precision": (0.9, 1.0), "recall": (0.9, 1.0), "f1": (0.9, 1.0)},
        },
    },
    {
        "name": "disjoint",
        "description": "3 completely unrelated cases",
        "generated": [_OTHER_AIR_FILTER, _OTHER_BLUETOOTH, _OTHER_TYRE_PRESSURE],
        "reference": list(_THREE_REFS),
        "expected": {
            "overlap": {"recall": (0.0, 0.1), "f1": (0.0, 0.1)},
            "llm": {"recall": (0.0, 0.1), "f1": (0.0, 0.1)},
        },
    },
    {
        "name": "subset",
        "description": "2 of 4 reference cases, verbatim",
        "generated": [_REF_DOOR_LOCK, _REF_MIRROR_FOLD],
        "reference": [_REF_DOOR_LOCK, _REF_ANTI_PINCH, _REF_MIRROR_FOLD, _REF_HAZARD],
        "expected": {
            "overlap": {"recall": (0.4, 0.6), "precision": (0.9, 1.0)},
            "llm": {"recall": (0.4, 0.6), "precision": (0.9, 1.0)},
        },
    },
    {
        "name": "paraphrase",
        "description": "3 reference scenarios reworded — the discriminating case",
        "generated": [_PARA_DOOR_LOCK, _PARA_ANTI_PINCH, _PARA_MIRROR_FOLD],
        "reference": list(_THREE_REFS),
        "expected": {
            # Overlap matches on string similarity and is EXPECTED to miss these.
            "overlap": {"f1": (0.0, 0.35)},
            # The judge's claimed advantage — this is what Phase 3b must earn.
            "llm": {"f1": (0.7, 1.0)},
        },
    },
    {
        "name": "noise",
        "description": "all 3 reference cases verbatim plus 2 unrelated extras",
        "generated": [*_THREE_REFS, _OTHER_AIR_FILTER, _OTHER_TYRE_PRESSURE],
        "reference": list(_THREE_REFS),
        "expected": {
            "overlap": {"recall": (0.9, 1.0), "precision": (0.4, 0.8)},
            "llm": {"recall": (0.9, 1.0), "precision": (0.4, 0.8)},
        },
    },
)
```

- [ ] **Step 2: Write the failing overlap-column tests**

Append to `tests/training/test_judge_calibration.py`:

```python
from src.training.content_scorer import ReferenceOverlapScorer
from src.training.judge_calibration_cases import DEFAULT_CALIBRATION_CASES


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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python3 -m pytest tests/training/test_judge_calibration.py -v -k "overlap or default_cases"`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.training.judge_calibration_cases'` (before Step 1's file exists) or assertion failures.

- [ ] **Step 4: Verify the fixtures empirically and reconcile**

The bands above assume how `SequenceMatcher` behaves on these exact strings. Verify:

```bash
python3 -c "
from src.training.content_scorer import ReferenceOverlapScorer
from src.training.judge_calibration import run_calibration
from src.training.judge_calibration_cases import DEFAULT_CALIBRATION_CASES
r = run_calibration(ReferenceOverlapScorer(0.85), 'overlap', DEFAULT_CALIBRATION_CASES)
for res in r['results']:
    print(res['name'], res['score'], 'PASS' if res['passed'] else 'FAIL')
"
```

Expected: `identity` f1 1.0; `disjoint` f1 0.0; `subset` recall 0.5 precision 1.0; `paraphrase` f1 0.0; `noise` recall 1.0 precision 0.6 — all PASS.

**If `paraphrase` scores above 0.35**, a paraphrase is too close to its reference in `test_steps` / `expected_result` / `preconditions` (the deduplicator's compared fields). **Reword that paraphrase further — do NOT widen the band.** The band encodes the design intent; loosening it would erase the very signal this case exists to produce.

**If `identity` scores below 1.0**, the generated and reference lists have drifted apart — they must be the same dicts.

- [ ] **Step 5: Run the full calibration test file**

Run: `python3 -m pytest tests/training/test_judge_calibration.py -v`
Expected: PASS — 17 passed

- [ ] **Step 6: Lint, format, type-check**

```bash
ruff check src/training/judge_calibration_cases.py tests/training/test_judge_calibration.py --fix
ruff format src/training/judge_calibration_cases.py tests/training/test_judge_calibration.py
mypy src/training/judge_calibration_cases.py --python-version 3.14
```
Expected: ruff "All checks passed!"; no new mypy errors.

- [ ] **Step 7: Commit**

```bash
git add src/training/judge_calibration_cases.py tests/training/test_judge_calibration.py
git commit -m "feat(training): add gold-by-construction judge calibration fixtures

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Scorecard report formatting

**Files:**
- Modify: `src/training/judge_calibration.py` (append `format_report` and `_format_result`)
- Modify: `tests/training/test_judge_calibration.py` (append formatting tests)

**Interfaces:**
- Consumes: `CalibrationReport`, `CalibrationResult` from Task 1
- Produces: `format_report(reports: Sequence[CalibrationReport]) -> str`

- [ ] **Step 1: Write the failing tests**

Append to `tests/training/test_judge_calibration.py`:

```python
from src.training.judge_calibration import format_report


def _report_with(scorer_kind: str, score: ContentScore | None, band: tuple):
    cases = [_case("identity", {scorer_kind: {"f1": band}})]
    return run_calibration(_FixedScorer(score), scorer_kind, cases)


def test_format_report_renders_case_name_and_pass_marker():
    report = _report_with("overlap", {"precision": 1.0, "recall": 1.0, "f1": 1.0, "quality": None}, (0.9, 1.0))

    text = format_report([report])

    assert "identity" in text
    assert "PASS" in text
    assert "RESULT: PASS" in text


def test_format_report_marks_a_breach_and_overall_failure():
    report = _report_with("llm", {"precision": 0.1, "recall": 0.1, "f1": 0.1, "quality": None}, (0.7, 1.0))

    text = format_report([report])

    assert "FAIL" in text
    assert "RESULT: FAIL" in text


def test_format_report_shows_errors_distinctly_from_breaches():
    cases = [_case("boom", {"llm": {"f1": (0.9, 1.0)}})]
    report = run_calibration(_RaisingScorer(), "llm", cases)

    text = format_report([report])

    assert "ERROR" in text
    assert "judge exploded" in text


def test_format_report_puts_both_scorers_side_by_side():
    good = _report_with("overlap", {"precision": 1.0, "recall": 1.0, "f1": 1.0, "quality": None}, (0.9, 1.0))
    bad = _report_with("llm", {"precision": 0.1, "recall": 0.1, "f1": 0.1, "quality": None}, (0.7, 1.0))

    text = format_report([good, bad])

    assert "overlap" in text
    assert "llm" in text
    assert "RESULT: FAIL" in text, "one failing scorer fails the whole scorecard"


def test_format_report_handles_no_reports():
    assert "no scorers run" in format_report([])


def test_format_report_notes_unchecked_cases():
    cases = [_case("identity", {"overlap": {"f1": (0.9, 1.0)}})]
    report = run_calibration(
        _FixedScorer({"precision": 1.0, "recall": 1.0, "f1": 1.0, "quality": None}), "llm", cases
    )

    assert "not checked" in format_report([report])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/training/test_judge_calibration.py -v -k format_report`
Expected: FAIL — `ImportError: cannot import name 'format_report'`

- [ ] **Step 3: Write the implementation**

Append to `src/training/judge_calibration.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/training/test_judge_calibration.py -v`
Expected: PASS — 23 passed

- [ ] **Step 5: Lint, format, type-check**

```bash
ruff check src/training/judge_calibration.py tests/training/test_judge_calibration.py --fix
ruff format src/training/judge_calibration.py tests/training/test_judge_calibration.py
mypy src/training/judge_calibration.py --python-version 3.14
```
Expected: ruff "All checks passed!"; no new mypy errors.

- [ ] **Step 6: Eyeball the real scorecard**

```bash
python3 -c "
from src.training.content_scorer import ReferenceOverlapScorer
from src.training.judge_calibration import format_report, run_calibration
from src.training.judge_calibration_cases import DEFAULT_CALIBRATION_CASES
print(format_report([run_calibration(ReferenceOverlapScorer(0.85), 'overlap', DEFAULT_CALIBRATION_CASES)]))
"
```
Expected: a readable five-case scorecard ending in `RESULT: PASS`.

- [ ] **Step 7: Commit**

```bash
git add src/training/judge_calibration.py tests/training/test_judge_calibration.py
git commit -m "feat(training): render the judge calibration scorecard

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: `--validate-judge` CLI mode

**Files:**
- Modify: `utilities/train_vision_model.py` — `parse_args` (args at `:145-160`, validation at `:164-167`), new `run_judge_calibration` function (place immediately after `run_evaluation`, which ends at `:498`), `main` (evaluate branch at `:519`)
- Test: `tests/training/test_judge_calibration_cli.py` (create)

**Interfaces:**
- Consumes: `run_calibration`, `format_report` (Tasks 1, 3); `DEFAULT_CALIBRATION_CASES` (Task 2); `ReferenceOverlapScorer`; `LLMJudgeScorer`; `VisionTrainingConfig`
- Produces: `run_judge_calibration(scorer_kinds: Sequence[str], judge_model: str | None = None) -> int`

**Behavioral contract:**
- `--validate-judge` takes no dataset and requires no trained model.
- Both columns run by default; an explicit `--content-scorer` narrows to one.
- Exit 1 on any breached band or error; exit 0 otherwise.
- `--validate-judge` with `--evaluate` is rejected by `parse_args`.
- `--compare-base` with `--validate-judge` is **already** rejected by the existing `--compare-base requires --evaluate` rule at `:166`. Do NOT add a redundant check.

**Note on narrowing:** `--content-scorer` currently defaults to `"overlap"`, so an explicit choice is indistinguishable from the default. Change its `default` to `None` and resolve it to `"overlap"` at the `run_evaluation` call site, preserving today's evaluate behavior exactly.

- [ ] **Step 1: Write the failing tests**

Create `tests/training/test_judge_calibration_cli.py`:

```python
"""CLI tests for --validate-judge on train_vision_model.py.

The calibration runner is monkeypatched, so these tests pin argument handling
and exit codes without touching Ollama.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_CLI_PATH = Path(__file__).resolve().parents[2] / "utilities" / "train_vision_model.py"


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("train_vision_model_cli_calib", _CLI_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cli():
    return _load_cli_module()


def _run_argv(cli, monkeypatch, argv: list[str]):
    monkeypatch.setattr(sys, "argv", ["train_vision_model.py", *argv])
    return cli.parse_args()


def test_validate_judge_defaults_content_scorer_to_none(cli, monkeypatch):
    args = _run_argv(cli, monkeypatch, ["--validate-judge"])

    assert args.validate_judge is True
    assert args.content_scorer is None


def test_validate_judge_rejects_combination_with_evaluate(cli, monkeypatch):
    with pytest.raises(SystemExit):
        _run_argv(cli, monkeypatch, ["--validate-judge", "--evaluate", "some.jsonl"])


def test_compare_base_without_evaluate_still_rejected(cli, monkeypatch):
    with pytest.raises(SystemExit):
        _run_argv(cli, monkeypatch, ["--validate-judge", "--compare-base"])


def test_run_judge_calibration_returns_zero_when_all_pass(cli, monkeypatch):
    monkeypatch.setattr(
        cli, "run_calibration", lambda *a, **k: {"scorer_kind": "overlap", "results": [], "total": 0, "failed": 0, "errors": 0, "passed": True}
    )

    assert cli.run_judge_calibration(["overlap"]) == 0


def test_run_judge_calibration_returns_one_on_breach(cli, monkeypatch):
    monkeypatch.setattr(
        cli, "run_calibration", lambda *a, **k: {"scorer_kind": "llm", "results": [], "total": 1, "failed": 1, "errors": 0, "passed": False}
    )

    assert cli.run_judge_calibration(["llm"]) == 1


def test_run_judge_calibration_runs_every_requested_kind(cli, monkeypatch):
    seen = []

    def _fake(scorer, kind, cases, **kwargs):
        seen.append(kind)
        return {"scorer_kind": kind, "results": [], "total": 0, "failed": 0, "errors": 0, "passed": True}

    monkeypatch.setattr(cli, "run_calibration", _fake)

    assert cli.run_judge_calibration(["overlap", "llm"]) == 0
    assert seen == ["overlap", "llm"]


def test_judge_model_override_reaches_the_calibration_run(cli, monkeypatch):
    seen = {}

    def _fake(scorer, kind, cases, **kwargs):
        seen["judge_model"] = kwargs.get("judge_model")
        return {"scorer_kind": kind, "results": [], "total": 0, "failed": 0, "errors": 0, "passed": True}

    monkeypatch.setattr(cli, "run_calibration", _fake)
    cli.run_judge_calibration(["llm"], judge_model="deepseek-coder-v2:16b")

    assert seen["judge_model"] == "deepseek-coder-v2:16b"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/training/test_judge_calibration_cli.py -v`
Expected: FAIL — `AttributeError: ... has no attribute 'run_judge_calibration'` / unrecognized argument `--validate-judge`

- [ ] **Step 3: Add the CLI arguments**

In `utilities/train_vision_model.py`, change the `--content-scorer` default and add `--validate-judge`. Replace the existing `--content-scorer` block (`:145-154`) with:

```python
    parser.add_argument(
        "--content-scorer",
        choices=("overlap", "llm"),
        default=None,
        help=(
            "Content scorer: 'overlap' (deterministic string similarity, the "
            "default for --evaluate) or 'llm' (LLM-as-judge semantic matching + "
            "quality; non-deterministic, needs a local judge model). With "
            "--validate-judge, omitting this runs BOTH scorers."
        ),
    )
```

Add after the `--judge-model` block (`:155-160`):

```python
    parser.add_argument(
        "--validate-judge",
        action="store_true",
        help=(
            "Calibration mode: score built-in gold-by-construction fixtures with "
            "the content scorer(s) and report whether each lands in its expected "
            "band. Needs no dataset and no trained model. Exits 1 on any breach."
        ),
    )
```

Add to the validation block, before the existing `--compare-base` check at `:166`:

```python
    # Calibration is a standalone mode over built-in fixtures; combining it with
    # dataset evaluation would silently run only one of them.
    if args.validate_judge and args.evaluate:
        parser.error("--validate-judge cannot be combined with --evaluate")
```

- [ ] **Step 4: Add the module-level imports**

At the top of `utilities/train_vision_model.py`, alongside the existing imports, add:

```python
from src.training.judge_calibration import format_report, run_calibration
from src.training.judge_calibration_cases import DEFAULT_CALIBRATION_CASES
```

These must be module-level (not function-local) so the CLI tests can monkeypatch `cli.run_calibration`.

- [ ] **Step 5: Write `run_judge_calibration`**

Insert immediately after `run_evaluation` (which ends at `:498`):

```python
def run_judge_calibration(
    scorer_kinds: Sequence[str],
    judge_model: str | None = None,
) -> int:
    """Calibrate content scorers against the built-in fixtures and print a scorecard.

    Args:
        scorer_kinds: Scorer kinds to run, in order ("overlap" and/or "llm").
        judge_model: Judge model for the "llm" scorer; None uses the config
            default.

    Returns:
        0 when every declared band held for every scorer, 1 when any band was
        breached or any scorer faulted.
    """
    config_kwargs: dict[str, Any] = {}
    if judge_model is not None:
        config_kwargs["judge_model"] = judge_model
    config = VisionTrainingConfig(**config_kwargs)

    reports = []
    for kind in scorer_kinds:
        if kind == "llm":
            from src.core.ollama_client import OllamaClient
            from src.training.llm_judge_scorer import LLMJudgeScorer

            scorer: Any = LLMJudgeScorer(judge_model=config.judge_model)
            client: Any = OllamaClient()
        else:
            from src.training.content_scorer import ReferenceOverlapScorer

            scorer = ReferenceOverlapScorer(config.content_match_threshold)
            client = None
        reports.append(
            run_calibration(
                scorer,
                kind,
                DEFAULT_CALIBRATION_CASES,
                client=client,
                judge_model=config.judge_model,
            )
        )

    print(format_report(reports))
    return 0 if all(report["passed"] for report in reports) else 1
```

Ensure `Sequence` is imported at the top: `from collections.abc import Sequence`.

- [ ] **Step 6: Wire the mode into `main`**

In `main`, insert this branch immediately **before** the `if args.evaluate:` block at `:519`:

```python
        # Calibration-only mode: validate the content scorers against built-in
        # fixtures. Needs no dataset, no trained model, and no Ollama unless the
        # llm column is being run.
        if args.validate_judge:
            kinds = ("overlap", "llm") if args.content_scorer is None else (args.content_scorer,)
            if "llm" in kinds:
                logger.info("Checking Ollama connection...")
                if not check_ollama_connection():
                    logger.error("Cannot connect to Ollama at http://localhost:11434")
                    logger.error("Please ensure Ollama is running: ollama serve")
                    return 1
                logger.info("✅ Ollama is running")
            return run_judge_calibration(kinds, judge_model=args.judge_model)
```

Then update the existing `run_evaluation` call at `:531` so the new `None` default still resolves to today's behavior:

```python
                content_scorer_kind=args.content_scorer or "overlap",
```

- [ ] **Step 7: Run the CLI tests**

Run: `python3 -m pytest tests/training/test_judge_calibration_cli.py -v`
Expected: PASS — 7 passed

- [ ] **Step 8: Verify the overlap column end-to-end with no Ollama**

```bash
python3 utilities/train_vision_model.py --validate-judge --content-scorer overlap; echo "exit=$?"
```
Expected: the five-case scorecard, `RESULT: PASS`, `exit=0`.

- [ ] **Step 9: Confirm no evaluate-path regression**

Run: `python3 -m pytest tests/training/test_train_vision_cli.py tests/training/test_vision_raft_evaluate.py -v`
Expected: PASS — all existing tests still green (this proves the `--content-scorer` default change was harmless).

- [ ] **Step 10: Lint, format, type-check**

```bash
ruff check src/ main.py utilities/ --fix
ruff format utilities/train_vision_model.py tests/training/test_judge_calibration_cli.py
mypy utilities/train_vision_model.py --python-version 3.14
```
Expected: ruff "All checks passed!"; no new mypy errors.

- [ ] **Step 11: Commit**

```bash
git add utilities/train_vision_model.py tests/training/test_judge_calibration_cli.py
git commit -m "feat(training): add --validate-judge calibration mode

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Live-Ollama integration test, docs, changelog

**Files:**
- Create: `tests/training/test_judge_calibration_integration.py`
- Modify: `docs/training/README.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: everything from Tasks 1–4.
- Produces: no new public API.

**This task carries the phase's actual finding.** The live run is the first time anyone learns whether the LLM judge clears the `paraphrase` band. If it does not, that is a legitimate result to report — see Step 5.

- [ ] **Step 1: Write the integration test**

Create `tests/training/test_judge_calibration_integration.py`:

```python
"""Live-Ollama calibration of the LLM judge (Phase 3c).

The unit tests use scripted scorers and so cannot tell whether the real judge
is any good. This test runs the llm column of the calibration harness against a
real Ollama and asserts the declared bands — in particular ``paraphrase``, the
case that justifies the LLM judge's cost over the deterministic scorer.

Opt-in: marked ``integration`` (excluded by ``-m "not integration"``) and
``slow``, and it skips itself when no reachable Ollama with the judge model is
available.
"""

import pytest
import requests

from src.config import ConfigManager
from src.core.ollama_client import OllamaClient
from src.training.judge_calibration import format_report, run_calibration
from src.training.judge_calibration_cases import DEFAULT_CALIBRATION_CASES
from src.training.llm_judge_scorer import LLMJudgeScorer

JUDGE_MODEL = "llama3.1:8b"


def _ollama_reason() -> str | None:
    """Return None when a reachable Ollama has JUDGE_MODEL, else a skip reason."""
    config = ConfigManager()
    tags_url = f"http://{config.ollama.host}:{config.ollama.port}/api/tags"
    try:
        response = requests.get(tags_url, timeout=2)
        response.raise_for_status()
        names = {model.get("name", "") for model in response.json().get("models", [])}
    except requests.RequestException as exc:
        return f"Ollama not reachable at {tags_url}: {exc}"

    family = JUDGE_MODEL.split(":", 1)[0]
    if not any(name == JUDGE_MODEL or name.startswith(family) for name in names):
        return f"model {JUDGE_MODEL} not pulled (available: {sorted(names)})"
    return None


# Probe once at collection, not twice — each call is a live HTTP request.
_SKIP_REASON = _ollama_reason()

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.skipif(_SKIP_REASON is not None, reason=_SKIP_REASON or ""),
]


@pytest.fixture(scope="module")
def llm_report():
    """Run the llm calibration column once for the whole module."""
    return run_calibration(
        LLMJudgeScorer(judge_model=JUDGE_MODEL),
        "llm",
        DEFAULT_CALIBRATION_CASES,
        client=OllamaClient(),
        judge_model=JUDGE_MODEL,
    )


def test_no_case_faulted(llm_report):
    errors = [(r["name"], r["error"]) for r in llm_report["results"] if r["error"]]
    assert errors == [], f"judge faulted on: {errors}"


def test_identity_is_recognised(llm_report):
    result = next(r for r in llm_report["results"] if r["name"] == "identity")
    assert result["passed"], f"identity breached its band: {result['score']}"


def test_disjoint_gets_no_credit(llm_report):
    result = next(r for r in llm_report["results"] if r["name"] == "disjoint")
    assert result["passed"], f"disjoint breached its band: {result['score']}"


def test_judge_beats_overlap_on_paraphrases(llm_report):
    """The discriminating case — this is what justifies the LLM judge's cost."""
    result = next(r for r in llm_report["results"] if r["name"] == "paraphrase")
    assert result["passed"], (
        f"the LLM judge did not clear the paraphrase band: {result['score']}. "
        "This is a real finding: report it rather than widening the band."
    )


def test_whole_llm_column_passes(llm_report):
    failures = [r["name"] for r in llm_report["results"] if not r["passed"]]
    assert failures == [], f"llm breached bands for: {failures}\n{format_report([llm_report])}"
```

- [ ] **Step 2: Run the integration test and CONFIRM IT RUNS, not skips**

Run: `python3 -m pytest tests/training/test_judge_calibration_integration.py -v -m integration -rs`
Expected: 5 passed. **If output says "skipped", the test proved nothing** — start Ollama (`ollama serve`), confirm `ollama list` shows `llama3.1:8b`, and re-run until it actually executes.

- [ ] **Step 3: Run the full scorecard live**

```bash
python3 utilities/train_vision_model.py --validate-judge; echo "exit=$?"
```
Expected: both columns rendered side by side. Record the actual `paraphrase` numbers — they are the phase's headline result.

- [ ] **Step 4: Update `docs/training/README.md`**

Add a "Judge calibration" section near the evaluation documentation covering:
- What the harness measures (the scorer in isolation — no generation model in the loop) and what it does not (it does not validate a trained model).
- How to run it: `--validate-judge`, `--validate-judge --content-scorer overlap` (no Ollama needed), `--judge-model <name>` to calibrate a different judge.
- How to read the scorecard: per-case bands, PASS/FAIL, the summary line, exit codes.
- The five cases and what each proves, with `paraphrase` called out as the discriminating case.
- The explicit caveat that bands are tolerances, not exact truth, and that a `paraphrase` failure means the LLM judge is not earning its cost — not that the bands need widening.
- The measured `paraphrase` numbers from Step 3.

- [ ] **Step 5: Record the finding honestly**

If the judge **cleared** `paraphrase`, state the measured f1 in the README and the CHANGELOG entry.

If the judge **did not clear it**, do not widen the band and do not quietly drop the case. Add a short "Known limitation" note to the README reporting the measured value and stating plainly that `--content-scorer llm` is not currently justified over `overlap` on this evidence, then surface it in the task's completion report.

- [ ] **Step 6: Update `CHANGELOG.md`**

Add under Added:

```markdown
- **Judge calibration harness (Phase 3c)**: `--validate-judge` scores built-in
  gold-by-construction fixtures through any `ContentScorer` and reports whether
  each metric lands in its expected band, so the Phase 3b LLM judge's quality is
  measurable rather than assumed. Runs both scorers side by side by default;
  `--content-scorer overlap` needs no Ollama. Exits 1 on any breached band.
  The originally-planned cloud judge was cancelled — the project's no-cloud-API
  principle applies to the evaluation path too.
```

- [ ] **Step 7: Run the full non-integration suite**

Run: `python3 -m pytest tests/ -q -m "not integration"`
Expected: PASS — previous baseline was 608 passed / 1 skipped; expect ~638 passed with this plan's new tests, 0 failures.

- [ ] **Step 8: Final lint and format gate**

```bash
ruff check src/ main.py utilities/
ruff format --check src/training/judge_calibration.py src/training/judge_calibration_cases.py utilities/train_vision_model.py
```
Expected: "All checks passed!"

- [ ] **Step 9: Commit**

```bash
git add tests/training/test_judge_calibration_integration.py docs/training/README.md CHANGELOG.md
git commit -m "test(training): live-Ollama calibration of the LLM judge

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Verification Checklist

Before declaring the phase done:

- [ ] `python3 -m pytest tests/ -q -m "not integration"` — all pass, no regressions vs the 608-passing baseline
- [ ] `python3 -m pytest tests/training/test_judge_calibration_integration.py -m integration -rs` — **runs, not skips**, and passes
- [ ] `ruff check src/ main.py utilities/` — clean
- [ ] `mypy` — no new errors in the three touched files
- [ ] `python3 utilities/train_vision_model.py --validate-judge --content-scorer overlap` — exits 0 with no Ollama running
- [ ] `python3 utilities/train_vision_model.py --validate-judge` — both columns render side by side
- [ ] `--evaluate` behavior unchanged (existing CLI and evaluator tests green)
- [ ] `vision_raft_trainer.py` untouched — `git diff main --stat` shows no change to it
- [ ] The measured `paraphrase` result is written down in the README, whichever way it went
