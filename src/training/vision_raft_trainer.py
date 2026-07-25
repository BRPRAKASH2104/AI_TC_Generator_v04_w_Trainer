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
import binascii
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

    from src.training.content_scorer import ContentScore, ContentScorer

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

    # Evaluation input bounds (evaluate_model). Malformed or oversized held-out
    # data must be rejected before any model call, not spike memory mid-run
    # (2026-07-24 review, Recommended 3).
    max_eval_examples: int = 5000  # Reject held-out sets larger than this
    max_images_per_example: int = 16  # Reject examples carrying more images
    max_image_bytes: int = 10 * 1024 * 1024  # Reject a single decoded image above 10 MB

    # Phase 3 content metric: minimum field similarity for a generated case to
    # count as covering a reference case (reuses the deduplicator's 0.85).
    content_match_threshold: float = 0.85

    # Phase 3b LLM-judge: the fixed evaluator model used by LLMJudgeScorer,
    # independent of the model under test and identical across the A/B passes.
    judge_model: str = "llama3.1:8b"

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

    def _customized_model_parameters(self) -> dict[str, float | int]:
        """The generation-control PARAMETERs baked into the customized Modelfile.

        Single source of truth shared by ``_prepare_modelfile`` (which writes
        these into the Modelfile) and the evaluation ``provenance`` block (which
        reports them), so the recorded provenance can never drift from the
        model actually created (2026-07-24 review, Recommended 4).

        Returns:
            An ordered mapping of Ollama generation parameter -> value.
        """
        return {
            "temperature": 0.0,
            "num_ctx": self.config.context_window,
            "num_predict": self.config.num_predict,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
        }

    def _prepare_modelfile(self) -> Path:
        """Build a static Ollama Modelfile for prompt customization.

        The system prompt is fixed and is not derived from the RAFT dataset;
        `_analyze_dataset` statistics are for reporting only (review
        2026-07-20 finding 6).
        """
        parameter_lines = "\n".join(
            f"PARAMETER {name} {value}"
            for name, value in self._customized_model_parameters().items()
        )
        modelfile_content = f"""# Vision RAFT Model
# Generated: {datetime.now().isoformat()}

FROM {self.config.base_model}

# RAFT Training Configuration
{parameter_lines}

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
        self,
        test_dataset: Path | None = None,
        client: Any = None,
        compare_base: bool = False,
        content_scorer: ContentScorer | None = None,
    ) -> dict[str, Any]:
        """Evaluate the prompt-customized model's output quality on held-out data.

        Runs the customized model over every example in ``test_dataset`` and
        scores each generation by the canonical-schema pass rate - the same
        ``is_canonical_test_case`` gate the production pipeline applies. This
        measures whether the model emits valid, parseable canonical test cases;
        it does not compare against the reference answer (that is a later phase).

        With ``compare_base=True``, the untouched base model is run over the same
        examples and the result gains ``baseline``, ``comparison`` and ``delta``
        (customized minus base) blocks. The delta is *paired*: it is computed
        only over examples both models generated for without error, and it is
        withheld (None, ``comparison.status == "failed"``) when no such example
        exists - a failed baseline must not be reported as lift.

        Args:
            test_dataset: Path to a JSONL file of held-out RAFT examples. This
                is required: no validation split is produced yet, so there is no
                honest default to fall back on.
            client: Ollama client used for generation. Defaults to a fresh
                ``OllamaClient``; injectable so tests can supply a deterministic
                fake instead of shelling out to a live model.
            compare_base: When True, also evaluate ``config.base_model`` and add
                ``baseline`` and ``delta`` blocks to the result.
            content_scorer: A ``ContentScorer`` used to score each generation
                against its example's reference answer. Defaults to a
                ``ReferenceOverlapScorer`` built from
                ``config.content_match_threshold``; injectable so tests can
                supply a deterministic fake.

        Returns:
            A metrics dict with keys ``model``, ``evaluation_date``,
            ``test_dataset``, ``metrics`` (aggregate scores and counts),
            ``per_example`` (per-example detail) and ``errors``. When
            ``compare_base`` is True it also carries ``baseline`` (the base
            model's ``model``/``metrics``/``per_example``/``errors``),
            ``comparison`` (pairing status and both sides' failure counts, see
            ``_compare_paired``) and ``delta`` (per-metric customized-minus-base
            over paired examples; None when the comparison failed, per-metric
            None where a metric is absent on either side).

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

        if content_scorer is None:
            from src.training.content_scorer import ReferenceOverlapScorer

            content_scorer = ReferenceOverlapScorer(self.config.content_match_threshold)

        examples = self._load_and_validate_examples(test_dataset)
        metrics, per_example = self._score_over_dataset(
            client, examples, self.config.output_model, content_scorer
        )

        if self.logger:
            self.logger.info(
                f"✅ Evaluation complete: canonical-pass score "
                f"{metrics['overall_score']:.2f} over {metrics['total_examples']} example(s)"
            )

        result: dict[str, Any] = {
            "model": self.config.output_model,
            "evaluation_date": datetime.now().isoformat(),
            "test_dataset": str(test_dataset),
            "metrics": metrics,
            "per_example": per_example,
            "errors": self._collect_errors(per_example),
        }

        if compare_base:
            if self.logger:
                self.logger.info(
                    f"📊 Evaluating base model for comparison: {self.config.base_model}"
                )
            base_metrics, base_per_example = self._score_over_dataset(
                client, examples, self.config.base_model, content_scorer
            )
            result["baseline"] = {
                "model": self.config.base_model,
                "metrics": base_metrics,
                "per_example": base_per_example,
                "errors": self._collect_errors(base_per_example),
            }
            result["comparison"], result["delta"] = self._compare_paired(
                per_example, base_per_example
            )
            result["provenance"] = self._comparison_provenance()

        return result

    def _comparison_provenance(self) -> dict[str, Any]:
        """Describe what the A/B delta actually compares.

        The customized Modelfile changes both the ``SYSTEM`` prompt and the
        generation ``PARAMETER``s, while the base model runs with its own
        defaults and no seed is set. The delta therefore measures the whole
        customized *bundle* against the base model, not the isolated effect of
        the system prompt (2026-07-24 review, Recommended 4). This block records
        that so the delta is not read as a causal prompt-only result.

        Returns:
            A provenance dict naming both models, the customized generation
            parameters, and a caveat about what the comparison does not isolate.
        """
        return {
            "customized_model": {
                "name": self.config.output_model,
                "kind": "prompt-customized bundle (custom SYSTEM prompt + PARAMETER overrides)",
                "parameters": self._customized_model_parameters(),
            },
            "base_model": {
                "name": self.config.base_model,
                "kind": "unmodified base model",
                "parameters": "model defaults (NOT matched to the customized parameters)",
            },
            "note": (
                "The delta reflects the full customized model bundle (its system prompt AND "
                "generation parameters) versus the base model's own defaults; it does not "
                "isolate the effect of the system prompt alone, and no fixed seed is set."
            ),
        }

    def _compare_paired(
        self, custom_rows: list[dict[str, Any]], base_rows: list[dict[str, Any]]
    ) -> tuple[dict[str, Any], dict[str, float | None] | None]:
        """Compare customized vs base metrics over rows both sides evaluated.

        A row where either side failed to generate carries zero-filled scores,
        so an unpaired aggregate delta would credit the surviving side with
        artificial lift — a totally failed baseline previously reported pure
        positive lift (2026-07-24 review, Critical 1). The delta is therefore
        computed only over rows with no generation error on either side; when
        no such row exists it is withheld entirely.

        Args:
            custom_rows: Per-example detail for the customized model.
            base_rows: Per-example detail for the base model, same order.

        Returns:
            A ``(comparison, delta)`` tuple. ``comparison`` carries ``status``
            (``complete`` when every row paired, ``partial`` when some did,
            ``failed`` when none did), ``paired_examples``, ``total_examples``
            and both sides' failure counts. ``delta`` is None when the status
            is ``failed``.
        """
        paired = [
            (custom, base)
            for custom, base in zip(custom_rows, base_rows, strict=True)
            if custom["error"] is None and base["error"] is None
        ]

        delta: dict[str, float | None] | None = None
        if not paired:
            status = "failed"
        else:
            status = "complete" if len(paired) == len(custom_rows) else "partial"
            delta = self._compute_delta(
                self._aggregate_eval_metrics([custom for custom, _ in paired]),
                self._aggregate_eval_metrics([base for _, base in paired]),
            )

        comparison = {
            "status": status,
            "paired_examples": len(paired),
            "total_examples": len(custom_rows),
            "custom_failures": sum(1 for row in custom_rows if row["error"]),
            "baseline_failures": sum(1 for row in base_rows if row["error"]),
        }
        return comparison, delta

    def _score_over_dataset(
        self,
        client: Any,
        examples: list[dict[str, Any]],
        model_name: str,
        content_scorer: ContentScorer,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Run one model over every example and aggregate the scores.

        Args:
            client: Ollama client used for generation.
            examples: Loaded RAFT examples.
            model_name: The Ollama model to evaluate.
            content_scorer: A ``ContentScorer`` used to score each generation
                against its example's reference answer.

        Returns:
            A tuple of (aggregate metrics, per-example detail).
        """
        per_example = [
            self._evaluate_example(client, example, index, model_name, content_scorer)
            for index, example in enumerate(examples)
        ]
        return self._aggregate_eval_metrics(per_example), per_example

    @staticmethod
    def _collect_errors(per_example: list[dict[str, Any]]) -> list[str]:
        """Collect per-example error strings into a flat list.

        Args:
            per_example: Per-example detail dicts.

        Returns:
            One ``"example {index}: {error}"`` string per errored example.
        """
        return [f"example {r['index']}: {r['error']}" for r in per_example if r["error"]]

    @staticmethod
    def _compute_delta(customized: dict[str, Any], base: dict[str, Any]) -> dict[str, float | None]:
        """Compute customized-minus-base deltas for the comparable numeric metrics.

        Args:
            customized: Aggregate metrics for the customized model.
            base: Aggregate metrics for the base model.

        Returns:
            Per-metric deltas; None where the metric is absent on either side
            (e.g. a score with no examples of that kind).
        """
        comparable = (
            "overall_score",
            "text_examples_score",
            "vision_examples_score",
            "parse_success_rate",
            "raw_test_cases_per_example",
            "unique_valid_test_cases_per_example",
            "content_precision",
            "content_recall",
            "content_f1",
            "content_quality",
        )
        delta: dict[str, float | None] = {}
        for key in comparable:
            new_value, base_value = customized.get(key), base.get(key)
            if new_value is None or base_value is None:
                delta[key] = None
            else:
                delta[key] = new_value - base_value
        return delta

    def _load_and_validate_examples(self, path: Path) -> list[dict[str, Any]]:
        """Load a JSONL RAFT dataset and validate its contract before any model call.

        Malformed or oversized held-out data must fail fast with a clear error
        rather than abort mid-run with an opaque ``AttributeError`` or spike
        memory decoding an unbounded image (2026-07-24 review, Recommended 3).
        Each non-blank line must be a JSON object carrying a ``messages`` list
        with a user message (role ``user`` or index 1) whose ``content`` is a
        string; any ``images`` must be a list of valid base64 strings, each
        within ``config.max_image_bytes`` and no more than
        ``config.max_images_per_example`` per example. The dataset must be
        non-empty and hold at most ``config.max_eval_examples`` examples.

        Args:
            path: Path to the JSONL file.

        Returns:
            One validated example dict per non-blank line.

        Raises:
            ValueError: On an empty dataset, an over-limit dataset, or any line
                that violates the contract (the message names the 1-based line).
        """
        examples: list[dict[str, Any]] = []
        with open(path, encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                if len(examples) >= self.config.max_eval_examples:
                    raise ValueError(
                        f"Evaluation dataset exceeds the {self.config.max_eval_examples}-example "
                        "limit (config.max_eval_examples); split it or raise the limit."
                    )
                try:
                    parsed = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"line {line_number}: invalid JSON ({exc})") from exc
                self._validate_example_contract(parsed, line_number)
                examples.append(parsed)

        if not examples:
            raise ValueError(f"Evaluation dataset is empty (no examples): {path}")
        return examples

    def _validate_example_contract(self, example: Any, line_number: int) -> None:
        """Validate one loaded example against the RAFT evaluation contract.

        Args:
            example: The parsed JSON value for a single dataset line.
            line_number: 1-based line number, used in error messages.

        Raises:
            ValueError: If the example is not a well-formed, size-bounded RAFT
                message object.
        """
        if not isinstance(example, dict):
            raise ValueError(
                f"line {line_number}: each example must be a JSON object, got "
                f"{type(example).__name__}"
            )

        messages = example.get("messages")
        if not isinstance(messages, list) or len(messages) < 2:
            raise ValueError(
                f"line {line_number}: 'messages' must be a list with at least a "
                "system and a user message"
            )

        # The RAFT builder emits [system, user, assistant]; the user turn is at
        # index 1. Accept an explicit role match too, in case of reordering.
        user_message = next(
            (m for m in messages if isinstance(m, dict) and m.get("role") == "user"),
            messages[1] if isinstance(messages[1], dict) else None,
        )
        if user_message is None:
            raise ValueError(f"line {line_number}: no user message found in 'messages'")

        content = user_message.get("content")
        if not isinstance(content, str):
            raise ValueError(
                f"line {line_number}: user message 'content' must be a string, got "
                f"{type(content).__name__}"
            )

        images = user_message.get("images")
        if images is not None:
            self._validate_images(images, line_number)

    def _validate_images(self, images: Any, line_number: int) -> None:
        """Validate the user message's ``images`` field.

        Args:
            images: The raw ``images`` value from the user message.
            line_number: 1-based line number, used in error messages.

        Raises:
            ValueError: If ``images`` is not a list of valid, size-bounded
                base64 strings within the per-example count limit.
        """
        if not isinstance(images, list):
            raise ValueError(
                f"line {line_number}: 'images' must be a list, got {type(images).__name__}"
            )
        if len(images) > self.config.max_images_per_example:
            raise ValueError(
                f"line {line_number}: {len(images)} images exceeds the per-example limit of "
                f"{self.config.max_images_per_example} (config.max_images_per_example)"
            )
        for position, encoded in enumerate(images):
            if not isinstance(encoded, str):
                raise ValueError(
                    f"line {line_number}: image {position} must be a base64 string, got "
                    f"{type(encoded).__name__}"
                )
            # Reject oversized images by their encoded length (~4/3 of the decoded
            # size) BEFORE decoding, so an unbounded string never hits memory.
            approx_decoded_bytes = len(encoded) * 3 // 4
            if approx_decoded_bytes > self.config.max_image_bytes:
                raise ValueError(
                    f"line {line_number}: image {position} is too large "
                    f"(~{approx_decoded_bytes} bytes > {self.config.max_image_bytes}-byte limit, "
                    "config.max_image_bytes)"
                )
            try:
                base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise ValueError(
                    f"line {line_number}: image {position} is not valid base64 ({exc})"
                ) from exc

    def _evaluate_example(
        self,
        client: Any,
        example: dict[str, Any],
        index: int,
        model_name: str,
        content_scorer: ContentScorer,
    ) -> dict[str, Any]:
        """Generate for one example and score the output.

        Args:
            client: Ollama client used for generation.
            example: A RAFT example with a ``messages`` list.
            index: Zero-based position of the example in the dataset.
            model_name: The Ollama model to run for this example.
            content_scorer: A ``ContentScorer`` used to score the generation
                against the example's reference answer.

        Returns:
            Per-example detail: index, has_images, parsed, num_test_cases,
            canonical_valid, unique_valid, invalid_test_cases,
            duplicate_test_cases, score, content, and error (None on success).
        """
        result: dict[str, Any] = {
            "index": index,
            "has_images": False,
            "parsed": False,
            "num_test_cases": 0,
            "canonical_valid": 0,
            "unique_valid": 0,
            "invalid_test_cases": 0,
            "duplicate_test_cases": 0,
            "content": None,
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
            raw_output = self._generate_for_example(
                client, user_message.get("content", ""), images, model_name
            )
        except Exception as exc:
            # One bad example must not abort the whole run; record and score 0.
            # `except Exception` (not a bare except) mirrors the generation
            # pipeline's own resilience pattern in generators.py.
            result["error"] = f"generation failed: {exc}"
            return result

        result.update(self._score_generation(raw_output))
        result["content"] = self._score_content(raw_output, example, content_scorer, client)
        return result

    def _generate_for_example(
        self, client: Any, prompt: str, images: list[str], model_name: str
    ) -> Any:
        """Run one model on one example, routing by image presence.

        Args:
            client: Ollama client used for generation.
            prompt: The example's user-message content.
            images: Base64-encoded image strings (empty for text-only examples).
            model_name: The Ollama model to run.

        Returns:
            The raw model response text (typed ``Any`` because the client is
            injectable and therefore untyped at this boundary).
        """
        from src.core.validators import TEST_CASE_RESPONSE_JSON_SCHEMA

        if images:
            with self._decoded_image_paths(images) as image_paths:
                return client.generate_response_with_vision(
                    model_name,
                    prompt,
                    image_paths,
                    is_json=True,
                    return_full_response=False,
                    format_schema=TEST_CASE_RESPONSE_JSON_SCHEMA,
                )

        return client.generate_completion(
            model_name,
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

        Beyond the raw object count, this also computes ``unique_valid`` - the
        number of canonical-valid cases that survive the *production*
        deduplicator (``TestCaseDeduplicator``, ``DEFAULT_FIELDS_TO_COMPARE``).
        Raw count is output volume and rewards duplicate or invalid bulk output
        (2026-07-24 review, Critical 2); ``unique_valid`` is the count that
        actually reflects distinct, usable coverage.

        Args:
            raw_output: The raw model response (text, or a dict coerced to text).

        Returns:
            parsed (did valid ``test_cases`` JSON come back), num_test_cases
            (raw object count), canonical_valid (count passing the canonical
            gate), unique_valid (canonical-valid cases after deduplication),
            invalid_test_cases and duplicate_test_cases counts, and score
            (canonical_valid / num_test_cases, 0.0 when nothing parsed).
        """
        from src.core.deduplicator import TestCaseDeduplicator
        from src.core.parsers import JSONResponseParser
        from src.core.validators import is_canonical_test_case

        empty = {
            "parsed": False,
            "num_test_cases": 0,
            "canonical_valid": 0,
            "unique_valid": 0,
            "invalid_test_cases": 0,
            "duplicate_test_cases": 0,
            "score": 0.0,
        }

        text = raw_output if isinstance(raw_output, str) else json.dumps(raw_output)
        parsed = JSONResponseParser.extract_json_from_response(text)

        if not parsed or not isinstance(parsed.get("test_cases"), list):
            return empty

        test_cases = parsed["test_cases"]
        num_test_cases = len(test_cases)
        valid_cases = [tc for tc in test_cases if is_canonical_test_case(tc)]
        canonical_valid = len(valid_cases)

        # Deduplicate only the canonical-valid cases, using the same fields and
        # threshold the production pipeline applies, so "coverage" counts
        # distinct usable scenarios rather than repeated or malformed output.
        if valid_cases:
            deduped, _ = TestCaseDeduplicator().deduplicate(valid_cases)
            unique_valid = len(deduped)
        else:
            unique_valid = 0

        score = canonical_valid / num_test_cases if num_test_cases else 0.0

        return {
            "parsed": True,
            "num_test_cases": num_test_cases,
            "canonical_valid": canonical_valid,
            "unique_valid": unique_valid,
            "invalid_test_cases": num_test_cases - canonical_valid,
            "duplicate_test_cases": canonical_valid - unique_valid,
            "score": score,
        }

    @staticmethod
    def _canonical_unique_cases(raw_output: str | dict[str, Any]) -> list[dict[str, Any]]:
        """Parse a raw response into canonical, deduplicated test cases.

        Shared by generated-output and reference-answer parsing for the content
        metric, so both sides are normalized identically to the production
        pipeline.

        Args:
            raw_output: Raw model response or reference answer (text or dict).

        Returns:
            Canonical-valid, deduplicated test-case dicts (possibly empty).
        """
        from src.core.deduplicator import TestCaseDeduplicator
        from src.core.parsers import JSONResponseParser
        from src.core.validators import is_canonical_test_case

        text = raw_output if isinstance(raw_output, str) else json.dumps(raw_output)
        parsed = JSONResponseParser.extract_json_from_response(text)
        if not parsed or not isinstance(parsed.get("test_cases"), list):
            return []
        valid = [tc for tc in parsed["test_cases"] if is_canonical_test_case(tc)]
        if not valid:
            return []
        deduped, _ = TestCaseDeduplicator().deduplicate(valid)
        return deduped

    @staticmethod
    def _reference_answer(example: dict[str, Any]) -> str | None:
        """Return the example's reference assistant answer, or None if absent.

        Args:
            example: A RAFT example dict.

        Returns:
            The assistant message content if present and non-blank, else None.
        """
        for message in example.get("messages", []):
            if isinstance(message, dict) and message.get("role") == "assistant":
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content
        return None

    def _score_content(
        self,
        raw_output: str | dict[str, Any],
        example: dict[str, Any],
        content_scorer: ContentScorer,
        client: Any,
    ) -> ContentScore | None:
        """Score one generation against the example's reference answer.

        Args:
            raw_output: The raw model response.
            example: The RAFT example (source of the reference answer).
            content_scorer: A ContentScorer implementation.
            client: The Ollama client, threaded to scorers that call a model
                (the deterministic scorer ignores it).

        Returns:
            A ContentScore dict, or None when there is no usable reference or the
            scorer raises (isolated like per-example generation errors).
        """
        reference_raw = self._reference_answer(example)
        if reference_raw is None:
            return None
        try:
            generated = self._canonical_unique_cases(raw_output)
            reference = self._canonical_unique_cases(reference_raw)
            return content_scorer.score(
                generated, reference, client=client, judge_model=self.config.judge_model
            )
        except Exception:  # noqa: BLE001 - a scorer fault must not abort the run
            return None

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
        total_raw_cases = sum(r["num_test_cases"] for r in per_example)
        total_unique_valid = sum(r["unique_valid"] for r in per_example)

        content_rows = [r for r in per_example if r.get("content") is not None]

        # Each aggregate below is a per-field macro-mean over only the examples
        # where that field is defined (`is not None`), not over `content_rows`
        # as a whole. By design (see `ReferenceOverlapScorer.score`), a
        # zero-case generation yields precision=None (0/0 is undefined) but
        # recall=0.0/f1=0.0 (defined against a non-empty reference). So
        # `content_precision` may be averaged over fewer examples than
        # `content_recall`/`content_f1` — this asymmetry is intentional, not a
        # bug.
        def mean_content(field: str) -> float | None:
            values = [
                r["content"][field] for r in content_rows if r["content"].get(field) is not None
            ]
            return sum(values) / len(values) if values else None

        return {
            "text_examples_score": mean_score(text_rows),
            "vision_examples_score": mean_score(vision_rows),
            "overall_score": overall if overall is not None else 0.0,
            "total_examples": total,
            "text_examples": len(text_rows),
            "vision_examples": len(vision_rows),
            "parse_success_rate": parse_ok / total if total else 0.0,
            # Raw object count is output volume, not coverage. The decision
            # metric is unique_valid_test_cases_per_example, which counts only
            # canonical-valid, deduplicated cases (2026-07-24 review, Critical 2).
            "raw_test_cases_per_example": total_raw_cases / total if total else 0.0,
            "unique_valid_test_cases_per_example": (total_unique_valid / total if total else 0.0),
            # Phase 3 content metric (reference-aware); None when no example
            # carried a usable reference answer.
            "content_precision": mean_content("precision"),
            "content_recall": mean_content("recall"),
            "content_f1": mean_content("f1"),
            # Phase 3b LLM-judge holistic quality (complementary to F1); None
            # unless an LLM judge scored at least one example.
            "content_quality": mean_content("quality"),
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
