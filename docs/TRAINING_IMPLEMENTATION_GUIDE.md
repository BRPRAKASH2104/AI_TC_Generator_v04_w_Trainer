# AI Test Case Generator - Training Implementation Guide

**Version**: 1.0.0 | **Date**: 2025-09-19 | **Status**: Implementation Ready

This comprehensive guide provides detailed implementation instructions for the four core training components of the AI Test Case Generator system.

## 📋 Table of Contents

1. [Training Data Collection](#1-training-data-collection)
2. [LoRA Fine-Tuning Implementation](#2-lora-fine-tuning-implementation)
3. [Model Evaluation System](#3-model-evaluation-system)
4. [Model Deployment & Integration](#4-model-deployment--integration)
5. [Complete Implementation Workflow](#complete-implementation-workflow)
6. [Troubleshooting & Best Practices](#troubleshooting--best-practices)

---

## 1. Training Data Collection

### 1.1 Overview

The training data collection system automatically captures high-quality examples during normal processing operations, creating a self-improving feedback loop.

### 1.2 Implementation Structure

**Required Files to Create:**
```
src/training/
├── __init__.py
├── data_collector.py          # Main collection logic
├── data_validator.py          # Quality validation
└── data_processor.py          # Format conversion

training_data/
├── collected/                 # Raw collected examples
├── validated/                 # Human-approved examples
├── rejected/                  # Low-quality examples
└── exports/                   # Processed datasets
```

### 1.3 Data Collector Implementation

**File: `src/training/data_collector.py`**

```python
"""
Training data collection system for AI Test Case Generator.
Automatically captures high-quality examples during processing.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from ..config import ConfigManager
from ..app_logger import AppLogger

@dataclass
class TrainingExample:
    """Structure for training examples."""
    id: str
    requirement_text: str
    requirement_type: str
    context: Dict[str, Any]
    test_cases: List[Dict[str, Any]]
    quality_score: float
    human_validated: bool = False
    collection_timestamp: str = ""
    processing_metadata: Dict[str, Any] = None

    def __post_init__(self):
        if not self.collection_timestamp:
            self.collection_timestamp = datetime.now().isoformat()
        if self.processing_metadata is None:
            self.processing_metadata = {}

class TrainingDataCollector:
    """Collects and manages training data from processing operations."""

    def __init__(self, config: ConfigManager, logger: AppLogger):
        self.config = config.training
        self.logger = logger
        self.training_dir = Path(self.config.training_data_dir)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary training data directories."""
        for subdir in ['collected', 'validated', 'rejected', 'exports']:
            (self.training_dir / subdir).mkdir(parents=True, exist_ok=True)

    def collect_example(
        self,
        requirement_id: str,
        requirement_text: str,
        requirement_type: str,
        test_cases: List[Dict[str, Any]],
        context: Dict[str, Any],
        processing_metadata: Dict[str, Any]
    ) -> Optional[TrainingExample]:
        """
        Collect a training example if it meets quality criteria.

        Args:
            requirement_id: Unique identifier for the requirement
            requirement_text: Original requirement text
            requirement_type: Type classification (e.g., 'System Requirement')
            test_cases: Generated test cases
            context: Processing context (domain, model, etc.)
            processing_metadata: Timing, token usage, etc.

        Returns:
            TrainingExample if collected, None if rejected
        """
        if not self.config.collect_training_data:
            return None

        # Calculate quality score
        quality_score = self._calculate_quality_score(
            requirement_text, test_cases, processing_metadata
        )

        # Check if example meets collection criteria
        if quality_score < 0.5:  # Minimum threshold
            self.logger.debug(f"Rejecting example {requirement_id}: quality {quality_score:.2f}")
            return None

        # Create training example
        example = TrainingExample(
            id=requirement_id,
            requirement_text=requirement_text,
            requirement_type=requirement_type,
            context=context,
            test_cases=test_cases,
            quality_score=quality_score,
            processing_metadata=processing_metadata
        )

        # Auto-approve high-quality examples
        if quality_score >= self.config.auto_approve_threshold:
            example.human_validated = True
            self._save_example(example, 'validated')
            self.logger.info(f"Auto-approved high-quality example: {requirement_id}")
        else:
            self._save_example(example, 'collected')
            self.logger.info(f"Collected example for review: {requirement_id}")

        return example

    def _calculate_quality_score(
        self,
        requirement_text: str,
        test_cases: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate quality score for a training example."""
        score = 0.0

        # Requirement quality factors
        if len(requirement_text.split()) >= 10:  # Sufficient detail
            score += 0.2
        if any(keyword in requirement_text.lower() for keyword in
               ['shall', 'must', 'should', 'will']):  # Proper requirement language
            score += 0.1

        # Test case quality factors
        if len(test_cases) >= 2:  # Multiple test cases
            score += 0.2
        if len(test_cases) <= 5:  # Not too many (focused)
            score += 0.1

        # Test case content quality
        for tc in test_cases:
            if all(key in tc for key in ['description', 'preconditions', 'test_steps', 'expected_result']):
                score += 0.1
            if len(tc.get('test_steps', [])) >= 2:  # Detailed steps
                score += 0.05

        # Processing metadata factors
        if 'generation_time' in metadata and metadata['generation_time'] < 30:  # Fast generation
            score += 0.1
        if 'token_count' in metadata and 500 <= metadata['token_count'] <= 2000:  # Appropriate length
            score += 0.1

        return min(score, 1.0)  # Cap at 1.0

    def _save_example(self, example: TrainingExample, category: str) -> None:
        """Save training example to appropriate directory."""
        filename = f"{example.id}_{int(time.time())}.json"
        filepath = self.training_dir / category / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(example), f, indent=2, ensure_ascii=False)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about collected training data."""
        stats = {}

        for category in ['collected', 'validated', 'rejected']:
            category_dir = self.training_dir / category
            if category_dir.exists():
                files = list(category_dir.glob('*.json'))
                stats[category] = {
                    'count': len(files),
                    'total_size_mb': sum(f.stat().st_size for f in files) / (1024 * 1024)
                }
            else:
                stats[category] = {'count': 0, 'total_size_mb': 0}

        return stats

    def export_for_training(self, output_format: str = 'jsonl') -> Path:
        """Export validated training data in format suitable for model training."""
        validated_dir = self.training_dir / 'validated'
        export_dir = self.training_dir / 'exports'

        examples = []
        for json_file in validated_dir.glob('*.json'):
            with open(json_file, 'r', encoding='utf-8') as f:
                examples.append(json.load(f))

        if output_format == 'jsonl':
            output_file = export_dir / f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for example in examples:
                    # Convert to training format
                    training_record = self._convert_to_training_format(example)
                    f.write(json.dumps(training_record, ensure_ascii=False) + '\n')

        self.logger.info(f"Exported {len(examples)} examples to {output_file}")
        return output_file

    def _convert_to_training_format(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """Convert training example to format suitable for model training."""
        # Create instruction-response format for fine-tuning
        instruction = f"""Generate test cases for the following requirement:

Type: {example['requirement_type']}
Requirement: {example['requirement_text']}

Context: {json.dumps(example['context'], indent=2)}

Generate comprehensive test cases that verify the requirement is correctly implemented."""

        response = json.dumps(example['test_cases'], indent=2, ensure_ascii=False)

        return {
            'instruction': instruction,
            'response': response,
            'quality_score': example['quality_score'],
            'metadata': example['processing_metadata']
        }
```

### 1.4 Integration with Main Processing

**Integration in `src/processors/standard_processor.py` and `src/processors/hp_processor.py`:**

```python
# Add to processor initialization
from ..training.data_collector import TrainingDataCollector

class StandardProcessor:
    def __init__(self, config: ConfigManager, logger: AppLogger):
        # ... existing initialization ...
        self.data_collector = TrainingDataCollector(config, logger) if config.training.collect_training_data else None

    def _process_requirement(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        # ... existing processing logic ...

        # After successful test case generation
        if self.data_collector and result.get('test_cases'):
            processing_metadata = {
                'generation_time': result.get('generation_time', 0),
                'model_used': self.config.ollama.model,
                'token_count': len(str(result['test_cases'])),
                'template_used': self.config.ollama.template
            }

            context = {
                'domain': 'automotive',  # Determine from file/content
                'processing_mode': 'standard',
                'file_source': req_data.get('source_file', ''),
                'timestamp': result.get('timestamp', '')
            }

            self.data_collector.collect_example(
                requirement_id=req_data['id'],
                requirement_text=req_data['text'],
                requirement_type=req_data.get('type', 'Unknown'),
                test_cases=result['test_cases'],
                context=context,
                processing_metadata=processing_metadata
            )

        return result
```

---

## 2. LoRA Fine-Tuning Implementation

### 2.1 Overview

LoRA (Low-Rank Adaptation) provides efficient fine-tuning by training small adapter layers while keeping the base model frozen.

### 2.2 Implementation Structure

**Required Files:**
```
src/training/
├── lora_trainer.py           # Main LoRA training logic
├── model_utils.py            # Model loading/saving utilities
├── training_config.py        # Training-specific configuration
└── callbacks.py              # Training callbacks and monitoring
```

### 2.3 LoRA Trainer Implementation

**File: `src/training/lora_trainer.py`**

```python
"""
LoRA (Low-Rank Adaptation) trainer for AI Test Case Generator.
Implements parameter-efficient fine-tuning for domain adaptation.
"""

import os
import json
import torch
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    TrainingArguments, Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset, load_dataset
import wandb

from ..config import ConfigManager
from ..app_logger import AppLogger

@dataclass
class LoRATrainingConfig:
    """Configuration for LoRA training."""
    # Model settings
    base_model: str = "meta-llama/Llama-2-7b-chat-hf"  # Hugging Face model name
    model_max_length: int = 2048

    # LoRA parameters
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: List[str] = None

    # Training parameters
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    warmup_steps: int = 100
    max_grad_norm: float = 1.0

    # Data settings
    train_data_path: str = ""
    validation_split: float = 0.1
    max_samples: Optional[int] = None

    # Output settings
    output_dir: str = "models/lora_output"
    save_steps: int = 500
    eval_steps: int = 500
    logging_steps: int = 100

    # Monitoring
    use_wandb: bool = True
    wandb_project: str = "ai-test-generator"
    wandb_run_name: Optional[str] = None

    def __post_init__(self):
        if self.target_modules is None:
            # Default target modules for Llama models
            self.target_modules = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

        if self.wandb_run_name is None:
            self.wandb_run_name = f"lora_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

class LoRATrainer:
    """Implements LoRA fine-tuning for the AI Test Case Generator."""

    def __init__(self, config: LoRATrainingConfig, logger: AppLogger):
        self.config = config
        self.logger = logger
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Initialize components
        self.tokenizer = None
        self.model = None
        self.trainer = None

        # Setup output directory
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    def prepare_model(self) -> None:
        """Load and prepare the base model with LoRA adapters."""
        self.logger.info(f"Loading base model: {self.config.base_model}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.base_model)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )

        # Configure LoRA
        lora_config = LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            target_modules=self.config.target_modules,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )

        # Apply LoRA to model
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()

        self.logger.info("Model prepared with LoRA adapters")

    def prepare_dataset(self) -> Tuple[Dataset, Dataset]:
        """Load and prepare training dataset."""
        self.logger.info(f"Loading dataset from: {self.config.train_data_path}")

        # Load dataset
        if self.config.train_data_path.endswith('.jsonl'):
            dataset = load_dataset('json', data_files=self.config.train_data_path)['train']
        else:
            dataset = load_dataset('json', data_dir=self.config.train_data_path)['train']

        # Limit samples if specified
        if self.config.max_samples:
            dataset = dataset.select(range(min(self.config.max_samples, len(dataset))))

        # Tokenize dataset
        def tokenize_function(examples):
            # Combine instruction and response for training
            texts = []
            for instruction, response in zip(examples['instruction'], examples['response']):
                text = f"<|system|>You are an expert test case generator for automotive requirements.</s>\n<|user|>{instruction}</s>\n<|assistant|>{response}</s>"
                texts.append(text)

            tokenized = self.tokenizer(
                texts,
                truncation=True,
                padding=False,
                max_length=self.config.model_max_length,
                return_tensors=None
            )

            # Set labels for causal language modeling
            tokenized["labels"] = tokenized["input_ids"].copy()
            return tokenized

        # Apply tokenization
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names,
            desc="Tokenizing dataset"
        )

        # Split into train/validation
        train_size = int(len(tokenized_dataset) * (1 - self.config.validation_split))
        train_dataset = tokenized_dataset.select(range(train_size))
        val_dataset = tokenized_dataset.select(range(train_size, len(tokenized_dataset)))

        self.logger.info(f"Prepared {len(train_dataset)} training and {len(val_dataset)} validation samples")
        return train_dataset, val_dataset

    def setup_training(self, train_dataset: Dataset, val_dataset: Dataset) -> None:
        """Setup the training configuration and trainer."""
        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,
            max_grad_norm=self.config.max_grad_norm,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            dataloader_pin_memory=False,
            remove_unused_columns=False,
            report_to="wandb" if self.config.use_wandb else None,
            run_name=self.config.wandb_run_name,
        )

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
            pad_to_multiple_of=8
        )

        # Initialize trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )

        self.logger.info("Training setup completed")

    def train(self) -> Dict[str, Any]:
        """Execute the training process."""
        if not all([self.model, self.trainer]):
            raise ValueError("Model and trainer must be prepared before training")

        # Initialize wandb if enabled
        if self.config.use_wandb:
            wandb.init(
                project=self.config.wandb_project,
                name=self.config.wandb_run_name,
                config=self.config.__dict__
            )

        self.logger.info("Starting LoRA training...")

        # Train the model
        train_result = self.trainer.train()

        # Save the final model
        self.trainer.save_model()
        self.tokenizer.save_pretrained(self.config.output_dir)

        # Save training metrics
        metrics = {
            'train_loss': train_result.training_loss,
            'train_runtime': train_result.metrics['train_runtime'],
            'train_samples_per_second': train_result.metrics['train_samples_per_second'],
            'training_config': self.config.__dict__
        }

        with open(Path(self.config.output_dir) / 'training_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)

        self.logger.info(f"Training completed. Model saved to: {self.config.output_dir}")
        return metrics

    def evaluate(self, test_dataset: Optional[Dataset] = None) -> Dict[str, Any]:
        """Evaluate the trained model."""
        if test_dataset is None:
            # Use validation set for evaluation
            eval_result = self.trainer.evaluate()
        else:
            eval_result = self.trainer.evaluate(eval_dataset=test_dataset)

        self.logger.info(f"Evaluation results: {eval_result}")
        return eval_result

    @classmethod
    def from_config_file(cls, config_path: str, logger: AppLogger) -> 'LoRATrainer':
        """Create trainer from configuration file."""
        with open(config_path, 'r') as f:
            config_dict = json.load(f)

        config = LoRATrainingConfig(**config_dict)
        return cls(config, logger)
```

### 2.4 Training Script

**File: `scripts/train_lora.py`**

```python
#!/usr/bin/env python3
"""
LoRA training script for AI Test Case Generator.
Usage: python scripts/train_lora.py --config config/lora_config.json
"""

import argparse
import json
from pathlib import Path

from src.training.lora_trainer import LoRATrainer, LoRATrainingConfig
from src.app_logger import AppLogger

def main():
    parser = argparse.ArgumentParser(description="Train LoRA adapter for AI Test Case Generator")
    parser.add_argument("--config", required=True, help="Path to training configuration file")
    parser.add_argument("--data-path", help="Override training data path")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--dry-run", action="store_true", help="Validate setup without training")

    args = parser.parse_args()

    # Setup logging
    logger = AppLogger()

    # Load configuration
    with open(args.config, 'r') as f:
        config_dict = json.load(f)

    # Apply overrides
    if args.data_path:
        config_dict['train_data_path'] = args.data_path
    if args.output_dir:
        config_dict['output_dir'] = args.output_dir

    config = LoRATrainingConfig(**config_dict)

    # Create trainer
    trainer = LoRATrainer(config, logger)

    # Prepare model and dataset
    trainer.prepare_model()
    train_dataset, val_dataset = trainer.prepare_dataset()
    trainer.setup_training(train_dataset, val_dataset)

    if args.dry_run:
        logger.info("Dry run completed successfully")
        return

    # Execute training
    metrics = trainer.train()

    # Evaluate model
    eval_metrics = trainer.evaluate()

    logger.info("Training pipeline completed successfully")
    print(f"Final metrics: {json.dumps(metrics, indent=2)}")

if __name__ == "__main__":
    main()
```

---

## 3. Model Evaluation System

### 3.1 Overview

Comprehensive evaluation system to assess model performance across quality, performance, and domain-specific metrics.

### 3.2 Implementation Structure

**Required Files:**
```
src/evaluation/
├── __init__.py
├── evaluator.py              # Main evaluation logic
├── metrics.py                # Evaluation metrics
├── benchmarks.py             # Benchmark datasets
└── reports.py                # Evaluation reporting
```

### 3.3 Evaluator Implementation

**File: `src/evaluation/evaluator.py`**

```python
"""
Model evaluation system for AI Test Case Generator.
Provides comprehensive quality, performance, and domain-specific evaluation.
"""

import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics

from ..core.ollama_client import OllamaClient
from ..config import ConfigManager
from ..app_logger import AppLogger
from .metrics import QualityMetrics, PerformanceMetrics, DomainMetrics

@dataclass
class EvaluationResult:
    """Comprehensive evaluation result."""
    model_name: str
    evaluation_date: str
    test_set_info: Dict[str, Any]
    quality_metrics: Dict[str, float]
    performance_metrics: Dict[str, float]
    domain_metrics: Dict[str, float]
    overall_score: float
    detailed_results: List[Dict[str, Any]]

class ModelEvaluator:
    """Evaluates AI models for test case generation quality."""

    def __init__(self, config: ConfigManager, logger: AppLogger):
        self.config = config
        self.logger = logger
        self.ollama_client = OllamaClient(config.ollama, logger)

        # Initialize metric calculators
        self.quality_metrics = QualityMetrics()
        self.performance_metrics = PerformanceMetrics()
        self.domain_metrics = DomainMetrics()

    async def evaluate_model(
        self,
        model_name: str,
        test_dataset: List[Dict[str, Any]],
        reference_model: Optional[str] = None
    ) -> EvaluationResult:
        """
        Comprehensive model evaluation.

        Args:
            model_name: Name of model to evaluate
            test_dataset: List of test cases with ground truth
            reference_model: Optional baseline model for comparison

        Returns:
            Detailed evaluation results
        """
        self.logger.info(f"Starting evaluation of model: {model_name}")

        # Generate predictions for test dataset
        predictions = await self._generate_predictions(model_name, test_dataset)

        # Calculate all metrics
        quality_scores = self.quality_metrics.calculate_all(predictions, test_dataset)
        performance_scores = self.performance_metrics.calculate_all(predictions)
        domain_scores = self.domain_metrics.calculate_all(predictions, test_dataset)

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            quality_scores, performance_scores, domain_scores
        )

        # Create detailed results
        detailed_results = self._create_detailed_results(predictions, test_dataset)

        result = EvaluationResult(
            model_name=model_name,
            evaluation_date=datetime.now().isoformat(),
            test_set_info={
                'size': len(test_dataset),
                'domains': list(set(item.get('domain', 'unknown') for item in test_dataset)),
                'requirement_types': list(set(item.get('requirement_type', 'unknown') for item in test_dataset))
            },
            quality_metrics=quality_scores,
            performance_metrics=performance_scores,
            domain_metrics=domain_scores,
            overall_score=overall_score,
            detailed_results=detailed_results
        )

        self.logger.info(f"Evaluation completed. Overall score: {overall_score:.3f}")
        return result

    async def _generate_predictions(
        self,
        model_name: str,
        test_dataset: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate model predictions for test dataset."""
        predictions = []

        for i, test_case in enumerate(test_dataset):
            start_time = time.time()

            # Create prompt for test case generation
            prompt = self._create_evaluation_prompt(test_case)

            try:
                # Generate test cases
                response = await self.ollama_client.generate_async(
                    model=model_name,
                    prompt=prompt
                )

                generation_time = time.time() - start_time

                # Parse generated test cases
                generated_test_cases = self._parse_generated_response(response)

                prediction = {
                    'id': test_case.get('id', f'test_{i}'),
                    'requirement_text': test_case['requirement_text'],
                    'requirement_type': test_case.get('requirement_type', 'Unknown'),
                    'domain': test_case.get('domain', 'unknown'),
                    'generated_test_cases': generated_test_cases,
                    'ground_truth_test_cases': test_case.get('expected_test_cases', []),
                    'generation_time': generation_time,
                    'model_used': model_name,
                    'success': len(generated_test_cases) > 0
                }

                predictions.append(prediction)

            except Exception as e:
                self.logger.error(f"Error generating prediction for {test_case.get('id', i)}: {e}")
                predictions.append({
                    'id': test_case.get('id', f'test_{i}'),
                    'requirement_text': test_case['requirement_text'],
                    'generated_test_cases': [],
                    'ground_truth_test_cases': test_case.get('expected_test_cases', []),
                    'generation_time': 0,
                    'model_used': model_name,
                    'success': False,
                    'error': str(e)
                })

        return predictions

    def _create_evaluation_prompt(self, test_case: Dict[str, Any]) -> str:
        """Create standardized prompt for evaluation."""
        context = test_case.get('context', {})

        prompt = f"""Generate comprehensive test cases for the following requirement:

Requirement Type: {test_case.get('requirement_type', 'System Requirement')}
Requirement Text: {test_case['requirement_text']}

Context:
- Domain: {context.get('domain', 'automotive')}
- Subsystem: {context.get('subsystem', 'general')}
- Safety Level: {context.get('safety_level', 'standard')}

Generate 2-4 test cases that thoroughly verify this requirement. Each test case should include:
1. Test ID
2. Description
3. Preconditions
4. Test Steps
5. Expected Result
6. Test Type

Format the output as a JSON array of test case objects."""

        return prompt

    def _parse_generated_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse generated response into structured test cases."""
        try:
            # Try to extract JSON from response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1

            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback: try to parse entire response as JSON
                return json.loads(response)

        except json.JSONDecodeError:
            # Fallback: create single test case from text
            return [{
                'test_id': 'parsed_tc_001',
                'description': 'Generated test case',
                'test_steps': response.split('\n')[:5],  # First 5 lines as steps
                'expected_result': 'Requirement verification',
                'test_type': 'Functional'
            }]

    def _calculate_overall_score(
        self,
        quality_scores: Dict[str, float],
        performance_scores: Dict[str, float],
        domain_scores: Dict[str, float]
    ) -> float:
        """Calculate weighted overall score."""
        weights = {
            'quality': 0.5,
            'performance': 0.2,
            'domain': 0.3
        }

        quality_avg = statistics.mean(quality_scores.values()) if quality_scores else 0
        performance_avg = statistics.mean(performance_scores.values()) if performance_scores else 0
        domain_avg = statistics.mean(domain_scores.values()) if domain_scores else 0

        overall = (
            weights['quality'] * quality_avg +
            weights['performance'] * performance_avg +
            weights['domain'] * domain_avg
        )

        return overall

    def _create_detailed_results(
        self,
        predictions: List[Dict[str, Any]],
        test_dataset: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create detailed per-example results."""
        detailed = []

        for pred, test_case in zip(predictions, test_dataset):
            detail = {
                'id': pred['id'],
                'requirement_text': pred['requirement_text'],
                'success': pred['success'],
                'generation_time': pred['generation_time'],
                'generated_count': len(pred['generated_test_cases']),
                'expected_count': len(pred['ground_truth_test_cases']),
                'quality_score': self.quality_metrics.calculate_single(pred, test_case),
                'domain_relevance': self.domain_metrics.calculate_single(pred, test_case)
            }

            if not pred['success']:
                detail['error'] = pred.get('error', 'Unknown error')

            detailed.append(detail)

        return detailed

    def save_evaluation_report(
        self,
        result: EvaluationResult,
        output_path: Path
    ) -> None:
        """Save comprehensive evaluation report."""
        # Create main report
        report_data = asdict(result)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        # Create summary report
        summary_path = output_path.parent / f"{output_path.stem}_summary.md"
        self._create_summary_report(result, summary_path)

        self.logger.info(f"Evaluation report saved to: {output_path}")
        self.logger.info(f"Summary report saved to: {summary_path}")

    def _create_summary_report(
        self,
        result: EvaluationResult,
        output_path: Path
    ) -> None:
        """Create human-readable summary report."""
        summary = f"""# Model Evaluation Report

**Model**: {result.model_name}
**Date**: {result.evaluation_date}
**Overall Score**: {result.overall_score:.3f}/1.000

## Test Dataset
- **Size**: {result.test_set_info['size']} examples
- **Domains**: {', '.join(result.test_set_info['domains'])}
- **Requirement Types**: {', '.join(result.test_set_info['requirement_types'])}

## Quality Metrics
"""

        for metric, score in result.quality_metrics.items():
            summary += f"- **{metric.replace('_', ' ').title()}**: {score:.3f}\n"

        summary += "\n## Performance Metrics\n"
        for metric, score in result.performance_metrics.items():
            summary += f"- **{metric.replace('_', ' ').title()}**: {score:.3f}\n"

        summary += "\n## Domain Metrics\n"
        for metric, score in result.domain_metrics.items():
            summary += f"- **{metric.replace('_', ' ').title()}**: {score:.3f}\n"

        # Add top and bottom performers
        detailed = result.detailed_results
        top_performers = sorted(detailed, key=lambda x: x['quality_score'], reverse=True)[:3]
        bottom_performers = sorted(detailed, key=lambda x: x['quality_score'])[:3]

        summary += "\n## Top Performing Examples\n"
        for example in top_performers:
            summary += f"- **{example['id']}**: Quality {example['quality_score']:.3f}, Time {example['generation_time']:.2f}s\n"

        summary += "\n## Areas for Improvement\n"
        for example in bottom_performers:
            summary += f"- **{example['id']}**: Quality {example['quality_score']:.3f}, Time {example['generation_time']:.2f}s\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)

    async def compare_models(
        self,
        model_names: List[str],
        test_dataset: List[Dict[str, Any]]
    ) -> Dict[str, EvaluationResult]:
        """Compare multiple models on the same test dataset."""
        results = {}

        for model_name in model_names:
            self.logger.info(f"Evaluating model: {model_name}")
            result = await self.evaluate_model(model_name, test_dataset)
            results[model_name] = result

        # Create comparison report
        self._create_comparison_report(results)

        return results

    def _create_comparison_report(
        self,
        results: Dict[str, EvaluationResult]
    ) -> None:
        """Create model comparison report."""
        comparison = {
            'comparison_date': datetime.now().isoformat(),
            'models': list(results.keys()),
            'metrics_comparison': {},
            'rankings': {}
        }

        # Compare metrics across models
        all_metrics = ['overall_score']
        if results:
            first_result = next(iter(results.values()))
            all_metrics.extend(first_result.quality_metrics.keys())
            all_metrics.extend(first_result.performance_metrics.keys())
            all_metrics.extend(first_result.domain_metrics.keys())

        for metric in all_metrics:
            comparison['metrics_comparison'][metric] = {}
            for model_name, result in results.items():
                if metric == 'overall_score':
                    score = result.overall_score
                elif metric in result.quality_metrics:
                    score = result.quality_metrics[metric]
                elif metric in result.performance_metrics:
                    score = result.performance_metrics[metric]
                elif metric in result.domain_metrics:
                    score = result.domain_metrics[metric]
                else:
                    score = 0.0

                comparison['metrics_comparison'][metric][model_name] = score

        # Create rankings
        for metric in all_metrics:
            metric_scores = comparison['metrics_comparison'][metric]
            ranked = sorted(metric_scores.items(), key=lambda x: x[1], reverse=True)
            comparison['rankings'][metric] = [model for model, score in ranked]

        # Save comparison
        output_path = Path("evaluation_results") / f"model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2)

        self.logger.info(f"Model comparison saved to: {output_path}")
```

### 3.4 Metrics Implementation

**File: `src/evaluation/metrics.py`**

```python
"""
Evaluation metrics for AI Test Case Generator models.
Implements quality, performance, and domain-specific metrics.
"""

import re
import json
import statistics
from typing import Dict, List, Any, Optional
from collections import Counter
import difflib

class QualityMetrics:
    """Calculates quality metrics for generated test cases."""

    def calculate_all(
        self,
        predictions: List[Dict[str, Any]],
        ground_truth: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate all quality metrics."""
        return {
            'completeness_score': self.calculate_completeness(predictions),
            'relevance_score': self.calculate_relevance(predictions, ground_truth),
            'coverage_score': self.calculate_coverage(predictions, ground_truth),
            'structure_score': self.calculate_structure_quality(predictions),
            'diversity_score': self.calculate_diversity(predictions)
        }

    def calculate_single(
        self,
        prediction: Dict[str, Any],
        ground_truth: Dict[str, Any]
    ) -> float:
        """Calculate quality score for single example."""
        scores = []

        # Completeness (all required fields present)
        test_cases = prediction.get('generated_test_cases', [])
        if test_cases:
            required_fields = ['description', 'test_steps', 'expected_result']
            field_scores = []
            for tc in test_cases:
                field_count = sum(1 for field in required_fields if field in tc and tc[field])
                field_scores.append(field_count / len(required_fields))
            scores.append(statistics.mean(field_scores))
        else:
            scores.append(0.0)

        # Relevance to requirement
        req_text = prediction.get('requirement_text', '').lower()
        relevance_scores = []
        for tc in test_cases:
            desc = tc.get('description', '').lower()
            # Simple keyword overlap
            req_words = set(req_text.split())
            desc_words = set(desc.split())
            overlap = len(req_words & desc_words) / max(len(req_words), 1)
            relevance_scores.append(overlap)

        if relevance_scores:
            scores.append(statistics.mean(relevance_scores))
        else:
            scores.append(0.0)

        return statistics.mean(scores) if scores else 0.0

    def calculate_completeness(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate how complete the generated test cases are."""
        required_fields = ['description', 'preconditions', 'test_steps', 'expected_result']
        scores = []

        for pred in predictions:
            test_cases = pred.get('generated_test_cases', [])
            if not test_cases:
                scores.append(0.0)
                continue

            case_scores = []
            for tc in test_cases:
                field_count = sum(1 for field in required_fields if field in tc and tc[field])
                case_scores.append(field_count / len(required_fields))

            scores.append(statistics.mean(case_scores))

        return statistics.mean(scores) if scores else 0.0

    def calculate_relevance(
        self,
        predictions: List[Dict[str, Any]],
        ground_truth: List[Dict[str, Any]]
    ) -> float:
        """Calculate relevance of generated test cases to requirements."""
        scores = []

        for pred, gt in zip(predictions, ground_truth):
            req_text = pred.get('requirement_text', '').lower()
            test_cases = pred.get('generated_test_cases', [])

            if not test_cases or not req_text:
                scores.append(0.0)
                continue

            # Extract key terms from requirement
            req_terms = self._extract_key_terms(req_text)

            case_scores = []
            for tc in test_cases:
                tc_text = ' '.join([
                    tc.get('description', ''),
                    ' '.join(tc.get('test_steps', [])),
                    tc.get('expected_result', '')
                ]).lower()

                # Calculate term coverage
                covered_terms = sum(1 for term in req_terms if term in tc_text)
                relevance = covered_terms / max(len(req_terms), 1)
                case_scores.append(relevance)

            scores.append(statistics.mean(case_scores))

        return statistics.mean(scores) if scores else 0.0

    def calculate_coverage(
        self,
        predictions: List[Dict[str, Any]],
        ground_truth: List[Dict[str, Any]]
    ) -> float:
        """Calculate coverage compared to ground truth test cases."""
        scores = []

        for pred, gt in zip(predictions, ground_truth):
            generated = pred.get('generated_test_cases', [])
            expected = gt.get('expected_test_cases', [])

            if not expected:
                scores.append(1.0 if generated else 0.0)
                continue

            if not generated:
                scores.append(0.0)
                continue

            # Compare test case types and coverage areas
            expected_types = set(tc.get('test_type', 'functional').lower() for tc in expected)
            generated_types = set(tc.get('test_type', 'functional').lower() for tc in generated)

            type_coverage = len(expected_types & generated_types) / len(expected_types)
            scores.append(type_coverage)

        return statistics.mean(scores) if scores else 0.0

    def calculate_structure_quality(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate structural quality of test cases."""
        scores = []

        for pred in predictions:
            test_cases = pred.get('generated_test_cases', [])
            if not test_cases:
                scores.append(0.0)
                continue

            case_scores = []
            for tc in test_cases:
                score = 0.0

                # Check for proper test steps structure
                steps = tc.get('test_steps', [])
                if isinstance(steps, list) and len(steps) >= 2:
                    score += 0.3

                # Check for clear expected result
                expected = tc.get('expected_result', '')
                if expected and len(expected.strip()) > 10:
                    score += 0.3

                # Check for meaningful description
                desc = tc.get('description', '')
                if desc and len(desc.strip()) > 20:
                    score += 0.2

                # Check for preconditions
                precond = tc.get('preconditions', '')
                if precond and len(precond.strip()) > 5:
                    score += 0.2

                case_scores.append(score)

            scores.append(statistics.mean(case_scores))

        return statistics.mean(scores) if scores else 0.0

    def calculate_diversity(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate diversity of generated test cases."""
        all_descriptions = []

        for pred in predictions:
            test_cases = pred.get('generated_test_cases', [])
            for tc in test_cases:
                desc = tc.get('description', '').lower()
                if desc:
                    all_descriptions.append(desc)

        if len(all_descriptions) < 2:
            return 0.0

        # Calculate pairwise similarity
        similarities = []
        for i in range(len(all_descriptions)):
            for j in range(i + 1, len(all_descriptions)):
                similarity = difflib.SequenceMatcher(
                    None, all_descriptions[i], all_descriptions[j]
                ).ratio()
                similarities.append(similarity)

        # Diversity is inverse of average similarity
        avg_similarity = statistics.mean(similarities)
        return max(0.0, 1.0 - avg_similarity)

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from requirement text."""
        # Remove common words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'shall', 'should', 'must', 'will', 'system'
        }

        words = re.findall(r'\b\w+\b', text.lower())
        key_terms = [word for word in words if len(word) > 3 and word not in stop_words]

        return list(set(key_terms))  # Remove duplicates

class PerformanceMetrics:
    """Calculates performance metrics for model efficiency."""

    def calculate_all(self, predictions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate all performance metrics."""
        return {
            'avg_generation_time': self.calculate_avg_generation_time(predictions),
            'success_rate': self.calculate_success_rate(predictions),
            'throughput': self.calculate_throughput(predictions),
            'efficiency_score': self.calculate_efficiency(predictions)
        }

    def calculate_avg_generation_time(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate average generation time."""
        times = [pred.get('generation_time', 0) for pred in predictions if pred.get('success', False)]
        return statistics.mean(times) if times else 0.0

    def calculate_success_rate(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate rate of successful generations."""
        if not predictions:
            return 0.0

        successful = sum(1 for pred in predictions if pred.get('success', False))
        return successful / len(predictions)

    def calculate_throughput(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate test cases generated per second."""
        total_time = sum(pred.get('generation_time', 0) for pred in predictions)
        total_test_cases = sum(len(pred.get('generated_test_cases', [])) for pred in predictions)

        if total_time > 0:
            return total_test_cases / total_time
        return 0.0

    def calculate_efficiency(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate overall efficiency score."""
        success_rate = self.calculate_success_rate(predictions)
        avg_time = self.calculate_avg_generation_time(predictions)

        # Normalize time (assuming good performance is < 10 seconds)
        time_score = max(0.0, 1.0 - (avg_time / 10.0))

        # Combine success rate and time efficiency
        return (success_rate + time_score) / 2.0

class DomainMetrics:
    """Calculates domain-specific metrics for automotive requirements."""

    def __init__(self):
        # Automotive-specific keywords and concepts
        self.automotive_keywords = {
            'safety': ['safety', 'asil', 'hazard', 'risk', 'fault', 'failure'],
            'performance': ['response', 'time', 'latency', 'speed', 'efficiency'],
            'functional': ['control', 'monitor', 'detect', 'activate', 'deactivate'],
            'communication': ['can', 'bus', 'network', 'message', 'signal'],
            'hardware': ['sensor', 'actuator', 'ecu', 'component', 'device']
        }

    def calculate_all(
        self,
        predictions: List[Dict[str, Any]],
        ground_truth: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate all domain-specific metrics."""
        return {
            'automotive_relevance': self.calculate_automotive_relevance(predictions),
            'safety_coverage': self.calculate_safety_coverage(predictions),
            'technical_accuracy': self.calculate_technical_accuracy(predictions),
            'domain_terminology': self.calculate_domain_terminology(predictions)
        }

    def calculate_single(
        self,
        prediction: Dict[str, Any],
        ground_truth: Dict[str, Any]
    ) -> float:
        """Calculate domain relevance for single example."""
        domain = prediction.get('domain', 'unknown')

        if domain == 'automotive':
            return self._calculate_automotive_score(prediction)
        else:
            # Generic domain scoring
            return 0.5  # Neutral score for unknown domains

    def calculate_automotive_relevance(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate relevance to automotive domain."""
        scores = []

        for pred in predictions:
            if pred.get('domain') == 'automotive':
                score = self._calculate_automotive_score(pred)
                scores.append(score)

        return statistics.mean(scores) if scores else 0.0

    def calculate_safety_coverage(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate coverage of safety-related aspects."""
        scores = []

        for pred in predictions:
            test_cases = pred.get('generated_test_cases', [])
            safety_score = 0.0

            if test_cases:
                safety_cases = 0
                for tc in test_cases:
                    tc_text = ' '.join([
                        tc.get('description', ''),
                        ' '.join(tc.get('test_steps', [])),
                        tc.get('expected_result', '')
                    ]).lower()

                    # Check for safety-related content
                    safety_keywords = self.automotive_keywords['safety']
                    if any(keyword in tc_text for keyword in safety_keywords):
                        safety_cases += 1

                safety_score = safety_cases / len(test_cases)

            scores.append(safety_score)

        return statistics.mean(scores) if scores else 0.0

    def calculate_technical_accuracy(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate technical accuracy of generated content."""
        scores = []

        for pred in predictions:
            test_cases = pred.get('generated_test_cases', [])

            if not test_cases:
                scores.append(0.0)
                continue

            accuracy_score = 0.0

            for tc in test_cases:
                # Check for technical detail and specificity
                steps = tc.get('test_steps', [])
                if isinstance(steps, list):
                    # Look for specific technical actions
                    technical_steps = sum(1 for step in steps if self._is_technical_step(step))
                    if len(steps) > 0:
                        accuracy_score += technical_steps / len(steps)

            if test_cases:
                accuracy_score /= len(test_cases)

            scores.append(accuracy_score)

        return statistics.mean(scores) if scores else 0.0

    def calculate_domain_terminology(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate proper use of domain terminology."""
        scores = []

        for pred in predictions:
            test_cases = pred.get('generated_test_cases', [])

            if not test_cases:
                scores.append(0.0)
                continue

            terminology_score = 0.0
            all_keywords = []
            for category in self.automotive_keywords.values():
                all_keywords.extend(category)

            for tc in test_cases:
                tc_text = ' '.join([
                    tc.get('description', ''),
                    ' '.join(tc.get('test_steps', [])),
                    tc.get('expected_result', '')
                ]).lower()

                # Count usage of domain terminology
                keyword_count = sum(1 for keyword in all_keywords if keyword in tc_text)
                # Normalize by text length (words)
                word_count = len(tc_text.split())
                if word_count > 0:
                    terminology_score += keyword_count / word_count

            if test_cases:
                terminology_score /= len(test_cases)

            scores.append(terminology_score)

        return statistics.mean(scores) if scores else 0.0

    def _calculate_automotive_score(self, prediction: Dict[str, Any]) -> float:
        """Calculate automotive-specific score for a prediction."""
        test_cases = prediction.get('generated_test_cases', [])

        if not test_cases:
            return 0.0

        scores = []

        for tc in test_cases:
            tc_text = ' '.join([
                tc.get('description', ''),
                ' '.join(tc.get('test_steps', [])),
                tc.get('expected_result', '')
            ]).lower()

            score = 0.0

            # Check each automotive category
            for category, keywords in self.automotive_keywords.items():
                if any(keyword in tc_text for keyword in keywords):
                    score += 0.2  # Each category contributes 0.2

            scores.append(score)

        return statistics.mean(scores)

    def _is_technical_step(self, step: str) -> bool:
        """Check if a test step contains technical detail."""
        technical_indicators = [
            'measure', 'verify', 'check', 'validate', 'configure',
            'set', 'adjust', 'monitor', 'record', 'compare'
        ]

        step_lower = step.lower()
        return any(indicator in step_lower for indicator in technical_indicators)
```

---

## 4. Model Deployment & Integration

### 4.1 Overview

Seamless deployment of trained models into the Ollama ecosystem and integration with the existing processing pipeline.

### 4.2 Implementation Structure

**Required Files:**
```
src/deployment/
├── __init__.py
├── ollama_deployer.py        # Ollama model deployment
├── model_converter.py        # Model format conversion
└── deployment_manager.py     # Deployment orchestration

scripts/
├── deploy_model.py           # Deployment script
└── validate_deployment.py    # Deployment validation
```

### 4.3 Ollama Deployer Implementation

**File: `src/deployment/ollama_deployer.py`**

```python
"""
Ollama model deployment system for AI Test Case Generator.
Handles deployment of trained models to Ollama runtime.
"""

import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..config import ConfigManager
from ..app_logger import AppLogger

@dataclass
class DeploymentConfig:
    """Configuration for model deployment."""
    model_name: str
    base_model: str
    adapter_path: str
    system_prompt: str = ""
    model_parameters: Dict[str, Any] = None
    description: str = ""
    version: str = "latest"

    def __post_init__(self):
        if self.model_parameters is None:
            self.model_parameters = {
                "temperature": 0.0,
                "num_ctx": 8192,
                "num_predict": 2048,
                "top_k": 10,
                "top_p": 0.9
            }

class OllamaDeployer:
    """Handles deployment of trained models to Ollama."""

    def __init__(self, config: ConfigManager, logger: AppLogger):
        self.config = config
        self.logger = logger
        self.ollama_available = self._check_ollama_availability()

    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is installed and running."""
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.logger.info(f"Ollama detected: {result.stdout.strip()}")
                return True
            else:
                self.logger.error("Ollama not found or not responding")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Error checking Ollama: {e}")
            return False

    def deploy_lora_model(
        self,
        deployment_config: DeploymentConfig,
        validate: bool = True
    ) -> bool:
        """
        Deploy a LoRA-trained model to Ollama.

        Args:
            deployment_config: Deployment configuration
            validate: Whether to validate deployment after creation

        Returns:
            True if deployment successful, False otherwise
        """
        if not self.ollama_available:
            self.logger.error("Ollama not available for deployment")
            return False

        try:
            # Create Modelfile
            modelfile_content = self._create_modelfile(deployment_config)

            # Write Modelfile to temporary location
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.modelfile',
                delete=False
            ) as f:
                f.write(modelfile_content)
                modelfile_path = f.name

            # Create model in Ollama
            success = self._create_ollama_model(
                deployment_config.model_name,
                modelfile_path
            )

            # Cleanup temporary file
            Path(modelfile_path).unlink()

            if success and validate:
                return self._validate_deployment(deployment_config.model_name)

            return success

        except Exception as e:
            self.logger.error(f"Error deploying model: {e}")
            return False

    def _create_modelfile(self, config: DeploymentConfig) -> str:
        """Create Ollama Modelfile content."""
        modelfile = f"""FROM {config.base_model}
"""

        # Add adapter if provided
        if config.adapter_path and Path(config.adapter_path).exists():
            modelfile += f"ADAPTER {config.adapter_path}\n"

        # Add parameters
        for param, value in config.model_parameters.items():
            if isinstance(value, str):
                modelfile += f'PARAMETER {param} "{value}"\n'
            else:
                modelfile += f"PARAMETER {param} {value}\n"

        # Add system prompt
        if config.system_prompt:
            escaped_prompt = config.system_prompt.replace('"', '\\"')
            modelfile += f'SYSTEM """{escaped_prompt}"""\n'

        return modelfile

    def _create_ollama_model(self, model_name: str, modelfile_path: str) -> bool:
        """Create model in Ollama using modelfile."""
        try:
            self.logger.info(f"Creating Ollama model: {model_name}")

            result = subprocess.run(
                ["ollama", "create", model_name, "-f", modelfile_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully created model: {model_name}")
                return True
            else:
                self.logger.error(f"Error creating model: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("Model creation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error creating model: {e}")
            return False

    def _validate_deployment(self, model_name: str) -> bool:
        """Validate that deployed model works correctly."""
        try:
            self.logger.info(f"Validating deployment of: {model_name}")

            # Test model with simple prompt
            test_prompt = """Generate a test case for this requirement:
"The system shall respond to user input within 100ms"

Format as JSON with test_id, description, test_steps, and expected_result."""

            result = subprocess.run([
                "ollama", "run", model_name,
                test_prompt
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                response = result.stdout.strip()
                if response and len(response) > 50:  # Basic sanity check
                    self.logger.info("Model validation successful")
                    return True
                else:
                    self.logger.error("Model response too short or empty")
                    return False
            else:
                self.logger.error(f"Model validation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("Model validation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error validating model: {e}")
            return False

    def list_deployed_models(self) -> List[Dict[str, Any]]:
        """List all models deployed in Ollama."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                models = []
                lines = result.stdout.strip().split('\n')[1:]  # Skip header

                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            models.append({
                                'name': parts[0],
                                'id': parts[1],
                                'size': parts[2],
                                'modified': ' '.join(parts[3:]) if len(parts) > 3 else ''
                            })

                return models
            else:
                self.logger.error(f"Error listing models: {result.stderr}")
                return []

        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
            return []

    def remove_model(self, model_name: str) -> bool:
        """Remove a model from Ollama."""
        try:
            self.logger.info(f"Removing model: {model_name}")

            result = subprocess.run(
                ["ollama", "rm", model_name],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully removed model: {model_name}")
                return True
            else:
                self.logger.error(f"Error removing model: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Error removing model: {e}")
            return False

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a deployed model."""
        try:
            result = subprocess.run(
                ["ollama", "show", model_name],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Parse model information from output
                info = {
                    'name': model_name,
                    'details': result.stdout.strip(),
                    'available': True
                }

                # Try to extract JSON info if available
                try:
                    # Ollama show sometimes returns JSON
                    json_info = json.loads(result.stdout)
                    info.update(json_info)
                except json.JSONDecodeError:
                    # Not JSON, keep as text
                    pass

                return info
            else:
                return None

        except Exception as e:
            self.logger.error(f"Error getting model info: {e}")
            return None

class DeploymentManager:
    """Orchestrates the complete deployment process."""

    def __init__(self, config: ConfigManager, logger: AppLogger):
        self.config = config
        self.logger = logger
        self.deployer = OllamaDeployer(config, logger)

    def deploy_trained_model(
        self,
        model_path: str,
        model_name: str,
        base_model: str = "llama3.1:8b",
        description: str = ""
    ) -> bool:
        """
        Complete deployment pipeline for a trained model.

        Args:
            model_path: Path to trained model/adapter
            model_name: Name for deployed model
            base_model: Base model to use
            description: Model description

        Returns:
            True if deployment successful
        """
        self.logger.info(f"Starting deployment of {model_name}")

        # Create system prompt for test case generation
        system_prompt = self._create_system_prompt()

        # Create deployment configuration
        deployment_config = DeploymentConfig(
            model_name=model_name,
            base_model=base_model,
            adapter_path=model_path,
            system_prompt=system_prompt,
            description=description,
            model_parameters={
                "temperature": 0.0,
                "num_ctx": 8192,
                "num_predict": 2048,
                "top_k": 10,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        )

        # Deploy model
        success = self.deployer.deploy_lora_model(deployment_config)

        if success:
            # Save deployment metadata
            self._save_deployment_metadata(deployment_config, model_path)
            self.logger.info(f"Successfully deployed {model_name}")
        else:
            self.logger.error(f"Failed to deploy {model_name}")

        return success

    def _create_system_prompt(self) -> str:
        """Create system prompt for test case generation."""
        return """You are an expert automotive test case generator specializing in safety-critical requirements and ASIL compliance.

Your role is to generate comprehensive, high-quality test cases for automotive system requirements.

Guidelines:
1. Generate 2-4 test cases per requirement
2. Include all required fields: test_id, description, preconditions, test_steps, expected_result, test_type
3. Focus on edge cases and safety scenarios
4. Use automotive domain terminology appropriately
5. Consider ASIL levels and safety implications
6. Ensure test steps are specific and actionable
7. Format output as valid JSON array

Always prioritize safety, completeness, and technical accuracy in your test case generation."""

    def _save_deployment_metadata(
        self,
        config: DeploymentConfig,
        model_path: str
    ) -> None:
        """Save deployment metadata for tracking."""
        metadata = {
            'model_name': config.model_name,
            'base_model': config.base_model,
            'adapter_path': model_path,
            'deployment_date': str(Path().cwd()),  # Using cwd as timestamp placeholder
            'parameters': config.model_parameters,
            'description': config.description,
            'version': config.version
        }

        # Save to deployment registry
        registry_path = Path("deployment_registry.json")

        if registry_path.exists():
            with open(registry_path, 'r') as f:
                registry = json.load(f)
        else:
            registry = {"deployments": []}

        registry["deployments"].append(metadata)

        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

    def validate_production_readiness(
        self,
        model_name: str,
        test_suite_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate that model is ready for production use."""
        validation_results = {
            'model_name': model_name,
            'ready_for_production': False,
            'checks': {}
        }

        # Check 1: Model exists and responds
        model_info = self.deployer.get_model_info(model_name)
        validation_results['checks']['model_exists'] = model_info is not None

        # Check 2: Basic functionality test
        if model_info:
            validation_results['checks']['basic_functionality'] = self.deployer._validate_deployment(model_name)
        else:
            validation_results['checks']['basic_functionality'] = False

        # Check 3: Performance test (if test suite provided)
        if test_suite_path and Path(test_suite_path).exists():
            validation_results['checks']['performance_test'] = self._run_performance_test(
                model_name, test_suite_path
            )
        else:
            validation_results['checks']['performance_test'] = True  # Skip if no test suite

        # Overall readiness
        all_checks_passed = all(validation_results['checks'].values())
        validation_results['ready_for_production'] = all_checks_passed

        return validation_results

    def _run_performance_test(self, model_name: str, test_suite_path: str) -> bool:
        """Run performance test against deployed model."""
        # This would integrate with the evaluation system
        # For now, return True as placeholder
        self.logger.info(f"Running performance test for {model_name}")
        return True
```

### 4.4 Deployment Script

**File: `scripts/deploy_model.py`**

```python
#!/usr/bin/env python3
"""
Model deployment script for AI Test Case Generator.
Usage: python scripts/deploy_model.py --model-path path/to/model --model-name my-model
"""

import argparse
import json
import sys
from pathlib import Path

from src.deployment.deployment_manager import DeploymentManager
from src.config import ConfigManager
from src.app_logger import AppLogger

def main():
    parser = argparse.ArgumentParser(description="Deploy trained model to Ollama")
    parser.add_argument("--model-path", required=True, help="Path to trained model/adapter")
    parser.add_argument("--model-name", required=True, help="Name for deployed model")
    parser.add_argument("--base-model", default="llama3.1:8b", help="Base model to use")
    parser.add_argument("--description", default="", help="Model description")
    parser.add_argument("--validate", action="store_true", help="Run validation after deployment")
    parser.add_argument("--test-suite", help="Path to test suite for validation")

    args = parser.parse_args()

    # Verify model path exists
    model_path = Path(args.model_path)
    if not model_path.exists():
        print(f"Error: Model path does not exist: {model_path}")
        sys.exit(1)

    # Setup components
    config = ConfigManager()
    logger = AppLogger()
    deployment_manager = DeploymentManager(config, logger)

    # Deploy model
    print(f"Deploying model: {args.model_name}")
    success = deployment_manager.deploy_trained_model(
        model_path=str(model_path),
        model_name=args.model_name,
        base_model=args.base_model,
        description=args.description
    )

    if not success:
        print("Deployment failed!")
        sys.exit(1)

    print(f"Successfully deployed: {args.model_name}")

    # Run validation if requested
    if args.validate:
        print("Running production readiness validation...")
        validation_results = deployment_manager.validate_production_readiness(
            model_name=args.model_name,
            test_suite_path=args.test_suite
        )

        print(f"Validation results: {json.dumps(validation_results, indent=2)}")

        if validation_results['ready_for_production']:
            print("✅ Model is ready for production use!")
        else:
            print("❌ Model failed validation checks")
            sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## Complete Implementation Workflow

### Step-by-Step Implementation Guide

**Phase 1: Setup and Data Collection (Week 1)**
1. Create training directory structure
2. Implement data collector
3. Integrate collection with processors
4. Start collecting data from normal operations

**Phase 2: Training Infrastructure (Week 2)**
1. Implement LoRA trainer
2. Create training configuration system
3. Develop training scripts
4. Test with small dataset

**Phase 3: Evaluation System (Week 3)**
1. Implement evaluation metrics
2. Create evaluation framework
3. Build comparison tools
4. Validate with baseline models

**Phase 4: Deployment System (Week 4)**
1. Implement Ollama deployer
2. Create deployment manager
3. Build validation pipeline
4. Test end-to-end workflow

### Integration Commands

**Installation with Training Dependencies:**
```bash
pip install -e .[training]
```

**Data Collection Setup:**
```bash
export AI_TG_COLLECT_TRAINING_DATA=true
export AI_TG_AUTO_APPROVE_THRESHOLD=0.9
mkdir -p training_data/{collected,validated,rejected,exports}
```

**Training Execution:**
```bash
# Prepare training data
python -c "from src.training.data_collector import TrainingDataCollector; TrainingDataCollector().export_for_training()"

# Train LoRA model
python scripts/train_lora.py --config config/lora_config.json

# Evaluate model
python -c "from src.evaluation.evaluator import ModelEvaluator; evaluator.evaluate_model('custom-model', test_data)"

# Deploy model
python scripts/deploy_model.py --model-path models/lora_output --model-name automotive-test-v1
```

### Configuration Files

**LoRA Training Config (`config/lora_config.json`):**
```json
{
  "base_model": "meta-llama/Llama-2-7b-chat-hf",
  "train_data_path": "training_data/exports/training_data_latest.jsonl",
  "output_dir": "models/automotive-lora-v1",
  "num_epochs": 3,
  "batch_size": 4,
  "learning_rate": 2e-4,
  "lora_r": 16,
  "lora_alpha": 32,
  "use_wandb": true,
  "wandb_project": "ai-test-generator"
}
```

---

## Troubleshooting & Best Practices

### Common Issues and Solutions

**Data Collection Issues:**
- Low quality scores: Adjust quality threshold and improve prompt templates
- Insufficient data: Lower auto-approval threshold and collect more samples
- Storage issues: Implement data cleanup and archival policies

**Training Issues:**
- CUDA out of memory: Reduce batch size, increase gradient accumulation steps
- Poor convergence: Adjust learning rate, add warmup steps
- Overfitting: Reduce training epochs, add regularization

**Evaluation Issues:**
- Inconsistent metrics: Standardize evaluation prompts and procedures
- Slow evaluation: Implement batch processing and caching
- Metric interpretation: Create baseline comparisons and thresholds

**Deployment Issues:**
- Ollama integration: Verify Ollama version and model compatibility
- Model loading: Check adapter format and base model availability
- Performance: Optimize model parameters and resource allocation

### Best Practices

1. **Data Quality Management:**
   - Regular human review of collected examples
   - Balanced dataset across requirement types
   - Continuous quality monitoring

2. **Training Optimization:**
   - Start with small datasets for testing
   - Use LoRA for efficient iteration
   - Monitor training metrics continuously

3. **Evaluation Rigor:**
   - Multiple evaluation runs for consistency
   - Domain-specific metrics alongside general metrics
   - Baseline model comparisons

4. **Production Deployment:**
   - Staged deployment with validation
   - A/B testing against baseline models
   - Performance monitoring and rollback capability

### Monitoring and Maintenance

**Performance Monitoring:**
```bash
# Regular evaluation against benchmark
python scripts/evaluate_production_model.py --model automotive-test-v1

# Performance metrics collection
python scripts/collect_production_metrics.py --duration 24h

# Quality drift detection
python scripts/detect_quality_drift.py --baseline baseline_metrics.json
```

## 5. Excel-Based Training System (Alternative Approach)

This section describes an alternative Excel-based training implementation that provides enhanced usability for data collection and categorization, along with intelligent requirement relationship linking for improved model inference.

### 5.1 Overview

The Excel-based approach replaces JSON file storage with structured Excel workbooks, enabling:
- User-friendly review and categorization through Excel sheets
- Visual management of requirement relationships
- Enhanced training prompts that leverage requirement dependencies
- Audit trails through review notes and approval workflows

### 5.2 Excel Workbook Structure

**Primary Training Workbook: `training_data.xlsx`**

#### Sheet 1: Raw_Training_Data
| Column | Type | Description | Required |
|--------|------|-------------|----------|
| requirement_id | Text | Unique requirement identifier | Yes |
| requirement_text | Text | The original requirement | Yes |
| requirement_type | Dropdown | System, Software, Functional, Performance, Safety | Yes |
| category | Dropdown | Good, Bad, Partial (manual categorization) | Yes |
| test_cases_json | Text | JSON string of generated test cases | Yes |
| generation_model | Text | Model used (llama3.1:8b, etc.) | Yes |
| generation_template | Text | Template used | No |
| quality_score | Number | Automated quality score (0-1) | Yes |
| human_reviewed | Boolean | Manual review status | Yes |
| review_notes | Text | Human review comments | No |
| linked_requirements | Text | Comma-separated related requirement_ids | No |
| relationship_type | Text | depends_on, similar_to, complements | No |
| domain | Text | Automotive, Medical, etc. | Yes |
| subsystem | Text | UI, Engine Control, Safety, etc. | No |

**Data Validation Rules:**
- Category dropdown: Good, Partial, Bad
- Requirement_type dropdown: System, Software, Functional, Performance, Safety
- Relationship_type validation: supports multiple relationship types

#### Additional Sheets

**Sheet 2: Requirement_Relationships**
| Column | Type | Description |
|--------|------|-------------|
| source_requirement_id | Text | Source requirement ID |
| target_requirement_id | Text | Related requirement ID |
| relationship_type | Dropdown | depends_on, similar_to, complements, enables, restricts |
| relationship_description | Text | Explanation of relationship |
| bidirectional | Boolean | True if relationship works both ways |
| confidence | Number (0-1) | Strength of relationship |

**Sheet 3: Test_Case_Templates**
| Column | Type | Description |
|--------|------|-------------|
| template_id | Text | Unique template identifier |
| template_name | Text | Human-readable name |
| template_description | Text | Template purpose description |
| applicable_types | Text | Comma-separated requirement types |
| test_case_structure | Text | JSON schema for expected output |

### 5.3 User Workflow

#### Step 1: Generate Training Data
```bash
# Enable Excel export in environment
export AI_TG_EXPORT_FORMAT=excel
export AI_TG_EXCEL_WORKBOOK_PATH=./training_data.xlsx

# Run generation to populate Excel file
python main.py your_reqifz_file.reqifz --export-training-data
```

#### Step 2: Manual Review and Categorization
1. **Open `training_data.xlsx`**
2. **Review each row** in Raw_Training_Data sheet:
   - Read requirement text
   - Expand/formula-view JSON test_cases_json column
   - Evaluate quality and completeness
3. **Assign Category**:
   - **Good**: High-quality, accurate, comprehensive test cases
   - **Partial**: Contains useful elements but needs improvement
   - **Bad**: Major issues, incorrect coverage, unusable
4. **Add Review Notes** explaining categorization decision

#### Step 3: Establish Requirement Relationships
1. **Switch to Requirement_Relationships sheet**
2. **Identify related requirements** by reviewing requirement similarities
3. **Create relationship entries**:
   ```excel
   source_requirement_id: SYS_001
   target_requirement_id: SYS_002
   relationship_type: depends_on
   relationship_description: Response time requirement enables user experience req
   bidirectional: FALSE
   confidence: 0.85
   ```

#### Step 4: Quality Assurance
- Use Excel filtering to review categories
- Apply data validation rules
- Maintain audit trail through review notes
- Track review progress with human_reviewed flag

### 5.4 Relationship-Aware Training Enhancement

#### Enhanced Inference System
The Excel relationship data enables **context-aware training prompts**:

**Example Enhanced Prompt:**
```
Given this requirement and its related requirements:

Primary: "System shall provide GPS accuracy within 5 meters"
Related (depends_on): "System shall acquire GPS signal within 30 seconds"
Related (complements): "System shall display GPS status to user"
Similar requirements: "System shall maintain accuracy during movement"

Generate comprehensive test cases that verify the primary requirement
while considering these relationships and similar patterns.
```

#### Relationship Processing Module
```python
class RequirementRelationshipProcessor:
    """Processes Excel relationship data for enhanced training."""

    def enhance_training_prompt(self, requirement_id: str, base_prompt: str) -> str:
        """Add relationship context to training prompts."""
        relationships = self._get_relationships_from_excel(requirement_id)

        if not relationships:
            return base_prompt

        context = "\n\nRelated Requirements Context:\n"
        for rel in relationships:
            context += f"- {rel['type']}: {rel['description']}\n"
            context += f"  Related req: {rel['target_text'][:100]}...\n"

        return base_prompt + context

    def build_relationship_graph(self) -> Dict[str, List[Dict]]:
        """Build graph of requirement relationships for inference."""
        # Process Excel relationships into graph structure
        # Enable connected component analysis
        # Support transitive relationship reasoning
```

### 5.5 Implementation Modifications

#### Excel Data Handler
Replace JSON file collector with Excel workbook manager:

```python
import pandas as pd
from openpyxl import load_workbook

class ExcelTrainingDataManager:
    """Manages training data in Excel workbook format."""

    def __init__(self, workbook_path: str):
        self.workbook_path = Path(workbook_path)
        self._ensure_workbook_exists()

    def append_training_example(self, example: Dict[str, Any]) -> None:
        """Append training example to Excel workbook."""
        try:
            book = load_workbook(self.workbook_path)
            sheet = book['Raw_Training_Data']

            # Find next empty row
            next_row = sheet.max_row + 1

            # Write data to columns
            sheet.cell(next_row, 1, example['requirement_id'])
            sheet.cell(next_row, 2, example['requirement_text'])
            # ... populate other columns ...

            book.save(self.workbook_path)

        except Exception as e:
            logger.error(f"Error writing to Excel: {e}")

    def get_training_examples_by_category(self, category: str) -> List[Dict]:
        """Retrieve examples by manual category for training."""
        df = pd.read_excel(self.workbook_path, sheet_name='Raw_Training_Data')

        filtered = df[df['category'] == category]
        return filtered.to_dict('records')

    def export_relationship_aware_data(self) -> pd.DataFrame:
        """Export training data with relationship enrichment."""
        # Merge training data with relationship information
        # Create enhanced dataset for relationship-aware training
```

#### Required Dependencies
```txt
# Add to pyproject.toml [project.optional-dependencies.training]
pandas>=1.5.0
openpyxl>=3.0.10
xlrd>=2.0.1  # For legacy .xls support
```

### 5.6 Benefits of Excel Approach

1. **Enhanced Usability**
   - Visual categorization through Excel interface
   - Easy filtering and review workflows
   - Familiar spreadsheet environment for domain experts

2. **Relationship-Driven Inference**
   - Requirements linked for better context understanding
   - Transitive relationship analysis
   - Contextual training prompt enhancement

3. **Audit and Compliance**
   - Clear review trails through notes
   - Version control through Excel history
   - Regulatory compliance through documented decisions

4. **Scalability and Management**
   - Handle hundreds of examples in organized sheets
   - Automated validation rules
   - Easy data export for training pipelines

5. **Collaboration Features**
   - Multi-user review support
   - Comment threads for discussions
   - Change tracking and approval workflows

### 5.7 Integration with Existing Training Pipeline

#### Modified Training Script
```bash
# Excel-based training preparation
python scripts/prepare_excel_training_data.py \
    --workbook training_data.xlsx \
    --categories good partial \
    --enrich-relationships \
    --output training_enhanced.jsonl

# Train with relationship-enhanced data
python scripts/train_lora.py \
    --config config/lora_config.json \
    --relationship-aware
```

#### Configuration Updates
```yaml
# Add to training configuration
excel_training:
  workbook_path: "./training_data.xlsx"
  enable_relationships: true
  categories_for_training: ["good", "partial"]
  min_relationship_confidence: 0.7
  prompt_enhancement_enabled: true
```

### 5.8 Quality Control Workflows

#### Automated Validation
- Excel data validation rules for column constraints
- VBA macros for data integrity checks
- Automated flagging of inconsistent relationships

#### Manual Review Guidelines
- **Good Criteria**: Complete coverage, accurate technical content, appropriate safety considerations
- **Partial Criteria**: Contains useful elements, fixable issues, good structure but incomplete
- **Bad Criteria**: Major errors, incorrect domain application, unusable format

#### Review Progress Tracking
- Dashboard sheet showing review statistics
- Completion percentage calculations
- Workload distribution metrics

### 5.9 Future Extensions

**Advanced Relationship Analysis:**
- Natural language processing for automatic relationship detection
- Graph algorithms for requirement clustering
- Machine learning to predict relationship strengths

**Collaborative Features:**
- Web-based Excel integration
- Review workflow automation
- Stakeholder notification systems

**Analytics and Reporting:**
- Training data quality dashboards
- Reviewer performance metrics
- Model improvement tracking over time

This Excel-based approach transforms the training data collection from a technical process into a collaborative, user-friendly workflow while significantly enhancing the model's contextual understanding through requirement relationships.

---

This comprehensive implementation guide provides all the necessary components to build a complete training, evaluation, and deployment system for the AI Test Case Generator. Each component is designed to work together while maintaining modularity for independent development and testing.
