#!/usr/bin/env python3
"""Train vision RAFT model using Ollama Modelfile.

This script trains a custom vision-capable model for automotive test case
generation using the RAFT methodology. It:
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

See docs/training/training_guideline.md for complete guide.
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

from src.training.vision_raft_trainer import create_vision_training_pipeline  # noqa: E402

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
        description="Train vision RAFT model using Ollama Modelfile",
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

    return parser.parse_args()


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
            "See docs/training/training_guideline.md for dataset preparation guide."
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
    """Print training result summary.

    Args:
        result: Training result dictionary from VisionRAFTTrainer
    """
    logger.info("")
    logger.info("=" * 60)
    if result["success"]:
        logger.info("✅ Training Completed Successfully")
        logger.info("=" * 60)
        logger.info(f"Model name:       {result['model_name']}")
        logger.info(f"Duration:         {result['duration_seconds']:.1f}s")
        logger.info(f"Modelfile:        {result.get('modelfile_path', 'N/A')}")
        logger.info("")
        logger.info("Dataset Statistics:")
        stats = result["dataset_stats"]
        logger.info(f"  Total examples:     {stats['total_examples']}")
        logger.info(
            f"  Vision examples:    {stats['vision_examples']} ({stats['total_images']} images)"
        )
        logger.info(f"  Text-only examples: {stats['text_examples']}")
        if stats["vision_examples"] > 0:
            logger.info(f"  Avg images/example: {stats['avg_images_per_example']:.2f}")
        logger.info("")
        logger.info("Next steps:")
        logger.info(
            "  1. Test model: ai-tc-generator input/sample.reqifz --model " + result["model_name"]
        )
        logger.info("  2. Compare with base model output")
        logger.info("  3. Deploy: export OLLAMA__VISION_MODEL=" + result["model_name"])
        logger.info("  4. See docs/training/training_guideline.md for evaluation guide")
    else:
        logger.error("❌ Training Failed")
        logger.error("=" * 60)
        errors = result.get("errors", [])
        for error in errors:
            logger.error(f"  Error: {error}")
        logger.error("")
        logger.error("Troubleshooting:")
        logger.error("  1. Check Ollama is running: ollama serve")
        logger.error("  2. Verify base model: ollama list | grep " + result.get("base_model", ""))
        logger.error("  3. Check Modelfile syntax in training_data/models/")
        logger.error("  4. See docs/training/training_guideline.md for troubleshooting")

    logger.info("=" * 60)
    logger.info("")


def main() -> int:
    """Train vision RAFT model.

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

        # Training summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("Vision RAFT Model Training")
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

        # Train model
        logger.info("Starting training...")
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
