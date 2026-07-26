# Phase 3c — Judge Calibration Harness Design

**Date:** 2026-07-26
**Branch:** `feat/phase3c-judge-calibration`
**Status:** Approved (design); implementation plan to follow.

## Goal

Answer one question with evidence: **is the Phase 3b LLM judge good enough to
trust?**

Phase 3b shipped `LLMJudgeScorer` and made `content_f1` the headline decision
metric when references exist. Nothing measures whether that number is any good.
Today the judge's scores drive A/B verdicts on trained models while being
themselves unvalidated — a metric grading a metric, with no ground truth
anywhere in the loop.

This phase adds a calibration harness: a fixed set of cases whose correct scores
are known **by construction**, run through any `ContentScorer`, producing a
pass/fail scorecard. It makes the judge's competence measurable, and in
particular measures the one thing the judge claims over the deterministic
scorer — recognizing paraphrased scenarios.

## Redirect from the original Phase 3c

Phase 3c was originally deferred as a **hosted/cloud LLM judge** (a stronger
model than local `llama3.1:8b`, behind the same seam). That is now cancelled:
the project principle in `CLAUDE.md` — *"Uses Ollama LLMs locally — no cloud API
calls"* — was confirmed (2026-07-26) as a **hard rule everywhere, including the
offline evaluation and training paths**. No cloud judge will be built.

The obvious local substitute needs no work at all: `LLMJudgeScorer` already
accepts any Ollama model, so `--judge-model deepseek-coder-v2:16b` is a flag
value, not a feature. What remains genuinely unbuilt is *validation* of the
judge, which is what this phase delivers under the Phase 3c name.

## Locked Decisions

| Decision | Choice |
|----------|--------|
| Cloud judge | **Cancelled** — no cloud API calls anywhere, including eval |
| Ground truth | **Gold-by-construction fixtures**, hand-authored and committed |
| Generation model in the loop | **None** — fixtures feed the scorer directly |
| Scope of validation | **Both** scorers, through one scorer-agnostic code path |
| Expectations | **Inclusive `(min, max)` bands**, keyed per scorer kind |
| Paraphrase source | **Hand-authored**, never LLM-generated at runtime |
| Delivery | `--validate-judge` CLI mode **plus** an opt-in integration test |
| Pass/fail | **Exit 1 on any breached band**, so it can gate CI |
| Default test suite | Overlap column runs by default (no Ollama); llm column opt-in |
| `evaluate_model` | **Untouched** — shares the seam, shares no code path |

## Architecture

Two new modules plus one CLI mode. No existing module changes shape.

```
src/training/judge_calibration_cases.py   # DEFAULT_CALIBRATION_CASES (fixture data)
src/training/judge_calibration.py         # types + runner + report formatting
utilities/train_vision_model.py           # --validate-judge mode (new branch)
```

The fixture literals are bulky (5 cases × 3–5 test cases × 5 canonical fields),
so they live apart from the runner to keep each file focused.

The runner depends only on the `ContentScorer` protocol, so
`ReferenceOverlapScorer` and `LLMJudgeScorer` are validated through **identical
code**:

```python
def run_calibration(
    scorer: ContentScorer,
    scorer_kind: str,                      # "overlap" | "llm" — selects which bands apply
    cases: Sequence[CalibrationCase] = DEFAULT_CALIBRATION_CASES,
    *,
    client: Any = None,
    judge_model: str | None = None,
) -> CalibrationReport:
    ...
```

For each case it calls
`scorer.score(case["generated"], case["reference"], client=..., judge_model=...)`,
compares each returned metric against that case's band for that scorer kind, and
records the outcome.

**No generation model runs anywhere in this path.** Fixtures go straight into
the scorer. That is what makes the harness a measurement of the *judge* rather
than of the judge plus a model — generation noise is the confound this phase
exists to remove. It also buys a useful property: the overlap column is fully
deterministic and needs no Ollama, so it can run in the default test suite.

### Types

Following the `content_scorer.py` convention — `TypedDict` for data, plain
`__slots__` classes for behaviour:

- `CalibrationCase` — `name`, `description`, `generated`, `reference`, `expected`
- `CalibrationResult` — the case, actual `ContentScore`, per-metric pass/fail, any error
- `CalibrationReport` — results, counts, overall `passed: bool`

`expected` is keyed by scorer kind, then metric, to an inclusive band:

```python
"expected": {
    "overlap": {"f1": (0.0, 0.35)},   # overlap is EXPECTED to fail paraphrase
    "llm":     {"f1": (0.7, 1.0)},    # the judge's claimed advantage, under test
}
```

Per-kind keying is what makes the scorecard readable: overlap's paraphrase
blindness is encoded as *expected behaviour* rather than reported as a
regression, so the headline question — does the judge beat overlap where it
claims to? — is a direct read off the table.

A metric with no declared band is not checked. Overlap declares no `quality`
band, since it always returns `None` there.

## The Fixture Cases

Built from a small canonical automotive test-case set using the canonical schema
(`summary_suffix`, `preconditions`, `test_steps`, `expected_result`,
`test_type`). Each case probes one failure mode a content metric must handle.

| Case | Generated vs reference | overlap band | llm band | What it proves |
|---|---|---|---|---|
| `identity` | identical, 3 cases | f1 ≥ 0.9 | f1 ≥ 0.9 | No false negatives on exact matches |
| `disjoint` | 3 unrelated cases | f1 ≤ 0.1 | f1 ≤ 0.1 | No credit for unrelated output |
| `subset` | 2 of 4 refs, verbatim | recall 0.4–0.6, precision ≥ 0.9 | same | Partial recall is measured, not rounded away |
| `paraphrase` | 3 refs reworded, same scenarios | **f1 ≤ 0.35** | **f1 ≥ 0.7** | The discriminator — judge must beat overlap here |
| `noise` | 3 refs verbatim + 2 junk | recall ≥ 0.9, precision 0.4–0.8 | same | Precision penalises padding (3/5 = 0.6) |

`paraphrase` carries the phase. Every other row is a sanity check either scorer
should pass; this is the only row that answers whether `--content-scorer llm`
earns its two-Ollama-calls-per-example cost. **If the judge cannot clear it,
that is a real and reportable finding** — the honest conclusion would be that
the LLM judge is not worth using, and the harness will have said so.

Two deliberate choices:

- **Bands, not points.** `identity` asks f1 ≥ 0.9, not `== 1.0`. The judge is
  non-deterministic, and even at temperature 0.0 nothing guarantees a stable
  response, so exact expectations would flake. Bands absorb judge wobble while
  staying narrow enough that a genuinely broken scorer breaches them.
- **Paraphrases are hand-authored and committed.** If a model generated them,
  the ground truth would itself be model-dependent — grading the judge against
  another model's opinion. Hand-authored fixtures stay deterministic and
  reviewable in the diff.

## CLI

A standalone mode on `utilities/train_vision_model.py`, parallel to `--evaluate`:

```bash
python3 utilities/train_vision_model.py --validate-judge
python3 utilities/train_vision_model.py --validate-judge --judge-model deepseek-coder-v2:16b
python3 utilities/train_vision_model.py --validate-judge --content-scorer overlap   # no Ollama needed
```

By default both columns run. The **existing** `--content-scorer` flag, when
explicitly given, narrows the run to one scorer — no new flag is introduced for
that; it reuses vocabulary already in place.

`--validate-judge` takes **no dataset argument** and requires no held-out set,
no trained model, and no Modelfile. Unlike `--evaluate`, its inputs are entirely
the committed fixtures, so it is runnable on a clean checkout.

Following the Optional-7 precedent (2026-07-24 review), `parse_args` rejects
combinations that would silently do nothing: `--validate-judge` with
`--evaluate`, and `--compare-base` with `--validate-judge`.

Output is a side-by-side scorecard — per case: expected band, actual, PASS/FAIL,
per scorer — followed by a summary line. **Exit 1 if any declared band is
breached**; exit 0 otherwise.

## Data Flow

```
DEFAULT_CALIBRATION_CASES
  -> run_calibration(scorer, scorer_kind, cases, client=, judge_model=)
      -> per case: scorer.score(generated, reference, ...)   # no model generation
      -> band check per declared metric
      -> CalibrationResult (actual, pass/fail, error)
  -> CalibrationReport (results, counts, passed)
  -> format_report()  -> side-by-side scorecard
  -> CLI exit code (0 pass / 1 breach)
```

## Error Handling

Follows the convention already established in this subsystem
(`llm_judge_scorer.py:131`, `vision_raft_trainer.py:1145`): a judge fault must
never abort the run.

- Scorer raises → caught per case, recorded as an error, counted as a breach,
  run continues to the remaining cases.
- Scorer returns `None`, or returns `None` for a metric that declared a band →
  breach, not a crash.
- Ollama unreachable → every `llm` case records an error and the run exits 1.
  This is deliberate: the report says *"the judge could not be validated,"* never
  *"the judge passed."*

**Breaches and errors are reported distinctly.** "The judge scored 0.2 where 0.7
was required" and "the judge never answered" are different problems and must not
be collapsed into one status.

## Testing

Three layers:

1. **Default suite, no Ollama** — band-checking logic, `None` handling,
   scorer-raises isolation, report aggregation, CLI exit codes (mocked runner),
   and the **entire overlap column over all five fixtures**. That last is fully
   deterministic, so overlap's real behaviour — including its expected
   paraphrase failure — is locked down by a normal `pytest` run.
2. **Opt-in integration** (`integration` / `slow`, self-skipping) — the llm
   column over all five fixtures against live Ollama, asserting the bands. Same
   pattern as `tests/training/test_vision_raft_evaluate_integration.py`.
3. **Live verification before completion** — the integration test must be
   observed *running, not skipping*. Per the durable lesson from Phases 2 and 3b,
   mocked tests miss wiring bugs that only a real run surfaces.

## Documentation

- `docs/training/README.md` — a calibration section: what the harness measures,
  how to run it, how to read the scorecard, and the explicit caveat that bands
  are tolerances rather than exact truth.
- `CLAUDE.md` — no change. The no-cloud principle stands as written and is now
  confirmed to apply everywhere.
- `CHANGELOG.md` — Added entry.

## Scope / YAGNI (explicitly out)

- **No cloud/hosted judge** — cancelled by the confirmed no-cloud rule.
- **No human-labeled match pairs** — considered and deferred; fixtures first.
  A human-label source can be added later behind the same runner.
- **No self-consistency sampling** and **no multi-model judge ensemble** —
  considered as alternative Phase 3c redirects and not chosen; both make scores
  more stable without establishing whether they are *correct*, which is the gap.
- **No changes to `evaluate_model`** — it shares the `ContentScorer` seam and no
  code path.
- **No user-supplied fixture files** — fixtures are committed Python constants.
  A loader can come later if a need appears.

## Files Touched

| File | Change |
|------|--------|
| `src/training/judge_calibration.py` | New — types, `run_calibration`, `format_report` |
| `src/training/judge_calibration_cases.py` | New — `DEFAULT_CALIBRATION_CASES` |
| `utilities/train_vision_model.py` | `--validate-judge` mode, arg validation, exit codes |
| `tests/training/test_judge_calibration.py` | New — unit + deterministic overlap column |
| `tests/training/test_judge_calibration_integration.py` | New — opt-in live llm column |
| `docs/training/README.md` | Calibration section |
| `CHANGELOG.md` | Added entry |
