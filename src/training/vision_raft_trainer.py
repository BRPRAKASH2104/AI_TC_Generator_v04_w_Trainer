"""
Vision-Aware RAFT Prompt-Customized Model Creation

This module does not fine-tune model weights. It builds an Ollama Modelfile
(FROM + PARAMETER + SYSTEM, no ADAPTER) with a fixed system prompt, then runs
`ollama create` to register it as a named model - a prompt customization, not
a trained model (review 2026-07-17 finding 3). The RAFT dataset is analyzed
for reporting statistics only; its contents do not currently alter the
Modelfile or system prompt (review 2026-07-20 finding 6). Supports both
text-only and vision RAFT datasets.

Vision Support (v2.2.0+): Modelfile creation for llama3.2-vision and other
vision models using the hybrid vision/text strategy.

Evaluation: `evaluate_model` runs the customized model over a held-out RAFT
dataset and scores each generation by the canonical-schema pass rate (the same
gate the production pipeline applies). It measures output validity, not
closeness to the reference answer.
"""

import base64
import json
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator
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
    Creates a prompt-customized Ollama model from a RAFT dataset.

    This class handles:
    1. Mixed text/vision dataset analysis
    2. Ollama Modelfile creation (system-prompt customization, not
       weight-level fine-tuning - see module docstring)
    3. RAFT oracle/distractor methodology (reflected in the system prompt)
    4. Hybrid vision/text strategy
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
        Create a prompt-customized Ollama model from the RAFT dataset.

        Returns:
            Creation results with metrics and model info
        """
        if self.logger:
            self.logger.info(f"🚀 Creating prompt-customized model: {self.config.output_model}")
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

            # Step 2: Prepare the Modelfile (system-prompt customization)
            modelfile = self._prepare_modelfile()
            result["modelfile"] = str(modelfile)

            # Step 3: Register the customized model with Ollama
            training_metrics = self._train_with_ollama(modelfile)
            result["metrics"] = training_metrics
            succeeded = training_metrics.get("success", False)
            result["success"] = succeeded

            # Populate final fields before persisting so the saved log is
            # consistent regardless of outcome.
            result["training_completed"] = datetime.now().isoformat()
            result["duration_seconds"] = time.time() - self.progress.start_time

            if succeeded:
                # Step 4: Persist a completed run
                self.progress.status = "completed"
                self._save_training_progress(result)
                if self.logger:
                    self.logger.info(
                        f"✅ Model created: {self.config.output_model} "
                        f"({result['duration_seconds']:.1f}s)"
                    )
            else:
                # Model creation failed. `_train_with_ollama` stores the cause
                # under metrics["errors"]; surface it at the top level so the
                # CLI failure printer (which reads result["errors"]) shows it.
                self.progress.status = "failed"
                error_detail = str(training_metrics.get("errors") or "Model creation failed")
                self.progress.error_message = error_detail
                result["errors"].append(error_detail)
                self._save_training_progress(result)
                if self.logger:
                    self.logger.error(
                        f"❌ Model creation failed: {self.config.output_model} ({error_detail})"
                    )

        except Exception as e:
            self.progress.status = "failed"
            self.progress.error_message = str(e)
            result["success"] = False
            result["errors"].append(str(e))

            if self.logger:
                self.logger.error(f"❌ Model creation failed: {e}")

        return result

    def _analyze_dataset(self) -> dict[str, Any]:
        """Analyze training dataset for statistics"""
        stats: dict[str, Any] = {
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
        """Build a static Ollama Modelfile for prompt customization.

        The system prompt is fixed and is not derived from the RAFT dataset;
        `_analyze_dataset` statistics are for reporting only (review
        2026-07-20 finding 6).
        """
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
        Register the Modelfile as a named model via `ollama create`.

        This is prompt customization, not fine-tuning: no adapter or weight
        update is produced. Real fine-tuning would require a training
        framework producing an adapter applied via Ollama's ADAPTER
        directive, or imported fine-tuned/fused weights.
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

    def evaluate_model(
        self, test_dataset: Path | None = None, client: Any = None
    ) -> dict[str, Any]:
        """Evaluate the prompt-customized model's output quality on held-out data.

        Runs the customized model over every example in ``test_dataset`` and
        scores each generation by the canonical-schema pass rate - the same
        ``is_canonical_test_case`` gate the production pipeline applies. This
        measures whether the model emits valid, parseable canonical test cases;
        it does not compare against the reference answer (that is a later phase).

        Args:
            test_dataset: Path to a JSONL file of held-out RAFT examples. This
                is required: no validation split is produced yet, so there is no
                honest default to fall back on.
            client: Ollama client used for generation. Defaults to a fresh
                ``OllamaClient``; injectable so tests can supply a deterministic
                fake instead of shelling out to a live model.

        Returns:
            A metrics dict with keys ``model``, ``evaluation_date``,
            ``test_dataset``, ``metrics`` (aggregate scores and counts),
            ``per_example`` (per-example detail) and ``errors``.

        Raises:
            ValueError: If ``test_dataset`` is None.
            FileNotFoundError: If ``test_dataset`` does not exist.
        """
        if test_dataset is None:
            raise ValueError(
                "evaluate_model requires an explicit test_dataset path: no held-out "
                "validation split is produced yet. Pass a JSONL file of held-out "
                "RAFT examples."
            )

        test_dataset = Path(test_dataset)
        if not test_dataset.exists():
            raise FileNotFoundError(f"Test dataset not found: {test_dataset}")

        if self.logger:
            self.logger.info(f"📊 Evaluating model: {self.config.output_model}")

        if client is None:
            # Imported lazily to keep module import light and avoid coupling the
            # trainer to the core generation stack at import time.
            from src.core.ollama_client import OllamaClient

            client = OllamaClient()

        examples = self._load_jsonl_examples(test_dataset)
        per_example = [
            self._evaluate_example(client, example, index) for index, example in enumerate(examples)
        ]
        metrics = self._aggregate_eval_metrics(per_example)
        errors = [f"example {r['index']}: {r['error']}" for r in per_example if r["error"]]

        if self.logger:
            self.logger.info(
                f"✅ Evaluation complete: canonical-pass score "
                f"{metrics['overall_score']:.2f} over {metrics['total_examples']} example(s)"
            )

        return {
            "model": self.config.output_model,
            "evaluation_date": datetime.now().isoformat(),
            "test_dataset": str(test_dataset),
            "metrics": metrics,
            "per_example": per_example,
            "errors": errors,
        }

    @staticmethod
    def _load_jsonl_examples(path: Path) -> list[dict[str, Any]]:
        """Load a JSONL RAFT dataset into a list of example dicts.

        Args:
            path: Path to the JSONL file.

        Returns:
            One dict per non-blank line.
        """
        examples: list[dict[str, Any]] = []
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    examples.append(json.loads(stripped))
        return examples

    def _evaluate_example(self, client: Any, example: dict[str, Any], index: int) -> dict[str, Any]:
        """Generate for one example and score the output.

        Args:
            client: Ollama client used for generation.
            example: A RAFT example with a ``messages`` list.
            index: Zero-based position of the example in the dataset.

        Returns:
            Per-example detail: index, has_images, parsed, num_test_cases,
            canonical_valid, score, and error (None on success).
        """
        result: dict[str, Any] = {
            "index": index,
            "has_images": False,
            "parsed": False,
            "num_test_cases": 0,
            "canonical_valid": 0,
            "score": 0.0,
            "error": None,
        }

        messages = example.get("messages", [])
        if len(messages) < 2:
            result["error"] = "example missing user message"
            return result

        user_message = messages[1]
        images = user_message.get("images") or []
        result["has_images"] = bool(images)

        try:
            raw_output = self._generate_for_example(client, user_message.get("content", ""), images)
        except Exception as exc:
            # One bad example must not abort the whole run; record and score 0.
            # `except Exception` (not a bare except) mirrors the generation
            # pipeline's own resilience pattern in generators.py.
            result["error"] = f"generation failed: {exc}"
            return result

        result.update(self._score_generation(raw_output))
        return result

    def _generate_for_example(self, client: Any, prompt: str, images: list[str]) -> Any:
        """Run the customized model on one example, routing by image presence.

        Args:
            client: Ollama client used for generation.
            prompt: The example's user-message content.
            images: Base64-encoded image strings (empty for text-only examples).

        Returns:
            The raw model response text (typed ``Any`` because the client is
            injectable and therefore untyped at this boundary).
        """
        from src.core.validators import TEST_CASE_RESPONSE_JSON_SCHEMA

        if images:
            with self._decoded_image_paths(images) as image_paths:
                return client.generate_response_with_vision(
                    self.config.output_model,
                    prompt,
                    image_paths,
                    is_json=True,
                    return_full_response=False,
                    format_schema=TEST_CASE_RESPONSE_JSON_SCHEMA,
                )

        return client.generate_completion(
            self.config.output_model,
            prompt,
            is_json=True,
            return_full_response=False,
            format_schema=TEST_CASE_RESPONSE_JSON_SCHEMA,
        )

    @staticmethod
    @contextmanager
    def _decoded_image_paths(images: list[str]) -> Iterator[list[Path]]:
        """Decode base64 image strings to temporary files for the vision method.

        The RAFT dataset stores images as base64 strings, but the vision client
        expects file paths. Files are written to a temp directory and removed
        when the context exits.

        Args:
            images: Base64-encoded image strings.

        Yields:
            Paths to the decoded temporary image files.
        """
        tmp_dir = Path(tempfile.mkdtemp(prefix="raft_eval_img_"))
        try:
            paths: list[Path] = []
            for position, encoded in enumerate(images):
                image_path = tmp_dir / f"image_{position}.png"
                image_path.write_bytes(base64.b64decode(encoded))
                paths.append(image_path)
            yield paths
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @staticmethod
    def _score_generation(raw_output: str | dict[str, Any]) -> dict[str, Any]:
        """Parse a raw model response and score it by canonical-schema pass rate.

        Args:
            raw_output: The raw model response (text, or a dict coerced to text).

        Returns:
            parsed (did valid ``test_cases`` JSON come back), num_test_cases,
            canonical_valid (count passing the canonical gate), and score
            (canonical_valid / num_test_cases, 0.0 when nothing parsed).
        """
        from src.core.parsers import JSONResponseParser
        from src.core.validators import is_canonical_test_case

        text = raw_output if isinstance(raw_output, str) else json.dumps(raw_output)
        parsed = JSONResponseParser.extract_json_from_response(text)

        if not parsed or not isinstance(parsed.get("test_cases"), list):
            return {"parsed": False, "num_test_cases": 0, "canonical_valid": 0, "score": 0.0}

        test_cases = parsed["test_cases"]
        num_test_cases = len(test_cases)
        canonical_valid = sum(1 for tc in test_cases if is_canonical_test_case(tc))
        score = canonical_valid / num_test_cases if num_test_cases else 0.0

        return {
            "parsed": True,
            "num_test_cases": num_test_cases,
            "canonical_valid": canonical_valid,
            "score": score,
        }

    @staticmethod
    def _aggregate_eval_metrics(per_example: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate per-example results into summary metrics.

        Args:
            per_example: Per-example detail dicts from ``_evaluate_example``.

        Returns:
            Aggregate scores and counts. ``text_examples_score`` and
            ``vision_examples_score`` are None when no example of that kind
            exists, rather than a fabricated 0.0.
        """
        total = len(per_example)
        text_rows = [r for r in per_example if not r["has_images"]]
        vision_rows = [r for r in per_example if r["has_images"]]

        def mean_score(rows: list[dict[str, Any]]) -> float | None:
            return sum(r["score"] for r in rows) / len(rows) if rows else None

        overall = mean_score(per_example)
        parse_ok = sum(1 for r in per_example if r["parsed"])
        total_test_cases = sum(r["num_test_cases"] for r in per_example)

        return {
            "text_examples_score": mean_score(text_rows),
            "vision_examples_score": mean_score(vision_rows),
            "overall_score": overall if overall is not None else 0.0,
            "total_examples": total,
            "text_examples": len(text_rows),
            "vision_examples": len(vision_rows),
            "parse_success_rate": parse_ok / total if total else 0.0,
            "avg_test_cases_per_example": total_test_cases / total if total else 0.0,
        }


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
        output_model: Name for the created model
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
