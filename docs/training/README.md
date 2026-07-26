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
| `content_quality` | LLM-judge holistic quality (0–1) of the generation vs the reference, from `--content-scorer llm` | **Complementary** to `content_f1` (not the headline). Non-deterministic; `None` under the default `overlap` scorer. |

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

**Before reaching for this flag**, see [Judge calibration](#judge-calibration)
below and its "Known limitation" — a live calibration run found this judge's
matching unreliable, so `--content-scorer llm` is not currently recommended
over the default `overlap` scorer.

## Judge calibration

`--validate-judge` answers a narrower question than `--evaluate`: is the content
scorer itself trustworthy? It scores five built-in, gold-by-construction
fixtures (`src/training/judge_calibration_cases.py`) directly through a
`ContentScorer` — **no generation model runs in this mode**, so it measures the
scorer in isolation, not a trained model's output quality. It does **not**
validate a customized model; use `--evaluate` for that.

**Running it:**

```bash
# Both scorers, side by side (needs Ollama for the llm column)
python3 utilities/train_vision_model.py --validate-judge

# Deterministic overlap scorer only — no Ollama required
python3 utilities/train_vision_model.py --validate-judge --content-scorer overlap

# Calibrate a different judge model
python3 utilities/train_vision_model.py --validate-judge --judge-model llama3.1:8b
```

**Reading the scorecard:** each case prints one line per scorer kind, one
`metric actual [band] PASS/FAIL` group per declared metric, followed by a
per-scorer `passed/total` summary and a final `RESULT: PASS`/`RESULT: FAIL`
line. The process exits 1 if any scorer breaches any band on any case, 0
otherwise.

**The five cases:**

| Case | What it proves |
|---|---|
| `identity` | Generated == reference verbatim — the easiest possible case; both scorers must score it near 1.0. |
| `disjoint` | Completely unrelated generations — both scorers must give it near-zero credit. |
| `subset` | Half the reference set, verbatim — checks recall/precision arithmetic on a known partial match. |
| `paraphrase` | **The discriminating case.** Three reference scenarios reworded in different words. The deterministic `overlap` scorer matches on string similarity and is *expected* to fail it (band `f1` 0.0–0.35); the LLM judge is expected to *clear* it (band `f1` ≥ 0.7), because recognizing paraphrases by meaning is the only thing that justifies its cost of two Ollama calls per example. |
| `noise` | The full reference set plus two unrelated extras — checks that recall stays high while precision correctly drops. |

**Caveat:** the bands are tolerances chosen to make each case's ground truth
unambiguous, not claims of exact truth. A scorer breaching a band — in
particular `llm` failing `paraphrase` — means that scorer is not earning its
keep for that case. It is **not** a signal to widen the band; the correct
response to a breach is to fix or reconsider the scorer, not the test.

**Limitation — the harness grades pair *count*, not pair *correctness*.**
`LLMJudgeScorer._count_valid_pairs` only counts how many generated↔reference
pairs came back, never whether they are the *right* pairs. A judge that
mispairs every single case would still score full marks:

```python
LLMJudgeScorer._count_valid_pairs([[0, 1], [1, 2], [2, 0]], 3, 3)  # -> 3
_prf(3, 3, 3)                                                       # -> (1.0, 1.0, 1.0)
```

so a judge whose matching is completely wrong would still pass precision,
recall, and F1, and would clear 4 of the current 5 fixtures. This limitation
is **inherited from the prior phase's metric** (the same pair-count
convention `content_f1` already used), not introduced by this harness. A
future `permutation` fixture — the same cases with match order shuffled —
would detect it; not implemented here, documentation only.

### Known limitation: the LLM judge returns a near-constant match list

Probing the live judge's raw match output — the `[[generated_idx,
reference_idx], ...]` pairs it returns before precision/recall/F1 are
computed — across all five fixtures plus two synthetic checks shows the judge
returning almost the same answer regardless of input:

```
identity           -> {"matches": [[0,0],[1,1]]}
paraphrase         -> {"matches": [[0,0],[1,1]]}
noise              -> {"matches": [[0,0],[1,1]]}
disjoint           -> {"matches": [[0,0],[1,None]]}
subset             -> {"matches": [[0,0],[1,2]]}    # only deviation
mirror-fold 1-vs-1 -> {"matches": [[0,0],[1,1]]}    # [1,1] out of range entirely
reordered 3-vs-3   -> {"matches": [[0,0],[1,1]]}    # reordering changes nothing
```

This is not truncation (`num_predict` is 4096 and the JSON is well-formed);
the judge emits a near-constant answer irrespective of the actual
generated/reference content.

Two live calibration runs against the same local `llama3.1:8b` judge
(2026-07-26, deterministic — both runs produced bit-identical scores because
the client's default judge temperature is 0.0) measured:

```
                  overlap          llm
identity   f1     1.000  PASS      0.667  FAIL  (band 0.90-1.00)
disjoint   f1     0.000  PASS      0.333  FAIL  (band 0.00-0.10)
subset     —      PASS            PASS
paraphrase f1     0.000  PASS      0.667  FAIL  (band 0.70-1.00)
noise      —      PASS            partial FAIL  (recall 0.667, band 0.90-1.00)

overlap: 5/5 passed · llm: 1/5 passed (only `subset`)
```

Read against the probe table above, `identity` and `paraphrase` produce the
*identical* `[[0,0],[1,1]]` match list and therefore the identical f1 = 0.667
— the harness got **zero paraphrase-specific signal** from this run. The
judge's competence at recognizing paraphrases by meaning is **unmeasured, not
failed**; the finding the probe actually supports is stronger and more
actionable: the judge's matching is unreliable across the board, not narrowly
weak at one case.

The scorecard's single `llm` PASS (`subset`) is a **false positive**, not
partial competence: `LLMJudgeScorer._count_valid_pairs` counts how many pairs
were reported, never whether they're the *correct* pairs, and the
near-constant `[[0,0],[1,2]]` output happens to yield the right count for
`subset` by coincidence.

**On this evidence, `--content-scorer llm` is not currently justified over the
default `overlap` scorer** — and more strongly than a single-case weakness
would suggest, since the judge is unreliable in general rather than
specifically weak at paraphrase recognition. Treat `llm` as experimental until
the matching prompt is revisited; `overlap`/`content_f1` remains the
recommended default and headline signal for `--evaluate`. See
`tests/training/test_judge_calibration_integration.py` for the reproducible
live check (`-m integration`, requires a local `llama3.1:8b`).

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
