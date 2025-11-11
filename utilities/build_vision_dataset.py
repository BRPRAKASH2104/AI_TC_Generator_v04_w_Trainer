#!/usr/bin/env python3
"""Build vision RAFT dataset from validated training examples.

This script builds a vision-capable RAFT training dataset from validated
and annotated examples collected during requirement processing. It:
1. Loads validated examples from training_data/validated/
2. Filters by minimum quality threshold
3. Creates Ollama-compatible JSONL format with base64-encoded images
4. Saves dataset for vision model training

Usage:
    python3 utilities/build_vision_dataset.py

    # With custom paths and quality threshold
    python3 utilities/build_vision_dataset.py \
        --validated-dir training_data/validated \
        --output-dir training_data/raft_dataset \
        --min-quality 4 \
        --filename custom_dataset_name

Environment Variables:
    AI_TG_MIN_QUALITY: Minimum quality rating (1-5, default: 3)
    AI_TG_VALIDATED_DIR: Path to validated examples directory
    AI_TG_OUTPUT_DIR: Path to output dataset directory

Example:
    # Standard usage
    python3 utilities/build_vision_dataset.py

    # High quality examples only
    python3 utilities/build_vision_dataset.py --min-quality 4

    # Custom paths
    python3 utilities/build_vision_dataset.py \
        --validated-dir /path/to/validated \
        --output-dir /path/to/output

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

from src.training.raft_dataset_builder import RAFTDatasetBuilder  # noqa: E402

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
        description="Build vision RAFT dataset from validated examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--validated-dir",
        type=str,
        default=os.getenv("AI_TG_VALIDATED_DIR", "training_data/validated"),
        help="Directory containing validated examples (default: training_data/validated)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.getenv("AI_TG_OUTPUT_DIR", "training_data/raft_dataset"),
        help="Output directory for RAFT dataset (default: training_data/raft_dataset)",
    )

    parser.add_argument(
        "--min-quality",
        type=int,
        default=int(os.getenv("AI_TG_MIN_QUALITY", "3")),
        choices=[1, 2, 3, 4, 5],
        help="Minimum quality rating to include (1-5, default: 3)",
    )

    parser.add_argument(
        "--filename",
        type=str,
        default="vision_raft_training_dataset",
        help="Output filename (without extension, default: vision_raft_training_dataset)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def validate_paths(validated_dir: str) -> None:
    """Validate input paths.

    Args:
        validated_dir: Path to validated examples directory

    Raises:
        FileNotFoundError: If validated directory doesn't exist
        ValueError: If no validated examples found
    """
    validated_path = Path(validated_dir)

    if not validated_path.exists():
        raise FileNotFoundError(
            f"Validated directory not found: {validated_dir}\n"
            "Please annotate and move examples to training_data/validated/ first.\n"
            "See docs/training/training_guideline.md for annotation guide."
        )

    # Check for JSON files
    json_files = list(validated_path.glob("*.json"))
    if not json_files:
        raise ValueError(
            f"No validated examples found in {validated_dir}\n"
            "Please annotate and move examples from training_data/collected/ first."
        )

    logger.info(f"Found {len(json_files)} validated examples in {validated_dir}")


def print_dataset_stats(raft_examples: list[dict[str, Any]]) -> None:
    """Print dataset statistics.

    Args:
        raft_examples: List of RAFT training examples
    """
    if not raft_examples:
        logger.warning("No examples in dataset!")
        return

    total = len(raft_examples)
    vision_examples = [ex for ex in raft_examples if ex.get("has_images", False)]
    text_examples = [ex for ex in raft_examples if not ex.get("has_images", False)]
    total_images = sum(len(ex.get("images", [])) for ex in vision_examples)

    logger.info("")
    logger.info("=" * 60)
    logger.info("Dataset Statistics")
    logger.info("=" * 60)
    logger.info(f"Total examples:       {total}")
    logger.info(
        f"Vision examples:      {len(vision_examples)} ({len(vision_examples) / total * 100:.1f}%)"
    )
    logger.info(
        f"Text-only examples:   {len(text_examples)} ({len(text_examples) / total * 100:.1f}%)"
    )
    logger.info(f"Total images:         {total_images}")
    if vision_examples:
        logger.info(f"Avg images/example:   {total_images / len(vision_examples):.2f}")
    logger.info("=" * 60)
    logger.info("")


def main() -> int:
    """Build vision RAFT dataset from validated examples.

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

        # Validate paths
        logger.info("Validating input paths...")
        validate_paths(args.validated_dir)

        # Create output directory
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {args.output_dir}")

        # Build dataset
        logger.info("")
        logger.info("=" * 60)
        logger.info("Building Vision RAFT Dataset")
        logger.info("=" * 60)
        logger.info(f"Validated examples: {args.validated_dir}")
        logger.info(f"Output directory:   {args.output_dir}")
        logger.info(f"Min quality:        {args.min_quality}")
        logger.info(f"Output filename:    {args.filename}")
        logger.info("=" * 60)
        logger.info("")

        builder = RAFTDatasetBuilder(
            validated_dir=args.validated_dir,
            output_dir=args.output_dir,
            logger=logger,
        )

        # Build dataset with quality filtering
        logger.info(f"Building dataset (min_quality={args.min_quality})...")
        raft_examples = builder.build_dataset(min_quality=args.min_quality)

        if not raft_examples:
            logger.error(f"No examples met quality threshold (min_quality={args.min_quality})")
            logger.error("Try lowering --min-quality or improving annotation quality")
            return 1

        logger.info(f"✅ Built {len(raft_examples)} RAFT training examples")

        # Print statistics
        print_dataset_stats(raft_examples)

        # Save dataset
        logger.info(f"Saving dataset as '{args.filename}'...")
        jsonl_path, json_path = builder.save_dataset(raft_examples, filename=args.filename)

        # Success summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Dataset Build Complete")
        logger.info("=" * 60)
        logger.info(f"JSONL file: {jsonl_path}")
        logger.info(f"JSON file:  {json_path}")
        logger.info(f"Examples:   {len(raft_examples)}")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Review dataset statistics above")
        logger.info("  2. Train vision model with utilities/train_vision_model.py")
        logger.info("  3. See docs/training/training_guideline.md for details")
        logger.info("=" * 60)

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during dataset build: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
