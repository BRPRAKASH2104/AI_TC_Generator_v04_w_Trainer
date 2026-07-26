# Training Guide

This is the **single current guide** for the training capability that ships in
this repository. Older, longer, and partly speculative guides have been moved to
[`archive/`](archive/) — do not follow them; several describe a weight
fine-tuning path that is **not implemented** here.

> **What "training" means in this tool.** This project does **not** fine-tune
> model weights. It runs a *prompt-customization* pipeline: it collects and
> annotates good generations (RAFT — Retrieval-Augmented Fine-Tuning data) and
> builds a dataset, then creates a **named Ollama model** via an Ollama
> `Modelfile` + `ollama create`. **The system prompt is a fixed template — it is
> not derived from the RAFT dataset.** The dataset is analyzed for *reporting
> statistics only*; it changes neither the model weights nor the system prompt
> (`VisionRAFTTrainer._prepare_modelfile`; review 2026-07-24 finding 6 /
> 2026-07-20 finding 6 / Archived finding 3).

## Requirements

- A normal install is enough: `pip install -e .` plus a running Ollama.
- The `[training]` extra (`torch`, `transformers`, `peft`, `datasets`, `wandb`)
  is **only** for the not-yet-implemented LoRA/adapter weight-fine-tuning path.
  None of the steps below need it.

## Workflow

All four steps operate on the `training_data/` directory (configurable via
`training.training_data_dir` in `config/cli_config.yaml`).

### 1. Collect RAFT examples during a normal run (opt-in)

Both toggles default to `false`. Enable them in `config/cli_config.yaml`:

```yaml
training:
  enable_raft: true            # enable RAFT data collection
  collect_training_data: true  # write examples during processing
```

Then run generation as usual — examples are collected as you process
requirements:

```bash
ai-tc-generator input/your_file.reqifz --verbose
```

Collected examples land under `training_data/`. Implemented by
`RAFTDataCollector` (`src/training/raft_collector.py`).

### 2. Annotate the collected examples

```bash
python3 utilities/annotate_raft.py
```

Interactive tool: mark context as **oracle** (relevant) or **distractor**
(irrelevant) and validate/reject generated test cases. Validated examples are
written to `training_data/validated/`. Implemented by `RAFTAnnotator`
(`src/training/raft_annotator.py`).

### 3. Build the vision RAFT dataset

```bash
python3 utilities/build_vision_dataset.py
```

Loads `training_data/validated/`, filters by quality threshold
(`training.min_quality_score`), and writes an Ollama-compatible JSONL dataset
with base64-encoded images. Implemented by `RAFTDatasetBuilder`
(`src/training/raft_dataset_builder.py`).

To also produce a held-out validation set for `--evaluate`, add a split ratio:

```bash
python3 utilities/build_vision_dataset.py --val-split-ratio 0.2
# writes train.jsonl + val.jsonl (deterministic; --split-seed to change, --force to overwrite)
```

### 4. Create the prompt-customized Ollama model

```bash
python3 utilities/train_vision_model.py
```

Builds an Ollama `Modelfile` with a **fixed** system prompt (not derived from
the dataset) plus generation `PARAMETER`s, and runs `ollama create` to register
a named custom model. **This does not change model weights, and the RAFT dataset
does not alter the prompt.** Implemented by `VisionRAFTTrainer`
(`src/training/vision_raft_trainer.py`).

### 5. Evaluate a customized model on held-out data (optional)

Score an existing customized model on a held-out RAFT dataset (JSONL) instead of
creating one. Requires an **explicit** held-out file — no train/val split is
produced, so there is no honest default:

```bash
# Score the customized model's output quality on a held-out set
python3 utilities/train_vision_model.py \
    --evaluate training_data/raft_dataset/held_out.jsonl \
    --output-model automotive-tc-vision-raft-v1

# A/B it against the base model (add --base-model to pick the baseline)
python3 utilities/train_vision_model.py \
    --evaluate training_data/raft_dataset/held_out.jsonl \
    --output-model automotive-tc-vision-raft-v1 \
    --base-model llama3.2-vision:11b \
    --compare-base
```

Implemented by `VisionRAFTTrainer.evaluate_model`
(`src/training/vision_raft_trainer.py`).

**What the metrics mean — and their limits:**

| Metric | Meaning | Caveat |
|---|---|---|
| `overall_score` | Canonical-schema **pass rate** (`is_canonical_test_case`) | Measures output *validity*, **not** closeness to the reference answer. Generation is grammar-constrained to the schema, so this is near-saturated (≈1.0) for most models. |
| `unique_valid_test_cases_per_example` | Canonical-valid cases after production **deduplication** | The meaningful coverage signal. Distinct usable scenarios per example. |
| `raw_test_cases_per_example` | Raw object count returned | **Output volume, not coverage** — includes duplicates and invalid objects. Do not use it for model selection. |
| `content_f1` (+ `content_precision`, `content_recall`) | Reference-aware scenario overlap between the generated cases and the held-out reference answer | **The meaningful quality signal when references exist.** Deterministic (deduplicator similarity ≥ 0.85); `None` when an example has no parseable reference. |

**A/B (`--compare-base`) honesty notes:**

- The delta is **paired**: computed only over examples both models generated for
  without error. If the baseline fails on every example the delta is **withheld**
  and the command exits non-zero — a failed baseline is never reported as lift.
- The comparison is **bundle-vs-base**: the customized model changes both the
  system prompt *and* generation parameters, while the base model runs with its
  own defaults (not parameter-matched, no fixed seed). The delta reflects the
  whole customized bundle, **not** the isolated effect of the system prompt. The
  result's `provenance` block records both models' effective parameters.
- When examples carry a reference answer, the **content F1 delta** is the
  headline signal (quality), above the count-based coverage delta. It is paired
  and withheld with the baseline exactly like the other deltas.

`--evaluate` scores content with the deterministic `overlap` scorer, which
matches generated↔reference cases by string similarity. An LLM-as-judge scorer
(`--content-scorer llm`) existed alongside it and was **retired 2026-07-26** —
calibration showed it returned a near-constant match list regardless of input.
See [Content scorer calibration](#content-scorer-calibration) for the evidence
and the retirement note.

## Content scorer calibration

`--validate-judge` answers a narrower question than `--evaluate`: is the content
scorer itself trustworthy? It scores six built-in, gold-by-construction fixtures
(`src/training/judge_calibration_cases.py`) directly through a `ContentScorer`
— **no generation model runs in this mode**, so it measures the scorer in
isolation, not a trained model's output quality. It does **not** validate a
customized model; use `--evaluate` for that.

**Running it** (needs no dataset, no trained model, and no Ollama):

```bash
python3 utilities/train_vision_model.py --validate-judge
```

**Reading the scorecard:** each case prints one `metric actual [band] PASS/FAIL`
group per declared metric, followed by a `passed/total` summary and a final
`RESULT: PASS`/`RESULT: FAIL` line. The process exits 1 if any band is breached
on any case, 0 otherwise.

**The six cases:**

| Case | What it proves |
|---|---|
| `identity` | Generated == reference verbatim — the easiest possible case; the scorer must score it near 1.0. |
| `disjoint` | Completely unrelated generations — must get near-zero credit. |
| `subset` | Half the reference set, verbatim — checks recall/precision arithmetic on a known partial match. |
| `paraphrase` | Three reference scenarios reworded. `overlap` matches on string similarity and is *expected* to miss them (band `f1` 0.0–0.35). This pins the documented limit of string matching — it is the bar a semantic scorer would have to beat to be worth its cost. |
| `noise` | The full reference set plus two unrelated extras — recall stays high while precision correctly drops. |
| `mixed` | One reference case verbatim plus two unrelated. Only 1 of 3 generated cases has a counterpart, well below `min(len(generated), len(reference))` = 3, so a scorer that pairs indiscriminately scores 1.0 and breaches the 0.2–0.5 band while correct matching lands on 1/3. |

**Caveat:** the bands are tolerances chosen to make each case's ground truth
unambiguous, not claims of exact truth. A breach means the scorer is not earning
its keep on that case. It is **not** a signal to widen the band; the correct
response is to fix or reconsider the scorer, not the test.

**Limitation — the metric grades pair *count*, not pair *correctness*.** The
precision/recall/F1 convention counts how many generated↔reference pairs matched,
never whether they are the *right* pairs. `mixed` narrows this (a scorer claiming
too many matches breaches its band) but cannot close it: a scorer claiming the
*right number* of matches between the *wrong items* is indistinguishable from a
correct one. Closing that requires `ContentScore` to expose the pairing itself,
not just counts — a metric-interface change. This convention is inherited from
the original content metric, not introduced by the harness.

A shuffled-order (`permutation`) fixture was proposed for this and **tested and
rejected**: a permutation has as many true matches as `min(len(generated),
len(reference))`, so pairing everything 1:1 reaches the correct score by the
wrong route and discriminates nothing.

### Retired: the LLM-as-judge content scorer

A second scorer — `LLMJudgeScorer`, selected via `--content-scorer llm` — matched
cases by *meaning* using a local Ollama judge, and was the reason this
calibration harness was built. **It was retired on 2026-07-26**, along with
`--content-scorer`, `--judge-model`, `VisionTrainingConfig.judge_model`, the
`ContentScore.quality` field, and the `content_quality` metric.

Calibration is what condemned it. Probing the judge's raw match output showed a
near-constant answer regardless of input:

```
identity           -> {"matches": [[0,0],[1,1]]}     # misses a third IDENTICAL pair
paraphrase         -> {"matches": [[0,0],[1,1]]}
noise              -> {"matches": [[0,0],[1,1]]}
disjoint           -> {"matches": [[0,0],[1,None]]}  # invents a match
mixed              -> {"matches": [[0,0],[1,None]]}
subset             -> {"matches": [[0,0],[1,2]]}     # only real deviation
reordered 3-vs-3   -> {"matches": [[0,0],[1,1]]}     # reordering changes nothing
```

This was not truncation (`num_predict` is 4096 and the JSON was well-formed).
Scores: `llama3.1:8b` passed 2 of 6 cases against `overlap`'s 6 of 6, and **both
passes were false positives** — the count-only check happened to land on the
right number.

A larger local judge did not help. `deepseek-coder-v2:16b` scored 3 of 6 and
appeared to clear `paraphrase` with f1 = 1.000, but probing showed it returning
`[[0,0],[1,1],[2,2]]` — pairing positionally. It scored *worse* on the trivial
`identity` case (2 pairs) than on the hard `paraphrase` one (3 pairs), which is
backwards for genuine comprehension; its `paraphrase` result was an artifact of
the fixture listing paraphrases in the same order as their references.

Both models failed the same way, and — because the metric counts pairs rather
than checking them — `paraphrase` could not have distinguished a competent judge
from a positional guesser even in principle. With no path to validating the one
case the feature existed for, the scorer was removed rather than carried as
permanently experimental. The harness remains: it validates `overlap` and would
validate any future scorer.

## Key configuration (`config/cli_config.yaml`, `training:` section)

| Key | Purpose |
|---|---|
| `enable_raft` | Master switch for RAFT data collection |
| `collect_training_data` | Write examples during processing |
| `training_data_dir` | Root directory for training data |
| `min_examples_for_training` | Minimum examples before a dataset is useful |
| `raft_collect_context` | Attach requirement context to each example |
| `raft_min_oracle_docs` / `raft_min_distractor_docs` | Oracle/distractor minimums per example |
| `raft_context_window` | Max context items per example |
| `min_quality_score` | Quality floor for dataset inclusion |
| `auto_approve_threshold` | Auto-approve examples scoring above this |

## What is NOT implemented

- **LoRA / adapter weight fine-tuning.** The `[training]` extra and the
  archived `MODEL_TRAINING_GUIDE.md` describe `lora_trainer.py` / `train_lora.py`
  scripts that **do not exist** in this repository.
- **Genuine dataset-derived model weights or prompt.** The dataset informs
  reporting statistics only — neither the underlying weights nor the fixed
  system prompt (review 2026-07-24 finding 6 / 2026-07-20 finding 6 / Archived
  finding 3). Real weight fine-tuning would need an HF-format + GPU pipeline this
  local-Ollama tool does not target.

## Related source modules

`src/training/`: `raft_collector.py`, `raft_annotator.py`,
`raft_dataset_builder.py`, `vision_raft_trainer.py`, `quality_scorer.py`, and
the experimental `progressive_trainer.py` (curriculum ordering; no packaged CLI
entry point).
