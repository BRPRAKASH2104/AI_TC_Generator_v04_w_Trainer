# Model Training and Fine-Tuning Guide

This document provides comprehensive guidance for training and fine-tuning AI models for the AI Test Case Generator system.

## 📋 Table of Contents

- [Overview](#overview)
- [Training Infrastructure](#training-infrastructure)
- [Prerequisites](#prerequisites)
- [Data Collection](#data-collection)
- [Fine-Tuning Methods](#fine-tuning-methods)
- [Training Workflows](#training-workflows)
- [Model Evaluation](#model-evaluation)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Overview

The AI Test Case Generator supports multiple approaches for model customization and training:

1. **LoRA Fine-Tuning**: Parameter-efficient fine-tuning using Low-Rank Adaptation
2. **Custom Model Training**: Full model training for domain-specific requirements
3. **Prompt Engineering**: Template-based prompt optimization
4. **Training Data Collection**: Automated collection of high-quality training examples

### Supported Models

- **Primary**: LLaMA 3.1 8B (via Ollama)
- **Advanced**: DeepSeek Coder v2 16B
- **Custom**: Any Ollama-compatible model

## Training Infrastructure

### Directory Structure

```
training_data/
├── collected/          # Automatically collected training examples
├── validated/          # Human-validated high-quality examples
├── rejected/           # Low-quality examples for negative training
└── exports/           # Processed datasets for training

src/config.py          # Training configuration settings
prompts/               # Prompt templates for training data generation
```

### Configuration Overview

Training settings are managed through the `TrainingConfig` class in `src/config.py`:

```python
class TrainingConfig(BaseModel):
    # Data collection
    collect_training_data: bool = False
    training_data_dir: str = "training_data"
    auto_approve_threshold: float = 0.9
    min_examples_for_training: int = 50

    # LoRA parameters
    lora_r: int = 16
    lora_alpha: int = 32
    learning_rate: float = 2e-4

    # Model settings
    enable_custom_models: bool = False
    custom_model_prefix: str = "automotive-test-"
    retraining_schedule: str = "weekly"
```

## Prerequisites

### System Requirements

- **Python**: 3.13.7+
- **GPU**: NVIDIA GPU with 8GB+ VRAM (recommended)
- **RAM**: 16GB+ system memory
- **Storage**: 50GB+ free space for model storage

### Installation

**Option 1: Training Dependencies Only**
```bash
pip install -e .[training]
```

**Option 2: Complete Development Environment**
```bash
pip install -e .[all]
```

### Core Training Dependencies

The training environment includes:

```python
training = [
    "torch>=2.1.0",           # PyTorch deep learning framework
    "transformers>=4.35.0",   # Hugging Face transformers
    "peft>=0.6.0",           # Parameter-Efficient Fine-Tuning
    "datasets>=2.14.0",      # Dataset processing
    "wandb>=0.16.0",         # Experiment tracking
]
```

## Data Collection

### Automatic Data Collection

Enable automatic training data collection:

```bash
# Enable in configuration
export AI_TG_COLLECT_TRAINING_DATA=true
export AI_TG_AUTO_APPROVE_THRESHOLD=0.9

# Run with data collection
ai-tc-generator input/ --verbose
```

### Manual Data Curation

1. **Collect Examples**:
   ```bash
   # Process files and collect training data
   ai-tc-generator input/automotive_examples/ --collect-training-data
   ```

2. **Review Collected Data**:
   ```bash
   ls training_data/collected/
   # Review JSON files for quality
   ```

3. **Validate Examples**:
   ```bash
   # Move high-quality examples to validated/
   mv training_data/collected/high_quality_*.json training_data/validated/

   # Move low-quality examples to rejected/
   mv training_data/collected/low_quality_*.json training_data/rejected/
   ```

### Training Data Format

Training examples follow this structure:

```json
{
  "id": "requirement_SR_001",
  "requirement_text": "The system shall detect door closure within 100ms",
  "requirement_type": "System Requirement",
  "context": {
    "domain": "automotive",
    "subsystem": "door_control",
    "safety_level": "ASIL-B"
  },
  "test_cases": [
    {
      "test_id": "TC_SR_001_01",
      "description": "Verify door closure detection timing",
      "preconditions": "Door is open, system is active",
      "test_steps": [
        "Close the door",
        "Measure detection time"
      ],
      "expected_result": "Detection occurs within 100ms",
      "test_type": "Functional"
    }
  ],
  "quality_score": 0.95,
  "human_validated": true
}
```

## Fine-Tuning Methods

### 1. LoRA Fine-Tuning (Recommended)

LoRA (Low-Rank Adaptation) provides efficient fine-tuning with minimal computational requirements.

**Configuration**:
```python
# In src/config.py
training = TrainingConfig(
    lora_r=16,              # Rank of adaptation
    lora_alpha=32,          # Scaling parameter
    learning_rate=2e-4,     # Learning rate
    enable_custom_models=True
)
```

**Training Script**:
```python
from src.training.lora_trainer import LoRATrainer

# Initialize trainer
trainer = LoRATrainer(
    base_model="llama3.1:8b",
    training_data_dir="training_data/validated",
    output_dir="models/automotive-test-llama3.1-8b-lora"
)

# Start training
trainer.train(
    num_epochs=3,
    batch_size=4,
    gradient_accumulation_steps=4
)
```

### 2. Full Model Fine-Tuning

For specialized domains requiring extensive customization:

```python
from src.training.full_trainer import FullModelTrainer

trainer = FullModelTrainer(
    base_model="deepseek-coder-v2:16b",
    training_data_dir="training_data/validated",
    output_dir="models/automotive-deepseek-custom"
)

trainer.train(
    num_epochs=1,
    batch_size=2,
    learning_rate=1e-5
)
```

### 3. Prompt Engineering

Optimize prompts without model training:

```bash
# Test different prompt templates
ai-tc-generator input/ --template automotive_v3 --performance
ai-tc-generator input/ --template safety_critical_v2 --performance

# Validate prompt effectiveness
ai-tc-generator --validate-prompts --verbose
```

## Training Workflows

### Basic Training Workflow

1. **Data Collection Phase**:
   ```bash
   # Collect training data over time
   ai-tc-generator input/batch1/ --collect-training-data
   ai-tc-generator input/batch2/ --collect-training-data
   ```

2. **Data Validation Phase**:
   ```bash
   # Review and validate collected data
   python utilities/validate_training_data.py
   ```

3. **Training Phase**:
   ```bash
   # Train LoRA adapter
   python src/training/train_lora.py --config automotive_config.yaml
   ```

4. **Evaluation Phase**:
   ```bash
   # Evaluate trained model
   python src/training/evaluate_model.py --model automotive-test-llama3.1-8b-lora
   ```

### Advanced Training Pipeline

```bash
# 1. Comprehensive data collection
export AI_TG_COLLECT_TRAINING_DATA=true
export AI_TG_MIN_EXAMPLES_FOR_TRAINING=100

# 2. Process multiple domains
ai-tc-generator input/automotive/ --collect-training-data
ai-tc-generator input/aerospace/ --collect-training-data
ai-tc-generator input/medical/ --collect-training-data

# 3. Automated training pipeline
python scripts/automated_training_pipeline.py \
    --data-dir training_data/validated \
    --model-type lora \
    --experiment-name automotive_v1 \
    --wandb-project ai-test-generator

# 4. Model deployment
python scripts/deploy_model.py \
    --model-path models/automotive-test-llama3.1-8b-lora \
    --deployment-type ollama
```

## Model Evaluation

### Evaluation Metrics

1. **Quality Metrics**:
   - Test case relevance score
   - Coverage completeness
   - Edge case identification

2. **Performance Metrics**:
   - Generation speed (test cases/second)
   - Memory usage
   - Token efficiency

3. **Domain Metrics**:
   - Automotive domain accuracy
   - Safety requirement coverage
   - Compliance verification

### Evaluation Scripts

```bash
# Comprehensive evaluation
python src/evaluation/evaluate_model.py \
    --model automotive-test-llama3.1-8b-lora \
    --test-set evaluation_data/automotive_test_set.json \
    --metrics quality,performance,domain

# Comparative evaluation
python src/evaluation/compare_models.py \
    --baseline llama3.1:8b \
    --custom automotive-test-llama3.1-8b-lora \
    --test-set evaluation_data/
```

### Evaluation Results Format

```json
{
  "model_name": "automotive-test-llama3.1-8b-lora",
  "evaluation_date": "2025-09-19",
  "metrics": {
    "quality": {
      "relevance_score": 0.92,
      "completeness_score": 0.88,
      "edge_case_coverage": 0.85
    },
    "performance": {
      "generation_speed": 12.5,
      "memory_usage_mb": 4200,
      "tokens_per_second": 45
    },
    "domain": {
      "automotive_accuracy": 0.94,
      "safety_coverage": 0.91,
      "compliance_score": 0.89
    }
  }
}
```

## Deployment

### Ollama Integration

Deploy custom models to Ollama:

```bash
# Create Ollama model file
cat > automotive-test-model.modelfile << EOF
FROM llama3.1:8b
ADAPTER ./models/automotive-test-llama3.1-8b-lora
PARAMETER temperature 0.0
PARAMETER num_ctx 8192
PARAMETER num_predict 2048
SYSTEM """You are an expert automotive test case generator specializing in safety-critical requirements and ASIL compliance."""
EOF

# Import to Ollama
ollama create automotive-test:latest -f automotive-test-model.modelfile

# Test deployment
ai-tc-generator input/sample.reqifz --model automotive-test:latest
```

### Production Deployment

```bash
# Validate model performance
python src/evaluation/production_readiness_check.py \
    --model automotive-test:latest \
    --benchmark-suite benchmarks/automotive/

# Deploy to production
ai-tc-generator input/production_data/ \
    --model automotive-test:latest \
    --hp \
    --performance \
    --verbose
```

## Environment Configuration

### Training Environment Variables

```bash
# Core training settings
export AI_TG_COLLECT_TRAINING_DATA=true
export AI_TG_TRAINING_DATA_DIR="training_data"
export AI_TG_MIN_EXAMPLES_FOR_TRAINING=50
export AI_TG_AUTO_APPROVE_THRESHOLD=0.9

# LoRA configuration
export AI_TG_LORA_R=16
export AI_TG_LORA_ALPHA=32
export AI_TG_LEARNING_RATE=2e-4

# Model settings
export AI_TG_ENABLE_CUSTOM_MODELS=true
export AI_TG_CUSTOM_MODEL_PREFIX="automotive-test-"
export AI_TG_RETRAINING_SCHEDULE="weekly"

# Experiment tracking
export WANDB_PROJECT="ai-test-generator"
export WANDB_API_KEY="your_wandb_key"
```

### Hardware Optimization

```bash
# GPU settings
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Memory optimization
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false
```

## Troubleshooting

### Common Issues

**1. CUDA Out of Memory**
```bash
# Reduce batch size
export AI_TG_BATCH_SIZE=2
export AI_TG_GRADIENT_ACCUMULATION_STEPS=8

# Enable gradient checkpointing
export AI_TG_GRADIENT_CHECKPOINTING=true
```

**2. Training Data Quality Issues**
```bash
# Validate training data
python utilities/validate_training_data.py --strict

# Clean low-quality examples
python utilities/clean_training_data.py --threshold 0.8
```

**3. Model Performance Issues**
```bash
# Check model evaluation
python src/evaluation/diagnose_model.py --model automotive-test:latest

# Compare with baseline
python src/evaluation/performance_comparison.py \
    --baseline llama3.1:8b \
    --custom automotive-test:latest
```

### Debug Commands

```bash
# Enable debug logging
export AI_TG_LOG_LEVEL=DEBUG

# Training debug mode
python src/training/train_lora.py --debug --dry-run

# Model inspection
python src/training/inspect_model.py --model automotive-test:latest --verbose
```

### Performance Optimization

```bash
# Optimize training performance
python src/training/optimize_training.py \
    --profile \
    --optimize-memory \
    --optimize-speed

# Benchmark training setup
python src/training/benchmark_setup.py \
    --hardware-check \
    --memory-test \
    --speed-test
```

## Advanced Topics

### Multi-Domain Training

Train models across multiple domains:

```python
# Multi-domain configuration
domains = ["automotive", "aerospace", "medical", "industrial"]

for domain in domains:
    trainer = LoRATrainer(
        base_model="llama3.1:8b",
        training_data_dir=f"training_data/{domain}/validated",
        output_dir=f"models/{domain}-test-llama3.1-8b-lora"
    )
    trainer.train()
```

### Continuous Learning

Implement continuous model improvement:

```bash
# Scheduled retraining
python scripts/continuous_training.py \
    --schedule weekly \
    --min-new-examples 20 \
    --auto-deploy \
    --rollback-on-regression
```

### Model Versioning

Manage model versions:

```bash
# Version model
python src/training/version_model.py \
    --model automotive-test-llama3.1-8b-lora \
    --version v1.2.0 \
    --tag "improved-safety-coverage"

# Deploy specific version
ai-tc-generator input/ --model automotive-test:v1.2.0
```

## Best Practices

1. **Data Quality**: Maintain high-quality training data with human validation
2. **Incremental Training**: Use LoRA for efficient incremental improvements
3. **Evaluation**: Comprehensive evaluation before deployment
4. **Versioning**: Maintain model versions for rollback capability
5. **Monitoring**: Continuous monitoring of model performance in production
6. **Documentation**: Document training procedures and model characteristics

## Security Considerations

- Store training data securely with encryption
- Use environment variables for sensitive configuration
- Validate model outputs for safety-critical applications
- Implement access controls for custom models
- Regular security audits of training pipeline

## Support and Resources

- **Configuration**: See `src/config.py` for all training parameters
- **Examples**: Check `training_data/examples/` for sample data formats
- **Scripts**: Training scripts in `src/training/` directory
- **Evaluation**: Evaluation tools in `src/evaluation/` directory
- **Documentation**: Additional docs in `docs/training/` directory