# Branch Review — Vision RAFT Evaluation and A/B Comparison

**Date:** 2026-07-24  
**Branch:** `feat/vision-raft-evaluate-model`  
**Current revision:** `c023893`  
**Comparison:** `main...HEAD` (`548b0bf...c023893`)  
**Recent-review baseline:** `docs/reviews/Review_Comments_2026_07_20.md`  
**Scope:** the new `VisionRAFTTrainer.evaluate_model()` implementation, its
base-model comparison, CLI wiring, tests, changelog, and affected training
documentation

> **Disposition update (2026-07-24):** both Critical findings below were fixed
> on `feat/vision-raft-evaluate-model` in `bc26473`. Critical 1 — the A/B
> comparison is now paired and validity-aware (delta computed over
> both-sides-successful rows only, withheld when the baseline is unusable, CLI
> exits non-zero). Critical 2 — the decision metric is now
> `unique_valid_test_cases_per_example` (canonical-valid cases deduplicated via
> the production `TestCaseDeduplicator`); the raw count is retained as
> `raw_test_cases_per_example` (output volume). The findings below are preserved
> as the point-in-time record. The Recommended/Optional items remain open.

## Recommendation

**REQUEST CHANGES — HIGH aggregate risk.**

The branch replaces the dead evaluation stub with a real held-out-dataset path,
threads `--base-model` correctly, handles text and vision examples, and adds
useful deterministic tests. The full repository remains green.

The A/B result is not yet safe to use for model-selection decisions, however:

1. a completely failed baseline still produces a positive delta and a successful
   CLI exit;
2. the advertised “coverage” lift counts raw objects before canonical filtering,
   semantic validation, or deduplication, so duplicates and invalid cases create
   artificial lift.

Both defects affect the feature's central claim — “did the customization help?” —
and should be fixed before merge.

## Change and Risk Summary

- **7 files changed:** 982 insertions, 114 deletions.
- **65 changed symbols** according to GitNexus.
- **11 affected execution flows**, all centered on the new evaluation path.
- **GitNexus aggregate risk:** **HIGH**. Individual methods have one direct
  caller each and LOW local impact, but the entire new CLI-to-score path changed
  together.
- Primary flow:

```text
utilities/train_vision_model.py::main
  -> run_evaluation
  -> VisionRAFTTrainer.evaluate_model
  -> _score_over_dataset
  -> _evaluate_example
  -> _generate_for_example
  -> OllamaClient
  -> _score_generation
  -> JSONResponseParser.extract_json_from_response
  -> is_canonical_test_case
```

Graphify confirms the intended rationale: `VisionRAFTTrainer` is a
prompt-customized Ollama model, while the training guidance connects evaluation
to “Compare with Base Model,” “Test the Trained Model,” and a validation
checklist.

## Recent Review Re-evaluation

| Recent-review item | Current status | Evidence |
|---|---|---|
| Optional dead surface: implement or remove `VisionRAFTTrainer.evaluate_model()` | **Partially fixed** | The stub now executes real generation and optional A/B comparison, but the comparison has two decision-corrupting defects below and still does not assess closeness to the held-out reference answer. |
| RAFT dataset does not influence the Modelfile | **Unchanged / deferred by design** | The implementation remains a fixed `SYSTEM` + `PARAMETER` Modelfile. This branch correctly calls it prompt customization, not weight training. |
| Honest RAFT documentation | **Reopened, pre-existing on `main`** | `docs/training/README.md` still says the dataset shapes/informs the system prompt, contradicting `VisionRAFTTrainer._prepare_modelfile()`, which says the prompt is fixed and dataset-independent. |
| Canonical structured-output enforcement | **Preserved** | The evaluator forwards `TEST_CASE_RESPONSE_JSON_SCHEMA`, and the real-Ollama schema smoke test passes. |
| Whole-repository quality gates | **Preserved** | Ruff check/format, mypy, compileall, focused tests, and the full suite pass. |
| All other 2026-07-20 findings | **Unaffected by this branch** | No changed code enters the REQIFZ extraction-to-Excel production path. |

## Findings

### [Critical] 1. A failed baseline still reports positive lift and exits successfully

`evaluate_model()` records base-model generation failures under
`result["baseline"]["errors"]`, but it always computes a delta from the resulting
all-zero metrics (`src/training/vision_raft_trainer.py:525-539`).

The CLI then:

- prints only the customized model's `result["errors"]`
  (`utilities/train_vision_model.py:312-315`);
- never prints baseline errors; and
- derives exit status only from customized-model failures
  (`utilities/train_vision_model.py:376-379`).

A focused reproduction used one valid customized response and a base client that
raised `RuntimeError("base model unavailable")`. Current behavior:

```json
{
  "custom_errors": [],
  "baseline_errors": [
    "example 0: generation failed: base model unavailable"
  ],
  "delta": {
    "overall_score": 1.0,
    "parse_success_rate": 1.0,
    "avg_test_cases_per_example": 1.0
  },
  "computed_cli_exit": 0
}
```

The command therefore says the customization improved the model even though no
usable baseline observation exists. That can lead directly to a false deployment
decision.

**Recommendation:** make comparison paired and validity-aware.

- If every baseline example fails, omit/null the delta, surface the baseline
  errors, and return failure.
- If only some rows fail on either side, either compare only rows successfully
  evaluated on both sides or mark the result partial and report the paired sample
  size.
- Include customized and baseline failure counts in the summary.
- Add CLI and trainer tests for total and partial baseline failure.

### [Critical] 2. “Coverage” rewards duplicates and canonical-invalid output

`_score_generation()` sets `num_test_cases = len(test_cases)` before canonical
validation (`src/training/vision_raft_trainer.py:751-754`).
`_aggregate_eval_metrics()` then averages that raw count
(`src/training/vision_raft_trainer.py:782-794`).

Unlike the production pipeline, evaluation never applies semantic validation or
`TestCaseDeduplicator` (`src/core/generators.py:283-345`). Nevertheless the CLI
and changelog call this value “coverage” and tell users it is usually the most
meaningful signal because schema-validity scores are saturated.

Two deterministic reproductions show why that interpretation is unsafe:

1. Customized output: five identical canonical cases. Base output: one copy of
   the same case. Both canonical scores are `1.0`, but reported coverage lift is
   `+4.0`.
2. Customized output: five canonical-invalid objects. Base output: one valid
   case. Customized score is `0.0`, but reported coverage lift is still `+4.0`.

Raw object count is output volume, not requirement coverage. In the first case
the customized model adds no unique scenario; in the second it adds no usable
scenario.

**Recommendation:**

- Rename the current metric to `raw_test_cases_per_example` if it remains.
- Compute the decision metric from canonical-valid, semantically accepted,
  deduplicated cases.
- Report invalid and duplicate counts explicitly.
- For actual output-quality/coverage claims, use the held-out assistant answer or
  another labeled oracle to measure scenario precision/recall; the dataset
  already contains a reference answer, but the evaluator currently ignores it.
- Add duplicate-heavy and invalid-heavy A/B regressions.

### [Recommended] 3. Test-dataset parsing is neither validated nor bounded

`_load_jsonl_examples()` accepts any non-blank JSON value and loads the entire
file into memory (`src/training/vision_raft_trainer.py:602-618`).
`_evaluate_example()` immediately assumes each value is a dict containing a
list-like `messages` field (`:645-651`).

A one-line dataset containing `[]` aborts the entire run with:

```text
AttributeError: 'list' object has no attribute 'get'
```

The same surface accepts unbounded base64 image strings and decodes all images
for an example before generation (`:704-728`). This makes malformed or
accidentally oversized evaluation data an avoidable full-run failure or
memory/disk spike.

**Recommendation:** validate the JSONL contract before any model calls:

- top-level object;
- exactly the supported message roles/order;
- string user content;
- list of valid, size-bounded base64 images;
- non-empty dataset and configurable example/image/byte limits.

Prefer streaming examples rather than retaining the full base64-bearing dataset
in memory. Reuse or strengthen `RAFTDatasetBuilder.validate_dataset()` so the
builder and evaluator share one contract.

### [Recommended] 4. The A/B experiment does not isolate prompt customization

The customized Modelfile changes both the system prompt and run parameters:

```text
temperature 0.0
num_ctx <configured>
num_predict <configured>
top_p 0.9
repeat_penalty 1.1
```

The untouched base model is invoked without matched runtime options. It therefore
uses its own Modelfile/default parameters. The comparison also sets no explicit
seed.

Ollama documents `PARAMETER` as controlling model execution and lists temperature,
seed, context, and prediction limits as generation controls:
[Modelfile reference](https://docs.ollama.com/modelfile).

The observed delta measures the complete named-model bundle, not just the effect
of the custom `SYSTEM` prompt. The current wording — “did the prompt
customization help?” — overstates what the experiment identifies.

**Recommendation:** either:

1. compare against a control model created from the same base with identical
   parameters and no custom system prompt, using a fixed seed where supported; or
2. label the result honestly as “customized model bundle vs base model,” record
   both models' effective parameters/provenance, and avoid causal prompt-only
   language.

### [Recommended] 5. The evaluator has no committed real-Ollama integration test

`tests/training/test_vision_raft_evaluate.py:7-10` says a separate
real-Ollama, `integration`-marked test covers the live path. No such evaluator
test exists. All 14 evaluator tests inject `FakeOllamaClient`; the 9 CLI tests
also mock `evaluate_model()`.

The repository's real test at
`tests/integration/test_ollama_schema_smoke.py` covers the shared
`OllamaClient` structured-output path, not `VisionRAFTTrainer.evaluate_model()`
or `--compare-base`. The branch's changelog records manual live runs, but those
are not executable regression coverage. This matters because the changelog also
notes that a base-model wiring bug escaped the mocked tests.

**Recommendation:** add an opt-in integration test that executes the evaluator
through the real client and asserts result shape, model routing, canonical
scoring, baseline error handling, and CLI status. Correct the test-module
docstring until that test exists.

### [Recommended] 6. The user-facing training guide was not updated and remains contradictory

The branch adds two user-visible CLI flags, but `docs/training/README.md` has no
evaluation/A/B instructions. It also says:

- the dataset creates a “RAFT-informed system prompt” (`:8-14`);
- the Modelfile uses a RAFT-informed prompt (`:70-79`); and
- the dataset informs the system prompt (`:95-103`).

The implementation explicitly says the fixed system prompt is not derived from
the RAFT dataset (`src/training/vision_raft_trainer.py:290-295`).
`utilities/train_vision_model.py` also still sends users to the archived,
nonexistent live path `docs/training/training_guideline.md`.

The contradiction predates this branch, so it is not attributed as a newly
introduced bug. It does reopen the recent review's “honest wording fixed” status,
and this user-facing CLI change was the natural point to correct it.

**Recommendation:** update the single current training guide with:

- `--evaluate` and `--compare-base` examples;
- the exact metric limitations;
- the distinction between fixed prompt customization and dataset-derived
  training;
- corrected links to `docs/training/README.md`.

### [Optional] 7. `--compare-base` is accepted without `--evaluate` and silently ignored

`argparse` accepts `--compare-base` in normal model-creation mode, while `main()`
consults it only inside the `args.evaluate` branch. A dependent-argument check
would turn a silent no-op into an immediate actionable error.

## Positive Observations

- Requiring an explicit held-out dataset avoids silently evaluating on training
  data or a fabricated split.
- Text and vision examples are routed through the correct client methods.
- Temporary decoded images are cleaned in a `finally` block.
- Generation exceptions are isolated per example rather than aborting the whole
  run.
- Metrics with no supporting text/vision examples use `None` rather than a fake
  zero.
- The CLI now threads the selected base model into `VisionTrainingConfig`; a
  dedicated regression test protects the wiring.
- The canonical JSON Schema is passed to both models.
- Changelog coverage is detailed and the changed production files pass current
  lint, format, type, and compile checks.

## Verification Results

| Check | Result |
|---|---|
| Working tree before review | Clean; branch matched `origin/feat/vision-raft-evaluate-model` |
| Diff scope | 7 files, 982 insertions, 114 deletions |
| `git diff --check main...HEAD` | Passed |
| GitNexus refresh | Passed after repairing an inconsistent FTS index; 5,620 nodes, 7,974 edges, 121 clusters, 147 flows at `c023893` |
| GitNexus `detect_changes(compare, main)` | HIGH aggregate risk; 65 changed symbols, 11 affected flows |
| Graphify | Existing graph queried successfully; package `0.9.20` is older than the repository skill `0.9.25` |
| Focused training/evaluation tests | **36 passed**, 2 warnings |
| Full suite, no coverage | **543 passed, 5 skipped**, 231 warnings |
| Whole-repository Ruff | Passed |
| Whole-repository Ruff format | Passed; 92 files already formatted |
| Mypy (`src`, `main.py`, `utilities`) | Passed; 38 source files (`--no-incremental`; the existing incremental cache stalled without a result) |
| Compileall | Passed |
| Evaluator CLI `--help` | Passed; also exposed the stale archived guide link |
| Real-Ollama schema smoke | **1 passed**, 2 warnings, 63.38s against local `llama3.1:8b` |
| Live evaluator CLI control | Completed against `llama3.1:8b` on both sides; exit 0, parse rate 1.0, canonical score 0.0, raw count 1.0, delta 0.0 |
| Exact customized-vs-base live A/B | **Not reproduced:** the local server has `llama3.1:8b`, `llama3.2-vision:11b`, and `deepseek-coder-v2:16b`, but not `automotive-tc-vision-raft-v1` |

The recurring local `RequestsDependencyWarning` for unrelated `chardet 7.4.3`
remains environment-specific and is not attributed to this branch.

## Missing Coverage

- Total baseline failure.
- Partial baseline failure and paired-sample accounting.
- Duplicate-heavy output.
- Canonical-invalid bulk output affecting the raw count.
- Malformed JSONL values/message structures.
- Invalid and oversized base64 images.
- `--compare-base` without `--evaluate`.
- A real-Ollama evaluator/A/B integration path.

## Chain-of-Verification

### Verification questions

1. Is the review scoped to committed branch changes rather than an empty working
   tree diff?
2. Can a failed baseline really create positive lift and exit 0?
3. Can duplicate or invalid cases create positive “coverage” lift?
4. Does the production pipeline perform validation/deduplication that evaluation
   omits?
5. Do the current tests cover the two critical cases?
6. Does green static/full-suite verification invalidate these findings?
7. Was the exact customized-model A/B claim reproduced live?
8. Which documentation issue is pre-existing rather than introduced here?

### Independent answers

1. **Yes.** Scope is `main...HEAD`; the working tree was clean at review start.
2. **Yes.** A deterministic reproduction produced baseline errors, `+1.0`
   deltas, and computed CLI exit `0`.
3. **Yes.** Five identical valid cases produced `+4.0` raw-count lift with equal
   canonical scores; five invalid cases also produced `+4.0`.
4. **Yes.** `_postprocess_test_cases()` applies canonical filtering, semantic
   validation, validation stamping, and deduplication. The evaluator stops after
   canonical counting.
5. **No.** The changed tests cover happy-path delta arithmetic but not baseline
   exceptions, duplicates, or invalid-volume inflation.
6. **No.** The checks prove implementation consistency and regression health,
   not correctness of the metric contract.
7. **No.** The shared live schema and evaluator wiring were exercised, but the
   customized model named by the feature is not installed locally.
8. **The false dataset-informed guide wording.** It already exists on `main`;
   the missing documentation for the new flags is a branch omission.

### Revised assessment

The branch is a substantial improvement over the zero-valued TODO stub and does
not regress the production REQIFZ-to-Excel path. Its A/B comparison cannot yet
support the decision it advertises. Fix the baseline-validity contract and
replace the raw-count “coverage” signal before merge; then close the validation,
experiment-design, live-test, and documentation gaps.

## Suggested Fix Order

1. **P0:** invalidate/withhold delta when the baseline is unusable; surface
   baseline errors and return failure/partial status.
2. **P0:** replace raw object count as the recommended decision metric with
   accepted, deduplicated, preferably reference-aware coverage.
3. **P1:** validate and bound JSONL/image inputs before model calls.
4. **P1:** make the control experiment parameter-matched or rename it as a
   full-model-bundle comparison.
5. **P1:** add the missing real evaluator integration test and correct the test
   docstring.
6. **P1:** update the single current training guide and stale utility links.
7. **P2:** reject `--compare-base` unless `--evaluate` is present.
