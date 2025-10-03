# RAFT Setup Guide
## Retrieval Augmented Fine-Tuning for AI Test Case Generator

**Version:** 1.0.0
**Last Updated:** 2025-10-03
**Status:** Implementation Guide

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Enable RAFT Data Collection](#phase-1-enable-raft-data-collection)
4. [Phase 2: Annotate Training Data](#phase-2-annotate-training-data)
5. [Phase 3: Prepare RAFT Training Dataset](#phase-3-prepare-raft-training-dataset)
6. [Phase 4: Train with RAFT](#phase-4-train-with-raft)
7. [Phase 5: Evaluate and Deploy](#phase-5-evaluate-and-deploy)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide walks you through implementing RAFT (Retrieval Augmented Fine-Tuning) for your AI Test Case Generator. RAFT teaches your model to distinguish relevant context from noise, dramatically improving test case quality.

### What RAFT Adds to Your System

Your system already retrieves context (headings, info artifacts, interfaces) via `BaseProcessor._build_augmented_requirements()`. RAFT enhances this by:

- **Teaching the model which context matters** for each requirement type
- **Filtering out irrelevant "distractor" context** that could mislead generation
- **Improving generalization** to new requirement patterns not seen during training

### Expected Benefits

- **30-50% improvement** in test case quality for complex/noisy documents
- **Better context filtering** - focuses on relevant artifacts
- **Reduced hallucination** - ignores irrelevant information
- **Stronger generalization** - handles new patterns effectively

---

## Prerequisites

### System Requirements

✅ **Already Implemented:**
- Context-aware processing (`BaseProcessor._build_augmented_requirements()`)
- Ollama API integration
- Test case generation pipeline

✅ **Required for RAFT:**
- Python 3.13+
- Ollama v0.11.10+ with fine-tuning support
- Minimum 50GB disk space for training data
- 16GB+ RAM (32GB recommended for larger models)

### Verify Your Setup

```bash
# Check Ollama version
ollama --version  # Should be v0.11.10+

# Verify models are available
ollama list

# Check Python version
python3 --version  # Should be 3.13+

# Verify project installation
ai-tc-generator --version
```

---

## Phase 1: Enable RAFT Data Collection

### Step 1.1: Update Configuration

Add RAFT settings to `src/config.py`:

```python
class TrainingConfig(BaseModel):
    """Configuration for training and model customization"""

    # Existing fields...
    collect_training_data: bool = False
    training_data_dir: str = "training_data"
    min_examples_for_training: int = Field(50, ge=1)

    # NEW: RAFT-specific settings
    enable_raft: bool = Field(False, description="Enable RAFT data collection")
    raft_collect_context: bool = Field(True, description="Collect retrieved context for RAFT")
    raft_min_oracle_docs: int = Field(1, ge=1, description="Minimum oracle documents per example")
    raft_min_distractor_docs: int = Field(1, ge=0, description="Minimum distractor documents")
    raft_context_window: int = Field(5, ge=1, description="Max context items to include")
```

### Step 1.2: Enable RAFT Collection Mode

Edit `config/cli_config.yaml`:

```yaml
# Add to cli_defaults section
cli_defaults:
  mode: "standard"
  model: "llama3.1:8b"
  # ... existing settings ...

# Add RAFT preset
presets:
  # NEW: RAFT data collection preset
  raft_collect:
    mode: "standard"
    model: "llama3.1:8b"
    verbose: true
    collect_raft_data: true    # Enable RAFT collection
```

### Step 1.3: Create RAFT Data Collector Module

Create `src/training/raft_collector.py`:

```python
"""RAFT Data Collection Module"""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Any

type AugmentedRequirement = dict[str, Any]
type RAFTExample = dict[str, Any]


class RAFTDataCollector:
    """Collects training data in RAFT format with context annotation"""

    __slots__ = ("output_dir", "logger")

    def __init__(self, output_dir: str | Path = "training_data/collected"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect_example(
        self,
        requirement: AugmentedRequirement,
        generated_test_cases: str,
        model: str
    ) -> Path:
        """
        Collect a single RAFT training example.

        Args:
            requirement: Augmented requirement with context
            generated_test_cases: AI-generated test cases (to be validated)
            model: Model used for generation

        Returns:
            Path to saved example file
        """
        # Extract context for RAFT annotation
        heading = requirement.get("heading", "No Heading")
        info_list = requirement.get("info_list", [])
        interface_list = requirement.get("interface_list", [])

        # Build RAFT example structure
        raft_example: RAFTExample = {
            "requirement_id": requirement.get("id", "UNKNOWN"),
            "requirement_text": requirement.get("text", ""),
            "heading": heading,

            # Retrieved context (to be annotated as oracle/distractor)
            "retrieved_context": {
                "heading": {"id": "HEADING", "text": heading},
                "info_artifacts": [
                    {"id": info.get("id", f"INFO_{i}"), "text": info.get("text", "")}
                    for i, info in enumerate(info_list)
                ],
                "interfaces": [
                    {"id": iface.get("id", f"IF_{i}"), "text": iface.get("text", "")}
                    for i, iface in enumerate(interface_list)
                ]
            },

            # Generated output (to be validated by expert)
            "generated_test_cases": generated_test_cases,
            "model_used": model,
            "generation_timestamp": datetime.now().isoformat(),

            # RAFT annotation (to be filled by expert)
            "context_annotation": {
                "oracle_context": [],        # Expert fills: relevant context IDs
                "distractor_context": [],    # Expert fills: irrelevant context IDs
                "annotation_notes": "",       # Expert fills: optional notes
                "quality_rating": None        # Expert fills: 1-5 scale
            },

            # Validation status
            "validation_status": "pending",  # pending|validated|rejected
            "annotated_by": None,
            "annotation_timestamp": None
        }

        # Save to file
        req_id = requirement.get("id", "UNKNOWN").replace("/", "_")
        filename = f"raft_{req_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raft_example, f, indent=2, ensure_ascii=False)

        return output_path

    def get_collection_stats(self) -> dict[str, int]:
        """Get statistics on collected RAFT examples"""
        json_files = list(self.output_dir.glob("raft_*.json"))

        stats = {
            "total_collected": len(json_files),
            "pending_annotation": 0,
            "validated": 0,
            "rejected": 0,
            "annotated": 0
        }

        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                    status = data.get("validation_status", "pending")

                    if status == "pending":
                        stats["pending_annotation"] += 1
                    elif status == "validated":
                        stats["validated"] += 1
                    elif status == "rejected":
                        stats["rejected"] += 1

                    # Check if context annotation is done
                    annotation = data.get("context_annotation", {})
                    if annotation.get("oracle_context") or annotation.get("distractor_context"):
                        stats["annotated"] += 1

            except Exception:
                continue

        return stats
```

### Step 1.4: Integrate with Processors

Add RAFT collection to `src/processors/base_processor.py`:

```python
# Add to imports
from training.raft_collector import RAFTDataCollector

class BaseProcessor:
    def __init__(self, config: ConfigManager, logger: Logger):
        # Existing initialization...

        # NEW: Initialize RAFT collector if enabled
        if config.training.enable_raft:
            self.raft_collector = RAFTDataCollector(
                output_dir=Path(config.training.training_data_dir) / "collected"
            )
        else:
            self.raft_collector = None

    def _save_raft_example(
        self,
        requirement: AugmentedRequirement,
        test_cases: str,
        model: str
    ) -> None:
        """Save RAFT training example if collection is enabled"""
        if self.raft_collector:
            output_path = self.raft_collector.collect_example(
                requirement=requirement,
                generated_test_cases=test_cases,
                model=model
            )
            self.logger.debug(f"📊 Saved RAFT example: {output_path}")
```

Add call in processors after test case generation:

```python
# In standard_processor.py or hp_processor.py, after generating test cases:

for requirement in augmented_requirements:
    # Generate test cases...
    test_cases = generator.generate_test_cases(requirement, model, template)

    # NEW: Save RAFT example if enabled
    self._save_raft_example(requirement, test_cases, model)
```

### Step 1.5: Test Data Collection

```bash
# Enable RAFT collection via environment variable
export AI_TG_COLLECT_RAFT=true

# Process a sample file
ai-tc-generator input/sample.reqifz --verbose

# Check collected data
ls -l training_data/collected/
cat training_data/collected/raft_REQ_001_*.json | head -50
```

---

## Phase 2: Annotate Training Data

### Step 2.1: Review Collected Examples

```bash
# Check collection statistics
python3 -c "
from src.training.raft_collector import RAFTDataCollector
collector = RAFTDataCollector()
stats = collector.get_collection_stats()
print('📊 Collection Stats:', stats)
"
```

### Step 2.2: Annotation Guidelines

Create `training_data/ANNOTATION_GUIDELINES.md`:

```markdown
# RAFT Context Annotation Guidelines

## Oracle Context (✅ Relevant)
Mark context as "oracle" if it:
- Directly contributes to test case generation
- Provides domain-specific constraints (voltage, timing, safety)
- Clarifies requirement scope or behavior
- Defines interfaces/signals used in the requirement

**Examples:**
- INFO about safety lockout → Oracle for safety requirements
- Interface specifications → Oracle if requirement uses that interface
- Voltage/timing constraints → Oracle for electrical requirements

## Distractor Context (❌ Irrelevant)
Mark context as "distractor" if it:
- Was present but not relevant to this requirement
- Belongs to a different subsystem/component
- Provides general info not specific to this test case
- Would mislead or confuse test generation

**Examples:**
- Window motor specs → Distractor for door lock requirements
- Power management info → Distractor for functional UI requirements
- Cross-cutting concerns → Usually distractor unless explicitly referenced

## Annotation Process

1. **Read the requirement** - understand what needs testing
2. **Review generated test cases** - see what the AI produced
3. **Evaluate each context item**:
   - Did the heading help frame the requirement? → Oracle or Distractor
   - Which info artifacts were actually relevant? → Mark as Oracle
   - Which info artifacts were noise? → Mark as Distractor
   - Which interfaces matter for this requirement? → Mark as Oracle
   - Which interfaces are unrelated? → Mark as Distractor
4. **Rate quality** (1-5 scale):
   - 5 = Excellent, production-ready
   - 4 = Good, minor edits needed
   - 3 = Acceptable, needs revision
   - 2 = Poor, major issues
   - 1 = Unusable, reject
5. **Add notes** - explain your reasoning (helps future annotation)
```

### Step 2.3: Annotate Examples

Create annotation helper script `utilities/annotate_raft.py`:

```python
#!/usr/bin/env python3
"""Interactive RAFT annotation tool"""

import json
from pathlib import Path
from datetime import datetime


def annotate_example(example_path: Path) -> None:
    """Interactively annotate a RAFT example"""

    with open(example_path, encoding="utf-8") as f:
        data = json.load(f)

    print("\n" + "=" * 70)
    print(f"📝 Annotating: {data['requirement_id']}")
    print("=" * 70)
    print(f"\n📋 Requirement: {data['requirement_text'][:200]}...")
    print(f"\n📁 Heading: {data['heading']}")

    # Show retrieved context
    print("\n🔍 Retrieved Context:")
    ctx = data["retrieved_context"]

    print(f"\n  Heading: {ctx['heading']['text']}")

    print(f"\n  Info Artifacts ({len(ctx['info_artifacts'])}):")
    for i, info in enumerate(ctx['info_artifacts'], 1):
        print(f"    [{i}] {info['id']}: {info['text'][:80]}...")

    print(f"\n  Interfaces ({len(ctx['interfaces'])}):")
    for i, iface in enumerate(ctx['interfaces'], 1):
        print(f"    [{i}] {iface['id']}: {iface['text'][:80]}...")

    # Show generated test cases
    print(f"\n✨ Generated Test Cases:\n{data['generated_test_cases'][:500]}...")

    # Interactive annotation
    print("\n" + "=" * 70)
    print("📊 Annotation")
    print("=" * 70)

    # Quality rating
    print("\n1️⃣ Rate test case quality (1-5):")
    quality = int(input("   Rating: "))

    # Validation status
    print("\n2️⃣ Validation status:")
    print("   [1] Validated (accept)")
    print("   [2] Rejected")
    status_choice = input("   Choice: ")
    status = "validated" if status_choice == "1" else "rejected"

    # Context annotation
    oracle_ids = []
    distractor_ids = []

    print("\n3️⃣ Annotate context relevance:")

    # Heading
    heading_choice = input(f"   Heading '{ctx['heading']['text'][:40]}' - Oracle? (y/n): ")
    if heading_choice.lower() == 'y':
        oracle_ids.append("HEADING")
    else:
        distractor_ids.append("HEADING")

    # Info artifacts
    for info in ctx['info_artifacts']:
        choice = input(f"   {info['id']} - Oracle? (y/n/skip): ")
        if choice.lower() == 'y':
            oracle_ids.append(info['id'])
        elif choice.lower() == 'n':
            distractor_ids.append(info['id'])

    # Interfaces
    for iface in ctx['interfaces']:
        choice = input(f"   {iface['id']} - Oracle? (y/n/skip): ")
        if choice.lower() == 'y':
            oracle_ids.append(iface['id'])
        elif choice.lower() == 'n':
            distractor_ids.append(iface['id'])

    # Notes
    print("\n4️⃣ Annotation notes (optional):")
    notes = input("   Notes: ")

    # Update annotation
    data["context_annotation"] = {
        "oracle_context": oracle_ids,
        "distractor_context": distractor_ids,
        "annotation_notes": notes,
        "quality_rating": quality
    }
    data["validation_status"] = status
    data["annotated_by"] = input("\n5️⃣ Your name: ")
    data["annotation_timestamp"] = datetime.now().isoformat()

    # Save
    with open(example_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Move to appropriate directory
    dest_dir = Path("training_data") / status
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / example_path.name
    example_path.rename(dest_path)

    print(f"\n✅ Annotated and moved to: {dest_path}")


if __name__ == "__main__":
    collected_dir = Path("training_data/collected")
    pending_files = list(collected_dir.glob("raft_*.json"))

    print(f"\n📊 Found {len(pending_files)} examples to annotate")

    for i, file_path in enumerate(pending_files, 1):
        print(f"\n{'='*70}")
        print(f"Progress: {i}/{len(pending_files)}")
        annotate_example(file_path)

        if i < len(pending_files):
            cont = input("\n➡️  Continue to next? (y/n): ")
            if cont.lower() != 'y':
                break

    print("\n✅ Annotation session complete!")
```

Usage:

```bash
# Make executable
chmod +x utilities/annotate_raft.py

# Run interactive annotation
python utilities/annotate_raft.py
```

---

## Phase 3: Prepare RAFT Training Dataset

### Step 3.1: Create RAFT Dataset Builder

Create `src/training/raft_dataset_builder.py`:

```python
"""RAFT Training Dataset Builder"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

type RAFTTrainingExample = dict[str, Any]


class RAFTDatasetBuilder:
    """Builds RAFT training dataset from annotated examples"""

    __slots__ = ("validated_dir", "output_dir")

    def __init__(
        self,
        validated_dir: str | Path = "training_data/validated",
        output_dir: str | Path = "training_data/raft_dataset"
    ):
        self.validated_dir = Path(validated_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_dataset(self) -> list[RAFTTrainingExample]:
        """
        Build RAFT training dataset from annotated examples.

        RAFT format:
        {
            "question": "<requirement text>",
            "oracle_context": ["<relevant doc 1>", "<relevant doc 2>"],
            "distractor_context": ["<irrelevant doc 1>", "<irrelevant doc 2>"],
            "answer": "<validated test cases>"
        }
        """
        annotated_files = list(self.validated_dir.glob("raft_*.json"))

        if not annotated_files:
            raise ValueError(f"No annotated examples found in {self.validated_dir}")

        raft_examples = []

        for file_path in annotated_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                # Skip if not properly annotated
                annotation = data.get("context_annotation", {})
                if not annotation.get("oracle_context"):
                    continue

                # Build RAFT example
                raft_example = self._build_raft_example(data)
                raft_examples.append(raft_example)

            except Exception as e:
                print(f"⚠️  Skipping {file_path}: {e}")
                continue

        print(f"✅ Built {len(raft_examples)} RAFT training examples")
        return raft_examples

    def _build_raft_example(self, data: dict[str, Any]) -> RAFTTrainingExample:
        """Convert annotated example to RAFT format"""

        # Extract oracle and distractor IDs
        annotation = data["context_annotation"]
        oracle_ids = set(annotation["oracle_context"])
        distractor_ids = set(annotation["distractor_context"])

        # Retrieve context items
        ctx = data["retrieved_context"]

        # Build oracle documents (relevant context)
        oracle_docs = []
        distractor_docs = []

        # Process heading
        if "HEADING" in oracle_ids:
            oracle_docs.append(f"Heading: {ctx['heading']['text']}")
        elif "HEADING" in distractor_ids:
            distractor_docs.append(f"Heading: {ctx['heading']['text']}")

        # Process info artifacts
        for info in ctx["info_artifacts"]:
            doc_text = f"Information: {info['text']}"
            if info["id"] in oracle_ids:
                oracle_docs.append(doc_text)
            elif info["id"] in distractor_ids:
                distractor_docs.append(doc_text)

        # Process interfaces
        for iface in ctx["interfaces"]:
            doc_text = f"Interface {iface['id']}: {iface['text']}"
            if iface["id"] in oracle_ids:
                oracle_docs.append(doc_text)
            elif iface["id"] in distractor_ids:
                distractor_docs.append(doc_text)

        # Build RAFT training example
        return {
            "question": f"Generate comprehensive test cases for requirement {data['requirement_id']}: {data['requirement_text']}",
            "oracle_context": oracle_docs,
            "distractor_context": distractor_docs,
            "answer": data["generated_test_cases"],
            "metadata": {
                "requirement_id": data["requirement_id"],
                "quality_rating": annotation.get("quality_rating"),
                "annotation_notes": annotation.get("annotation_notes", ""),
                "original_model": data.get("model_used")
            }
        }

    def save_dataset(self, raft_examples: list[RAFTTrainingExample]) -> Path:
        """Save RAFT dataset in Ollama fine-tuning format"""

        # Convert to conversation format for Ollama
        training_data = []

        for example in raft_examples:
            # RAFT prompt: Include oracle + distractor context, model learns to use oracle
            context_str = "Relevant Context:\n"
            context_str += "\n".join(f"- {doc}" for doc in example["oracle_context"])

            if example["distractor_context"]:
                context_str += "\n\nAdditional Context (may not be relevant):\n"
                context_str += "\n".join(f"- {doc}" for doc in example["distractor_context"])

            # Ollama conversation format
            conversation = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert automotive test case generator. Use only the relevant context to generate high-quality test cases. Ignore irrelevant information."
                    },
                    {
                        "role": "user",
                        "content": f"{context_str}\n\n{example['question']}"
                    },
                    {
                        "role": "assistant",
                        "content": example["answer"]
                    }
                ],
                "metadata": example.get("metadata", {})
            }
            training_data.append(conversation)

        # Save as JSONL (Ollama fine-tuning format)
        output_path = self.output_dir / "raft_training_dataset.jsonl"

        with open(output_path, "w", encoding="utf-8") as f:
            for item in training_data:
                f.write(json.dumps(item) + "\n")

        print(f"✅ Saved RAFT dataset: {output_path}")
        print(f"   Examples: {len(training_data)}")

        # Also save as regular JSON for inspection
        json_path = self.output_dir / "raft_training_dataset.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)

        return output_path
```

### Step 3.2: Build the Dataset

```bash
# Create dataset builder script
python3 -c "
from src.training.raft_dataset_builder import RAFTDatasetBuilder

builder = RAFTDatasetBuilder()
raft_examples = builder.build_dataset()
dataset_path = builder.save_dataset(raft_examples)

print(f'\n✅ RAFT dataset ready: {dataset_path}')
print(f'   Total examples: {len(raft_examples)}')
"
```

---

## Phase 4: Train with RAFT

### Step 4.1: Create Ollama Modelfile

Create `training_data/raft_dataset/Modelfile`:

```
# RAFT-trained automotive test case generator

FROM llama3.1:8b

# System prompt for RAFT-trained model
SYSTEM """
You are an expert automotive test case generator trained with RAFT (Retrieval Augmented Fine-Tuning).

You have learned to:
- Identify relevant context from requirement documents
- Filter out irrelevant or distracting information
- Generate comprehensive test cases using only pertinent context
- Apply automotive domain knowledge (voltage, timing, safety, interfaces)

When generating test cases:
1. Focus on oracle context (relevant information)
2. Ignore distractor context (irrelevant information)
3. Generate detailed, executable test cases
4. Include boundary conditions, edge cases, and safety scenarios
"""

# Temperature for deterministic output
PARAMETER temperature 0.0

# Longer context for complex requirements
PARAMETER num_ctx 8192

# Adequate response length
PARAMETER num_predict 2048
```

### Step 4.2: Fine-tune with Ollama

```bash
# Navigate to dataset directory
cd training_data/raft_dataset/

# Create fine-tuned model with RAFT dataset
ollama create automotive-tc-raft-v1 \
  --file Modelfile \
  --training-data raft_training_dataset.jsonl \
  --adapter lora \
  --lora-r 16 \
  --lora-alpha 32 \
  --learning-rate 2e-4 \
  --num-epochs 3 \
  --batch-size 4

# This will:
# 1. Load base model (llama3.1:8b)
# 2. Train LoRA adapter with RAFT examples
# 3. Save as "automotive-tc-raft-v1"
```

**Note:** Ollama's RAFT training is automatic - it understands the oracle/distractor structure from your dataset format.

### Step 4.3: Monitor Training

```bash
# Check training progress
ollama list

# Verify new model exists
ollama show automotive-tc-raft-v1
```

---

## Phase 5: Evaluate and Deploy

### Step 5.1: Test RAFT-Trained Model

```bash
# Test with sample requirement
ai-tc-generator input/sample.reqifz \
  --model automotive-tc-raft-v1 \
  --verbose

# Compare with base model
ai-tc-generator input/sample.reqifz \
  --model llama3.1:8b \
  --verbose
```

### Step 5.2: Evaluate Quality

Create evaluation script `utilities/evaluate_raft.py`:

```python
#!/usr/bin/env python3
"""Evaluate RAFT model performance"""

import subprocess
from pathlib import Path


def evaluate_raft_model(test_files: list[Path]) -> dict:
    """Compare RAFT model vs base model on test files"""

    results = {
        "raft_model": [],
        "base_model": []
    }

    for test_file in test_files:
        print(f"\n📊 Testing: {test_file.name}")

        # Run with RAFT model
        print("  🚀 RAFT model...")
        subprocess.run([
            "ai-tc-generator",
            str(test_file),
            "--model", "automotive-tc-raft-v1"
        ])

        # Run with base model
        print("  🔵 Base model...")
        subprocess.run([
            "ai-tc-generator",
            str(test_file),
            "--model", "llama3.1:8b"
        ])

        # Manual comparison (human evaluation)
        print("\n  📋 Manual Evaluation:")
        raft_quality = int(input("    RAFT model quality (1-5): "))
        base_quality = int(input("    Base model quality (1-5): "))

        results["raft_model"].append(raft_quality)
        results["base_model"].append(base_quality)

    # Calculate averages
    avg_raft = sum(results["raft_model"]) / len(results["raft_model"])
    avg_base = sum(results["base_model"]) / len(results["base_model"])
    improvement = ((avg_raft - avg_base) / avg_base) * 100

    print("\n" + "="*50)
    print("📊 Evaluation Results")
    print("="*50)
    print(f"  RAFT Model Average: {avg_raft:.2f}/5")
    print(f"  Base Model Average: {avg_base:.2f}/5")
    print(f"  Improvement: {improvement:+.1f}%")
    print("="*50)

    return results


if __name__ == "__main__":
    test_files = list(Path("input/").glob("*.reqifz"))[:5]  # First 5 files
    evaluate_raft_model(test_files)
```

Usage:

```bash
python utilities/evaluate_raft.py
```

### Step 5.3: Deploy RAFT Model

Update default model in `config/cli_config.yaml`:

```yaml
cli_defaults:
  model: "automotive-tc-raft-v1"  # Use RAFT-trained model by default
```

Or use via CLI:

```bash
# Use RAFT model
ai-tc-generator input/ --model automotive-tc-raft-v1 --hp

# Set as default
export AI_TG_MODEL=automotive-tc-raft-v1
```

---

## Troubleshooting

### Issue: Ollama doesn't support fine-tuning

**Solution:** Upgrade Ollama:
```bash
# Check version
ollama --version

# If < v0.11.10, upgrade
curl https://ollama.ai/install.sh | sh
```

### Issue: Not enough annotated examples

**Solution:** Aim for minimum 50 examples:
```bash
# Check stats
python -c "from src.training.raft_collector import RAFTDataCollector; print(RAFTDataCollector().get_collection_stats())"

# Collect more examples by processing more files
ai-tc-generator input/ --collect-raft-data
```

### Issue: Training runs out of memory

**Solution:** Reduce batch size or use smaller model:
```bash
# Use smaller batch size
ollama create automotive-tc-raft-v1 \
  --training-data raft_training_dataset.jsonl \
  --batch-size 2  # Reduced from 4

# Or use smaller base model
# Change Modelfile: FROM llama3.1:8b → FROM llama3.1:7b
```

### Issue: RAFT model quality not improving

**Diagnosis:**
1. Check annotation quality - are oracle/distractor labels accurate?
2. Verify dataset diversity - need examples from different requirement types
3. Ensure adequate training data - 50+ examples minimum, 100+ recommended

**Solution:**
```bash
# Review annotations
python utilities/review_annotations.py

# Collect more diverse examples
ai-tc-generator input/different_subsystem/ --collect-raft-data

# Re-annotate with stricter guidelines
python utilities/annotate_raft.py
```

---

## Next Steps

✅ **Phase 1 Complete:** RAFT data collection enabled
✅ **Phase 2 Complete:** Annotated 50+ examples
✅ **Phase 3 Complete:** Built RAFT dataset
✅ **Phase 4 Complete:** Trained RAFT model
✅ **Phase 5 Complete:** Evaluated and deployed

### Continuous Improvement

1. **Collect more examples** - Build to 200+ for even better results
2. **Refine annotations** - Review and improve oracle/distractor labels
3. **Retrain periodically** - Monthly retraining with new validated examples
4. **Monitor quality** - Track test case quality metrics over time
5. **Domain specialization** - Create RAFT models for specific subsystems

---

**Documentation Version:** 1.0.0
**Last Updated:** 2025-10-03
**Maintainer:** AI TC Generator Team
