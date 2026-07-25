# Phase 3b — LLM-Judge Content Scorer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in `LLMJudgeScorer` (LLM-as-judge) behind the existing
`ContentScorer` seam that matches generated↔reference test cases by *meaning*
(semantic precision/recall/F1) and rates the generation on a holistic 0–1
quality rubric, threading a new `content_quality` metric through the per-example
→ aggregate → paired-delta → CLI path.

**Architecture:** Two `ContentScorer` implementations share one Protocol.
The Protocol's `score()` is widened with keyword-only `client` and `judge_model`
so the trainer can thread its Ollama client and a fixed judge model into the
judge (identically for the A/B passes). The judge makes two model calls per
example (matching, then quality); each call fails independently to `None`. The
CLI builds the chosen scorer and injects it via the existing
`evaluate_model(content_scorer=...)` parameter.

**Tech Stack:** Python 3.14+, pytest, ruff, mypy, local Ollama (`llama3.1:8b`).
No new third-party dependencies.

## Execution Decision (2026-07-25)

**Approved approach: Subagent-Driven Development** (superpowers:subagent-driven-development).
Dispatch a fresh implementer subagent per task, run a task-review gate (spec +
quality) after each, and a final whole-branch review before pushing — the same
workflow used for Phase 3.

**Status at close of 2026-07-25 session: NOT STARTED.** Design (`d99f084`) and
this plan (`e0021d1`) are committed on branch `feat/phase3b-llm-judge` (off
`main`). None of Tasks 1–7 have been implemented. Next session: resume with the
subagent-driven skill, check `.superpowers/sdd/progress.md` for the Phase 3b
ledger, and begin at Task 1.

## Global Constraints

- Python 3.14+, no backward compatibility. Google-style docstrings on every
  module/class/function/method.
- `ruff check src/ main.py utilities/` is the enforced gate and must pass before
  every commit; only format/type-clean files you actually touch.
- Canonical test-case schema is exactly `summary_suffix`, `preconditions`,
  `test_steps`, `expected_result`, `test_type`. Never introduce `action`/`data`.
- Core classes declare `__slots__`; adding an *instance attribute* requires
  adding it to the slots tuple first (adding a *method* does not).
- TDD: write the failing test, watch it fail, minimal code, watch it pass,
  commit. Real-Ollama e2e is the only way to catch schema/grammar regressions.
- Preserve the prior-review contracts: paired A/B delta, the
  `unique_valid_test_cases_per_example` coverage decision metric, and the
  bundle-vs-base `provenance` block.
- `content_f1` stays the headline "meaningful signal"; `content_quality` is a
  complementary line, never relabeled as the headline.
- The judge model is fixed (`VisionTrainingConfig.judge_model`, default
  `llama3.1:8b`), independent of the model under test, and passed identically
  for the customized and base scoring passes (A/B fairness).
- Default scorer is `overlap` (deterministic) — the deterministic path's
  behavior must not change except for the added `quality: None` key.
- Determinism relies on the client's `OllamaConfig.temperature` (default `0.0`),
  not a per-call setting — `generate_completion` takes no temperature argument.
- Update `CHANGELOG.md` `[Unreleased]` for every change.
- Branch: `feat/phase3b-llm-judge` (already created off `main`).

---

### Task 1: Extend `ContentScore`, add the `_prf` helper, widen the Protocol

**Files:**
- Modify: `src/training/content_scorer.py`
- Test: `tests/training/test_content_scorer.py`

**Interfaces:**
- Consumes: `TestCaseDeduplicator` (unchanged).
- Produces:
  - `ContentScore` gains `quality: float | None`.
  - `_prf(matched: int, n_generated: int, n_reference: int) -> tuple[float | None, float, float]` (module-level).
  - `ContentScorer.score(self, generated_cases: list[dict], reference_cases: list[dict], *, client: Any = None, judge_model: str | None = None) -> ContentScore | None`.
  - `ReferenceOverlapScorer.score` accepts and ignores the two new params and emits `quality: None`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/training/test_content_scorer.py`:

```python
def test_overlap_scorer_emits_quality_none():
    scorer = ReferenceOverlapScorer()
    assert scorer.score([CASE_A], [CASE_A]) == {
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
        "quality": None,
    }


def test_overlap_scorer_ignores_widened_params():
    scorer = ReferenceOverlapScorer()
    baseline = scorer.score([CASE_A, CASE_B], [CASE_A])
    widened = scorer.score([CASE_A, CASE_B], [CASE_A], client=object(), judge_model="x")
    assert widened == baseline
```

- [ ] **Step 2: Update the two existing exact-dict assertions**

In `tests/training/test_content_scorer.py`, add `"quality": None` to the two
tests that assert full-dict equality:

```python
def test_perfect_overlap_scores_one():
    scorer = ReferenceOverlapScorer()
    score = scorer.score([CASE_A, CASE_B], [CASE_A, CASE_B])
    assert score == {"precision": 1.0, "recall": 1.0, "f1": 1.0, "quality": None}
```

```python
def test_no_generated_gives_zero_recall_none_precision():
    scorer = ReferenceOverlapScorer()
    score = scorer.score([], [CASE_A])
    assert score == {"precision": None, "recall": 0.0, "f1": 0.0, "quality": None}
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python3 -m pytest tests/training/test_content_scorer.py -v --no-cov`
Expected: FAIL — the new/updated tests fail with a `KeyError`/mismatch (`quality`
not yet in the returned dict); the widened-params test fails with a `TypeError`
(unexpected keyword argument `client`).

- [ ] **Step 4: Extend `ContentScore` and add `_prf`**

In `src/training/content_scorer.py`, change the import line and add the `quality`
field plus the helper. Replace:

```python
from typing import Protocol, TypedDict

from src.core.deduplicator import TestCaseDeduplicator


class ContentScore(TypedDict):
    """Per-example content-quality scores; a field is None when undefined."""

    precision: float | None
    recall: float | None
    f1: float | None
```

with:

```python
from typing import Any, Protocol, TypedDict

from src.core.deduplicator import TestCaseDeduplicator


class ContentScore(TypedDict):
    """Per-example content-quality scores; a field is None when undefined."""

    precision: float | None
    recall: float | None
    f1: float | None
    quality: float | None


def _prf(
    matched: int, n_generated: int, n_reference: int
) -> tuple[float | None, float, float]:
    """Precision/recall/F1 from a match count (shared by both scorers).

    Args:
        matched: Generated cases matched to a distinct reference case.
        n_generated: Total generated cases.
        n_reference: Total reference cases (caller guarantees > 0).

    Returns:
        ``(precision, recall, f1)``; precision is None when ``n_generated`` is 0
        (0/0 undefined); recall/f1 are defined against the non-empty reference.
    """
    precision = None if n_generated == 0 else matched / n_generated
    recall = matched / n_reference
    p = 0.0 if precision is None else precision
    f1 = 0.0 if (p + recall) == 0 else 2 * p * recall / (p + recall)
    return precision, recall, f1
```

- [ ] **Step 5: Widen the Protocol and update `ReferenceOverlapScorer.score`**

In `src/training/content_scorer.py`, replace the `ContentScorer.score` signature:

```python
    def score(
        self,
        generated_cases: list[dict],
        reference_cases: list[dict],
        *,
        client: Any = None,
        judge_model: str | None = None,
    ) -> ContentScore | None:
        """Return precision/recall/F1/quality for the generation, or None.

        Args:
            generated_cases: Canonical, deduplicated generated test cases.
            reference_cases: Canonical, deduplicated reference test cases.
            client: Optional model client for scorers that call an LLM
                (ignored by deterministic scorers).
            judge_model: Optional judge model name (ignored by deterministic
                scorers).
        """
        ...
```

Then replace `ReferenceOverlapScorer.score` (the whole method body) with:

```python
    def score(
        self,
        generated_cases: list[dict],
        reference_cases: list[dict],
        *,
        client: Any = None,
        judge_model: str | None = None,
    ) -> ContentScore | None:
        """Score generated cases against reference cases by string overlap.

        The ``client`` and ``judge_model`` arguments are part of the widened
        ``ContentScorer`` protocol and are ignored here — this scorer is
        deterministic and makes no model calls.

        Args:
            generated_cases: Canonical, deduplicated generated test cases.
            reference_cases: Canonical, deduplicated reference test cases.
            client: Ignored.
            judge_model: Ignored.

        Returns:
            A ``ContentScore`` (``quality`` always None), or None when there are
            no reference cases.
        """
        if not reference_cases:
            return None
        if not generated_cases:
            return {"precision": None, "recall": 0.0, "f1": 0.0, "quality": None}

        matched = self._count_matches(generated_cases, reference_cases)
        precision, recall, f1 = _prf(matched, len(generated_cases), len(reference_cases))
        return {"precision": precision, "recall": recall, "f1": f1, "quality": None}
```

- [ ] **Step 6: Run all Task 1 tests to verify they pass**

Run: `python3 -m pytest tests/training/test_content_scorer.py -v --no-cov`
Expected: PASS (all existing + 2 new).

- [ ] **Step 7: Lint, format, type-check**

Run: `ruff check src/training/content_scorer.py tests/training/test_content_scorer.py && ruff format --check src/training/content_scorer.py tests/training/test_content_scorer.py && mypy src/training/content_scorer.py --python-version 3.14 --no-incremental`
Expected: all pass; `Success: no issues found`.

- [ ] **Step 8: Commit**

```bash
git add src/training/content_scorer.py tests/training/test_content_scorer.py
git commit -m "feat(training): add quality field, _prf helper, and widen the ContentScorer seam"
```

---

### Task 2: `LLMJudgeScorer`

**Files:**
- Create: `src/training/llm_judge_scorer.py`
- Test: `tests/training/test_llm_judge_scorer.py`

**Interfaces:**
- Consumes: `ContentScore`, `_prf` from `src.training.content_scorer`;
  `JSONResponseParser` from `src.core.parsers`; `OllamaClient.generate_completion(model_name, prompt, is_json=False, return_full_response=True, format_schema=None) -> dict | str`.
- Produces:
  - `class LLMJudgeScorer` with `__init__(self, judge_model: str = "llama3.1:8b") -> None` and
    `score(self, generated_cases: list[dict], reference_cases: list[dict], *, client: Any = None, judge_model: str | None = None) -> ContentScore | None`.

- [ ] **Step 1: Write the failing tests**

Create `tests/training/test_llm_judge_scorer.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/training/test_llm_judge_scorer.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.training.llm_judge_scorer'`.

- [ ] **Step 3: Implement `src/training/llm_judge_scorer.py`**

```python
"""LLM-as-judge content scorer for RAFT evaluation (Phase 3b).

Matches generated test cases to the held-out reference answer by *meaning*
(semantic precision/recall/F1) and rates the generation on a holistic 0–1
quality rubric, using a local Ollama judge model. Implements the widened
``ContentScorer`` protocol; determinism relies on the client's configured
temperature (default 0.0), so correctness is pinned by mocked unit tests.
"""

import json
from typing import Any

from src.core.parsers import JSONResponseParser
from src.training.content_scorer import ContentScore, _prf

_MATCH_PROMPT = """You are grading generated automotive test cases against a reference (gold) set.

Two test cases MATCH when they exercise the same scenario or behavior, even if worded differently.

Generated test cases:
{generated}

Reference (gold) test cases:
{reference}

Return ONLY a JSON object of the matches, using the 0-based numbers above:
{{"matches": [[generated_number, reference_number], ...]}}
Each generated case matches at most one reference case and vice versa. If nothing matches, return {{"matches": []}}."""

_QUALITY_PROMPT = """You are grading the overall quality of generated automotive test cases against a reference (gold) set.

Judge the correctness, completeness, and testability of the generated cases relative to the gold set, as a single holistic score.

Generated test cases:
{generated}

Reference (gold) test cases:
{reference}

Return ONLY a JSON object:
{{"quality": <a number from 0.0 to 1.0>, "rationale": "<one short sentence>"}}"""


class LLMJudgeScorer:
    """Semantic precision/recall/F1 + holistic quality via a local LLM judge.

    Makes two model calls per generation (matching, then quality). Each call
    fails independently to None so one fault never wipes the other score.
    """

    __slots__ = ("judge_model",)

    def __init__(self, judge_model: str = "llama3.1:8b") -> None:
        """Initialize the judge.

        Args:
            judge_model: Fixed evaluator model name; used when ``score`` is
                called without an explicit ``judge_model``.
        """
        self.judge_model = judge_model

    def score(
        self,
        generated_cases: list[dict],
        reference_cases: list[dict],
        *,
        client: Any = None,
        judge_model: str | None = None,
    ) -> ContentScore | None:
        """Score generated cases against reference cases with an LLM judge.

        Args:
            generated_cases: Canonical, deduplicated generated test cases.
            reference_cases: Canonical, deduplicated reference test cases.
            client: Ollama client; lazily constructed if None.
            judge_model: Overrides the instance's judge model when provided.

        Returns:
            A ``ContentScore``, or None when there are no reference cases.
        """
        if not reference_cases:
            return None
        if not generated_cases:
            return {"precision": None, "recall": 0.0, "f1": 0.0, "quality": None}

        model = judge_model or self.judge_model
        if client is None:
            from src.core.ollama_client import OllamaClient

            client = OllamaClient()

        precision, recall, f1 = self._run_matching(
            client, model, generated_cases, reference_cases
        )
        quality = self._run_quality(client, model, generated_cases, reference_cases)
        return {"precision": precision, "recall": recall, "f1": f1, "quality": quality}

    @staticmethod
    def _numbered(cases: list[dict]) -> str:
        """Render cases as a 0-based numbered list for a judge prompt."""
        return "\n".join(
            f"{i}. summary: {tc.get('summary_suffix', '')} | "
            f"preconditions: {tc.get('preconditions', '')} | "
            f"steps: {tc.get('test_steps', '')} | "
            f"expected: {tc.get('expected_result', '')}"
            for i, tc in enumerate(cases)
        )

    @staticmethod
    def _parse(text: str | dict) -> dict | None:
        """Extract a JSON object from a raw model response."""
        raw = text if isinstance(text, str) else json.dumps(text)
        parsed = JSONResponseParser.extract_json_from_response(raw)
        return parsed if isinstance(parsed, dict) else None

    def _run_matching(
        self, client: Any, model: str, generated: list[dict], reference: list[dict]
    ) -> tuple[float | None, float | None, float | None]:
        """Return (precision, recall, f1), or (None, None, None) on any fault."""
        try:
            prompt = _MATCH_PROMPT.format(
                generated=self._numbered(generated), reference=self._numbered(reference)
            )
            text = client.generate_completion(model, prompt, is_json=True, return_full_response=False)
            parsed = self._parse(text)
            pairs = parsed.get("matches") if parsed else None
            if not isinstance(pairs, list):
                return None, None, None
            matched = self._count_valid_pairs(pairs, len(generated), len(reference))
            return _prf(matched, len(generated), len(reference))
        except Exception:  # noqa: BLE001 - a judge fault must not abort the run
            return None, None, None

    @staticmethod
    def _count_valid_pairs(pairs: list, n_generated: int, n_reference: int) -> int:
        """Count valid, in-range, one-to-one [gen, ref] index pairs."""
        used_gen: set[int] = set()
        used_ref: set[int] = set()
        count = 0
        for pair in pairs:
            if not (isinstance(pair, (list, tuple)) and len(pair) == 2):
                continue
            g, r = pair
            if not (isinstance(g, int) and isinstance(r, int)):
                continue
            if not (0 <= g < n_generated and 0 <= r < n_reference):
                continue
            if g in used_gen or r in used_ref:
                continue
            used_gen.add(g)
            used_ref.add(r)
            count += 1
        return count

    def _run_quality(
        self, client: Any, model: str, generated: list[dict], reference: list[dict]
    ) -> float | None:
        """Return the clamped [0,1] holistic quality, or None on any fault."""
        try:
            prompt = _QUALITY_PROMPT.format(
                generated=self._numbered(generated), reference=self._numbered(reference)
            )
            text = client.generate_completion(model, prompt, is_json=True, return_full_response=False)
            parsed = self._parse(text)
            if not parsed or "quality" not in parsed:
                return None
            return max(0.0, min(1.0, float(parsed["quality"])))
        except Exception:  # noqa: BLE001 - a judge fault must not abort the run
            return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/training/test_llm_judge_scorer.py -v --no-cov`
Expected: PASS (10 tests).

- [ ] **Step 5: Lint, format, type-check**

Run: `ruff check src/training/llm_judge_scorer.py tests/training/test_llm_judge_scorer.py && ruff format --check src/training/llm_judge_scorer.py tests/training/test_llm_judge_scorer.py && mypy src/training/llm_judge_scorer.py --python-version 3.14 --no-incremental`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/training/llm_judge_scorer.py tests/training/test_llm_judge_scorer.py
git commit -m "feat(training): add LLM-judge content scorer (semantic match + quality)"
```

---

### Task 3: Thread the judge through the trainer and aggregate `content_quality`

**Files:**
- Modify: `src/training/vision_raft_trainer.py` (`VisionTrainingConfig`, `_evaluate_example`, `_score_content`, `_aggregate_eval_metrics`, `_compute_delta`)
- Test: `tests/training/test_vision_raft_evaluate.py`

**Interfaces:**
- Consumes: the widened `ContentScorer.score(..., client=, judge_model=)` (Task 1).
- Produces:
  - `VisionTrainingConfig.judge_model: str = "llama3.1:8b"`.
  - `_score_content(self, raw_output, example, content_scorer, client)` (new `client` param) passes `client=` and `judge_model=self.config.judge_model` to `score()`.
  - Aggregate key `content_quality` (macro mean, None-safe); same key added to the delta.

- [ ] **Step 1: Write the failing tests**

Append to `tests/training/test_vision_raft_evaluate.py` (module already imports
`json`, `VisionRAFTTrainer`, `VisionTrainingConfig`, `FakeOllamaClient`,
`VALID_TEST_CASE`, `VALID_RESPONSE`, `_write_jsonl`, `_example_with_reference`,
`trainer` fixture from Phase 3):

```python
# --- Phase 3b: LLM-judge quality threading -----------------------------------


class _RecordingScorer:
    """A ContentScorer stub that returns a fixed score and records kwargs."""

    def __init__(self, score_value):
        self.score_value = score_value
        self.calls = []

    def score(self, generated_cases, reference_cases, *, client=None, judge_model=None):
        self.calls.append({"client": client, "judge_model": judge_model})
        return self.score_value


_QUALITY_SCORE = {"precision": 1.0, "recall": 1.0, "f1": 1.0, "quality": 0.8}


def test_quality_threads_to_per_example_and_aggregate(trainer, tmp_path):
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_example_with_reference([VALID_TEST_CASE])])
    scorer = _RecordingScorer(_QUALITY_SCORE)

    result = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(VALID_RESPONSE), content_scorer=scorer
    )

    assert result["per_example"][0]["content"]["quality"] == 0.8
    assert result["metrics"]["content_quality"] == 0.8


def test_score_content_threads_client_and_judge_model(trainer, tmp_path):
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_example_with_reference([VALID_TEST_CASE])])
    scorer = _RecordingScorer(_QUALITY_SCORE)
    client = FakeOllamaClient(VALID_RESPONSE)

    trainer.evaluate_model(test_dataset=test_set, client=client, content_scorer=scorer)

    assert scorer.calls[0]["client"] is client
    assert scorer.calls[0]["judge_model"] == "llama3.1:8b"


def test_content_quality_in_delta(trainer, tmp_path):
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_example_with_reference([VALID_TEST_CASE])])
    scorer = _RecordingScorer(_QUALITY_SCORE)

    result = trainer.evaluate_model(
        test_dataset=test_set,
        client=FakeOllamaClient(VALID_RESPONSE),
        content_scorer=scorer,
        compare_base=True,
    )

    assert "content_quality" in result["delta"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/training/test_vision_raft_evaluate.py -k "quality or content_quality or threads" -v --no-cov`
Expected: FAIL — `KeyError: 'content_quality'` (aggregate/delta) and the
threading test fails because `score()` is called without `client`/`judge_model`.

- [ ] **Step 3: Add the `judge_model` config field**

In `src/training/vision_raft_trainer.py`, in `VisionTrainingConfig`, immediately
after the `content_match_threshold` field (~line 71):

```python
    # Phase 3b LLM-judge: the fixed evaluator model used by LLMJudgeScorer,
    # independent of the model under test and identical across the A/B passes.
    judge_model: str = "llama3.1:8b"
```

- [ ] **Step 4: Thread `client` into `_score_content`**

In `_evaluate_example`, change the content-scoring call (the line
`result["content"] = self._score_content(raw_output, example, content_scorer)`) to:

```python
        result["content"] = self._score_content(raw_output, example, content_scorer, client)
```

Then change `_score_content`'s signature and its `score()` call. Replace the
signature:

```python
    def _score_content(
        self,
        raw_output: str | dict[str, Any],
        example: dict[str, Any],
        content_scorer: ContentScorer,
        client: Any,
    ) -> ContentScore | None:
```

and update the docstring `Args:` to add:

```python
            client: The Ollama client, threaded to scorers that call a model
                (the deterministic scorer ignores it).
```

and replace the `return content_scorer.score(generated, reference)` line with:

```python
            return content_scorer.score(
                generated, reference, client=client, judge_model=self.config.judge_model
            )
```

- [ ] **Step 5: Aggregate `content_quality` and add it to the delta**

In `_aggregate_eval_metrics`, in the returned dict, add `content_quality` right
after the `content_f1` line:

```python
            "content_f1": mean_content("f1"),
            # Phase 3b LLM-judge holistic quality (complementary to F1); None
            # unless an LLM judge scored at least one example.
            "content_quality": mean_content("quality"),
```

In `_compute_delta`, add `"content_quality"` to the `comparable` tuple, after
`"content_f1"`:

```python
            "content_f1",
            "content_quality",
        )
```

- [ ] **Step 6: Run the new + existing evaluator tests**

Run: `python3 -m pytest tests/training/test_vision_raft_evaluate.py -v --no-cov`
Expected: PASS — the 3 new tests pass and all pre-existing evaluator tests still
pass (the deterministic default now also returns `quality: None`, which the
aggregate treats as "no quality", leaving `content_quality` None).

- [ ] **Step 7: Lint, format, type-check**

Run: `ruff check src/training/vision_raft_trainer.py tests/training/test_vision_raft_evaluate.py && ruff format --check src/training/vision_raft_trainer.py tests/training/test_vision_raft_evaluate.py && mypy src/training/vision_raft_trainer.py --python-version 3.14 --no-incremental`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add src/training/vision_raft_trainer.py tests/training/test_vision_raft_evaluate.py
git commit -m "feat(training): thread the judge client and aggregate content_quality"
```

---

### Task 4: CLI — select the scorer and print `content_quality`

**Files:**
- Modify: `utilities/train_vision_model.py` (`parse_args`, `run_evaluation`, its call site in `main`, `print_evaluation_result`)
- Test: `tests/training/test_train_vision_cli.py`

**Interfaces:**
- Consumes: `LLMJudgeScorer` (Task 2), `evaluate_model(content_scorer=...)`,
  aggregate/delta `content_quality` (Task 3).
- Produces: `--content-scorer {overlap,llm}` (default `overlap`), `--judge-model`;
  `run_evaluation(..., content_scorer_kind="overlap", judge_model=None)`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/training/test_train_vision_cli.py` (module has `_RecordingLogger`,
`_failed_comparison_result`, `_write_example`, `tvm`, `pytest`; add `import sys`
at the top of the file if not already present):

```python
def test_content_scorer_flag_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--evaluate", "x.jsonl"])
    args = tvm.parse_args()
    assert args.content_scorer == "overlap"
    assert args.judge_model is None


def test_content_scorer_flag_llm(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "--evaluate", "x.jsonl", "--content-scorer", "llm", "--judge-model", "llama3.1:8b"],
    )
    args = tvm.parse_args()
    assert args.content_scorer == "llm"
    assert args.judge_model == "llama3.1:8b"


def test_print_shows_content_quality_when_present(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    result = _failed_comparison_result(test_set)
    result["metrics"]["content_quality"] = 0.66
    rec = _RecordingLogger()
    monkeypatch.setattr(tvm, "logger", rec)

    tvm.print_evaluation_result(result)

    lines = " ".join(rec.infos + rec.warnings + rec.errors).lower()
    assert "content quality" in lines and "0.66" in lines


def test_print_omits_content_quality_when_absent(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    result = _failed_comparison_result(test_set)
    result["metrics"]["content_quality"] = None
    rec = _RecordingLogger()
    monkeypatch.setattr(tvm, "logger", rec)

    tvm.print_evaluation_result(result)

    lines = " ".join(rec.infos + rec.warnings + rec.errors).lower()
    assert "content quality" not in lines
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/training/test_train_vision_cli.py -k "content_scorer or content_quality" -v --no-cov`
Expected: FAIL — `AttributeError: 'Namespace' object has no attribute 'content_scorer'` and no quality line printed.

- [ ] **Step 3: Add the CLI flags**

In `utilities/train_vision_model.py`, in `parse_args`, immediately after the
`--compare-base` argument block (before `args = parser.parse_args()`):

```python
    parser.add_argument(
        "--content-scorer",
        choices=("overlap", "llm"),
        default="overlap",
        help=(
            "Content scorer for --evaluate: 'overlap' (deterministic string "
            "similarity, default) or 'llm' (LLM-as-judge semantic matching + "
            "quality; non-deterministic, needs a local judge model)."
        ),
    )
    parser.add_argument(
        "--judge-model",
        type=str,
        default=None,
        help="Judge model for --content-scorer llm (default: config judge_model, llama3.1:8b).",
    )
```

- [ ] **Step 4: Build and inject the scorer in `run_evaluation`**

In `run_evaluation`, change the signature to add the two parameters:

```python
def run_evaluation(
    test_dataset: str,
    output_model: str,
    compare_base: bool = False,
    base_model: str | None = None,
    content_scorer_kind: str = "overlap",
    judge_model: str | None = None,
) -> int:
```

and add to its docstring `Args:`:

```python
        content_scorer_kind: "overlap" (deterministic, default) or "llm"
            (LLM-as-judge). Selects the content scorer.
        judge_model: Judge model for the "llm" scorer; None uses the config
            default.
```

Then replace the single line
`result = trainer.evaluate_model(test_dataset=test_path, compare_base=compare_base)`
with:

```python
    content_scorer = None
    if content_scorer_kind == "llm":
        from src.training.llm_judge_scorer import LLMJudgeScorer

        content_scorer = LLMJudgeScorer(judge_model=judge_model or config.judge_model)
    result = trainer.evaluate_model(
        test_dataset=test_path, compare_base=compare_base, content_scorer=content_scorer
    )
```

- [ ] **Step 5: Thread the args at the `run_evaluation` call site**

In `main`, replace the `run_evaluation(...)` call (currently
`return run_evaluation(args.evaluate, args.output_model, args.compare_base, args.base_model)`)
with:

```python
            return run_evaluation(
                args.evaluate,
                args.output_model,
                args.compare_base,
                args.base_model,
                content_scorer_kind=args.content_scorer,
                judge_model=args.judge_model,
            )
```

- [ ] **Step 6: Print `content_quality` in both blocks**

In `print_evaluation_result`, in the single-model block, immediately after the
content-F1 `Precision/Recall` info line and before `if result["errors"]:`:

```python
    content_quality = metrics.get("content_quality")
    if content_quality is not None:
        logger.info(
            f"Content Quality:  {content_quality:.2f}  <- LLM-judge holistic "
            "rubric (complementary to F1)"
        )
```

And in the A/B delta block, immediately after the existing `content_f1` delta
`if` block and before `provenance = result.get("provenance")`:

```python
            if delta.get("content_quality") is not None:
                logger.info(
                    f"  Content Qual.:  {_format_delta(delta.get('content_quality'))}  "
                    "<- LLM-judge quality delta (complementary)"
                )
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `python3 -m pytest tests/training/test_train_vision_cli.py -v --no-cov`
Expected: PASS (all CLI tests).

- [ ] **Step 8: Verify the CLI still parses**

Run: `python3 utilities/train_vision_model.py --help`
Expected: help lists `--content-scorer` and `--judge-model`; exit 0.

- [ ] **Step 9: Lint, format, type-check**

Run: `ruff check utilities/train_vision_model.py tests/training/test_train_vision_cli.py && ruff format --check utilities/train_vision_model.py tests/training/test_train_vision_cli.py && mypy utilities/train_vision_model.py --python-version 3.14 --no-incremental`
Expected: all pass.

- [ ] **Step 10: Commit**

```bash
git add utilities/train_vision_model.py tests/training/test_train_vision_cli.py
git commit -m "feat(training): select LLM/overlap scorer and print content quality"
```

---

### Task 5: Opt-in real-Ollama LLM-judge integration test

**Files:**
- Modify: `tests/training/test_vision_raft_evaluate_integration.py`

**Interfaces:**
- Consumes: `LLMJudgeScorer` (Task 2); `evaluate_model(content_scorer=...)`;
  `VisionTrainingConfig.judge_model` (Task 3). Reuses the module's existing
  `_text_example_with_reference`, `_ollama_reason`, `_write_jsonl`, `TEXT_MODEL`,
  `VisionRAFTTrainer`, `VisionTrainingConfig`, `pytest` (all added in Phase 3).

- [ ] **Step 1: Write the failing (skip-guarded) integration test**

Append to `tests/training/test_vision_raft_evaluate_integration.py`:

```python
@pytest.mark.integration
@pytest.mark.slow
def test_real_ollama_llm_judge_populates_quality(tmp_path) -> None:
    """A live LLM-judge run must populate content quality and P/R/F1 in [0,1]."""
    reason = _ollama_reason()
    if reason:
        pytest.skip(reason)
    from src.training.llm_judge_scorer import LLMJudgeScorer

    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_text_example_with_reference()])
    trainer = VisionRAFTTrainer(
        dataset_path=test_set,
        config=VisionTrainingConfig(output_model=TEXT_MODEL, judge_model=TEXT_MODEL),
        output_dir=tmp_path / "models",
    )

    result = trainer.evaluate_model(
        test_dataset=test_set, content_scorer=LLMJudgeScorer(judge_model=TEXT_MODEL)
    )

    content = result["per_example"][0]["content"]
    assert content is not None
    for key in ("precision", "recall", "f1", "quality"):
        if content[key] is not None:
            assert 0.0 <= content[key] <= 1.0
    # At least one of the judge's two calls should have produced a number.
    assert any(content[k] is not None for k in ("f1", "quality"))
```

- [ ] **Step 2: Run the integration test against local Ollama**

Run: `python3 -m pytest tests/training/test_vision_raft_evaluate_integration.py -k llm_judge -v --no-cov -m integration`
Expected: PASS (or skip if Ollama/`llama3.1:8b` unavailable). With Ollama up it
must RUN and pass — the judge populates content metrics on a real generation.

- [ ] **Step 3: Lint and format**

Run: `ruff check tests/training/test_vision_raft_evaluate_integration.py && ruff format --check tests/training/test_vision_raft_evaluate_integration.py`
Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add tests/training/test_vision_raft_evaluate_integration.py
git commit -m "test(training): live-Ollama coverage for the LLM-judge scorer"
```

---

### Task 6: Documentation and CHANGELOG

**Files:**
- Modify: `docs/training/README.md`
- Modify: `CHANGELOG.md`

**Interfaces:** none (docs only).

- [ ] **Step 1: Document the metric and flags in the evaluation section**

In `docs/training/README.md`, in the "5. Evaluate a customized model" metric
table, add a row after the `content_f1` row:

```markdown
| `content_quality` | LLM-judge holistic quality (0–1) of the generation vs the reference, from `--content-scorer llm` | **Complementary** to `content_f1` (not the headline). Non-deterministic; `None` under the default `overlap` scorer. |
```

And append to that section (after the metric table):

```markdown
By default `--evaluate` uses the deterministic `overlap` content scorer. To score
by *meaning* instead, add an LLM-as-judge:

```bash
python3 utilities/train_vision_model.py --evaluate val.jsonl --output-model my-model \
  --content-scorer llm --judge-model llama3.1:8b
```

The judge matches generated↔reference cases semantically (precision/recall/F1) and
adds a holistic `content_quality` score. It is non-deterministic (a local model
call per example, temperature from the client config, default 0.0), so treat small
run-to-run differences as noise. `content_f1` remains the headline signal.
```

- [ ] **Step 2: Add CHANGELOG entries**

In `CHANGELOG.md` under `## [Unreleased]` → `### Added (feature)`:

```markdown
- **Phase 3b LLM-as-judge content scorer.** New opt-in `LLMJudgeScorer`
  (`src/training/llm_judge_scorer.py`) scores generated test cases against the
  reference answer by *semantic* matching (precision/recall/F1) plus a holistic
  0–1 `content_quality` rubric, using a local Ollama judge model. Selected via
  `train_vision_model.py --content-scorer llm` (`--judge-model`, default
  `llama3.1:8b`); the deterministic `overlap` scorer stays the default. The
  `ContentScorer` protocol's `score()` is widened with keyword-only `client` /
  `judge_model`; `content_quality` threads through the aggregate, the paired A/B
  delta, and the CLI as a complementary signal (F1 stays the headline). New
  `VisionTrainingConfig.judge_model`.
```

- [ ] **Step 3: Commit**

```bash
git add docs/training/README.md CHANGELOG.md
git commit -m "docs(training): document the LLM-judge scorer and its flags"
```

---

### Task 7: Full-suite gate, index refresh, and push

**Files:** none (verification only).

- [ ] **Step 1: Run the full non-integration suite**

Run: `python3 -m pytest tests/ -q -p no:cacheprovider --no-cov -m "not integration"`
Expected: all pass (Phase 3 baseline 588 + the Phase 3b unit tests), ≤1 skip.

- [ ] **Step 2: Whole-suite quality gates on touched files**

Run: `ruff check src/ main.py utilities/ && ruff format --check src/training/content_scorer.py src/training/llm_judge_scorer.py src/training/vision_raft_trainer.py utilities/train_vision_model.py && mypy src/training/content_scorer.py src/training/llm_judge_scorer.py src/training/vision_raft_trainer.py --python-version 3.14`
Expected: ruff clean; `Success: no issues found`.

- [ ] **Step 3: Refresh code-intelligence indexes**

Run: `graphify update . && node .gitnexus/run.cjs analyze`
Expected: both complete; note the refreshed counts (gitnexus may throw a
transient graph-load error on the first run — re-run once; it succeeds).

- [ ] **Step 4: Commit the index refresh**

```bash
git add AGENTS.md CLAUDE.md graphify-out/
git commit -m "chore: refresh indexes after Phase 3b LLM-judge scorer"
```

- [ ] **Step 5: Push the branch**

Run: `git push -u origin feat/phase3b-llm-judge`
Expected: branch pushed; no merge to main.

---

## Self-Review

**Spec coverage:**
- LLM-judge behind the `ContentScorer` seam → Tasks 1–2. ✓
- Two calls per example (matching + quality), independent failure → Task 2. ✓
- Widened Protocol threading `client` + `judge_model` → Tasks 1, 3. ✓
- Single holistic quality 0–1 + rationale → Task 2 (`_QUALITY_PROMPT`, clamp). ✓
- Fixed judge model, identical across A/B → Task 3 (`self.config.judge_model` in
  `_score_content`, one scorer instance used for both passes). ✓
- Empty-generation quality = None; reference-aware quality; F1 headline → Tasks 2, 3, 4. ✓
- `content_quality` through aggregate/delta/CLI → Tasks 3–4. ✓
- CLI selection via existing injection point → Task 4 (no `evaluate_model`
  selection branch). ✓
- Mocked unit tests + opt-in live test → Tasks 2, 3, 5. ✓
- Docs + CHANGELOG → Task 6. ✓
- Full-suite/gates + index refresh + push → Task 7. ✓

**Deviation from spec (noted for the reviewer):** the spec listed a
`temperature=0.0` parameter on `LLMJudgeScorer`. `OllamaClient.generate_completion`
takes no per-call temperature — temperature is set at client construction via
`OllamaConfig.temperature` (default `0.0`), so a lazily-built judge client is
already deterministic-leaning and an injected client uses the eval config's
temperature. The plan therefore **omits the `temperature` param** (YAGNI); the
determinism guarantee is unchanged. Add a param later only if per-judge
temperature control is actually needed.

**Placeholder scan:** no TBD/TODO; every code step shows complete code.

**Type consistency:** `ContentScore` keys (`precision`/`recall`/`f1`/`quality`)
are used consistently across `_prf`, both scorers, per-example `content`,
aggregate `content_*`, delta, and CLI. `score(..., *, client=None, judge_model=None)`
is identical across the Protocol, `ReferenceOverlapScorer`, `LLMJudgeScorer`, and
the trainer call. `run_evaluation`'s new params (`content_scorer_kind`,
`judge_model`) match between the signature, the `main` call site, and the tests.
