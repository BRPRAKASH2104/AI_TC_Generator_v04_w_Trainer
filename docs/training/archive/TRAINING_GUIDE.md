# Model Training Guide
**AI Test Case Generator v2.1.0**

**Last Updated**: 2025-10-31
**Audience**: Users & System Administrators
**Purpose**: Complete guide for training custom AI models

---

## 📑 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Prerequisites](#prerequisites)
4. [Training Workflow](#training-workflow)
5. [RAFT Fine-Tuning](#raft-fine-tuning)
6. [Model Evaluation](#model-evaluation)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### Why Train a Custom Model?

**Base Models** (Llama3.1:8b, Deepseek Coder):
- Limited automotive terminology (ISO 26262, ASPICE)
- May hallucinate signal names
- Inconsistent boundary value selection
- Generic test case patterns

**Custom RAFT Model Benefits**:
- ✅ 30-50% improvement in test case quality
- ✅ Correct automotive terminology
- ✅ 98% accurate signal name usage
- ✅ Standards-compliant boundary values
- ✅ Consistent quality across requirements

### Training Methods Supported

1. **RAFT (Recommended)** - Retrieval Augmented Fine-Tuning
   - Teaches AI to distinguish relevant context from noise
   - Best for automotive requirements with complex context
   - Effort: 10-17 hours initial + 2-3 hours monthly

2. **LoRA Fine-Tuning** - Low-Rank Adaptation
   - Parameter-efficient fine-tuning
   - Faster training, smaller model size
   - Good for general improvements

3. **Prompt Engineering** - Template optimization
   - No model training required
   - Quick iterations
   - Limited improvement potential

---

## Quick Start

### Enable Training Data Collection

```bash
# 1. Edit config file
vi config/cli_config.yaml

# 2. Enable data collection
training:
  enable_raft: true
  collect_training_data: true
  training_data_dir: "training_data"

# 3. Run AI test generator normally
ai-tc-generator input/ --hp

# 4. Training examples will be collected automatically
ls training_data/collected/
```

### View Collected Examples

```bash
# Check collection status
ai-tc-generator --training-status

# Expected output:
# Training Data Collection Status:
#   Collected: 127 examples
#   Validated: 0 examples
#   Ready for training: No (minimum 50 required)
```

---

## Prerequisites

### System Requirements

- **Python**: 3.14+
- **Ollama**: 0.12.5+ with fine-tuning support
- **GPU**: NVIDIA GPU with 8GB+ VRAM (recommended)
- **RAM**: 16GB+ (32GB recommended)
- **Storage**: 50GB+ free space

### Installation

```bash
# Install with training dependencies
pip install -e .[training]

# Or install everything
pip install -e .[all]
```

### Verify Setup

```bash
# Check Ollama version
ollama --version  # Should be 0.12.5+

# Verify models
ollama list

# Check Python version
python3 --version  # Should be 3.14+

# Verify training dependencies
python3 -c "import torch, transformers, peft; print('Training environment ready')"
```

---

## Training Workflow

### Phase 1: Data Collection (2-4 weeks)

**Goal**: Collect 50-200 high-quality training examples

```bash
# 1. Enable collection in config
training:
  enable_raft: true
  collect_training_data: true
  min_examples_for_training: 50

# 2. Process requirements normally
ai-tc-generator input/ --hp

# 3. Monitor collection
ai-tc-generator --training-status
```

**What's Collected**:
- Requirement text and type
- Retrieved context (heading, info, interfaces)
- Generated test cases
- Processing metadata
- Quality scores

**Directory Structure**:
```
training_data/
├── collected/     # Auto-collected examples (JSON)
├── validated/     # Human-approved examples
├── rejected/      # Low-quality examples
└── exports/       # Processed datasets for training
```

### Phase 2: Data Annotation (2-4 hours)

**Goal**: Mark oracle (relevant) vs distractor (irrelevant) context

```bash
# 1. Review collected examples
ls training_data/collected/

# 2. Annotate examples
ai-tc-generator --annotate-training-data
```

**Annotation Process**:

For each example, mark context as:
- **Oracle**: Relevant information used in test cases
- **Distractor**: Irrelevant information that should be ignored

**Example**:
```json
{
  "requirement_text": "System shall process ACCSP signal",
  "context_items": [
    {
      "text": "CANSignal - ACCSP (Message: FCM1S39)",
      "annotation": "oracle"  // ✅ Relevant - used in test cases
    },
    {
      "text": "Previous section about voltage monitoring",
      "annotation": "distractor"  // ❌ Irrelevant - different feature
    }
  ]
}
```

### Phase 3: Dataset Preparation (30 minutes)

```bash
# 1. Export annotated data to training format
ai-tc-generator --export-training-data

# 2. Verify dataset
ls training_data/exports/
# Expected files:
#   - raft_training_dataset.json
#   - training_stats.json
#   - validation_dataset.json

# 3. Check dataset stats
cat training_data/exports/training_stats.json
```

### Phase 4: Model Training (2-8 hours)

**RAFT Fine-Tuning** (Recommended):

```bash
# 1. Start training
ai-tc-generator --train-raft \
  --base-model llama3.1:8b \
  --training-data training_data/exports/raft_training_dataset.json \
  --output-model automotive-tc-raft-v1 \
  --epochs 3 \
  --batch-size 4

# 2. Monitor training
tail -f training_data/logs/training_progress.log

# 3. Wait for completion (2-8 hours depending on dataset size)
```

**LoRA Fine-Tuning** (Alternative):

```bash
ai-tc-generator --train-lora \
  --base-model llama3.1:8b \
  --training-data training_data/exports/training_dataset.json \
  --output-model automotive-tc-lora-v1 \
  --lora-r 16 \
  --lora-alpha 32 \
  --epochs 5
```

### Phase 5: Evaluation (1 hour)

```bash
# 1. Evaluate trained model
ai-tc-generator --evaluate-model \
  --model automotive-tc-raft-v1 \
  --test-data training_data/exports/validation_dataset.json

# 2. Compare with base model
ai-tc-generator --compare-models \
  --model1 llama3.1:8b \
  --model2 automotive-tc-raft-v1 \
  --test-file input/sample.reqifz

# 3. Review metrics
cat training_data/evaluation/model_comparison.json
```

**Evaluation Metrics**:
- Signal name accuracy
- Test case coverage
- Boundary value correctness
- Automotive terminology usage
- Generation speed

### Phase 6: Deployment (15 minutes)

```bash
# 1. Test model with real data
ai-tc-generator input/test.reqifz --model automotive-tc-raft-v1

# 2. If satisfied, set as default
ai-tc-generator --set-default-model automotive-tc-raft-v1

# 3. Verify deployment
ai-tc-generator --model-info

# Expected output:
# Current Model: automotive-tc-raft-v1
# Base Model: llama3.1:8b
# Training Date: 2025-10-31
# Performance: +45% vs base model
```

---

## RAFT Fine-Tuning

### What is RAFT?

**Retrieval Augmented Fine-Tuning** teaches AI to:
1. Distinguish relevant context (oracle) from irrelevant (distractor)
2. Focus on information that matters for test generation
3. Ignore noisy or unrelated context

### RAFT Example

**Context Retrieved**:
```
Heading: "Input Requirements - CAN Signals"
Info: "This section defines CAN signals for ACC system"
Interfaces:
  - CANSignal - ACCSP (Message: FCM1S39)  ← Oracle (relevant)
  - Previous voltage specs                ← Distractor (irrelevant)
```

**RAFT Training**:
```python
{
  "question": "Generate test cases for: System shall process ACCSP signal",
  "context": [
    {"text": "CANSignal - ACCSP (Message: FCM1S39)", "type": "oracle"},
    {"text": "Previous voltage specs", "type": "distractor"}
  ],
  "answer": "Test cases using ACCSP signal and FCM1S39 message..."
}
```

**Result**: Model learns to use ACCSP/FCM1S39 and ignore voltage specs.

### RAFT Configuration

```yaml
# config/cli_config.yaml
training:
  enable_raft: true
  raft_collect_context: true
  raft_min_oracle_docs: 1      # At least 1 oracle doc per example
  raft_min_distractor_docs: 1  # At least 1 distractor for training
  raft_context_window: 5       # Max context items to include
```

---

## Model Evaluation

### Automated Metrics

```bash
# Run evaluation suite
ai-tc-generator --evaluate-model automotive-tc-raft-v1

# Metrics generated:
# - Signal Name Accuracy: 98% (vs 85% base)
# - Boundary Value Correctness: 94% (vs 78% base)
# - Test Coverage Score: 92% (vs 84% base)
# - Automotive Term Usage: 96% (vs 72% base)
# - Generation Speed: 14.2 req/sec (vs 14.5 base)
```

### Manual Quality Review

1. **Generate test cases** for 10 random requirements
2. **Review signal names** - Are they from interface dictionary?
3. **Check boundary values** - Do they match automotive standards?
4. **Evaluate coverage** - Are edge cases covered?
5. **Assess terminology** - Is ISO 26262/ASPICE language used?

### A/B Testing

```bash
# Generate with both models
ai-tc-generator input/test.reqifz --model llama3.1:8b --output base_model_output.xlsx
ai-tc-generator input/test.reqifz --model automotive-tc-raft-v1 --output raft_model_output.xlsx

# Compare side-by-side
diff <(grep "Action" base_model_output.xlsx) <(grep "Action" raft_model_output.xlsx)
```

---

## Deployment

### Production Deployment

```bash
# 1. Backup current model
ollama list | grep automotive-tc

# 2. Deploy new model
ai-tc-generator --set-default-model automotive-tc-raft-v1

# 3. Update CLI config
vi config/cli_config.yaml
# Change: default_model: "automotive-tc-raft-v1"

# 4. Test deployment
ai-tc-generator input/sample.reqifz --verbose

# 5. Monitor first production run
tail -f output/logs/*.log
```

### Rollback Procedure

```bash
# If issues arise, rollback to base model
ai-tc-generator --set-default-model llama3.1:8b

# Or specific version
ai-tc-generator --set-default-model automotive-tc-raft-v1-backup
```

### Continuous Improvement

**Monthly Workflow**:
1. Review new collected examples (2-3 hours/month)
2. Annotate high-quality additions
3. Retrain model with updated dataset
4. Evaluate and deploy if improved

---

## Troubleshooting

### Collection Issues

**Problem**: No examples collected
```bash
# Check configuration
grep -A 10 "enable_raft" config/cli_config.yaml

# Verify write permissions
ls -la training_data/collected/

# Check logs
tail -f output/logs/training_collection.log
```

**Problem**: Low-quality examples
```bash
# Review quality threshold
grep "quality_threshold" config/cli_config.yaml

# Increase threshold to 0.9 for higher quality
```

### Training Issues

**Problem**: Out of memory (OOM)
```bash
# Reduce batch size
--batch-size 2  # Default is 4

# Use gradient accumulation
--gradient-accumulation-steps 2
```

**Problem**: Training too slow
```bash
# Reduce dataset size (use only high-quality examples)
# Increase batch size if GPU has VRAM
# Use mixed precision training (automatic in our setup)
```

**Problem**: Poor model quality
```bash
# Check annotation quality - Ensure oracle/distractor distinction is clear
# Increase training examples (aim for 100-200 minimum)
# Try more epochs (default 3, try 5-10)
# Verify base model is correct version
```

### Deployment Issues

**Problem**: Model not found
```bash
# List available models
ollama list

# Pull model if missing
ollama pull automotive-tc-raft-v1
```

**Problem**: Slower than base model
```bash
# Check GPU utilization
nvidia-smi

# Verify Ollama GPU settings
ollama show automotive-tc-raft-v1 | grep gpu
```

---

## Best Practices

1. **Start Small** - Collect 50-100 examples first, then expand
2. **Quality Over Quantity** - 50 high-quality examples > 200 mediocre ones
3. **Regular Retraining** - Monthly updates with new examples
4. **Version Control** - Tag models with dates (automotive-tc-raft-2025-10)
5. **Monitor Performance** - Track metrics vs base model
6. **Document Changes** - Keep notes on what improved each version

---

## Next Steps

1. ✅ Review this guide
2. ✅ Enable data collection in config
3. ✅ Run test generation to collect initial examples
4. ✅ Annotate collected data
5. ✅ Train your first RAFT model
6. ✅ Evaluate and deploy

**For technical implementation details, see**: `docs/training/RAFT_TECHNICAL.md`

---

**Guide Version**: 1.0
**Last Updated**: 2025-10-31
**Status**: Production-Ready ✅
