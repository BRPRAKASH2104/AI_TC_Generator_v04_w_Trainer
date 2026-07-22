# Archived Training Documents

> ⚠️ **These documents are archived and superseded.** They are kept for
> historical reference only. Several describe an LoRA / weight-fine-tuning
> workflow (e.g. `lora_trainer.py`, `train_lora.py`) that is **not implemented**
> in this repository, and their instructions may not match the current code.
>
> **Follow the single current guide instead:** [`../README.md`](../README.md).

The training capability that actually ships is a *prompt-customization*
pipeline (RAFT data collection → annotation → dataset build → Ollama Modelfile),
not weight fine-tuning. The current guide documents it accurately and concisely.

## Contents (superseded)

| File | Was | Superseded because |
|---|---|---|
| `GETTING_STARTED_WITH_TRAINING.md` | Beginner intro | Folded into the current guide |
| `MODEL_TRAINING_GUIDE.md` | LoRA/fine-tuning guide | References `lora_trainer.py` / `train_lora.py` that do not exist |
| `RAFT_TECHNICAL.md` | RAFT design deep-dive | Describes a training path not present in code |
| `TRAINING_GUIDE.md` | General training guide | Redundant with the current guide |
| `training_guideline.md` | Vision training guide (1394 lines) | Redundant / partly aspirational |
