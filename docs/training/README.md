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

**A/B (`--compare-base`) honesty notes:**

- The delta is **paired**: computed only over examples both models generated for
  without error. If the baseline fails on every example the delta is **withheld**
  and the command exits non-zero — a failed baseline is never reported as lift.
- The comparison is **bundle-vs-base**: the customized model changes both the
  system prompt *and* generation parameters, while the base model runs with its
  own defaults (not parameter-matched, no fixed seed). The delta reflects the
  whole customized bundle, **not** the isolated effect of the system prompt. The
  result's `provenance` block records both models' effective parameters.

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
