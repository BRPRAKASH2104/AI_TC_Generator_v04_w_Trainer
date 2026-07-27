# Current-State Review — July 24 Fix Verification and Regression Audit

**Date:** 2026-07-26
**Branch:** `main`
**Current revision:** `d3bd074`
**Remote revision:** `origin/main` = `d3bd074`
**Review baseline:** `docs/reviews/Review_Comments_2026_07_24.md` at
`c023893`
**Comparison:** `c023893..d3bd074`
**Scope:** current verification of all seven 2026-07-24 findings, all maintained
Python source and utilities, the complete test suite, live-Ollama evaluation
paths, training/evaluation documentation, and wheel packaging

## Recommendation

**REQUEST CHANGES — CRITICAL.**

The statement that all July 24 findings are fixed is not correct for the current
tree:

- **5 of 7** findings are fixed as originally scoped.
- **1 of 7** is only partially fixed: evaluation input validation added useful
  local bounds, but the accepted message contract and the message actually
  evaluated disagree, and aggregate input memory remains unbounded.
- **1 of 7** was fixed and then regressed: the real-Ollama evaluator tests were
  added, but the current full suite fails because judge retirement left a live
  test importing the deleted scorer.

The broader regression audit also found:

- **3 newly introduced Critical defects** in the dataset split, evaluation
  summary, and reference-aware decision metric;
- **1 pre-existing Critical defect** in the successful model-creation CLI path;
- **2 Recommended regressions/incomplete fixes**; and
- **2 Optional documentation/statistics defects**.

The production REQIFZ extraction-to-Excel path remains green in the available
tests. The blockers are concentrated in the training, held-out evaluation, and
model-selection workflow.

## July 24 Finding Re-evaluation

| July 24 item | Current status | Current evidence |
|---|---|---|
| Critical 1 — failed baseline reports positive lift and exits 0 | **Fixed** | Comparison is paired; total baseline failure withholds the delta and returns non-zero. The unit regression passes, and the live missing-baseline test passes against local Ollama. |
| Critical 2 — raw “coverage” rewards duplicates and invalid cases | **Fixed for the recorded reproductions** | Raw volume and canonical-valid deduplicated counts are separate. Duplicate-heavy and invalid-heavy unit regressions pass. The later reference-aware metric has different decision-integrity defects in Critical 3 below. |
| Recommended 3 — dataset parsing is unvalidated and unbounded | **Partially fixed** | Object/content/base64 checks, per-image limits, per-example image limits, and an example-count limit exist. Exact role/order is not enforced, the evaluator can use a different message than the validator, and the loader retains the complete base64-bearing dataset. See Recommended 5. |
| Recommended 4 — A/B wording overclaims prompt isolation | **Fixed** | Output and documentation say bundle-vs-base, record provenance, and disclose unmatched parameters/defaults. |
| Recommended 5 — no committed real-Ollama evaluator test | **Regressed after being fixed** | Three active evaluator integration cases pass live. A fourth test still imports the deleted LLM judge and makes the documented full suite fail. See Recommended 6. |
| Recommended 6 — training guide is contradictory and lacks evaluation guidance | **Fixed as originally scoped** | `docs/training/README.md` now explains prompt customization, evaluation, metrics, A/B limitations, and scorer calibration; the stale link in `utilities/train_vision_model.py` is fixed. New documentation drift remains; see Optional 7. |
| Optional 7 — `--compare-base` is silently ignored without `--evaluate` | **Fixed** | Argument parsing rejects the unsupported combination, and its regression tests pass. |

## Change and Risk Summary

From the reviewed revision to current `main`, the maintained training/evaluation
surface changed across 17 source, test, documentation, and changelog files:
2,883 insertions and 90 deletions.

GitNexus mapped the current execution flow as:

```text
utilities/train_vision_model.py::main
  -> run_evaluation
  -> VisionRAFTTrainer.evaluate_model
  -> _load_and_validate_examples
  -> _score_over_dataset
  -> _evaluate_example
  -> _generate_for_example
  -> _score_generation
  -> _score_content
  -> _aggregate_eval_metrics
  -> _compare_paired
  -> print_evaluation_result
```

The comparison-wide GitNexus result is **CRITICAL** and partial because the
revision range also contains regenerated graph/index artifacts. Narrowed symbol
impact shows most leaf changes as LOW/MEDIUM, but
`_aggregate_eval_metrics` is **HIGH** risk: seven upstream dependents across
three evaluator flow families consume it.

Graphify connects the same code path to the current rationale:

- `val.jsonl` is presented as the held-out input to `--evaluate`;
- `content_f1` is presented as the meaningful reference-aware decision signal;
- production deduplication is intended to normalize both generated and reference
  cases; and
- calibration is intended to validate the scorer independently of generation.

The defects below therefore violate documented workflow contracts rather than
only internal implementation preferences.

## Findings

### [Critical] 1. The new `val.jsonl` split is not valid evaluator input

`RAFTDatasetBuilder.build_dataset()` returns intermediate RAFT objects containing
fields such as `question`, `oracle_context`, `distractor_context`, and `answer`
(`src/training/raft_dataset_builder.py:167-184`).

`save_dataset()` converts those objects into the evaluator's conversation
contract with a `messages` list (`:202-251`). The new split path bypasses that
conversion:

- `utilities/build_vision_dataset.py:255-263` passes the intermediate
  `raft_examples` directly to `save_split()`;
- `src/training/raft_dataset_builder.py:435-437` shuffles and serializes those
  rows unchanged; and
- `VisionRAFTTrainer._validate_example_contract()` requires `messages`
  (`src/training/vision_raft_trainer.py:807-812`).

This directly contradicts the user guide, which says
`--val-split-ratio 0.2` produces a validation set for `--evaluate`
(`docs/training/README.md:72-76`).

A deterministic reproduction saved two valid intermediate RAFT examples and
passed the resulting `val.jsonl` to `evaluate_model()`:

```text
val keys: ['answer', 'distractor_context', 'oracle_context', 'question']
ValueError: line 1: 'messages' must be a list with at least a system and a user message
```

The existing split test only verifies deterministic partitioning and JSONL
writing; it never feeds the saved validation file into the evaluator. The
feature's advertised build → split → evaluate workflow therefore cannot run.

**Recommendation:** create one shared intermediate-to-conversation converter,
use it for the full dataset and both split outputs, then add an integration test
that builds a split and loads `val.jsonl` through
`_load_and_validate_examples()` or `evaluate_model()`.

### [Critical] 2. A valid zero-output evaluation crashes while printing its result

The content scorer intentionally represents zero generated cases against a
non-empty reference as:

```python
{"precision": None, "recall": 0.0, "f1": 0.0}
```

(`src/training/content_scorer.py:101-104`).

The aggregate consequently has `content_f1 == 0.0` and
`content_precision is None`. `print_evaluation_result()` enters the content
block because F1 is defined, then formats precision with `:.2f`
(`utilities/train_vision_model.py:346-355`). `dict.get(..., 0.0)` does not
replace an existing `None`.

A direct reproduction with a valid reference and no canonical generated cases
produced:

```text
content_f1: 0.0
content_precision: None
TypeError: unsupported format string passed to NoneType.__format__
```

`run_evaluation()` calls this printer before calculating its exit code
(`utilities/train_vision_model.py:458-469`), so the command reports an unexpected
training error instead of the legitimate zero-quality evaluation.

**Recommendation:** format precision and recall through the same None-safe
helper used for text/vision scores, and add a CLI regression using an empty or
canonical-invalid generation with a valid reference.

### [Critical] 3. The headline content F1 is order-dependent and hides its usable-reference denominator

The guide calls `content_f1` the meaningful decision signal when references
exist (`docs/training/README.md:121,133-135`). It is not currently safe for that
role.

#### Greedy matching changes score when only input order changes

`ReferenceOverlapScorer._count_matches()` greedily assigns each generated case
to its best still-unmatched reference (`src/training/content_scorer.py:110-127`).
This does not compute a maximum-cardinality or maximum-weight one-to-one
matching.

A deterministic two-generated/two-reference reproduction at threshold 0.85 had
this similarity matrix:

```text
             reference 1   reference 2
generated 1      0.90          0.90
generated 2      1.00          0.80
```

With generated order `[1, 2]`, the greedy result matches one pair and returns
F1 `0.50`. With the same cases ordered `[2, 1]`, it matches two pairs and returns
F1 `1.00`. A set-level quality metric should not double merely because the model
listed the same cases in a different order.

#### Missing/unparseable references silently disappear from the headline score

`_score_content()` returns `None` for missing/unparseable references or any
scorer exception (`src/training/vision_raft_trainer.py:1111-1136`).
`_aggregate_eval_metrics()` averages only non-None content rows and reports no
content sample count, reference coverage, or scorer-error count (`:1162-1195`).

A two-example reproduction used one parseable reference with a perfect match and
one unparseable reference. The aggregate reported `content_f1 == 1.0` even though
only one of two examples contributed, and the result contained no field exposing
the 50% usable-reference coverage.

This can make two model runs with different reference/scorer failure rates look
directly comparable, or select a model based on a small favorable subset.

**Recommendation:**

1. use maximum-cardinality/max-weight bipartite matching, with explicit,
   testable pair identities;
2. add permutation regressions for generated and reference order;
3. report `content_reference_examples`, `content_scored_examples`, and
   `content_scoring_errors`;
4. surface reference parse/scorer failures rather than silently converting both
   to `None`; and
5. withhold or explicitly mark the content delta partial when the paired usable
   content sample is incomplete.

### [Critical] 4. Successful model creation is reported as a failure because the CLI reads impossible keys

This defect predates the July 24 evaluator work, but the requested whole-code
review reproduced it in the current mainline.

`VisionRAFTTrainer.train()` returns:

- `result["modelfile"]` (`src/training/vision_raft_trainer.py:191-192`);
- `dataset_stats["text_only_examples"]` (`:241-246`); and
- `dataset_stats["avg_images_per_vision_example"]` (`:290-293`).

`print_training_result()` instead reads:

- `modelfile_path`;
- `text_examples`; and
- `avg_images_per_example`

(`utilities/train_vision_model.py:269-279`).

A direct current-shape success result first printed `Modelfile: N/A`, then
raised:

```text
KeyError: 'text_examples'
```

`main()` catches that exception and returns 1
(`utilities/train_vision_model.py:581-594`), even though `ollama create` already
succeeded. Git blame attributes the mismatched printer keys to the 2025
implementation, not the current fix series.

**Recommendation:** define the result/statistics shape once (TypedDict or data
class), use the trainer's actual keys in the printer, and add a test that passes
a real `train()` success result through `print_training_result()` and `main()`.

### [Recommended] 5. July input hardening validates one message but evaluates another, and still permits an unsafe aggregate envelope

The validator explicitly permits reordered messages by searching for the first
`role == "user"` object (`src/training/vision_raft_trainer.py:814-832`).
`_evaluate_example()` ignores that selected object and always generates from
`messages[1]` (`:913-925`).

A dataset ordered as `[system, assistant, user]` passed validation, but the
captured generation prompt was the assistant reference content rather than the
actual user prompt. This can produce a syntactically valid but meaningless
evaluation.

The original review also requested an aggregate byte bound or streaming.
`_load_and_validate_examples()` reads line by line but retains every parsed
example in a list (`:768-788`). The defaults permit 5,000 examples × 16 images ×
10 MiB per image — roughly 800 GiB of decoded payload, plus base64 overhead —
without a file or aggregate byte limit.

**Recommendation:** either enforce the exact builder contract
`[system, user, assistant]` or pass the validator-selected user message into
evaluation. Stream examples where possible and add total encoded/decoded byte
limits. Test reordered roles, extra roles, duplicate user turns, and aggregate
size rejection.

### [Recommended] 6. Retiring the LLM judge left the documented full suite red

The LLM judge implementation and its config/result fields were deliberately
removed in `cfe064d`, but
`tests/training/test_vision_raft_evaluate_integration.py:178-205` still:

- imports `src.training.llm_judge_scorer.LLMJudgeScorer`;
- passes the removed `judge_model` config field;
- requests removed `quality` output.

On a reachable local Ollama, the test fails immediately:

```text
ModuleNotFoundError: No module named 'src.training.llm_judge_scorer'
```

The repository's documented full runner consequently ends:

```text
1 failed, 620 passed, 3 skipped
```

The three non-judge evaluator integration cases and the independent canonical
schema smoke test all pass live. This isolates the failure to incomplete judge
retirement rather than the active overlap evaluator.

**Recommendation:** remove or replace the retired-judge integration case and
add a repository-wide assertion that retired module/config/result names do not
remain in maintained tests and docs.

### [Optional] 7. Training documentation still contains stale and contradictory contracts

The main guide now first says `--val-split-ratio` writes a validation set for
evaluation (`docs/training/README.md:72-76`), then says no train/validation split
is produced (`:93-95`).

Other current text also drifted:

- `utilities/build_vision_dataset.py:38,148,278` links the archived/nonexistent
  `docs/training/training_guideline.md`;
- `utilities/train_vision_model.py:4-6` still calls the fixed prompt
  “RAFT-informed”;
- `src/training/vision_raft_trainer.py:15-18` says evaluation does not compare
  against the reference answer, although `_score_content()` now does; and
- `src/training/judge_calibration.py:8-10` still describes `"llm"` calibration
  bands after the judge was retired.

These do not change runtime behavior, but they obscure the current contracts and
made the incompatible split in Critical 1 look supported.

### [Optional] 8. Vision dataset statistics always report zero images for the builder's own examples

`RAFTDatasetBuilder._build_raft_example()` stores images under
`oracle_images` and `distractor_images`
(`src/training/raft_dataset_builder.py:150-183`).
`print_dataset_stats()` sums `example["images"]`, a field those objects do not
have (`utilities/build_vision_dataset.py:172-175`).

The build can therefore contain vision examples and images while its user-facing
summary prints zero total images. Git blame identifies this as pre-existing.

**Recommendation:** use the builder metadata's `image_count` or sum the two
actual image lists, and cover one vision example in the utility test.

## Positive Observations

- Paired baseline handling now behaves correctly in both fake-client and live
  Ollama tests.
- Duplicate-heavy and canonical-invalid output no longer creates artificial
  unique-valid lift.
- Bundle-vs-base labeling and provenance are materially more honest.
- `--compare-base` dependency validation is explicit.
- The overlap scorer's six current calibration fixtures pass 6/6 without
  invoking a generation model.
- The production Ollama client still returns a canonical test case under the
  real structured-output schema.
- The maintained Python surface passes Ruff, format verification, mypy, and
  compileall.
- A built wheel installs outside the source checkout; its console CLI and prompt
  validation run successfully from `/private/tmp`.
- A targeted scan found no hosted-model API client/call in maintained source.
  The Azure-named fields in `src/config.py` are configuration metadata only; the
  active generation clients remain local Ollama clients.

## Verification Results

| Check | Result |
|---|---|
| Initial branch/worktree | `main` at `d3bd074`, exactly matching `origin/main`; pre-existing user edits only in `AGENTS.md` and `CLAUDE.md` |
| Latest review located | `docs/reviews/Review_Comments_2026_07_24.md`, reviewed revision `c023893` |
| GitNexus flow/impact analysis | Completed; comparison aggregate CRITICAL/partial; `_aggregate_eval_metrics` HIGH impact |
| Graphify rationale query | Completed against the existing graph; package 0.9.20 remains older than skill 0.9.25 |
| Focused training/evaluation tests | **108 passed**, 2 warnings |
| Non-live suite | **615 passed, 2 skipped, 7 deselected** |
| Documented full runner, including live tests | **FAILED: 1 failed, 620 passed, 3 skipped**; sole failure is the stale retired-judge test |
| Active live evaluator tests | **3 passed**, 1 retired-judge case deselected |
| Retired-judge live test | **FAILED** with `ModuleNotFoundError` |
| Live canonical schema smoke test | **1 passed** |
| `--validate-judge` | **PASS: overlap 6/6** |
| `ruff check src/ main.py utilities/` | Passed |
| `ruff format --check src/ main.py utilities/` | Passed; 41 files already formatted |
| `mypy src/ main.py utilities/ --python-version 3.14 --no-incremental` | Passed; 41 source files |
| `python3 -m compileall -q src main.py utilities` | Passed |
| `python3 -m build` | Passed after permitting build-isolation dependency download |
| Wheel installed outside source checkout | Passed; metadata 2.3.0, console `--help` and `--validate-prompts` both exit 0 |
| `twine check dist/*` | Not run: `twine` is not installed |
| Current worktree whitespace | `git diff --check HEAD` passed |
| Source changes made by this review | None; only this review report was added |

The full runner also reports 85% aggregate line coverage. High coverage did not
catch Critical 1-3 because the tests assert each component in isolation but do
not exercise the cross-component contracts or adversarial metric ordering.

## Verification Limits

- Local Ollama had `llama3.1:8b` and `llama3.2-vision:11b`, but not
  `automotive-tc-vision-raft-v1`. The live A/B integration therefore compared
  the text base model with itself to verify wiring and used a missing model to
  verify baseline failure; a real customized-model lift was not measured.
- The live evaluator test deliberately uses text input. Vision evaluator routing
  is covered by injected-client tests; a live vision evaluation was not run.
- `twine` metadata validation is unavailable in the environment. Wheel build,
  external installation, entry point, and packaged prompt assets were verified
  independently.
- GitNexus taint findings were unavailable because the current index has no PDG
  taint layer. No “no security findings” conclusion is drawn from that absence.
- Passing tests and static checks reduce risk but cannot prove the absence of
  every defect. The findings above are confirmed reproductions, not an exhaustive
  claim that no other bug exists.

## Chain of Verification

### Verification questions

1. Was every July 24 item checked against current code and a current test or
   reproduction?
2. Do the new tests exercise the user-visible build → split → evaluate contract?
3. Is the headline content metric invariant to case ordering and explicit about
   its sample denominator?
4. Does the documented full test command pass on the available live environment?
5. Were new findings separated from pre-existing defects?
6. Did this review preserve the user's worktree and avoid source changes?

### Answers

1. **Yes.** The table above records code and runtime evidence for all seven
   items.
2. **No.** Split tests stop after file writing; the produced `val.jsonl` is
   rejected by the evaluator.
3. **No.** Reordering the same generated set changed F1 from 0.50 to 1.00, and a
   one-of-two usable-reference run reported F1 1.00 without a denominator.
4. **No.** It fails only on the stale retired-judge integration test:
   620 passed, 3 skipped, 1 failed.
5. **Yes.** Critical 1-3 and Recommended 5-6 are attributable to the July
   fix/follow-on series. Critical 4 and Optional 8 are explicitly marked
   pre-existing.
6. **Yes.** The initial `AGENTS.md` and `CLAUDE.md` edits were preserved. Tool
   cache artifacts created during review were removed, and no source/config/test
   file was edited.

### Revised assessment

The July 24 Critical baseline and raw-count defects are genuinely fixed, along
with honest A/B labeling, the dependent CLI argument guard, and the cited
training-guide gap. The current tree is nevertheless **not ready to treat the
training/evaluation work as complete**: the input-hardening item remains partial,
live integration coverage has regressed, the advertised validation split is
unusable, the evaluator can crash on a legitimate zero-quality result, and the
headline content metric can change with ordering or silently score a favorable
subset.
