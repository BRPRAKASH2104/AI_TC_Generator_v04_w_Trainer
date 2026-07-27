#!/usr/bin/env python3
"""Create a prompt-customized vision model using Ollama Modelfile.

This script does not fine-tune model weights. It creates a named Ollama
model with a RAFT-informed system prompt for automotive test case
generation. It:
1. Loads vision RAFT dataset (JSONL format with base64 images)
2. Creates Ollama Modelfile with optimized system prompt
3. Registers custom model in Ollama
4. Validates model creation

Usage:
    python3 utilities/train_vision_model.py

    # With custom parameters
    python3 utilities/train_vision_model.py \
        --dataset training_data/raft_dataset/vision_raft_training_dataset.jsonl \
        --base-model llama3.2-vision:11b \
        --output-model automotive-tc-vision-raft-v1

Environment Variables:
    AI_TG_DATASET_PATH: Path to RAFT dataset JSONL file
    AI_TG_BASE_MODEL: Base vision model to use (default: llama3.2-vision:11b)
    AI_TG_OUTPUT_MODEL: Output model name (default: automotive-tc-vision-raft-v1)

Example:
    # Standard usage (Modelfile creation)
    python3 utilities/train_vision_model.py

    # With custom base model
    python3 utilities/train_vision_model.py --base-model llama3.2-vision:90b

    # With custom output name
    python3 utilities/train_vision_model.py --output-model my-custom-model-v2

Hardware Requirements:
    - Minimum: 12 GB VRAM (for model loading)
    - Recommended: 24 GB VRAM (for concurrent usage)
    - Note: Modelfile creation doesn't require GPU training

See docs/training/README.md for the complete guide.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.training.judge_calibration import format_report, run_calibration  # noqa: E402
from src.training.judge_calibration_cases import DEFAULT_CALIBRATION_CASES  # noqa: E402
from src.training.vision_raft_trainer import (  # noqa: E402
    VisionRAFTTrainer,
    VisionTrainingConfig,
    create_vision_training_pipeline,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Create a prompt-customized vision model using Ollama Modelfile",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default=os.getenv(
            "AI_TG_DATASET_PATH",
            "training_data/raft_dataset/vision_raft_training_dataset.jsonl",
        ),
        help="Path to RAFT dataset JSONL file (default: training_data/raft_dataset/vision_raft_training_dataset.jsonl)",
    )

    parser.add_argument(
        "--base-model",
        type=str,
        default=os.getenv("AI_TG_BASE_MODEL", "llama3.2-vision:11b"),
        help="Base vision model to use (default: llama3.2-vision:11b)",
    )

    parser.add_argument(
        "--output-model",
        type=str,
        default=os.getenv("AI_TG_OUTPUT_MODEL", "automotive-tc-vision-raft-v1"),
        help="Output model name (default: automotive-tc-vision-raft-v1)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force model creation even if model already exists",
    )

    parser.add_argument(
        "--evaluate",
        type=str,
        default=None,
        metavar="TEST_DATASET",
        help=(
            "Evaluation-only mode: score the --output-model on this held-out "
            "RAFT dataset (JSONL) instead of creating a model. Reports the "
            "canonical-schema pass rate."
        ),
    )

    parser.add_argument(
        "--compare-base",
        action="store_true",
        help=(
            "With --evaluate, also run the --base-model over the same set and "
            "report the customized-minus-base delta. This compares the whole "
            "customized bundle (system prompt + parameters) against the base "
            "model's own defaults, not the prompt in isolation. Note: validity "
            "scores are grammar-saturated, so the unique-valid coverage delta is "
            "usually the more meaningful signal."
        ),
    )

    parser.add_argument(
        "--validate-judge",
        action="store_true",
        help=(
            "Calibration mode: score built-in gold-by-construction fixtures "
            "with the content scorer and report whether each lands in its "
            "expected band. Needs no dataset, no trained model, and no Ollama. "
            "Exits 1 on any breach."
        ),
    )

    args = parser.parse_args()

    # Calibration is a standalone mode over built-in fixtures; combining it with
    # dataset evaluation would silently run only one of them.
    if args.validate_judge and args.evaluate:
        parser.error("--validate-judge cannot be combined with --evaluate")

    # --compare-base only has meaning in evaluation mode; accepting it during
    # model creation would silently ignore it (2026-07-24 review, Optional 7).
    if args.compare_base and not args.evaluate:
        parser.error("--compare-base requires --evaluate")

    return args


def validate_dataset(dataset_path: str) -> None:
    """Validate dataset file exists.

    Args:
        dataset_path: Path to RAFT dataset JSONL file

    Raises:
        FileNotFoundError: If dataset file doesn't exist
    """
    dataset_file = Path(dataset_path)

    if not dataset_file.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {dataset_path}\n"
            "Please build the dataset first using utilities/build_vision_dataset.py\n"
            "See docs/training/README.md for the dataset preparation guide."
        )

    if dataset_file.suffix != ".jsonl":
        logger.warning(f"Dataset file should be JSONL format, got {dataset_file.suffix}")

    logger.info(
        f"Dataset file: {dataset_path} ({dataset_file.stat().st_size / 1024 / 1024:.2f} MB)"
    )


def check_ollama_connection() -> bool:
    """Check if Ollama is running and accessible.

    Returns:
        True if Ollama is accessible, False otherwise
    """
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def check_base_model_exists(base_model: str) -> bool:
    """Check if base model is available in Ollama.

    Args:
        base_model: Base model name to check

    Returns:
        True if base model exists, False otherwise
    """
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(m.get("name") == base_model for m in models)
        return False
    except Exception:
        return False


def check_output_model_exists(output_model: str) -> bool:
    """Check if output model already exists in Ollama.

    Args:
        output_model: Output model name to check

    Returns:
        True if output model exists, False otherwise
    """
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(m.get("name") == output_model for m in models)
        return False
    except Exception:
        return False


def print_training_result(result: dict[str, Any]) -> None:
    """Print model-creation result summary.

    Args:
        result: Result dictionary from VisionRAFTTrainer.train()
    """
    logger.info("")
    logger.info("=" * 60)
    if result["success"]:
        logger.info("✅ Model Created Successfully")
        logger.info("=" * 60)
        logger.info(f"Model name:       {result['model_name']}")
        logger.info(f"Duration:         {result['duration_seconds']:.1f}s")
        # These key names must match VisionRAFTTrainer's TrainResult/DatasetStats
        # exactly. Reading keys the trainer never emits turned a successful
        # `ollama create` into a KeyError and exit 1 (2026-07-26 review, Critical 4).
        logger.info(f"Modelfile:        {result.get('modelfile', 'N/A')}")
        logger.info("")
        logger.info("Dataset Statistics:")
        stats = result["dataset_stats"]
        logger.info(f"  Total examples:     {stats['total_examples']}")
        logger.info(
            f"  Vision examples:    {stats['vision_examples']} ({stats['total_images']} images)"
        )
        logger.info(f"  Text-only examples: {stats['text_only_examples']}")
        if stats["vision_examples"] > 0:
            logger.info(f"  Avg images/example: {stats['avg_images_per_vision_example']:.2f}")
        logger.info("")
        logger.info("Next steps:")
        logger.info(
            "  1. Test model: ai-tc-generator input/sample.reqifz --model " + result["model_name"]
        )
        logger.info("  2. Compare with base model output")
        logger.info("  3. Deploy: export OLLAMA__VISION_MODEL=" + result["model_name"])
        logger.info("  4. See docs/training/README.md for the evaluation guide")
    else:
        logger.error("❌ Model Creation Failed")
        logger.error("=" * 60)
        errors = result.get("errors", [])
        for error in errors:
            logger.error(f"  Error: {error}")
        logger.error("")
        logger.error("Troubleshooting:")
        logger.error("  1. Check Ollama is running: ollama serve")
        logger.error("  2. Verify base model: ollama list | grep " + result.get("base_model", ""))
        logger.error("  3. Check Modelfile syntax in training_data/models/")
        logger.error("  4. See docs/training/README.md for troubleshooting")

    logger.info("=" * 60)
    logger.info("")


def _format_delta(value: float | None) -> str:
    """Format a signed delta, or ``n/a`` when it could not be computed."""
    return "n/a" if value is None else f"{value:+.2f}"


def print_evaluation_result(result: dict[str, Any]) -> None:
    """Print an evaluation summary, including the A/B delta when present.

    Args:
        result: Result dictionary from ``VisionRAFTTrainer.evaluate_model()``.
    """
    metrics = result["metrics"]
    text_score = metrics.get("text_examples_score")
    vision_score = metrics.get("vision_examples_score")
    text_str = "n/a" if text_score is None else f"{text_score:.2f}"
    vision_str = "n/a" if vision_score is None else f"{vision_score:.2f}"

    logger.info("")
    logger.info("=" * 60)
    logger.info("Vision RAFT Model Evaluation")
    logger.info("=" * 60)
    logger.info(f"Model:            {result['model']}")
    logger.info(f"Test dataset:     {result['test_dataset']}")
    logger.info(
        f"Examples:         {metrics.get('total_examples', 0)} "
        f"(text: {metrics.get('text_examples', 0)}, vision: {metrics.get('vision_examples', 0)})"
    )
    logger.info(
        f"Overall score:    {metrics.get('overall_score', 0.0):.2f}  (canonical-schema pass rate)"
    )
    logger.info(f"  Text score:     {text_str}")
    logger.info(f"  Vision score:   {vision_str}")
    logger.info(f"Parse success:    {metrics.get('parse_success_rate', 0.0):.2f}")
    logger.info(
        f"Unique valid TCs: {metrics.get('unique_valid_test_cases_per_example', 0.0):.2f}"
        "/example  (canonical-valid, deduplicated)"
    )
    logger.info(
        f"Raw TCs/example:  {metrics.get('raw_test_cases_per_example', 0.0):.2f}  "
        "(output volume, not coverage)"
    )
    content_f1 = metrics.get("content_f1")
    if content_f1 is not None:
        logger.info(
            f"Content F1:       {content_f1:.2f}  <- reference-aware quality "
            "(the meaningful signal when references exist)"
        )
        logger.info(
            f"  Precision:      {metrics.get('content_precision', 0.0):.2f}   "
            f"Recall: {metrics.get('content_recall', 0.0):.2f}"
        )
    if result["errors"]:
        logger.warning(f"{len(result['errors'])} example(s) failed to generate:")
        for error in result["errors"]:
            logger.warning(f"  - {error}")

    if "baseline" in result:
        base_metrics = result["baseline"]["metrics"]
        delta = result.get("delta")
        comparison = result.get("comparison") or {}
        logger.info("-" * 60)
        logger.info(f"Baseline model:   {result['baseline']['model']}")
        logger.info(f"  Base overall:   {base_metrics.get('overall_score', 0.0):.2f}")
        logger.info(
            f"  Base coverage:  "
            f"{base_metrics.get('unique_valid_test_cases_per_example', 0.0):.2f} "
            "unique-valid TCs/example"
        )
        base_errors = result["baseline"]["errors"]
        if base_errors:
            logger.warning(f"{len(base_errors)} baseline example(s) failed to generate:")
            for error in base_errors:
                logger.warning(f"  - {error}")
        if comparison:
            logger.info(
                f"Comparison:       {comparison.get('status', 'unknown')} "
                f"({comparison.get('paired_examples', 0)}/{comparison.get('total_examples', 0)} "
                "paired example(s))"
            )
        if delta is None:
            logger.warning(
                "Delta withheld: the baseline produced no usable observation, "
                "so no customized-vs-base lift can be claimed."
            )
        else:
            logger.info("Delta (customized - base, paired examples only):")
            logger.info(f"  Overall score:  {_format_delta(delta.get('overall_score'))}")
            logger.info(
                f"  Coverage:       "
                f"{_format_delta(delta.get('unique_valid_test_cases_per_example'))} "
                "unique-valid TCs/example  <- the meaningful signal "
                "(validity is grammar-saturated)"
            )
            logger.info(
                f"  Raw volume:     {_format_delta(delta.get('raw_test_cases_per_example'))} "
                "TCs/example  (includes duplicates and invalid output)"
            )
            if delta.get("content_f1") is not None:
                logger.info(
                    f"  Content F1:     {_format_delta(delta.get('content_f1'))}  "
                    "<- reference-aware quality delta (the meaningful signal)"
                )
            provenance = result.get("provenance")
            if provenance:
                logger.info(
                    "  NB: compares the customized BUNDLE (system prompt + parameters) "
                    "vs the base model's own defaults (NOT parameter-matched); "
                    "it does not isolate the prompt's effect."
                )

    logger.info("=" * 60)
    logger.info("")


def run_evaluation(
    test_dataset: str,
    output_model: str,
    compare_base: bool = False,
    base_model: str | None = None,
) -> int:
    """Evaluate a customized model on a held-out RAFT dataset and print metrics.

    Args:
        test_dataset: Path to the held-out RAFT dataset (JSONL).
        output_model: Name of the customized Ollama model to evaluate.
        compare_base: When True, also evaluate the base model and print the
            customized-minus-base delta.
        base_model: Base model used for the ``compare_base`` comparison. None
            keeps ``VisionTrainingConfig``'s default.

    Returns:
        0 if at least one example was evaluated without a generation error
        (and, when comparing, the baseline produced at least one usable paired
        observation), 1 if the dataset is missing/empty, every example failed,
        or the requested baseline comparison could not be established.
    """
    test_path = Path(test_dataset)
    if not test_path.exists():
        logger.error(f"Evaluation dataset not found: {test_dataset}")
        return 1

    # Only override base_model when provided, so the config default still
    # applies.
    config_kwargs: dict[str, Any] = {"output_model": output_model}
    if base_model is not None:
        config_kwargs["base_model"] = base_model
    config = VisionTrainingConfig(**config_kwargs)

    trainer = VisionRAFTTrainer(
        dataset_path=test_path,
        config=config,
        logger=logger,
    )
    result = trainer.evaluate_model(test_dataset=test_path, compare_base=compare_base)
    print_evaluation_result(result)

    total = result["metrics"].get("total_examples", 0)
    failed = len(result["errors"])
    # A requested comparison whose baseline never produced a usable paired
    # observation cannot support the A/B claim; fail instead of exiting 0
    # alongside a withheld delta (2026-07-24 review, Critical 1).
    comparison = result.get("comparison") or {}
    baseline_unusable = comparison.get("status") == "failed"
    # Nothing scored (empty set or every example errored) is not a usable result.
    return 1 if total == 0 or failed >= total or baseline_unusable else 0


def run_judge_calibration() -> int:
    """Calibrate the content scorer against the built-in fixtures and print a scorecard.

    Returns:
        0 when every declared band held, 1 when any band was breached or the
        scorer faulted.
    """
    from src.training.content_scorer import ReferenceOverlapScorer

    config = VisionTrainingConfig()
    scorer = ReferenceOverlapScorer(config.content_match_threshold)
    report = run_calibration(scorer, "overlap", DEFAULT_CALIBRATION_CASES)

    print(format_report([report]))
    return 0 if report["passed"] else 1


def main() -> int:
    """Create a prompt-customized vision model from the RAFT dataset.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Parse arguments
        args = parse_args()

        # Set log level
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Verbose logging enabled")

        # Calibration-only mode: validate the content scorer against built-in
        # fixtures. Needs no dataset, no trained model, and no Ollama.
        if args.validate_judge:
            return run_judge_calibration()

        # Evaluation-only mode: score an existing customized model on a held-out
        # dataset. This is a separate path - the training dataset and the base /
        # output-model existence guards below are irrelevant here.
        if args.evaluate:
            logger.info("Checking Ollama connection...")
            if not check_ollama_connection():
                logger.error("Cannot connect to Ollama at http://localhost:11434")
                logger.error("Please ensure Ollama is running: ollama serve")
                return 1
            logger.info("✅ Ollama is running")
            return run_evaluation(
                args.evaluate,
                args.output_model,
                args.compare_base,
                args.base_model,
            )

        # Validate dataset
        logger.info("Validating dataset...")
        validate_dataset(args.dataset)

        # Check Ollama connection
        logger.info("Checking Ollama connection...")
        if not check_ollama_connection():
            logger.error("Cannot connect to Ollama at http://localhost:11434")
            logger.error("Please ensure Ollama is running: ollama serve")
            return 1
        logger.info("✅ Ollama is running")

        # Check base model
        logger.info(f"Checking base model '{args.base_model}'...")
        if not check_base_model_exists(args.base_model):
            logger.error(f"Base model '{args.base_model}' not found in Ollama")
            logger.error(f"Please install: ollama pull {args.base_model}")
            return 1
        logger.info(f"✅ Base model '{args.base_model}' is available")

        # Check if output model already exists
        if check_output_model_exists(args.output_model):
            if args.force:
                logger.warning(
                    f"Output model '{args.output_model}' already exists, overwriting (--force)"
                )
            else:
                logger.error(f"Output model '{args.output_model}' already exists")
                logger.error("Use --force to overwrite or choose a different --output-model name")
                return 1

        # Model creation summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("Vision RAFT Prompt-Customized Model Creation")
        logger.info("=" * 60)
        logger.info(f"Dataset:      {args.dataset}")
        logger.info(f"Base model:   {args.base_model}")
        logger.info(f"Output model: {args.output_model}")
        logger.info("Method:       Ollama Modelfile (custom system prompt)")
        logger.info("=" * 60)
        logger.info("")

        # Create training pipeline
        logger.info("Creating training pipeline...")
        trainer = create_vision_training_pipeline(
            dataset_path=args.dataset,
            base_model=args.base_model,
            output_model=args.output_model,
            logger=logger,
        )

        # Create the customized model
        logger.info("Creating model...")
        logger.info("")
        result = trainer.train()

        # Print result
        print_training_result(result)

        # Return exit code
        return 0 if result["success"] else 1

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during training: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
