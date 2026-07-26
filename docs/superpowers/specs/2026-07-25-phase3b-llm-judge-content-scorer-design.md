# Phase 3b — LLM-Judge Content Scorer Design

**Date:** 2026-07-25
**Branch:** `feat/phase3b-llm-judge`
**Status:** Approved (design); implementation plan to follow.

## Goal

Add a second `ContentScorer` implementation — an LLM-as-judge — behind the seam
Phase 3 established. Where the deterministic `ReferenceOverlapScorer` matches
generated and reference test cases by *string* similarity (`SequenceMatcher`
≥ 0.85), the LLM judge matches by *meaning* (catching paraphrased, reworded, or
reordered scenarios that string overlap scores as "different") and additionally
rates the generation's intrinsic quality on a holistic rubric. It plugs into the
existing per-example → aggregate → paired-delta → CLI evaluation path.

## Locked Decisions

| Decision | Choice |
|----------|--------|
| Judge output | **Hybrid**: semantic matching (precision/recall/F1) **and** a holistic quality rating |
| Calls per example | **Two**: one matching call, one quality call |
| Client access | **Widen the `ContentScorer` Protocol** to thread `client` + `judge_model` through `score()` |
| Rubric shape | **Single holistic `quality` 0–1 + one-line rationale** (no per-dimension sub-scores) |
| Judge model | Fixed evaluator `llama3.1:8b` (a new `VisionTrainingConfig.judge_model`), **not** the model under test |
| Empty-generation quality | `None` (undefined — nothing to rate; mirrors precision's `None` for 0/0) |
| Quality grounding | **Reference-aware** — the quality call sees the reference (gold) cases |
| Headline signal | `content_f1` stays the headline; `content_quality` is a complementary line |
| Default scorer | `overlap` (deterministic) — behavior unchanged unless the user opts into `llm` |

## Architecture

The `ContentScorer` Protocol remains the single seam. Two implementations:

- `ReferenceOverlapScorer` (existing, deterministic) — unchanged behavior.
- `LLMJudgeScorer` (new) — non-deterministic, calls a local Ollama model.

`evaluate_model` selects nothing new: the CLI builds the chosen scorer and
injects it via the existing `evaluate_model(content_scorer=...)` parameter.
`evaluate_model` only gains the responsibility of **threading its Ollama client
and the configured judge model into `score()`** (identically for the customized
and base passes, so A/B stays fair).

### Component 1 — Shared contract & math (`src/training/content_scorer.py`)

- Extend `ContentScore` (TypedDict) with `quality: float | None`.
  `ReferenceOverlapScorer` returns `quality: None` in every dict it produces; the
  deterministic path is otherwise untouched.
- Extract the precision/recall/F1 computation into a module-level helper
  `_prf(matched: int, n_generated: int, n_reference: int) -> tuple[float | None, float, float]`
  reused by both scorers (no formula duplication). Contract:
  - `n_reference == 0` is handled by the caller (returns `None` before `_prf`).
  - `n_generated == 0` → `(None, 0.0, 0.0)` (precision undefined, recall/f1 defined against a non-empty reference).
  - otherwise `precision = matched / n_generated`, `recall = matched / n_reference`,
    `f1 = 0.0 if precision + recall == 0 else 2·p·r/(p+r)`.
- Widen the Protocol:
  ```python
  class ContentScorer(Protocol):
      def score(
          self,
          generated_cases: list[dict],
          reference_cases: list[dict],
          *,
          client: Any = None,
          judge_model: str | None = None,
      ) -> ContentScore | None: ...
  ```
  The two new params are keyword-only so call sites stay explicit.
  `ReferenceOverlapScorer.score` accepts and ignores them.

### Component 2 — `LLMJudgeScorer` (new `src/training/llm_judge_scorer.py`)

Its own module, keeping `content_scorer.py` as the shared contract plus the
deterministic scorer. `__slots__` declared (project convention).

```python
class LLMJudgeScorer:
    __slots__ = ("judge_model", "temperature")
    def __init__(self, judge_model: str = "llama3.1:8b", temperature: float = 0.0) -> None: ...
    def score(self, generated_cases, reference_cases, *, client=None, judge_model=None) -> ContentScore | None: ...
```

`score()` control flow:
1. `if not reference_cases: return None`.
2. `if not generated_cases: return {"precision": None, "recall": 0.0, "f1": 0.0, "quality": None}`.
3. Resolve `model = judge_model or self.judge_model`. If `client is None`, lazily
   build an `OllamaClient()` (the widened seam normally supplies one from
   `evaluate_model`).
4. **Matching call** — render `_MATCH_PROMPT` with numbered generated and
   reference cases; request strict JSON `{"matches": [[gen_index, ref_index], ...]}`.
   Parse via `JSONResponseParser.extract_json_from_response`. Enforce one-to-one:
   each reference index counts at most once and each generated index at most once
   (dedupe, first occurrence wins). `matched` = number of accepted pairs →
   `_prf(matched, len(generated_cases), len(reference_cases))`.
5. **Quality call** — render `_QUALITY_PROMPT` with the generated cases **and the
   reference cases as the gold standard**; request strict JSON
   `{"quality": <0-1 float>, "rationale": "<one line>"}`. Parse, coerce to float,
   clamp to `[0.0, 1.0]`.
6. Each call is wrapped in its own `try/except` (`BLE001`-style broad catch, as in
   Phase 3's `_score_content`): a malformed or failed **matching** call sets
   precision/recall/f1 to `None`; a malformed or failed **quality** call sets
   `quality` to `None`. One sub-call failing never wipes the other.
7. Return `{"precision": ..., "recall": ..., "f1": ..., "quality": ...}`.

Prompts are two module-level string constants. Both instruct the model to return
*only* JSON. `temperature=0.0` for maximum reproducibility (still not fully
deterministic — see Testing).

### Component 3 — Trainer wiring (`src/training/vision_raft_trainer.py`)

- Add `VisionTrainingConfig.judge_model: str = "llama3.1:8b"`.
- `_score_content` threads the already-available `client` and
  `self.config.judge_model` into `content_scorer.score(...)`. The client is
  already passed down to `_evaluate_example` for generation, so it is in scope;
  pass it into `_score_content`. The judge model is identical for the customized
  and base passes.
- `_aggregate_eval_metrics`: add `content_quality` to the per-field macro-mean set
  (`None` when no example carried a quality score). The existing per-field
  denominator comment already documents that each `content_*` aggregate averages
  only over examples where that field is defined; `content_quality` follows the
  same rule.
- `_compute_delta`: add `content_quality` to the `comparable` tuple.
- Headline unchanged: `content_f1` remains the "meaningful signal"; `content_quality`
  is an additional reported line, not relabeled as the headline.

### Component 4 — CLI selection (`utilities/train_vision_model.py`)

- `--content-scorer {overlap,llm}`, default `overlap`.
- `--judge-model <name>`, optional, default `None` (falls back to
  `config.judge_model`); only meaningful with `--content-scorer llm`.
- The CLI constructs the chosen scorer:
  `ReferenceOverlapScorer(config.content_match_threshold)` or
  `LLMJudgeScorer(judge_model=args.judge_model or config.judge_model)`, and passes
  it via `evaluate_model(content_scorer=...)`. No scorer-selection branch is added
  inside `evaluate_model`.
- `print_evaluation_result`: print a `Content Quality` line (single-model block)
  and a `content_quality` delta line (A/B block) when the value is present, beneath
  the existing content-F1 lines. Guard for `--content-scorer llm` without
  `--evaluate` is unnecessary because scorer selection is inert without a dataset.

## Data Flow

```
CLI: --content-scorer llm  --> build LLMJudgeScorer(judge_model)
     --> evaluate_model(test_dataset, client, compare_base, content_scorer=judge)
         per example (customized model, then base model if compare_base):
           generate raw_output
           _score_content(raw_output, example, content_scorer, client, judge_model)
             parse generated -> canonical unique cases
             parse reference  -> canonical unique cases
             content_scorer.score(generated, reference, client=client, judge_model=model)
               matching call -> matches -> _prf -> precision/recall/f1
               quality  call -> quality (0-1)
             -> {precision, recall, f1, quality} | None
         aggregate -> content_precision/recall/f1/quality (macro means, None-safe)
         paired delta over comparable incl. content_quality
     CLI prints content F1 (headline) + content quality (secondary)
```

## Error Handling

- **No reference cases** → `score()` returns `None` (whole example content is `None`).
- **Empty generation** (reference present) → `{precision: None, recall: 0.0, f1: 0.0, quality: None}`.
- **Malformed/failed matching call** → precision/recall/f1 = `None`; quality still attempted.
- **Malformed/failed quality call** → quality = `None`; matching still returned.
- **Client/connection error inside a call** → treated as that call failing (sub-score `None`); never aborts the eval run — same isolation guarantee as Phase 3.
- All aggregates are `None`-safe (macro mean over defined values only).

## Testing

- `temperature=0.0` and strict JSON prompts for maximum reproducibility; the judge
  is still non-deterministic, so correctness is pinned by **mocked** unit tests.
- **Unit tests** (`tests/training/test_llm_judge_scorer.py`) use a `FakeOllamaClient`
  returning canned JSON:
  - perfect matching (all pairs) → precision/recall/f1 = 1.0;
  - partial matching → expected fractional P/R/F1;
  - quality parse + clamp (e.g. `1.3` → `1.0`, `-0.2` → `0.0`);
  - malformed matching JSON → P/R/F1 `None` but quality still scored;
  - malformed quality JSON → quality `None` but P/R/F1 still scored;
  - no reference → `None`; empty generation → the documented dict.
- **Protocol-widening regression**: assert `ReferenceOverlapScorer.score(gen, ref, client=object(), judge_model="x")` ignores the new params and returns the same result as without them.
- **Trainer integration (mocked)** in `tests/training/test_vision_raft_evaluate.py`:
  injecting an `LLMJudgeScorer` backed by a `FakeOllamaClient` populates
  per-example `content.quality`, aggregate `content_quality`, and the delta key.
- **Opt-in real-Ollama integration test**
  (`tests/training/test_vision_raft_evaluate_integration.py`, `integration`/`slow`,
  self-skipping): a live judge run against `llama3.1:8b` populates
  `content_quality` and P/R/F1 all within `[0.0, 1.0]`.

## Documentation

- `docs/training/README.md`: document the `--content-scorer`/`--judge-model` flags,
  the `content_quality` metric, the non-determinism caveat, and that `overlap`
  (deterministic) remains the default.
- `CHANGELOG.md` `[Unreleased]` → Added: the LLM-judge content scorer and its flags.

## Scope / YAGNI (explicitly out)

- No cloud/hosted judge (local Ollama only) — the seam keeps it a future drop-in.
- No per-dimension rubric (single holistic quality).
- No caching, batching, or async judge.
- No change to the deterministic default; opt-in only.
- No auto train/val default for `--evaluate` (unchanged from Phase 3).

## Files Touched

| File | Change |
|------|--------|
| `src/training/content_scorer.py` | `ContentScore.quality`; `_prf` helper; widened Protocol; `ReferenceOverlapScorer` emits `quality: None` and ignores new params |
| `src/training/llm_judge_scorer.py` | **New** — `LLMJudgeScorer` + two prompt constants |
| `src/training/vision_raft_trainer.py` | `judge_model` config; thread client+judge_model in `_score_content`; aggregate + delta `content_quality` |
| `utilities/train_vision_model.py` | `--content-scorer`/`--judge-model`; build+inject scorer; print quality lines |
| `tests/training/test_llm_judge_scorer.py` | **New** — mocked unit tests |
| `tests/training/test_vision_raft_evaluate.py` | LLM-judge (mocked) aggregate/delta tests |
| `tests/training/test_vision_raft_evaluate_integration.py` | opt-in live-judge test |
| `docs/training/README.md`, `CHANGELOG.md` | docs |
