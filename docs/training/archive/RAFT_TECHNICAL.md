# RAFT Technical Implementation
**AI Test Case Generator v2.1.0**

**Last Updated**: 2025-10-31
**Audience**: Developers & Engineers
**Purpose**: Technical implementation details for RAFT fine-tuning

---

## 📑 Table of Contents

1. [RAFT Methodology](#raft-methodology)
2. [System Architecture](#system-architecture)
3. [Implementation](#implementation)
4. [Training Data Format](#training-data-format)
5. [Training Process](#training-process)
6. [Code Integration](#code-integration)
7. [Performance Optimization](#performance-optimization)
8. [Advanced Topics](#advanced-topics)

---

## RAFT Methodology

### Core Concept

**RAFT (Retrieval Augmented Fine-Tuning)** trains models to distinguish:
- **Oracle Context**: Relevant information that should influence generation
- **Distractor Context**: Irrelevant information that should be ignored

### Why RAFT for Automotive Test Generation?

Our system (`BaseProcessor._build_augmented_requirements()`) retrieves:
1. **Heading**: Section context
2. **Info List**: Information artifacts since heading
3. **Interface List**: System interfaces (CAN signals, parameters)

**Problem**: Not all retrieved context is relevant for every requirement.

**RAFT Solution**: Teach AI which context matters for each requirement type.

### Example

**Retrieved Context**:
```python
{
  "heading": "Input Requirements - CAN Signals",
  "info_list": [
    "This section defines CAN signals for ACC system",
    "Previous section covered voltage monitoring"  # Distractor!
  ],
  "interface_list": [
    {"id": "IF_001", "text": "CANSignal - ACCSP (Message: FCM1S39)"},  # Oracle!
    {"id": "IF_002", "text": "VoltageParameter - BattVolt"}  # Distractor!
  ]
}
```

**RAFT Training Labels**:
```python
{
  "oracle_context": [
    "This section defines CAN signals for ACC system",
    "CANSignal - ACCSP (Message: FCM1S39)"
  ],
  "distractor_context": [
    "Previous section covered voltage monitoring",
    "VoltageParameter - BattVolt"
  ]
}
```

---

## System Architecture

### Data Flow

```
Requirement Processing
    ↓
Context Retrieval (BaseProcessor)
    ↓
[IF enable_raft=True]
    ↓
RAFT Data Collector
    ├─ Capture requirement
    ├─ Capture context
    ├─ Capture generated test cases
    ├─ Calculate quality score
    └─ Save to training_data/collected/
    ↓
Continue Normal Processing
```

### Non-Invasive Design

**Key Principle**: RAFT collection happens AFTER test case generation

```python
# src/processors/standard_processor.py
def process_file(self, reqifz_path, model, template, output_dir):
    # 1. Extract artifacts
    artifacts = extractor.extract_reqifz_content(reqifz_path)

    # 2. Build augmented requirements
    augmented_requirements = self._build_augmented_requirements(artifacts)

    # 3. Generate test cases (normal flow)
    test_cases = generator.generate_test_cases_batch(augmented_requirements)

    # 4. Collect RAFT data (if enabled)
    if self.config.training.enable_raft:
        raft_collector.collect_examples(augmented_requirements, test_cases)

    # 5. Format and save
    formatter.format_to_excel(test_cases, output_path)
```

**Benefits**:
- Zero impact on core logic
- Can be enabled/disabled without code changes
- No performance penalty when disabled

---

## Implementation

### File Structure

```
src/training/
├── __init__.py
├── raft_collector.py          # RAFT data collection
├── raft_dataset_builder.py    # Dataset preparation
├── raft_trainer.py            # Training orchestration
└── raft_evaluator.py          # Model evaluation

training_data/
├── collected/                 # Raw RAFT examples
│   └── example_001.json
├── annotated/                 # Human-annotated examples
│   └── example_001_annotated.json
├── exports/                   # Training datasets
│   ├── raft_training_dataset.json
│   └── raft_validation_dataset.json
└── models/                    # Trained models
    └── automotive-tc-raft-v1/
```

### RAFTDataCollector Implementation

**File**: `src/training/raft_collector.py`

```python
"""RAFT data collector for AI Test Case Generator."""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any
import json
from datetime import datetime

@dataclass
class RAFTExample:
    """Structure for RAFT training examples."""
    requirement_id: str
    requirement_text: str
    heading: str
    retrieved_context: Dict[str, Any]  # All context items
    generated_test_cases: str
    model_used: str
    generation_timestamp: str
    context_annotation: Dict[str, List[str]] = None  # Oracle/distractor labels

    def __post_init__(self):
        if self.context_annotation is None:
            self.context_annotation = {
                "oracle_context": [],
                "distractor_context": [],
                "annotation_notes": "",
                "quality_rating": None
            }

class RAFTDataCollector:
    """Collects RAFT training examples from processing operations."""

    def __init__(self, config, logger):
        self.config = config.training
        self.logger = logger
        self.output_dir = Path(self.config.training_data_dir) / "collected"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect_example(
        self,
        requirement: Dict[str, Any],
        test_cases: List[Dict[str, Any]],
        model_name: str
    ) -> None:
        """Collect a single RAFT example."""
        if not self.config.enable_raft:
            return

        # Build retrieved context structure
        retrieved_context = {
            "heading": {
                "id": "HEADING",
                "text": requirement.get("heading", "No Heading")
            },
            "info_artifacts": [
                {"id": f"INFO_{i}", "text": info.get("text", "")}
                for i, info in enumerate(requirement.get("info_list", []))
            ],
            "interfaces": [
                {"id": interface.get("id", f"IF_{i}"), "text": interface.get("text", "")}
                for i, interface in enumerate(requirement.get("interface_list", []))
            ]
        }

        # Create RAFT example
        example = RAFTExample(
            requirement_id=requirement.get("id", "UNKNOWN"),
            requirement_text=requirement.get("text", ""),
            heading=requirement.get("heading", "No Heading"),
            retrieved_context=retrieved_context,
            generated_test_cases=json.dumps(test_cases, indent=2),
            model_used=model_name,
            generation_timestamp=datetime.now().isoformat()
        )

        # Save to disk
        self._save_example(example)

    def _save_example(self, example: RAFTExample) -> None:
        """Save RAFT example to JSON file."""
        filename = f"raft_example_{example.requirement_id}_{int(datetime.now().timestamp())}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(example), f, indent=2, ensure_ascii=False)

        self.logger.debug(f"Saved RAFT example: {filename}")
```

### Integration Points

**1. Standard Processor Integration**

```python
# src/processors/standard_processor.py

from ..training.raft_collector import RAFTDataCollector

class REQIFZFileProcessor(BaseProcessor):
    def __init__(self, config, logger):
        super().__init__(config, logger)
        # Initialize RAFT collector if enabled
        if self.config.training.enable_raft:
            self.raft_collector = RAFTDataCollector(config, logger)
        else:
            self.raft_collector = None

    def process_file(self, reqifz_path, model, template, output_dir):
        # ... existing extraction and generation code ...

        # Collect RAFT examples after generation
        if self.raft_collector:
            for requirement, test_case_list in zip(augmented_requirements, all_test_cases):
                self.raft_collector.collect_example(requirement, test_case_list, model)

        # ... existing formatting and output code ...
```

**2. HP Processor Integration**

```python
# src/processors/hp_processor.py

async def process_file(self, reqifz_path, model, template, output_dir):
    # ... existing async processing ...

    # Collect RAFT examples asynchronously
    if self.raft_collector:
        for requirement, test_case_list in zip(augmented_requirements, batch_results):
            self.raft_collector.collect_example(requirement, test_case_list, model)
```

---

## Training Data Format

### Raw RAFT Example

```json
{
  "requirement_id": "TFDCX32348-18153",
  "requirement_text": "System shall process ACCSP signal when ignition ON",
  "heading": "Input Requirements - CAN Signals",
  "retrieved_context": {
    "heading": {
      "id": "HEADING",
      "text": "Input Requirements - CAN Signals"
    },
    "info_artifacts": [
      {
        "id": "INFO_0",
        "text": "This section defines CAN signals for ACC system"
      },
      {
        "id": "INFO_1",
        "text": "Previous section covered voltage monitoring specs"
      }
    ],
    "interfaces": [
      {
        "id": "IF_001",
        "text": "CANSignal - ACCSP (Message Label: FCM1S39)"
      },
      {
        "id": "IF_002",
        "text": "CANSignal - ACCSPST1 (Message Label: FCM1S39)"
      },
      {
        "id": "IF_003",
        "text": "VoltageParameter - BattVolt"
      }
    ]
  },
  "generated_test_cases": "[{...test cases...}]",
  "model_used": "llama3.1:8b",
  "generation_timestamp": "2025-10-31T10:30:00",
  "context_annotation": {
    "oracle_context": [],      // To be filled by expert
    "distractor_context": [],  // To be filled by expert
    "annotation_notes": "",
    "quality_rating": null
  }
}
```

### Annotated RAFT Example

```json
{
  "requirement_id": "TFDCX32348-18153",
  "requirement_text": "System shall process ACCSP signal when ignition ON",
  "retrieved_context": { ... },
  "context_annotation": {
    "oracle_context": [
      "HEADING",           // Section context relevant
      "INFO_0",           // ACC system info relevant
      "IF_001",           // ACCSP signal is the requirement subject
      "IF_002"            // ACCSPST1 related to ACC system
    ],
    "distractor_context": [
      "INFO_1",           // Voltage monitoring unrelated
      "IF_003"            // BattVolt unrelated to ACC signals
    ],
    "annotation_notes": "Requirement focuses on ACCSP signal processing. Voltage monitoring from previous section is noise.",
    "quality_rating": 0.95
  },
  "validation_status": "approved"
}
```

### RAFT Training Dataset Format

```json
{
  "examples": [
    {
      "question": "Generate test cases for the following automotive requirement:\n\nRequirement: System shall process ACCSP signal when ignition ON\n\nGenerate comprehensive test cases covering positive, negative, and edge cases.",
      "context": [
        {
          "id": "HEADING",
          "text": "Input Requirements - CAN Signals",
          "type": "oracle"
        },
        {
          "id": "INFO_0",
          "text": "This section defines CAN signals for ACC system",
          "type": "oracle"
        },
        {
          "id": "INFO_1",
          "text": "Previous section covered voltage monitoring specs",
          "type": "distractor"
        },
        {
          "id": "IF_001",
          "text": "CANSignal - ACCSP (Message Label: FCM1S39)",
          "type": "oracle"
        },
        {
          "id": "IF_003",
          "text": "VoltageParameter - BattVolt",
          "type": "distractor"
        }
      ],
      "answer": "[{...generated test cases using ACCSP and FCM1S39...}]"
    }
  ]
}
```

---

## Training Process

### Dataset Preparation

**File**: `src/training/raft_dataset_builder.py`

```python
"""Build RAFT training datasets from annotated examples."""

def build_raft_dataset(annotated_examples: List[Dict]) -> Dict:
    """Convert annotated examples to RAFT training format."""
    training_examples = []

    for example in annotated_examples:
        # Build question (prompt)
        question = f"""Generate test cases for the following automotive requirement:

Requirement: {example['requirement_text']}

Generate comprehensive test cases covering positive, negative, and edge cases."""

        # Build context with oracle/distractor labels
        context = []

        # Add heading
        heading = example['retrieved_context']['heading']
        is_oracle = heading['id'] in example['context_annotation']['oracle_context']
        context.append({
            "id": heading['id'],
            "text": heading['text'],
            "type": "oracle" if is_oracle else "distractor"
        })

        # Add info artifacts
        for info in example['retrieved_context']['info_artifacts']:
            is_oracle = info['id'] in example['context_annotation']['oracle_context']
            context.append({
                "id": info['id'],
                "text": info['text'],
                "type": "oracle" if is_oracle else "distractor"
            })

        # Add interfaces
        for interface in example['retrieved_context']['interfaces']:
            is_oracle = interface['id'] in example['context_annotation']['oracle_context']
            context.append({
                "id": interface['id'],
                "text": interface['text'],
                "type": "oracle" if is_oracle else "distractor"
            })

        # Add to training set
        training_examples.append({
            "question": question,
            "context": context,
            "answer": example['generated_test_cases']
        })

    return {"examples": training_examples}
```

### Training Configuration

```yaml
# training_config.yaml
raft_training:
  base_model: "llama3.1:8b"
  output_model: "automotive-tc-raft-v1"

  # Training hyperparameters
  learning_rate: 2.0e-5
  num_epochs: 3
  batch_size: 4
  gradient_accumulation_steps: 2
  warmup_steps: 100
  max_seq_length: 16384  # Match Ollama context window

  # RAFT-specific
  oracle_probability: 0.8  # Probability of including oracle docs
  distractor_ratio: 1.5    # Distractors per oracle doc

  # Optimization
  fp16: true               # Mixed precision training
  gradient_checkpointing: true
  dataloader_num_workers: 4
```

### Training Script

**File**: `src/training/raft_trainer.py`

```python
"""RAFT model training orchestration."""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from peft import get_peft_model, LoraConfig, TaskType

def train_raft_model(config_path: str, dataset_path: str, output_dir: str):
    """Train RAFT model using prepared dataset."""

    # 1. Load base model
    model = AutoModelForCausalLM.from_pretrained(
        "meta-llama/Llama-3.1-8B",
        torch_dtype=torch.float16,
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B")

    # 2. Configure LoRA for parameter-efficient training
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )
    model = get_peft_model(model, lora_config)

    # 3. Load RAFT dataset
    dataset = load_raft_dataset(dataset_path)

    # 4. Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=2,
        learning_rate=2e-5,
        warmup_steps=100,
        logging_steps=10,
        save_steps=500,
        fp16=True,
        gradient_checkpointing=True
    )

    # 5. Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset['train'],
        eval_dataset=dataset['validation']
    )

    # 6. Train
    trainer.train()

    # 7. Save model
    model.save_pretrained(f"{output_dir}/final_model")
    tokenizer.save_pretrained(f"{output_dir}/final_model")
```

---

## Code Integration

### Configuration Updates

**File**: `src/config.py`

```python
class TrainingConfig(BaseModel):
    """Training and fine-tuning configuration."""

    # RAFT data collection
    enable_raft: bool = Field(False, description="Enable RAFT data collection")
    collect_training_data: bool = Field(False, description="Collect training examples")
    training_data_dir: str = Field("training_data", description="Training data directory")

    # RAFT-specific settings
    raft_collect_context: bool = Field(True, description="Collect context for RAFT")
    raft_min_oracle_docs: int = Field(1, ge=1, description="Minimum oracle documents")
    raft_min_distractor_docs: int = Field(1, ge=0, description="Minimum distractors")
    raft_context_window: int = Field(5, ge=1, description="Max context items")

    # Quality thresholds
    min_quality_score: float = Field(0.7, ge=0.0, le=1.0)
    auto_approve_threshold: float = Field(0.9, ge=0.0, le=1.0)
```

### CLI Commands

**File**: `main.py`

```python
# New CLI arguments for RAFT
parser.add_argument(
    "--train-raft",
    action="store_true",
    help="Train RAFT model from annotated data"
)

parser.add_argument(
    "--annotate-training-data",
    action="store_true",
    help="Start annotation UI for collected examples"
)

parser.add_argument(
    "--export-training-data",
    action="store_true",
    help="Export annotated data to training format"
)

parser.add_argument(
    "--evaluate-model",
    type=str,
    metavar="MODEL",
    help="Evaluate trained model quality"
)
```

---

## Performance Optimization

### Training Performance

**Expected Times** (llama3.1:8b on RTX 3090):
- **Data Collection**: Real-time (0 overhead when disabled)
- **Annotation**: 2-4 hours (manual, 100 examples)
- **Dataset Export**: <1 minute
- **Training**: 2-8 hours (100-500 examples, 3 epochs)
- **Evaluation**: 30-60 minutes

### Memory Optimization

```python
# Use gradient checkpointing to save VRAM
training_args = TrainingArguments(
    gradient_checkpointing=True,  # Trade compute for memory
    fp16=True,                    # Half precision
    per_device_train_batch_size=4  # Adjust based on VRAM
)
```

### Training Acceleration

1. **Mixed Precision**: Automatic with `fp16=True`
2. **Gradient Accumulation**: Effective larger batch size
3. **LoRA**: 10x faster than full fine-tuning
4. **DataLoader Workers**: Parallel data loading

---

## Advanced Topics

### Custom Context Selection

Override context retrieval for specific requirement types:

```python
def _build_augmented_requirements_raft_aware(self, artifacts):
    """RAFT-aware context augmentation."""
    # ... existing logic ...

    # Add RAFT metadata for filtering
    augmented_requirement.update({
        "raft_metadata": {
            "context_relevance_scores": self._score_context_relevance(obj, context),
            "suggested_oracle": [ctx for ctx, score in scores if score > 0.7],
            "suggested_distractor": [ctx for ctx, score in scores if score < 0.3]
        }
    })
```

### Quality Scoring

Automatic quality estimation:

```python
def calculate_quality_score(test_cases, requirement):
    """Estimate test case quality automatically."""
    score = 0.0

    # Check signal name accuracy (from interface list)
    signals_in_requirement = extract_signal_names(requirement['interface_list'])
    signals_in_test_cases = extract_signal_names_from_tests(test_cases)
    accuracy = len(set(signals_in_requirement) & set(signals_in_test_cases)) / len(signals_in_requirement)
    score += accuracy * 0.4

    # Check test coverage
    coverage = estimate_coverage(test_cases)
    score += coverage * 0.3

    # Check automotive terminology
    term_usage = check_automotive_terms(test_cases)
    score += term_usage * 0.3

    return min(score, 1.0)
```

### Continuous Learning Pipeline

```python
# Automated monthly retraining
def monthly_retraining_workflow():
    # 1. Collect examples from last month
    examples = collect_examples(since=last_month)

    # 2. Filter high-quality examples (auto-approve > 0.9)
    high_quality = [ex for ex in examples if ex['quality_score'] > 0.9]

    # 3. Combine with existing training set
    combined_dataset = merge_datasets(existing_dataset, high_quality)

    # 4. Retrain model
    new_model = train_raft_model(combined_dataset)

    # 5. Evaluate
    metrics = evaluate_model(new_model, validation_set)

    # 6. Deploy if improved
    if metrics['quality_score'] > current_model_quality + 0.05:
        deploy_model(new_model)
```

---

## Next Steps

1. Review `docs/training/TRAINING_GUIDE.md` for user-facing workflow
2. Implement `RAFTDataCollector` in processors
3. Enable collection and process test files
4. Annotate initial dataset (50-100 examples)
5. Train first RAFT model
6. Evaluate and iterate

---

**Document Version**: 1.0
**Last Updated**: 2025-10-31
**Status**: Implementation-Ready ✅
