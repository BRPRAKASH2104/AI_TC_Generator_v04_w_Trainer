# Phase 3 — Content Metric + Train/Val Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic reference-aware content metric (scenario
precision/recall/F1) to `VisionRAFTTrainer.evaluate_model`, plus a seeded
train/val split producer, so A/B comparison finally measures output *quality*,
not just validity and count.

**Architecture:** A new `ContentScorer` protocol with a deterministic
`ReferenceOverlapScorer` (the seam for a future LLM-judge). Generated and
reference test cases are parsed to canonical, deduplicated cases and matched by
the production deduplicator's field similarity; precision/recall/F1 thread
through the existing per-example → aggregate → delta → CLI path. A
`RAFTDatasetBuilder.split_dataset` produces a held-out `val.jsonl`.

**Tech Stack:** Python 3.14+, pytest, ruff, mypy, Ollama (llama3.1:8b for the
opt-in live test). No new third-party dependencies.

## Global Constraints

- Python 3.14+, no backward compatibility.
- `ruff check` is the enforced gate and must pass before every commit; only
  format/type-clean files you actually touch.
- Google-style docstrings on every module/class/function/method.
- Canonical test-case schema is `summary_suffix`, `preconditions`, `test_steps`,
  `expected_result`, `test_type`. Never reintroduce `action`/`data`.
- Deduplicator compares `DEFAULT_FIELDS_TO_COMPARE = ["test_steps",
  "expected_result", "preconditions"]`. Reuse it; do not replicate its logic.
- Core classes declare `__slots__` — adding an *instance attribute* requires
  adding it to the slots tuple first (adding a *method* does not).
- TDD: write the failing test, watch it fail, minimal code, watch it pass,
  commit. Real-Ollama e2e is the only way to catch schema/grammar regressions.
- Update `CHANGELOG.md` `[Unreleased]` (Added/Changed/Fixed) for every change.
- Preserve the 2026-07-24 review contracts: paired delta (Critical 1),
  `unique_valid` coverage decision metric (Critical 2), bundle-vs-base
  provenance (Rec 4), input validation (Rec 3).
- Branch: `feat/phase3-content-metric` (already created off
  `feat/vision-raft-evaluate-model`).

---

### Task 1: `ReferenceOverlapScorer` and the `ContentScorer` seam

**Files:**
- Create: `src/training/content_scorer.py`
- Modify: `src/core/deduplicator.py` (add public `similarity` method after `_calculate_similarity`, ~line 166)
- Test: `tests/training/test_content_scorer.py`

**Interfaces:**
- Consumes: `TestCaseDeduplicator` from `src/core/deduplicator.py`.
- Produces:
  - `class ContentScore(TypedDict)` with `precision`, `recall`, `f1`: `float | None`.
  - `class ContentScorer(Protocol)` with `score(self, generated_cases: list[dict], reference_cases: list[dict]) -> ContentScore | None`.
  - `class ReferenceOverlapScorer` implementing it; `__init__(self, match_threshold: float = 0.85)`.
  - `TestCaseDeduplicator.similarity(self, tc1: dict, tc2: dict) -> float`.

- [ ] **Step 1: Write the failing test for the deduplicator public similarity**

Add to a new `tests/training/test_content_scorer.py`:

```python
"""Unit tests for the deterministic content scorer (Phase 3)."""

from src.core.deduplicator import TestCaseDeduplicator
from src.training.content_scorer import ReferenceOverlapScorer

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


def test_deduplicator_similarity_is_public_and_symmetric():
    dedup = TestCaseDeduplicator()
    assert dedup.similarity(CASE_A, CASE_A) == 1.0
    assert dedup.similarity(CASE_A, CASE_B) < 0.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/training/test_content_scorer.py::test_deduplicator_similarity_is_public_and_symmetric -v --no-cov`
Expected: FAIL — `ImportError` (no `content_scorer` module) or `AttributeError: 'TestCaseDeduplicator' object has no attribute 'similarity'`.

- [ ] **Step 3: Add the public `similarity` method to the deduplicator**

In `src/core/deduplicator.py`, immediately after `_calculate_similarity` (after its `return` at ~line 166):

```python
    def similarity(self, tc1: TestCase, tc2: TestCase) -> SimilarityScore:
        """Public field-similarity (0.0–1.0) between two test cases.

        Single source of truth for "how similar are two test cases", reused by
        Phase 3 content scoring so the content metric can never drift from
        deduplication.

        Args:
            tc1: First test case.
            tc2: Second test case.

        Returns:
            Similarity across ``fields_to_compare`` in the range 0.0–1.0.
        """
        return self._calculate_similarity(tc1, tc2)
```

- [ ] **Step 4: Write the failing scorer tests**

Append to `tests/training/test_content_scorer.py`:

```python
def test_perfect_overlap_scores_one():
    scorer = ReferenceOverlapScorer()
    score = scorer.score([CASE_A, CASE_B], [CASE_A, CASE_B])
    assert score == {"precision": 1.0, "recall": 1.0, "f1": 1.0}


def test_disjoint_scores_zero():
    scorer = ReferenceOverlapScorer()
    score = scorer.score([CASE_A], [CASE_B])
    assert score["precision"] == 0.0
    assert score["recall"] == 0.0
    assert score["f1"] == 0.0


def test_partial_overlap_precision_and_recall():
    # 2 generated (1 matches), 1 reference (matched) -> P 0.5, R 1.0.
    scorer = ReferenceOverlapScorer()
    score = scorer.score([CASE_A, CASE_B], [CASE_A])
    assert score["precision"] == 0.5
    assert score["recall"] == 1.0
    assert round(score["f1"], 3) == 0.667


def test_one_reference_matched_by_at_most_one_generated():
    # Two identical generated cases must not both match the single reference.
    scorer = ReferenceOverlapScorer()
    score = scorer.score([CASE_A, CASE_A], [CASE_A])
    assert score["recall"] == 1.0
    assert score["precision"] == 0.5  # only one of the two counts as a match


def test_no_reference_returns_none():
    scorer = ReferenceOverlapScorer()
    assert scorer.score([CASE_A], []) is None


def test_no_generated_gives_zero_recall_none_precision():
    scorer = ReferenceOverlapScorer()
    score = scorer.score([], [CASE_A])
    assert score == {"precision": None, "recall": 0.0, "f1": 0.0}
```

- [ ] **Step 5: Run scorer tests to verify they fail**

Run: `python3 -m pytest tests/training/test_content_scorer.py -v --no-cov`
Expected: FAIL — `ImportError`/`AttributeError` (scorer not yet defined). The similarity test from Step 3 now passes.

- [ ] **Step 6: Implement `src/training/content_scorer.py`**

```python
"""Reference-aware content scoring for RAFT evaluation (Phase 3).

Scores a model's generated test cases against the held-out example's reference
answer by scenario precision/recall/F1. ``ReferenceOverlapScorer`` is the
deterministic first scorer; the ``ContentScorer`` protocol is the seam for a
future LLM-as-judge (Phase 3b).
"""

from typing import Protocol, TypedDict

from src.core.deduplicator import TestCaseDeduplicator


class ContentScore(TypedDict):
    """Per-example content-quality scores; a field is None when undefined."""

    precision: float | None
    recall: float | None
    f1: float | None


class ContentScorer(Protocol):
    """Scores generated test cases against reference cases.

    Implementations return None when scoring is impossible (e.g. no reference).
    """

    def score(
        self, generated_cases: list[dict], reference_cases: list[dict]
    ) -> ContentScore | None:
        """Return precision/recall/F1 for the generation, or None."""
        ...


class ReferenceOverlapScorer:
    """Deterministic scenario precision/recall/F1 by test-case overlap.

    A generated case "matches" a reference case when their field similarity
    (the production ``TestCaseDeduplicator`` similarity over
    ``DEFAULT_FIELDS_TO_COMPARE``) is >= ``match_threshold``. Matching is greedy
    and one-to-one: each generated case takes its highest-similarity
    still-unmatched reference case at or above the threshold (ties broken by
    reference order), so it is deterministic and order-stable.
    """

    __slots__ = ("match_threshold", "_dedup")

    def __init__(self, match_threshold: float = 0.85) -> None:
        """Initialize the scorer.

        Args:
            match_threshold: Minimum field similarity for a match (0.0–1.0);
                defaults to the deduplicator's 0.85.
        """
        self.match_threshold = match_threshold
        self._dedup = TestCaseDeduplicator(similarity_threshold=match_threshold)

    def score(
        self, generated_cases: list[dict], reference_cases: list[dict]
    ) -> ContentScore | None:
        """Score generated cases against reference cases.

        Args:
            generated_cases: Canonical, deduplicated generated test cases.
            reference_cases: Canonical, deduplicated reference test cases.

        Returns:
            A ``ContentScore``, or None when there are no reference cases.
        """
        if not reference_cases:
            return None
        if not generated_cases:
            return {"precision": None, "recall": 0.0, "f1": 0.0}

        matched = self._count_matches(generated_cases, reference_cases)
        precision = matched / len(generated_cases)
        recall = matched / len(reference_cases)
        f1 = 0.0 if (precision + recall) == 0 else 2 * precision * recall / (precision + recall)
        return {"precision": precision, "recall": recall, "f1": f1}

    def _count_matches(
        self, generated_cases: list[dict], reference_cases: list[dict]
    ) -> int:
        """Count greedy one-to-one matches between generated and reference."""
        matched_ref: set[int] = set()
        count = 0
        for gen in generated_cases:
            best_j: int | None = None
            best_sim = -1.0
            for j, ref in enumerate(reference_cases):
                if j in matched_ref:
                    continue
                sim = self._dedup.similarity(gen, ref)
                if sim >= self.match_threshold and sim > best_sim:
                    best_sim = sim
                    best_j = j
            if best_j is not None:
                matched_ref.add(best_j)
                count += 1
        return count
```

- [ ] **Step 7: Run all Task 1 tests to verify they pass**

Run: `python3 -m pytest tests/training/test_content_scorer.py -v --no-cov`
Expected: PASS (7 tests).

- [ ] **Step 8: Lint, format, type-check touched files**

Run: `ruff check src/training/content_scorer.py src/core/deduplicator.py tests/training/test_content_scorer.py && ruff format --check src/training/content_scorer.py src/core/deduplicator.py tests/training/test_content_scorer.py && mypy src/training/content_scorer.py --python-version 3.14 --no-incremental`
Expected: All checks pass; `Success: no issues found`.

- [ ] **Step 9: Commit**

```bash
git add src/training/content_scorer.py src/core/deduplicator.py tests/training/test_content_scorer.py
git commit -m "feat(training): add deterministic reference-overlap content scorer"
```

---

### Task 2: Thread content scoring into `evaluate_model` per-example

**Files:**
- Modify: `src/training/vision_raft_trainer.py` (config field; `evaluate_model`, `_score_over_dataset`, `_evaluate_example`; new `_canonical_unique_cases`, `_reference_answer`, `_score_content`)
- Test: `tests/training/test_vision_raft_evaluate.py`

**Interfaces:**
- Consumes: `ReferenceOverlapScorer`, `ContentScorer` from Task 1.
- Produces:
  - `VisionTrainingConfig.content_match_threshold: float = 0.85`.
  - `evaluate_model(self, test_dataset=None, client=None, compare_base=False, content_scorer=None)`.
  - Per-example dicts gain `content: ContentScore | None`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/training/test_vision_raft_evaluate.py` (module already imports `json`, `pytest`, `VisionRAFTTrainer`, `VisionTrainingConfig`, `FakeOllamaClient`, `VALID_TEST_CASE`, `_write_jsonl`, `_text_example`, `trainer` fixture):

```python
# --- Phase 3: per-example content scoring -----------------------------------


def _example_with_reference(reference_cases):
    ex = _text_example()
    ex["messages"][2]["content"] = json.dumps({"test_cases": reference_cases})
    return ex


def test_per_example_content_matches_reference(trainer, tmp_path):
    # Customized model emits VALID_TEST_CASE; reference is the same case ->
    # perfect precision/recall/f1.
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_example_with_reference([VALID_TEST_CASE])])

    result = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(VALID_RESPONSE)
    )

    content = result["per_example"][0]["content"]
    assert content == {"precision": 1.0, "recall": 1.0, "f1": 1.0}


def test_per_example_content_none_without_reference(trainer, tmp_path):
    ex = _text_example()
    ex["messages"][2]["content"] = ""  # no usable reference answer
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [ex])

    result = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient())

    assert result["per_example"][0]["content"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/training/test_vision_raft_evaluate.py -k "per_example_content" -v --no-cov`
Expected: FAIL — `KeyError: 'content'`.

- [ ] **Step 3: Add the config field**

In `src/training/vision_raft_trainer.py`, in `VisionTrainingConfig`, after the eval input-bound fields (`max_image_bytes`):

```python
    # Phase 3 content metric: minimum field similarity for a generated case to
    # count as covering a reference case (reuses the deduplicator's 0.85).
    content_match_threshold: float = 0.85
```

- [ ] **Step 4: Add the helper methods**

In `src/training/vision_raft_trainer.py`, add these methods to `VisionRAFTTrainer` (place them next to `_score_generation`):

```python
    @staticmethod
    def _canonical_unique_cases(raw_output: str | dict[str, Any]) -> list[dict[str, Any]]:
        """Parse a raw response into canonical, deduplicated test cases.

        Shared by generated-output and reference-answer parsing for the content
        metric, so both sides are normalized identically to the production
        pipeline.

        Args:
            raw_output: Raw model response or reference answer (text or dict).

        Returns:
            Canonical-valid, deduplicated test-case dicts (possibly empty).
        """
        from src.core.deduplicator import TestCaseDeduplicator
        from src.core.parsers import JSONResponseParser
        from src.core.validators import is_canonical_test_case

        text = raw_output if isinstance(raw_output, str) else json.dumps(raw_output)
        parsed = JSONResponseParser.extract_json_from_response(text)
        if not parsed or not isinstance(parsed.get("test_cases"), list):
            return []
        valid = [tc for tc in parsed["test_cases"] if is_canonical_test_case(tc)]
        if not valid:
            return []
        deduped, _ = TestCaseDeduplicator().deduplicate(valid)
        return deduped

    @staticmethod
    def _reference_answer(example: dict[str, Any]) -> str | None:
        """Return the example's reference assistant answer, or None if absent.

        Args:
            example: A RAFT example dict.

        Returns:
            The assistant message content if present and non-blank, else None.
        """
        for message in example.get("messages", []):
            if isinstance(message, dict) and message.get("role") == "assistant":
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content
        return None

    def _score_content(
        self, raw_output: str | dict[str, Any], example: dict[str, Any], content_scorer: Any
    ) -> dict[str, float | None] | None:
        """Score one generation against the example's reference answer.

        Args:
            raw_output: The raw model response.
            example: The RAFT example (source of the reference answer).
            content_scorer: A ContentScorer implementation.

        Returns:
            A ContentScore dict, or None when there is no usable reference or the
            scorer raises (isolated like per-example generation errors).
        """
        reference_raw = self._reference_answer(example)
        if reference_raw is None:
            return None
        try:
            generated = self._canonical_unique_cases(raw_output)
            reference = self._canonical_unique_cases(reference_raw)
            return content_scorer.score(generated, reference)
        except Exception:  # noqa: BLE001 - a scorer fault must not abort the run
            return None
```

- [ ] **Step 5: Thread the scorer through the eval methods**

In `evaluate_model`, add the parameter and default. Change the signature line:

```python
    def evaluate_model(
        self,
        test_dataset: Path | None = None,
        client: Any = None,
        compare_base: bool = False,
        content_scorer: Any = None,
    ) -> dict[str, Any]:
```

After the `client` lazy-init block (after `client = OllamaClient()`), add:

```python
        if content_scorer is None:
            from src.training.content_scorer import ReferenceOverlapScorer

            content_scorer = ReferenceOverlapScorer(self.config.content_match_threshold)
```

Update both `_score_over_dataset` calls to pass `content_scorer`:

```python
        metrics, per_example = self._score_over_dataset(
            client, examples, self.config.output_model, content_scorer
        )
```
```python
            base_metrics, base_per_example = self._score_over_dataset(
                client, examples, self.config.base_model, content_scorer
            )
```

Change `_score_over_dataset` to accept and forward the scorer:

```python
    def _score_over_dataset(
        self, client: Any, examples: list[dict[str, Any]], model_name: str, content_scorer: Any
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
```
```python
        per_example = [
            self._evaluate_example(client, example, index, model_name, content_scorer)
            for index, example in enumerate(examples)
        ]
```

Change `_evaluate_example` to accept the scorer, add `"content": None` to its default result dict, and set content after scoring. Signature:

```python
    def _evaluate_example(
        self,
        client: Any,
        example: dict[str, Any],
        index: int,
        model_name: str,
        content_scorer: Any,
    ) -> dict[str, Any]:
```

In its default `result` dict, add the key (after `"duplicate_test_cases": 0,`):

```python
            "content": None,
```

After `result.update(self._score_generation(raw_output))` and before `return result`:

```python
        result["content"] = self._score_content(raw_output, example, content_scorer)
```

- [ ] **Step 6: Run the new + existing evaluator tests**

Run: `python3 -m pytest tests/training/test_vision_raft_evaluate.py -v --no-cov`
Expected: PASS — the two new `per_example_content` tests pass and all pre-existing tests still pass (the `content_scorer` default keeps them green).

- [ ] **Step 7: Lint, format, type-check**

Run: `ruff check src/training/vision_raft_trainer.py tests/training/test_vision_raft_evaluate.py && ruff format --check src/training/vision_raft_trainer.py tests/training/test_vision_raft_evaluate.py && mypy src/training/vision_raft_trainer.py --python-version 3.14 --no-incremental`
Expected: All pass.

- [ ] **Step 8: Commit**

```bash
git add src/training/vision_raft_trainer.py tests/training/test_vision_raft_evaluate.py
git commit -m "feat(training): score generated cases against the reference answer"
```

---

### Task 3: Aggregate content metrics and add them to the A/B delta

**Files:**
- Modify: `src/training/vision_raft_trainer.py` (`_aggregate_eval_metrics`, `_compute_delta`)
- Test: `tests/training/test_vision_raft_evaluate.py`

**Interfaces:**
- Consumes: per-example `content` dicts from Task 2.
- Produces: aggregate keys `content_precision`, `content_recall`, `content_f1`
  (macro means, `None` when no example had content); same keys added to the
  paired delta.

- [ ] **Step 1: Write the failing tests**

Append to `tests/training/test_vision_raft_evaluate.py`:

```python
def test_aggregate_reports_content_metrics(trainer, tmp_path):
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(
        test_set,
        [_example_with_reference([VALID_TEST_CASE]), _example_with_reference([VALID_TEST_CASE])],
    )

    metrics = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(VALID_RESPONSE)
    )["metrics"]

    assert metrics["content_f1"] == 1.0
    assert metrics["content_precision"] == 1.0
    assert metrics["content_recall"] == 1.0


def test_content_metrics_none_when_no_references(trainer, tmp_path):
    # _text_example() carries a non-JSON reference ("reference answer") -> no
    # canonical reference cases -> content is None -> aggregate is None.
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_text_example()])

    metrics = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient())["metrics"]

    assert metrics["content_f1"] is None


def test_content_f1_is_in_the_delta(trainer, tmp_path):
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_example_with_reference([VALID_TEST_CASE])])

    result = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(VALID_RESPONSE), compare_base=True
    )

    assert "content_f1" in result["delta"]
```

Note: `_text_example`'s assistant content is the literal string `"reference
answer"`, which parses to zero canonical cases, so its content score is `None` —
this is what `test_content_metrics_none_when_no_references` relies on.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/training/test_vision_raft_evaluate.py -k "content_metrics or content_f1 or aggregate_reports_content" -v --no-cov`
Expected: FAIL — `KeyError: 'content_f1'`.

- [ ] **Step 3: Aggregate content metrics**

In `_aggregate_eval_metrics`, before the `return` dict, add:

```python
        content_rows = [r for r in per_example if r.get("content") is not None]

        def mean_content(field: str) -> float | None:
            values = [
                r["content"][field]
                for r in content_rows
                if r["content"].get(field) is not None
            ]
            return sum(values) / len(values) if values else None
```

Add these three keys to the returned dict (after `unique_valid_test_cases_per_example`):

```python
            # Phase 3 content metric (reference-aware); None when no example
            # carried a usable reference answer.
            "content_precision": mean_content("precision"),
            "content_recall": mean_content("recall"),
            "content_f1": mean_content("f1"),
```

- [ ] **Step 4: Add content metrics to the delta comparable set**

In `_compute_delta`, extend the `comparable` tuple:

```python
        comparable = (
            "overall_score",
            "text_examples_score",
            "vision_examples_score",
            "parse_success_rate",
            "raw_test_cases_per_example",
            "unique_valid_test_cases_per_example",
            "content_precision",
            "content_recall",
            "content_f1",
        )
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m pytest tests/training/test_vision_raft_evaluate.py -v --no-cov`
Expected: PASS (all evaluator tests).

- [ ] **Step 6: Lint, format, type-check**

Run: `ruff check src/training/vision_raft_trainer.py tests/training/test_vision_raft_evaluate.py && ruff format --check src/training/vision_raft_trainer.py tests/training/test_vision_raft_evaluate.py && mypy src/training/vision_raft_trainer.py --python-version 3.14 --no-incremental`
Expected: All pass.

- [ ] **Step 7: Commit**

```bash
git add src/training/vision_raft_trainer.py tests/training/test_vision_raft_evaluate.py
git commit -m "feat(training): aggregate content metrics and add content_f1 to the delta"
```

---

### Task 4: CLI — print content metrics and move the "meaningful signal" label

**Files:**
- Modify: `utilities/train_vision_model.py` (`print_evaluation_result`)
- Test: `tests/training/test_train_vision_cli.py`

**Interfaces:**
- Consumes: aggregate `content_f1`/`content_precision`/`content_recall` and delta
  `content_f1` from Task 3.
- Produces: no new symbols; CLI output lines only.

- [ ] **Step 1: Write the failing tests**

Append to `tests/training/test_train_vision_cli.py` (module has `_RecordingLogger`, `_failed_comparison_result`, `_write_example`, `tvm`, `pytest`):

```python
def test_print_shows_content_f1_when_present(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    result = _failed_comparison_result(test_set)
    result["metrics"]["content_f1"] = 0.75
    result["metrics"]["content_precision"] = 0.8
    result["metrics"]["content_recall"] = 0.7
    rec = _RecordingLogger()
    monkeypatch.setattr(tvm, "logger", rec)

    tvm.print_evaluation_result(result)

    lines = " ".join(rec.infos + rec.warnings + rec.errors).lower()
    assert "content" in lines and "0.75" in lines
    # The "meaningful signal" label moves to content F1 when it is present.
    assert "meaningful signal" in lines


def test_print_omits_content_when_absent(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    result = _failed_comparison_result(test_set)
    result["metrics"]["content_f1"] = None
    rec = _RecordingLogger()
    monkeypatch.setattr(tvm, "logger", rec)

    tvm.print_evaluation_result(result)

    lines = " ".join(rec.infos + rec.warnings + rec.errors).lower()
    assert "content f1" not in lines
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/training/test_train_vision_cli.py -k "content" -v --no-cov`
Expected: FAIL — no content line printed / "meaningful signal" not on a content line.

- [ ] **Step 3: Print content metrics in the single-model summary**

In `print_evaluation_result`, after the `Raw TCs/example` info line and before the `if result["errors"]:` block, add:

```python
    content_f1 = metrics.get("content_f1")
    if content_f1 is not None:
        logger.info(
            f"Content F1:       {content_f1:.2f}  <- reference-aware quality "
            "(the meaningful signal when references exist)"
        )
        logger.info(
            f"  Precision:      {metrics.get('content_precision', 0.0):.2f}   "
            f"Recall: {metrics.get('content_recall', 0.0):.2f}"
        )
```

- [ ] **Step 4: Reflect content F1 in the A/B delta block**

In `print_evaluation_result`, inside the `else:` branch that prints the delta
(where `Coverage` and `Raw volume` are printed), append after the `Raw volume`
line:

```python
            if delta.get("content_f1") is not None:
                logger.info(
                    f"  Content F1:     {_format_delta(delta.get('content_f1'))}  "
                    "<- reference-aware quality delta (the meaningful signal)"
                )
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m pytest tests/training/test_train_vision_cli.py -v --no-cov`
Expected: PASS (all CLI tests).

- [ ] **Step 6: Lint, format, type-check**

Run: `ruff check utilities/train_vision_model.py tests/training/test_train_vision_cli.py && ruff format --check utilities/train_vision_model.py tests/training/test_train_vision_cli.py && mypy utilities/train_vision_model.py --python-version 3.14 --no-incremental`
Expected: All pass.

- [ ] **Step 7: Commit**

```bash
git add utilities/train_vision_model.py tests/training/test_train_vision_cli.py
git commit -m "feat(training): surface reference-aware content F1 in the eval CLI"
```

---

### Task 5: Train/val split producer

**Files:**
- Modify: `src/training/raft_dataset_builder.py` (`split_dataset`, `save_split`)
- Modify: `utilities/build_vision_dataset.py` (`--val-split-ratio`, `--split-seed`, `--force`)
- Test: `tests/training/test_raft_dataset_builder.py`

**Interfaces:**
- Produces:
  - `RAFTDatasetBuilder.split_dataset(self, examples: list[dict], val_ratio: float = 0.2, seed: int = 42) -> tuple[list[dict], list[dict]]`.
  - `RAFTDatasetBuilder.save_split(self, examples: list[dict], out_dir: Path, val_ratio: float = 0.2, seed: int = 42, force: bool = False) -> tuple[Path, Path]` writing `train.jsonl` and `val.jsonl`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/training/test_raft_dataset_builder.py` (add `import pytest` and
`from pathlib import Path` at the top if not already present; confirm the module
name imported is `RAFTDatasetBuilder`):

```python
def _examples(n):
    return [{"messages": [{"role": "user", "content": f"ex {i}"}]} for i in range(n)]


def test_split_is_deterministic_for_a_seed():
    builder = RAFTDatasetBuilder.__new__(RAFTDatasetBuilder)  # no __init__ side effects
    train_a, val_a = builder.split_dataset(_examples(10), val_ratio=0.2, seed=7)
    train_b, val_b = builder.split_dataset(_examples(10), val_ratio=0.2, seed=7)
    assert (train_a, val_a) == (train_b, val_b)
    assert len(val_a) == 2 and len(train_a) == 8


def test_split_keeps_at_least_one_val_and_one_train():
    builder = RAFTDatasetBuilder.__new__(RAFTDatasetBuilder)
    train, val = builder.split_dataset(_examples(2), val_ratio=0.01, seed=1)
    assert len(val) == 1 and len(train) == 1


def test_split_rejects_too_few_examples():
    builder = RAFTDatasetBuilder.__new__(RAFTDatasetBuilder)
    with pytest.raises(ValueError, match="at least 2"):
        builder.split_dataset(_examples(1))


def test_save_split_writes_two_jsonl_files(tmp_path):
    builder = RAFTDatasetBuilder.__new__(RAFTDatasetBuilder)
    train_path, val_path = builder.save_split(_examples(10), tmp_path, val_ratio=0.2, seed=7)
    assert train_path.name == "train.jsonl" and val_path.name == "val.jsonl"
    assert len(val_path.read_text().strip().splitlines()) == 2
    assert len(train_path.read_text().strip().splitlines()) == 8


def test_save_split_refuses_overwrite_without_force(tmp_path):
    builder = RAFTDatasetBuilder.__new__(RAFTDatasetBuilder)
    builder.save_split(_examples(10), tmp_path)
    with pytest.raises(FileExistsError):
        builder.save_split(_examples(10), tmp_path)
    # force overwrites cleanly
    builder.save_split(_examples(10), tmp_path, force=True)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/training/test_raft_dataset_builder.py -k "split" -v --no-cov`
Expected: FAIL — `AttributeError: ... has no attribute 'split_dataset'`.

- [ ] **Step 3: Implement `split_dataset` and `save_split`**

Add `import random` to the top of `src/training/raft_dataset_builder.py` if not
present (it already imports `json`; add `from pathlib import Path` if absent).
Add both methods to `RAFTDatasetBuilder`:

```python
    def split_dataset(
        self, examples: list[dict[str, Any]], val_ratio: float = 0.2, seed: int = 42
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Split examples into (train, val) deterministically.

        Args:
            examples: The full example list.
            val_ratio: Fraction held out for validation (0 < ratio < 1).
            seed: RNG seed; the same seed yields the same split.

        Returns:
            A (train, val) tuple; both are non-empty.

        Raises:
            ValueError: If ``val_ratio`` is out of range or there are fewer than
                2 examples to split.
        """
        if not 0.0 < val_ratio < 1.0:
            raise ValueError(f"val_ratio must be in (0, 1), got {val_ratio}")
        if len(examples) < 2:
            raise ValueError("need at least 2 examples to split")

        shuffled = list(examples)
        random.Random(seed).shuffle(shuffled)
        n_val = max(1, round(len(shuffled) * val_ratio))
        n_val = min(n_val, len(shuffled) - 1)  # keep >= 1 in train
        return shuffled[n_val:], shuffled[:n_val]

    def save_split(
        self,
        examples: list[dict[str, Any]],
        out_dir: Path,
        val_ratio: float = 0.2,
        seed: int = 42,
        force: bool = False,
    ) -> tuple[Path, Path]:
        """Write ``train.jsonl`` and ``val.jsonl`` to ``out_dir``.

        Args:
            examples: The full example list.
            out_dir: Directory to write the two files into.
            val_ratio: Validation fraction (see ``split_dataset``).
            seed: RNG seed (see ``split_dataset``).
            force: Overwrite existing files instead of raising.

        Returns:
            A (train_path, val_path) tuple.

        Raises:
            FileExistsError: If a target file exists and ``force`` is False.
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        train_path = out_dir / "train.jsonl"
        val_path = out_dir / "val.jsonl"
        if not force:
            for path in (train_path, val_path):
                if path.exists():
                    raise FileExistsError(f"{path} exists; pass force=True to overwrite")

        train, val = self.split_dataset(examples, val_ratio=val_ratio, seed=seed)
        for path, rows in ((train_path, train), (val_path, val)):
            path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
            )
        return train_path, val_path
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/training/test_raft_dataset_builder.py -k "split" -v --no-cov`
Expected: PASS (5 tests).

- [ ] **Step 5: Wire the CLI flags into `build_vision_dataset.py`**

Read `utilities/build_vision_dataset.py` to find its argument parser and the
point where it has built the example list and saved the dataset. Add three
arguments to the parser:

```python
    parser.add_argument(
        "--val-split-ratio",
        type=float,
        default=None,
        help="If set (0-1), also write val.jsonl with this fraction held out.",
    )
    parser.add_argument(
        "--split-seed",
        type=int,
        default=42,
        help="Seed for the train/val split (default: 42).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing train.jsonl/val.jsonl split.",
    )
```

After the dataset is built and saved (where the builder and the example list are
in scope — call the local variables `builder` and `examples` to match the
existing code, adjusting names to whatever that file uses), add:

```python
    if args.val_split_ratio is not None:
        train_path, val_path = builder.save_split(
            examples,
            out_dir=Path(args.output_dir) if hasattr(args, "output_dir") else Path("."),
            val_ratio=args.val_split_ratio,
            seed=args.split_seed,
            force=args.force,
        )
        logger.info(f"Wrote split: {train_path} + {val_path}")
```

(The executor adapts `args.output_dir`/`logger`/`examples` to the actual names
in that file.)

- [ ] **Step 6: Verify the CLI still parses and the split flag is optional**

Run: `python3 utilities/build_vision_dataset.py --help`
Expected: help text lists `--val-split-ratio`, `--split-seed`, `--force`; exit 0.

- [ ] **Step 7: Lint, format, type-check**

Run: `ruff check src/training/raft_dataset_builder.py utilities/build_vision_dataset.py tests/training/test_raft_dataset_builder.py && ruff format --check src/training/raft_dataset_builder.py utilities/build_vision_dataset.py tests/training/test_raft_dataset_builder.py && mypy src/training/raft_dataset_builder.py --python-version 3.14 --no-incremental`
Expected: All pass.

- [ ] **Step 8: Commit**

```bash
git add src/training/raft_dataset_builder.py utilities/build_vision_dataset.py tests/training/test_raft_dataset_builder.py
git commit -m "feat(training): add seeded train/val split producer"
```

---

### Task 6: Documentation and CHANGELOG

**Files:**
- Modify: `docs/training/README.md`
- Modify: `CHANGELOG.md`

**Interfaces:** none (docs only).

- [ ] **Step 1: Document the content metric in the evaluation section**

In `docs/training/README.md`, in the "5. Evaluate a customized model" metric
table, add a row (after the `raw_test_cases_per_example` row):

```markdown
| `content_f1` (+ `content_precision`, `content_recall`) | Reference-aware scenario overlap between the generated cases and the held-out reference answer | **The meaningful quality signal when references exist.** Deterministic (deduplicator similarity ≥ 0.85); `None` when an example has no parseable reference. |
```

And append to the "A/B honesty notes" list:

```markdown
- When examples carry a reference answer, the **content F1 delta** is the
  headline signal (quality), above the count-based coverage delta. It is paired
  and withheld with the baseline exactly like the other deltas.
```

- [ ] **Step 2: Document the split step**

In `docs/training/README.md`, in "### 3. Build the vision RAFT dataset", append:

```markdown
To also produce a held-out validation set for `--evaluate`, add a split ratio:

```bash
python3 utilities/build_vision_dataset.py --val-split-ratio 0.2
# writes train.jsonl + val.jsonl (deterministic; --split-seed to change, --force to overwrite)
```
```

- [ ] **Step 3: Add CHANGELOG entries**

In `CHANGELOG.md` under `## [Unreleased]`, add to `### Added (feature)` (create
the subsection if ordering requires, matching existing style):

```markdown
- **Phase 3 reference-aware content metric for `evaluate_model`.** A
  deterministic `ReferenceOverlapScorer` (new `src/training/content_scorer.py`,
  behind a `ContentScorer` protocol seam for a future LLM-judge) scores generated
  test cases against the held-out example's reference answer by scenario
  precision/recall/F1, matching cases with the production deduplicator's
  similarity (new public `TestCaseDeduplicator.similarity`). Metrics thread
  through per-example detail, aggregates (`content_precision`/`content_recall`/
  `content_f1`, macro means, `None` without references), the paired A/B delta,
  and the CLI, where content F1 becomes the "meaningful signal" when references
  exist. New `VisionTrainingConfig.content_match_threshold` (default 0.85).
- **Seeded train/val split producer** — `RAFTDatasetBuilder.split_dataset` /
  `save_split` write `train.jsonl` + `val.jsonl` deterministically, exposed via
  `build_vision_dataset.py --val-split-ratio` (`--split-seed`, `--force`).
```

- [ ] **Step 4: Commit**

```bash
git add docs/training/README.md CHANGELOG.md
git commit -m "docs(training): document the content metric and train/val split"
```

---

### Task 7: Opt-in real-Ollama integration test

**Files:**
- Modify: `tests/training/test_vision_raft_evaluate_integration.py`

**Interfaces:**
- Consumes: `evaluate_model` content metrics (Tasks 2–3).

- [ ] **Step 1: Write the failing (skip-guarded) integration test**

Append to `tests/training/test_vision_raft_evaluate_integration.py` (module has
`_ollama_reason`, `_write_jsonl`, `_text_example`, `TEXT_MODEL`, `pytest`, `json`,
`VisionRAFTTrainer`, `VisionTrainingConfig`):

```python
def _text_example_with_reference() -> dict:
    ex = _text_example()
    ex["messages"][2]["content"] = json.dumps(
        {
            "test_cases": [
                {
                    "summary_suffix": "doors unlock at standstill",
                    "preconditions": "vehicle speed 0 km/h",
                    "test_steps": "1. Press the central unlock button.",
                    "expected_result": "All doors unlock.",
                    "test_type": "functional",
                }
            ]
        }
    )
    return ex


@pytest.mark.integration
@pytest.mark.slow
def test_real_ollama_populates_content_metrics(tmp_path) -> None:
    """A live run with a reference answer must populate content metrics."""
    reason = _ollama_reason()
    if reason:
        pytest.skip(reason)

    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_text_example_with_reference()])
    trainer = VisionRAFTTrainer(
        dataset_path=test_set,
        config=VisionTrainingConfig(output_model=TEXT_MODEL),
        output_dir=tmp_path / "models",
    )

    result = trainer.evaluate_model(test_dataset=test_set)

    content = result["per_example"][0]["content"]
    assert content is not None
    assert 0.0 <= content["recall"] <= 1.0
    assert result["metrics"]["content_f1"] is not None
```

- [ ] **Step 2: Run the integration test against local Ollama**

Run: `python3 -m pytest tests/training/test_vision_raft_evaluate_integration.py -v --no-cov -m integration`
Expected: PASS (skips if Ollama/llama3.1:8b unavailable). The new test asserts
content metrics populate on a real generation.

- [ ] **Step 3: Lint and format**

Run: `ruff check tests/training/test_vision_raft_evaluate_integration.py && ruff format --check tests/training/test_vision_raft_evaluate_integration.py`
Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add tests/training/test_vision_raft_evaluate_integration.py
git commit -m "test(training): live-Ollama coverage for content metrics"
```

---

### Task 8: Full-suite gate and finalize

**Files:** none (verification only).

- [ ] **Step 1: Run the full non-integration suite**

Run: `python3 -m pytest tests/ -q -p no:cacheprovider --no-cov -m "not integration"`
Expected: all pass (previous baseline 569 + the Phase 3 unit tests), ≤1 skip.

- [ ] **Step 2: Whole-suite quality gates on touched files**

Run: `ruff check src/ main.py utilities/ && ruff format --check src/training/content_scorer.py src/training/vision_raft_trainer.py src/core/deduplicator.py src/training/raft_dataset_builder.py utilities/train_vision_model.py utilities/build_vision_dataset.py && mypy src/ main.py --python-version 3.14`
Expected: ruff clean; mypy no new errors beyond the documented pre-existing baseline.

- [ ] **Step 3: Refresh code-intelligence indexes**

Run: `graphify update . && node .gitnexus/run.cjs analyze`
Expected: both complete; note the refreshed counts.

- [ ] **Step 4: Commit the index refresh**

```bash
git add AGENTS.md CLAUDE.md graphify-out/
git commit -m "chore: refresh indexes after Phase 3 content metric"
```

- [ ] **Step 5: Push the branch**

Run: `git push -u origin feat/phase3-content-metric`
Expected: branch pushed; no merge to main.

---

## Self-Review

**Spec coverage:**
- Content metric (deterministic overlap) → Tasks 1–3. ✓
- `ContentScorer` seam for future judge → Task 1 (Protocol). ✓
- Matching via deduplicator SequenceMatcher (defaulted decision A) → Task 1 public `similarity`. ✓
- F1 headline (defaulted decision B) → Tasks 3–4 (content_f1 in aggregate/delta/CLI label). ✓
- Result-shape integration (per-example, aggregate, delta, CLI) → Tasks 2–4. ✓
- Edge cases (no reference → None; |G|=0 → recall 0/precision None/f1 0) → Task 1 Steps 4/6, Task 2 tests. ✓
- Train/val split producer (seeded, guards, `--val-split-ratio`) → Task 5. ✓
- Docs + CHANGELOG → Task 6. ✓
- Opt-in live integration test → Task 7. ✓
- Full-suite/gates + index refresh + push → Task 8. ✓

**Deviation from spec (noted for the reviewer):** the spec listed
`training.val_split_ratio` / `training.split_seed` as `config/cli_config.yaml`
keys. This plan implements them as CLI flags with defaults (0.2 / 42) on
`build_vision_dataset.py` instead of adding Pydantic ConfigManager keys — the
flags fully deliver the capability with a smaller blast radius. Add the config
keys later if a non-CLI default source is wanted.

**Placeholder scan:** no TBD/TODO; every code step shows complete code. Task 5
Step 5 and its note flag the one place (`build_vision_dataset.py` variable
names) where the executor adapts to the existing file — with the exact code to
insert.

**Type consistency:** `ContentScore` keys (`precision`/`recall`/`f1`) are used
consistently across scorer, per-example `content`, aggregate `content_*`, delta,
and CLI. `split_dataset`/`save_split` signatures match between Task 5's
Interfaces, tests, and implementation. `content_scorer` parameter name is
consistent across `evaluate_model`/`_score_over_dataset`/`_evaluate_example`.
