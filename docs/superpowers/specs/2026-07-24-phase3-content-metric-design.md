# Phase 3 — Content Metric + Train/Val Split (Design)

**Date:** 2026-07-24
**Branch:** `feat/phase3-content-metric` (based off `feat/vision-raft-evaluate-model`,
which holds the unmerged Phase 1–2 + review-fix evaluator work this depends on)
**Status:** Approved design, pending implementation plan
**Context:** Completes `VisionRAFTTrainer.evaluate_model`. Phases 1–2 and the
2026-07-24 review fixes measure only output *validity* (grammar-saturated ≈1.0
for every model) and coverage *count* (`unique_valid_test_cases_per_example`),
neither of which reflects whether the model produced the *right* scenarios. The
held-out RAFT example already carries a structured reference answer
(`assistant` message = prior validated `generated_test_cases`), which the
evaluator currently ignores. Phase 3 adds a reference-aware content metric and a
train/val split producer so a held-out set exists to score against.

## Goals

1. A **deterministic, reference-aware content metric** (scenario
   precision/recall/F1) that becomes the meaningful A/B decision signal, above
   the count-based `unique_valid` coverage.
2. A **clean scorer seam** so an optional LLM-as-judge layer can be added later
   with no harness changes.
3. A **train/val split producer** in `RAFTDatasetBuilder` so a held-out set is
   produced automatically rather than hand-built.

## Non-goals

- **LLM-as-judge** (Phase 3b, future, behind a flag). This spec only builds the
  seam for it.
- **Live vision content scoring.** The local llama.cpp server lacks `mllama`
  support (see `local-ollama-dev-setup`), so live tests stay text-only, as with
  the Rec 5 integration test.
- **Weight fine-tuning.** Unchanged: this remains prompt customization; the
  "held-out" split is nominal (no weight training occurs).

## Architecture & components

Four independently testable units:

### 1. `ContentScorer` protocol — `src/training/content_scorer.py` (new)

```python
class ContentScore(TypedDict):
    precision: float | None
    recall: float | None
    f1: float | None

class ContentScorer(Protocol):
    def score(
        self, generated_cases: list[dict], reference_cases: list[dict]
    ) -> ContentScore | None: ...
```

- Single method; returns `None` when scoring is impossible (no reference).
- This is the seam. A future `LLMJudgeScorer` implements the same protocol.

### 2. `ReferenceOverlapScorer` — `src/training/content_scorer.py` (new)

Deterministic implementation, ships now (semantics below).

### 3. Split producer — `RAFTDatasetBuilder` (change)

`split_dataset(examples, val_ratio, seed) -> (train, val)` plus a save path that
writes `train.jsonl` + `val.jsonl`.

### 4. Evaluator wiring — `VisionRAFTTrainer` (change)

`evaluate_model` gains an optional `content_scorer` parameter (default
`ReferenceOverlapScorer()`), injected like the existing `client`. `_evaluate_example`
extracts the example's reference answer, scores it, and threads content metrics
into per-example detail → aggregates → delta → provenance → CLI.

The scorer is injected so unit tests stay deterministic and a judge can be
swapped in later with zero harness changes.

## Reference-overlap metric semantics

- **Parse both sides** to canonical, deduplicated cases (reuse
  `is_canonical_test_case` + `TestCaseDeduplicator`, already in the P0 path).
  Generated set `G`, reference set `R`. The reference answer may be a JSON string
  or an already-parsed structure; the scorer normalizes both via the existing
  `JSONResponseParser.extract_json_from_response` path.
- **Match** a generated case to a reference case when field-similarity ≥ τ over
  `DEFAULT_FIELDS_TO_COMPARE`, using the deduplicator's existing `SequenceMatcher`
  similarity — already the project's definition of "same test case." Matching is
  **greedy one-to-one**: iterate generated cases in list order, and match each to
  its highest-similarity still-unmatched reference case whose similarity ≥ τ
  (ties broken by reference list order). Each reference case is matched at most
  once. `M` = number of matched pairs. This is deterministic and order-stable.
- **precision = M / |G|** — of the distinct cases the model generated, how many
  correspond to a reference scenario (on-topic-ness).
- **recall = M / |R|** — of the reference scenarios, how many the model covered.
- **F1** = harmonic mean of precision and recall. **Headline decision metric.**
- **τ knob:** `VisionTrainingConfig.content_match_threshold`, default `0.85`
  (the deduplicator's default `similarity_threshold`).
- **Aggregate:** macro-average (mean over examples that have a content score),
  matching the existing `overall_score` style.

### Edge cases

| Case | Behavior |
|---|---|
| No reference / unparseable reference (`R` absent) | `score()` returns `None`; example excluded from the content aggregate (existing "None, never fake 0.0" pattern). |
| `|R| > 0`, `|G| = 0` (model produced nothing valid) | recall `0.0`, precision `None`, f1 `0.0`. |
| `|R| = 0` but reference field present-but-empty | treated as no reference → `None`. |
| Both sides identical | precision = recall = f1 = `1.0`. |

## Result shape, CLI & split producer

### Per-example detail (`_evaluate_example`)

Gains `content: ContentScore | None` alongside the existing `score`,
`unique_valid`, etc.

### Aggregate metrics (`_aggregate_eval_metrics`)

Gains `content_precision`, `content_recall`, `content_f1` (macro means; `None`
when no example carried a reference). Existing keys unchanged.

### Delta / provenance / CLI

- `_compute_delta` comparable set gains `content_f1` (and precision/recall),
  paired like the others (2026-07-24 Critical 1 contract preserved).
- CLI "meaningful signal" label moves to **content F1** when content metrics are
  present, falling back to `unique_valid` coverage when no references exist (so
  reference-less datasets still evaluate, just without the content signal).
- The bundle-vs-base provenance caveat (Rec 4) is unchanged and still applies.

### Split producer (`RAFTDatasetBuilder`)

- `split_dataset(examples, val_ratio, seed) -> (train, val)` — deterministic via
  `random.Random(seed)` (shuffle then slice).
- A save path writes `train.jsonl` + `val.jsonl` next to the source dataset.
- **Invocation:** exposed as a `--val-split-ratio` option on the existing
  `utilities/build_vision_dataset.py` — when set, it also writes `val.jsonl`
  beside the main dataset. No new top-level script.
- New config: `training.val_split_ratio` (default `0.2`), `training.split_seed`
  (default fixed int for reproducibility).
- Guards: needs ≥2 examples to split; ensures ≥1 val example when `ratio > 0`;
  raises `ValueError` rather than overwriting an existing `val.jsonl` unless a
  `--force` flag is passed.

## Error handling

- Content scoring never aborts a run: a scorer exception on one example is
  isolated and recorded (mirrors the existing per-example generation-error
  isolation), yielding `content = None` for that example.
- The split producer raises a clear `ValueError` on too-few-examples rather than
  emitting an empty or single-sided split.

## Testing

**Deterministic unit tests (no model):**

- Perfect overlap → f1 `1.0`; fully disjoint → `0.0`; partial → known
  precision/recall (e.g. 3 generated, 2 reference, 1 match → P `0.33`, R `0.5`).
- Paraphrased-but-similar case matches at τ; a case just below τ does not.
- Missing / unparseable reference → `content` `None`, excluded from aggregate.
- `|G|=0, |R|>0` → recall `0.0`, precision `None`, f1 `0.0`.
- A/B content-F1 delta arithmetic (paired), and content delta withheld with the
  baseline (Critical 1 contract).
- CLI "meaningful signal" label switches to content F1 when present.
- Split: same seed → identical split; ratio honored; tiny-dataset guard raises.

**One opt-in live integration test** (`integration`/`slow`, self-skipping;
`llama3.1:8b`, text-only): content metrics populate and the A/B completes.

TDD throughout (watch each test fail first). Full suite + ruff + mypy gates on
touched files, per project protocol.

## Files touched

| File | Change |
|---|---|
| `src/training/content_scorer.py` | New — protocol + `ReferenceOverlapScorer`. |
| `src/training/vision_raft_trainer.py` | Inject scorer; thread content metrics through eval/aggregate/delta/provenance; add `content_match_threshold`, `val_split_ratio`, `split_seed` to config. |
| `src/training/raft_dataset_builder.py` | Add `split_dataset` + save-split path. |
| `utilities/build_vision_dataset.py` | Add `--val-split-ratio` / `--force` to write `val.jsonl`. |
| `utilities/train_vision_model.py` | CLI "meaningful signal" label switch to content F1. |
| `docs/training/README.md` | Document the content metric and the split step. |
| `tests/training/` | Unit tests (scorer, split, wiring) + one integration test. |
| `CHANGELOG.md` | `[Unreleased]` entries. |

## Open decisions (defaulted, override in review)

- **A. Matching** = deduplicator `SequenceMatcher` over `DEFAULT_FIELDS_TO_COMPARE`
  at τ (vs. embeddings — rejected, needs a non-local model).
- **B. Headline** = **F1** (vs. recall-only). Precision & recall reported
  regardless.
