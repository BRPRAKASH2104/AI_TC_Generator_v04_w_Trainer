#!/usr/bin/env python3
"""
LoRA Fine-tuning System for Automotive Test Case Generation
Integrates with training data collector to create custom models
"""

import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Optional imports - only loaded when training is requested
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
    from peft import LoraConfig, get_peft_model, TaskType, PeftModel
    from datasets import Dataset
    import wandb
    TRAINING_AVAILABLE = True
except ImportError as e:
    TRAINING_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from training_data_collector import TrainingDataCollector


@dataclass
class LoRATrainingConfig:
    """Configuration for LoRA fine-tuning"""
    base_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    output_dir: str = "models/automotive-lora"
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: List[str] = None
    learning_rate: float = 2e-4
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    warmup_ratio: float = 0.1
    max_seq_length: int = 2048
    use_wandb: bool = False
    wandb_project: str = "automotive-test-generation"
    
    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


class AutomotiveModelTrainer:
    """LoRA fine-tuning system for automotive test case generation"""
    
    def __init__(self, config: LoRATrainingConfig):
        if not TRAINING_AVAILABLE:
            raise ImportError(f"Training dependencies not available: {IMPORT_ERROR}")
        
        self.config = config
        self.model = None
        self.tokenizer = None
        self.peft_model = None
        
        # Create output directories
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
    
    def prepare_model(self) -> None:
        """Load and prepare base model for LoRA training"""
        print(f"🔥 Loading base model: {self.config.base_model}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.base_model)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model with optimizations
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            use_cache=False  # Required for training
        )
        
        # Prepare LoRA configuration
        peft_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.target_modules,
        )
        
        # Apply LoRA
        self.peft_model = get_peft_model(self.model, peft_config)
        self.peft_model.print_trainable_parameters()
        
        print("✅ Model prepared for LoRA training")
    
    def prepare_dataset(self, training_file: str) -> Any:
        """Prepare dataset from collected training examples"""
        print(f"📊 Preparing dataset from: {training_file}")
        
        examples = []
        with open(training_file, 'r') as f:
            for line in f:
                examples.append(json.loads(line))
        
        print(f"📋 Loaded {len(examples)} training examples")
        
        # Format for training
        formatted_examples = []
        for example in examples:
            # Convert ChatML format to training format
            conversation = self._format_conversation(example["messages"])
            
            # Tokenize
            tokenized = self.tokenizer(
                conversation,
                max_length=self.config.max_seq_length,
                truncation=True,
                padding=False,
                return_tensors=None
            )
            
            # Add labels (same as input_ids for causal LM)
            tokenized["labels"] = tokenized["input_ids"].copy()
            formatted_examples.append(tokenized)
        
        if TRAINING_AVAILABLE:
            return Dataset.from_list(formatted_examples)
        else:
            raise ImportError("Training dependencies not available - Dataset class not imported")
    
    def _format_conversation(self, messages: List[Dict]) -> str:
        """Format ChatML messages into training text"""
        conversation = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                conversation += f"<|system|>\n{content}\n"
            elif role == "user":
                conversation += f"<|user|>\n{content}\n"
            elif role == "assistant":
                conversation += f"<|assistant|>\n{content}\n"
        
        return conversation
    
    def train(self, training_file: str) -> str:
        """Execute LoRA fine-tuning"""
        if not self.peft_model:
            self.prepare_model()
        
        # Prepare dataset
        train_dataset = self.prepare_dataset(training_file)
        
        # Initialize wandb if enabled
        if self.config.use_wandb:
            wandb.init(project=self.config.wandb_project)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            warmup_ratio=self.config.warmup_ratio,
            learning_rate=self.config.learning_rate,
            fp16=True,
            logging_steps=10,
            save_strategy="epoch",
            eval_strategy="no",  # No validation set for now
            remove_unused_columns=False,
            report_to="wandb" if self.config.use_wandb else None,
        )
        
        # Data collator
        def data_collator(features):
            batch = self.tokenizer.pad(
                features,
                padding=True,
                max_length=self.config.max_seq_length,
                return_tensors="pt"
            )
            return batch
        
        # Trainer
        trainer = Trainer(
            model=self.peft_model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=data_collator,
        )
        
        # Start training
        print("🚀 Starting LoRA fine-tuning...")
        start_time = time.time()
        
        trainer.train()
        
        training_time = time.time() - start_time
        print(f"✅ Training completed in {training_time:.2f} seconds")
        
        # Save the adapter
        adapter_path = Path(self.config.output_dir) / "adapter"
        trainer.model.save_pretrained(adapter_path)
        self.tokenizer.save_pretrained(adapter_path)
        
        # Save training metadata
        metadata = {
            "base_model": self.config.base_model,
            "training_file": training_file,
            "training_examples": len(train_dataset),
            "training_time_seconds": training_time,
            "config": self.config.__dict__,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(Path(self.config.output_dir) / "training_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"🎯 LoRA adapter saved to: {adapter_path}")
        return str(adapter_path)
    
    def merge_and_save_full_model(self, adapter_path: str, output_path: str) -> str:
        """Merge LoRA weights into base model and save full model"""
        print(f"🔄 Merging LoRA adapter into base model...")
        
        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # Load and merge adapter
        model_with_adapter = PeftModel.from_pretrained(base_model, adapter_path)
        merged_model = model_with_adapter.merge_and_unload()
        
        # Save merged model
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        merged_model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        
        print(f"✅ Merged model saved to: {output_dir}")
        return str(output_dir)
    
    def create_ollama_model(self, merged_model_path: str, model_name: str = "automotive-test-generator") -> str:
        """Create Ollama model from merged weights"""
        print(f"🦙 Creating Ollama model: {model_name}")
        
        # Create Modelfile for Ollama
        modelfile_content = f"""FROM {merged_model_path}

SYSTEM \"\"\"You are an expert automotive test engineer specializing in REQIF-based test case generation.

Generate comprehensive test cases with:
- Valid automotive signal names and interfaces  
- Realistic value ranges and units (speed in km/h, voltage in V, temperature in °C)
- Proper automotive error handling and safety scenarios
- Both positive and negative test cases for complete coverage
- JSON format output with test_type field (positive/negative)

Focus on automotive domain expertise and practical test case validity.\"\"\"

PARAMETER temperature 0.0
PARAMETER num_ctx 8192
PARAMETER num_predict 2048
PARAMETER top_k 40
PARAMETER top_p 0.9
"""
        
        modelfile_path = Path(merged_model_path).parent / "Modelfile"
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)
        
        # Create Ollama model
        import subprocess
        result = subprocess.run([
            "ollama", "create", model_name, "-f", str(modelfile_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Ollama model '{model_name}' created successfully")
            return model_name
        else:
            print(f"❌ Failed to create Ollama model: {result.stderr}")
            return ""


class AutomatedTrainingPipeline:
    """Automated pipeline for continuous model improvement"""
    
    def __init__(self, data_collector: TrainingDataCollector, trainer: AutomotiveModelTrainer):
        self.data_collector = data_collector
        self.trainer = trainer
        self.model_versions = []
    
    def check_training_readiness(self, min_examples: int = 50) -> Tuple[bool, str]:
        """Check if enough validated data is available for training"""
        stats = self.data_collector.get_collection_stats()
        validated_count = stats["files_validated"]
        
        if validated_count >= min_examples:
            return True, f"Ready for training with {validated_count} validated examples"
        else:
            return False, f"Need {min_examples - validated_count} more validated examples"
    
    def execute_training_pipeline(self, model_name: str = None) -> Dict[str, str]:
        """Execute complete training pipeline"""
        if not model_name:
            model_name = f"automotive-test-v{len(self.model_versions) + 1}"
        
        # Check readiness
        ready, message = self.check_training_readiness()
        if not ready:
            return {"status": "failed", "reason": message}
        
        # Export training data
        training_file = self.data_collector.export_training_dataset()
        
        # Train LoRA adapter
        adapter_path = self.trainer.train(training_file)
        
        # Merge and save full model
        merged_path = self.trainer.merge_and_save_full_model(
            adapter_path, 
            f"models/{model_name}"
        )
        
        # Create Ollama model
        ollama_model = self.trainer.create_ollama_model(merged_path, model_name)
        
        # Track model version
        version_info = {
            "model_name": model_name,
            "ollama_model": ollama_model,
            "adapter_path": adapter_path,
            "merged_path": merged_path,
            "training_file": training_file,
            "timestamp": datetime.now().isoformat()
        }
        
        self.model_versions.append(version_info)
        
        return {
            "status": "success",
            "model_name": ollama_model,
            "version_info": version_info
        }


if __name__ == "__main__":
    if not TRAINING_AVAILABLE:
        print(f"❌ Training dependencies not available: {IMPORT_ERROR}")
        print("Install with: pip install torch transformers peft datasets wandb")
        sys.exit(1)
    
    # Example usage
    config = LoRATrainingConfig()
    trainer = AutomotiveModelTrainer(config)
    data_collector = TrainingDataCollector()
    
    pipeline = AutomatedTrainingPipeline(data_collector, trainer)
    
    print("🧪 Automotive Model Training Pipeline Ready")
    print("Next steps:")
    print("1. Collect training data using your main application")  
    print("2. Validate examples using data_collector.approve_example()")
    print("3. Run pipeline.execute_training_pipeline() when ready")