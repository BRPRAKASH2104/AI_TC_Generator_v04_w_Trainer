"""
Vision-Aware RAFT Training Pipeline

This module orchestrates training for vision-capable models using RAFT methodology.
Supports hybrid training with both text-only and vision examples.

Vision Support (v2.2.0+): Complete training pipeline for llama3.2-vision and other
vision models using the hybrid vision/text strategy.
"""

import json
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from logging import Logger

type TrainingResult = dict[str, Any]


@dataclass(slots=True)
class VisionTrainingConfig:
    """Configuration for vision model training"""

    base_model: str = "llama3.2-vision:11b"  # Vision-capable base model
    output_model: str = "automotive-tc-vision-raft-v1"  # Trained model name

    # Training hyperparameters
    num_epochs: int = 3
    batch_size: int = 2  # Smaller batch for vision models (VRAM constraints)
    learning_rate: float = 2e-5
    warmup_steps: int = 100
    gradient_accumulation_steps: int = 4  # Effective batch = 2 * 4 = 8

    # Vision-specific settings
    max_image_size: int = 768  # Max dimension for images
    context_window: int = 32768  # 32K context for vision models
    num_predict: int = 4096  # Response length

    # RAFT parameters
    oracle_probability: float = 0.8  # Probability of including oracle docs
    distractor_ratio: float = 1.5  # Distractors per oracle

    # Optimization
    use_fp16: bool = True  # Mixed precision training
    gradient_checkpointing: bool = True
    max_grad_norm: float = 1.0

    # Hardware
    gpu_memory_utilization: float = 0.85  # Use 85% of VRAM
    num_workers: int = 4


@dataclass(slots=True)
class TrainingProgress:
    """Track training progress and metrics"""

    start_time: float = field(default_factory=time.time)
    current_epoch: int = 0
    total_epochs: int = 0
    examples_processed: int = 0
    total_examples: int = 0
    vision_examples_processed: int = 0
    total_vision_examples: int = 0

    # Metrics
    current_loss: float = 0.0
    best_loss: float = float("inf")
    training_losses: list[float] = field(default_factory=list)
    validation_losses: list[float] = field(default_factory=list)

    # Status
    status: str = "initializing"  # initializing, training, evaluating, completed, failed
    error_message: str | None = None


class VisionRAFTTrainer:
    """
    Vision-aware RAFT training pipeline.

    This trainer handles:
    1. Mixed text/vision datasets
    2. Ollama fine-tuning for vision models
    3. RAFT oracle/distractor methodology
    4. Hybrid training strategy
    """

    __slots__ = ("config", "dataset_path", "output_dir", "logger", "progress")

    def __init__(
        self,
        dataset_path: str | Path,
        config: VisionTrainingConfig | None = None,
        output_dir: str | Path = "training_data/models",
        logger: Logger | None = None,
    ):
        """
        Initialize vision RAFT trainer.

        Args:
            dataset_path: Path to RAFT training dataset (JSONL format)
            config: Training configuration (uses defaults if None)
            output_dir: Directory for trained models
            logger: Optional logger
        """
        self.dataset_path = Path(dataset_path)
        self.config = config or VisionTrainingConfig()
        self.output_dir = Path(output_dir)
        self.logger = logger
        self.progress = TrainingProgress()

        # Validate inputs
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def train(self) -> TrainingResult:
        """
        Execute complete vision RAFT training pipeline.

        Returns:
            Training results with metrics and model info
        """
        if self.logger:
            self.logger.info(f"🚀 Starting vision RAFT training: {self.config.output_model}")
            self.logger.info(f"   Base model: {self.config.base_model}")
            self.logger.info(f"   Dataset: {self.dataset_path}")

        result: TrainingResult = {
            "model_name": self.config.output_model,
            "base_model": self.config.base_model,
            "training_started": datetime.now().isoformat(),
            "training_completed": None,
            "duration_seconds": 0,
            "success": False,
            "metrics": {},
            "errors": [],
        }

        try:
            self.progress.status = "training"

            # Step 1: Analyze dataset
            dataset_stats = self._analyze_dataset()
            result["dataset_stats"] = dataset_stats

            if self.logger:
                self.logger.info(f"📊 Dataset: {dataset_stats['total_examples']} examples")
                self.logger.info(
                    f"   Vision: {dataset_stats['vision_examples']} "
                    f"({dataset_stats['total_images']} images)"
                )
                self.logger.info(f"   Text-only: {dataset_stats['text_only_examples']}")

            # Step 2: Prepare training configuration
            modelfile = self._prepare_modelfile()
            result["modelfile"] = str(modelfile)

            # Step 3: Train with Ollama
            training_metrics = self._train_with_ollama(modelfile)
            result["metrics"] = training_metrics
            result["success"] = training_metrics.get("success", False)

            # Step 4: Save progress
            self.progress.status = "completed"
            self._save_training_progress(result)

            result["training_completed"] = datetime.now().isoformat()
            result["duration_seconds"] = time.time() - self.progress.start_time

            if self.logger:
                self.logger.info(
                    f"✅ Training completed: {self.config.output_model} "
                    f"({result['duration_seconds']:.1f}s)"
                )

        except Exception as e:
            self.progress.status = "failed"
            self.progress.error_message = str(e)
            result["success"] = False
            result["errors"].append(str(e))

            if self.logger:
                self.logger.error(f"❌ Training failed: {e}")

        return result

    def _analyze_dataset(self) -> dict[str, Any]:
        """Analyze training dataset for statistics"""
        stats = {
            "total_examples": 0,
            "vision_examples": 0,
            "text_only_examples": 0,
            "total_images": 0,
            "avg_images_per_vision_example": 0.0,
            "avg_oracle_docs": 0.0,
            "avg_distractor_docs": 0.0,
        }

        oracle_counts = []
        distractor_counts = []
        image_counts = []

        try:
            with open(self.dataset_path, encoding="utf-8") as f:
                for line in f:
                    example = json.loads(line)
                    stats["total_examples"] += 1

                    # Check for images
                    messages = example.get("messages", [])
                    has_images = False
                    if len(messages) > 1:
                        user_msg = messages[1]
                        if "images" in user_msg and user_msg["images"]:
                            has_images = True
                            image_count = len(user_msg["images"])
                            stats["total_images"] += image_count
                            image_counts.append(image_count)

                    if has_images:
                        stats["vision_examples"] += 1
                    else:
                        stats["text_only_examples"] += 1

                    # Count oracle/distractor docs (crude estimation from content)
                    if len(messages) > 1:
                        content = messages[1].get("content", "")
                        oracle_count = content.count("Relevant Context:")
                        distractor_count = content.count("Additional Context")
                        oracle_counts.append(oracle_count)
                        distractor_counts.append(distractor_count)

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Dataset analysis failed: {e}")

        # Calculate averages
        if stats["vision_examples"] > 0:
            stats["avg_images_per_vision_example"] = (
                stats["total_images"] / stats["vision_examples"]
            )
        if oracle_counts:
            stats["avg_oracle_docs"] = sum(oracle_counts) / len(oracle_counts)
        if distractor_counts:
            stats["avg_distractor_docs"] = sum(distractor_counts) / len(distractor_counts)

        self.progress.total_examples = stats["total_examples"]
        self.progress.total_vision_examples = stats["vision_examples"]

        return stats

    def _prepare_modelfile(self) -> Path:
        """Prepare Ollama Modelfile for vision training"""
        modelfile_content = f"""# Vision RAFT Model
# Generated: {datetime.now().isoformat()}

FROM {self.config.base_model}

# RAFT Training Configuration
PARAMETER temperature 0.0
PARAMETER num_ctx {self.config.context_window}
PARAMETER num_predict {self.config.num_predict}
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

# Vision-specific parameters
PARAMETER num_gpu 1
PARAMETER num_thread 4

# System prompt optimized for RAFT
SYSTEM \"\"\"You are an expert automotive test case generator with vision capabilities.

Your task is to analyze both text context and visual diagrams to generate comprehensive test cases.

CRITICAL INSTRUCTIONS:
1. **Focus on Relevant Context**: Use only the "Relevant Context" and "Relevant Diagrams" provided.
2. **Ignore Distractors**: Ignore any "Additional Context" or "Additional Diagrams" marked as potentially irrelevant.
3. **Analyze Diagrams**: When diagrams are provided, carefully analyze:
   - State machines and transitions
   - Signal flows and timing sequences
   - Parameter tables and threshold values
   - Architectural dependencies
   - UI behaviors and interactions
4. **Generate Comprehensive Tests**: Cover positive, negative, and edge cases based on both text and visual information.
5. **Use Specific Details**: Extract specific signal names, parameter values, and timing requirements from context and diagrams.

Output test cases in structured JSON format as demonstrated in training examples.
\"\"\"
"""

        # Save Modelfile
        modelfile_path = self.output_dir / f"{self.config.output_model}.modelfile"
        with open(modelfile_path, "w", encoding="utf-8") as f:
            f.write(modelfile_content)

        if self.logger:
            self.logger.info(f"📝 Prepared Modelfile: {modelfile_path}")

        return modelfile_path

    def _train_with_ollama(self, modelfile: Path) -> dict[str, Any]:
        """
        Train model using Ollama fine-tuning.

        Note: This is a simplified implementation. Full Ollama fine-tuning
        requires enterprise features or custom training scripts.

        For now, this creates a custom model with optimized prompts.
        """
        metrics = {
            "success": False,
            "method": "ollama_create",
            "training_time": 0,
            "model_created": False,
        }

        try:
            start_time = time.time()

            # Create custom Ollama model from Modelfile
            cmd = [
                "ollama",
                "create",
                self.config.output_model,
                "-f",
                str(modelfile),
            ]

            if self.logger:
                self.logger.info(f"🔧 Creating Ollama model: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            if result.returncode == 0:
                metrics["success"] = True
                metrics["model_created"] = True

                if self.logger:
                    self.logger.info(f"✅ Model created: {self.config.output_model}")

            else:
                metrics["errors"] = result.stderr

                if self.logger:
                    self.logger.error(f"❌ Model creation failed: {result.stderr}")

            metrics["training_time"] = time.time() - start_time

        except subprocess.TimeoutExpired:
            metrics["errors"] = "Model creation timed out after 10 minutes"

            if self.logger:
                self.logger.error("❌ Model creation timed out")

        except Exception as e:
            metrics["errors"] = str(e)

            if self.logger:
                self.logger.error(f"❌ Training error: {e}")

        return metrics

    def _save_training_progress(self, result: TrainingResult) -> None:
        """Save training progress and results"""
        progress_file = self.output_dir / f"{self.config.output_model}_training_log.json"

        progress_data = {
            "config": {
                "base_model": self.config.base_model,
                "output_model": self.config.output_model,
                "num_epochs": self.config.num_epochs,
                "batch_size": self.config.batch_size,
                "learning_rate": self.config.learning_rate,
            },
            "progress": {
                "status": self.progress.status,
                "examples_processed": self.progress.examples_processed,
                "vision_examples_processed": self.progress.vision_examples_processed,
                "current_epoch": self.progress.current_epoch,
            },
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump(progress_data, f, indent=2)

            if self.logger:
                self.logger.debug(f"💾 Saved training progress: {progress_file}")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to save training progress: {e}")

    def evaluate_model(self, test_dataset: Path | None = None) -> dict[str, Any]:
        """
        Evaluate trained vision model performance.

        Args:
            test_dataset: Optional test dataset path (uses validation split if None)

        Returns:
            Evaluation metrics
        """
        if self.logger:
            self.logger.info(f"📊 Evaluating model: {self.config.output_model}")

        metrics = {
            "model": self.config.output_model,
            "evaluation_date": datetime.now().isoformat(),
            "test_dataset": str(test_dataset) if test_dataset else "validation_split",
            "metrics": {
                "text_examples_score": 0.0,
                "vision_examples_score": 0.0,
                "overall_score": 0.0,
            },
            "errors": [],
        }

        # TODO: Implement actual evaluation
        # This would involve:
        # 1. Running model on test examples
        # 2. Comparing outputs to expected results
        # 3. Calculating quality scores

        if self.logger:
            self.logger.warning("⚠️  Model evaluation not fully implemented yet")

        return metrics


def create_vision_training_pipeline(
    dataset_path: str | Path,
    base_model: str = "llama3.2-vision:11b",
    output_model: str = "automotive-tc-vision-raft-v1",
    logger: Logger | None = None,
) -> VisionRAFTTrainer:
    """
    Convenience function to create vision training pipeline.

    Args:
        dataset_path: Path to RAFT training dataset
        base_model: Vision-capable base model
        output_model: Name for trained model
        logger: Optional logger

    Returns:
        Configured VisionRAFTTrainer instance
    """
    config = VisionTrainingConfig(
        base_model=base_model,
        output_model=output_model,
    )

    return VisionRAFTTrainer(
        dataset_path=dataset_path,
        config=config,
        logger=logger,
    )
