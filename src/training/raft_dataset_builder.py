"""
RAFT Training Dataset Builder

This module builds RAFT training datasets from annotated examples,
converting them to Ollama fine-tuning format.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from logging import Logger

type RAFTTrainingExample = dict[str, Any]


class RAFTDatasetBuilder:
    """Builds RAFT training dataset from annotated examples"""

    __slots__ = ("validated_dir", "output_dir", "logger")

    def __init__(
        self,
        validated_dir: str | Path = "training_data/validated",
        output_dir: str | Path = "training_data/raft_dataset",
        logger: Logger | None = None,
    ):
        """
        Initialize RAFT dataset builder.

        Args:
            validated_dir: Directory containing annotated/validated examples
            output_dir: Directory to save RAFT training dataset
            logger: Optional logger for output
        """
        self.validated_dir = Path(validated_dir)
        self.output_dir = Path(output_dir)
        self.logger = logger

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_dataset(self, min_quality: int = 3) -> list[RAFTTrainingExample]:
        """
        Build RAFT training dataset from annotated examples.

        RAFT format:
        {
            "question": "<requirement text>",
            "oracle_context": ["<relevant doc 1>", "<relevant doc 2>"],
            "distractor_context": ["<irrelevant doc 1>", "<irrelevant doc 2>"],
            "answer": "<validated test cases>"
        }

        Args:
            min_quality: Minimum quality rating (1-5) to include in dataset

        Returns:
            List of RAFT training examples
        """
        if not self.validated_dir.exists():
            if self.logger:
                self.logger.warning(f"Validated directory does not exist: {self.validated_dir}")
            return []

        annotated_files = list(self.validated_dir.glob("raft_*.json"))

        if not annotated_files:
            if self.logger:
                self.logger.warning(f"No annotated examples found in {self.validated_dir}")
            return []

        raft_examples = []

        for file_path in annotated_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                # Skip if not properly annotated
                annotation = data.get("context_annotation", {})
                if not annotation.get("oracle_context"):
                    if self.logger:
                        self.logger.debug(f"Skipping {file_path.name}: No oracle context annotated")
                    continue

                # Skip low quality examples
                quality = annotation.get("quality_rating", 0)
                if quality and quality < min_quality:
                    if self.logger:
                        self.logger.debug(
                            f"Skipping {file_path.name}: Quality {quality} < {min_quality}"
                        )
                    continue

                # Build RAFT example
                raft_example = self._build_raft_example(data)
                raft_examples.append(raft_example)

            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Skipping {file_path}: {e}")
                continue

        if self.logger:
            self.logger.info(f"✅ Built {len(raft_examples)} RAFT training examples")

        return raft_examples

    def _build_raft_example(self, data: dict[str, Any]) -> RAFTTrainingExample:
        """Convert annotated example to RAFT format"""

        # Extract oracle and distractor IDs
        annotation = data["context_annotation"]
        oracle_ids = set(annotation["oracle_context"])
        distractor_ids = set(annotation["distractor_context"])

        # Retrieve context items
        ctx = data["retrieved_context"]

        # Build oracle documents (relevant context)
        oracle_docs = []
        distractor_docs = []

        # Process heading
        if "HEADING" in oracle_ids:
            oracle_docs.append(f"Heading: {ctx['heading']['text']}")
        elif "HEADING" in distractor_ids:
            distractor_docs.append(f"Heading: {ctx['heading']['text']}")

        # Process info artifacts
        for info in ctx["info_artifacts"]:
            doc_text = f"Information: {info['text']}"
            if info["id"] in oracle_ids:
                oracle_docs.append(doc_text)
            elif info["id"] in distractor_ids:
                distractor_docs.append(doc_text)

        # Process interfaces
        for iface in ctx["interfaces"]:
            doc_text = f"Interface {iface['id']}: {iface['text']}"
            if iface["id"] in oracle_ids:
                oracle_docs.append(doc_text)
            elif iface["id"] in distractor_ids:
                distractor_docs.append(doc_text)

        # Build RAFT training example
        return {
            "question": f"Generate comprehensive test cases for requirement {data['requirement_id']}: {data['requirement_text']}",
            "oracle_context": oracle_docs,
            "distractor_context": distractor_docs,
            "answer": data["generated_test_cases"],
            "metadata": {
                "requirement_id": data["requirement_id"],
                "quality_rating": annotation.get("quality_rating"),
                "annotation_notes": annotation.get("annotation_notes", ""),
                "original_model": data.get("model_used"),
            },
        }

    def save_dataset(
        self, raft_examples: list[RAFTTrainingExample], filename: str = "raft_training_dataset"
    ) -> tuple[Path, Path]:
        """
        Save RAFT dataset in Ollama fine-tuning format.

        Args:
            raft_examples: List of RAFT training examples
            filename: Base filename (without extension)

        Returns:
            Tuple of (jsonl_path, json_path)
        """
        if not raft_examples:
            raise ValueError("No RAFT examples to save")

        # Convert to conversation format for Ollama
        training_data = []

        for example in raft_examples:
            # RAFT prompt: Include oracle + distractor context, model learns to use oracle
            context_str = "Relevant Context:\n"
            context_str += "\n".join(f"- {doc}" for doc in example["oracle_context"])

            if example["distractor_context"]:
                context_str += "\n\nAdditional Context (may not be relevant):\n"
                context_str += "\n".join(f"- {doc}" for doc in example["distractor_context"])

            # Ollama conversation format
            conversation = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert automotive test case generator. Use only the relevant context to generate high-quality test cases. Ignore irrelevant information.",
                    },
                    {"role": "user", "content": f"{context_str}\n\n{example['question']}"},
                    {"role": "assistant", "content": example["answer"]},
                ],
                "metadata": example.get("metadata", {}),
            }
            training_data.append(conversation)

        # Save as JSONL (Ollama fine-tuning format)
        jsonl_path = self.output_dir / f"{filename}.jsonl"

        with open(jsonl_path, "w", encoding="utf-8") as f:
            for item in training_data:
                f.write(json.dumps(item) + "\n")

        if self.logger:
            self.logger.info(f"✅ Saved RAFT dataset (JSONL): {jsonl_path}")
            self.logger.info(f"   Examples: {len(training_data)}")

        # Also save as regular JSON for inspection
        json_path = self.output_dir / f"{filename}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)

        if self.logger:
            self.logger.info(f"✅ Saved RAFT dataset (JSON): {json_path}")

        return jsonl_path, json_path

    def get_dataset_stats(self) -> dict[str, Any]:
        """Get statistics on the RAFT dataset"""
        jsonl_files = list(self.output_dir.glob("*.jsonl"))
        json_files = list(self.output_dir.glob("*.json"))

        stats = {
            "jsonl_files": len(jsonl_files),
            "json_files": len(json_files),
            "latest_dataset": None,
            "total_examples": 0,
        }

        # Get stats from latest JSONL file
        if jsonl_files:
            latest = max(jsonl_files, key=lambda p: p.stat().st_mtime)
            stats["latest_dataset"] = latest.name

            with open(latest, encoding="utf-8") as f:
                stats["total_examples"] = sum(1 for _ in f)

        return stats

    def validate_dataset(self, dataset_path: Path) -> dict[str, Any]:
        """
        Validate RAFT dataset format and quality.

        Args:
            dataset_path: Path to RAFT dataset (JSONL or JSON)

        Returns:
            Validation report with issues and statistics
        """
        issues = []
        stats = {
            "total_examples": 0,
            "with_oracle_context": 0,
            "with_distractor_context": 0,
            "avg_oracle_docs": 0,
            "avg_distractor_docs": 0,
        }

        try:
            if dataset_path.suffix == ".jsonl":
                with open(dataset_path, encoding="utf-8") as f:
                    examples = [json.loads(line) for line in f]
            else:
                with open(dataset_path, encoding="utf-8") as f:
                    examples = json.load(f)

            oracle_counts = []
            distractor_counts = []

            for i, example in enumerate(examples):
                stats["total_examples"] += 1

                # Check required fields
                if "messages" not in example:
                    issues.append(f"Example {i}: Missing 'messages' field")
                    continue

                messages = example["messages"]
                if len(messages) != 3:
                    issues.append(f"Example {i}: Expected 3 messages, got {len(messages)}")

                # Check for oracle/distractor context in user message
                user_msg = messages[1]["content"] if len(messages) > 1 else ""

                if "Relevant Context:" in user_msg:
                    stats["with_oracle_context"] += 1
                    # Count oracle docs (crude estimation)
                    oracle_count = user_msg.count("- ") if "Relevant Context:" in user_msg else 0
                    oracle_counts.append(oracle_count)

                if "Additional Context" in user_msg:
                    stats["with_distractor_context"] += 1
                    # Estimate distractor count
                    distractor_section = (
                        user_msg.split("Additional Context")[-1]
                        if "Additional Context" in user_msg
                        else ""
                    )
                    distractor_count = distractor_section.count("- ")
                    distractor_counts.append(distractor_count)

            # Calculate averages
            if oracle_counts:
                stats["avg_oracle_docs"] = sum(oracle_counts) / len(oracle_counts)
            if distractor_counts:
                stats["avg_distractor_docs"] = sum(distractor_counts) / len(distractor_counts)

        except Exception as e:
            issues.append(f"Critical error: {e}")

        return {"valid": len(issues) == 0, "issues": issues, "stats": stats}
