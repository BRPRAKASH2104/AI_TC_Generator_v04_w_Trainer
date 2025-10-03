# Training Data Directory

This directory contains RAFT (Retrieval Augmented Fine-Tuning) training data for the AI Test Case Generator.

## Directory Structure

```
training_data/
├── collected/          # Raw RAFT examples collected during test case generation
├── validated/          # Annotated examples accepted for training
├── rejected/           # Annotated examples rejected (poor quality)
└── raft_dataset/       # Final RAFT training datasets (JSONL/JSON format)
```

## Workflow

1. **Collection** (`collected/`):
   - Enable RAFT collection: Set `enable_raft: true` in config or use env var
   - Run test case generation normally
   - RAFT examples saved automatically to `collected/`

2. **Annotation** (`validated/` or `rejected/`):
   - Run: `python utilities/annotate_raft.py`
   - Mark context as oracle (relevant) or distractor (irrelevant)
   - Rate quality (1-5 scale)
   - Examples moved to `validated/` (if accepted) or `rejected/` (if rejected)

3. **Dataset Building** (`raft_dataset/`):
   - Build RAFT dataset from annotated examples
   - Converts to Ollama fine-tuning format (JSONL)
   - Minimum 50 validated examples recommended

4. **Training**:
   - Use `raft_training_dataset.jsonl` to train custom model
   - Fine-tune with LoRA using Ollama
   - Deploy RAFT-trained model for better performance

## RAFT Data Format

### Collected Example (`collected/*.json`)

```json
{
  "requirement_id": "REQ_001",
  "requirement_text": "Door lock shall...",
  "heading": "Door Control System",
  "retrieved_context": {
    "heading": {"id": "HEADING", "text": "Door Control System"},
    "info_artifacts": [
      {"id": "INFO_001", "text": "CAN-based signals..."}
    ],
    "interfaces": [
      {"id": "IF_BCM_001", "text": "Body Control Module"}
    ]
  },
  "generated_test_cases": "...",
  "context_annotation": {
    "oracle_context": [],       // To be filled
    "distractor_context": [],   // To be filled
    "annotation_notes": "",
    "quality_rating": null
  },
  "validation_status": "pending"
}
```

### Annotated Example (`validated/*.json` or `rejected/*.json`)

Same structure, but with filled annotation:

```json
{
  "context_annotation": {
    "oracle_context": ["HEADING", "INFO_001", "IF_BCM_001"],
    "distractor_context": ["INFO_002"],
    "annotation_notes": "CAN signals and BCM interface were critical",
    "quality_rating": 4
  },
  "validation_status": "validated",
  "annotated_by": "john_doe",
  "annotation_timestamp": "2025-10-03T14:30:00"
}
```

### RAFT Training Dataset (`raft_dataset/*.jsonl`)

Ollama fine-tuning format:

```jsonl
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}], "metadata": {...}}
```

## Best Practices

1. **Aim for 50+ validated examples** for minimum quality improvements
2. **100+ examples** recommended for production-quality RAFT models
3. **Diverse examples** from different requirement types improve generalization
4. **Consistent annotation** - follow annotation guidelines strictly
5. **Regular retraining** - collect new examples and retrain monthly

## See Also

- `docs/RAFT_SETUP_GUIDE.md` - Complete RAFT implementation guide
- `Trainer.md` - Training philosophy and workflow
- `utilities/annotate_raft.py` - Interactive annotation tool
