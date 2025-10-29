"""
RAFT Data Collection Module

This module collects training data in RAFT format with context annotation support.
It saves generated test cases along with their retrieved context for expert annotation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from logging import Logger

type AugmentedRequirement = dict[str, Any]
type RAFTExample = dict[str, Any]


class RAFTDataCollector:
    """Collects training data in RAFT format with context annotation"""

    __slots__ = ("output_dir", "logger", "enabled")

    def __init__(
        self,
        output_dir: str | Path = "training_data/collected",
        logger: Logger | None = None,
        enabled: bool = True,
    ):
        """
        Initialize RAFT data collector.

        Args:
            output_dir: Directory to save collected examples
            logger: Optional logger for debug output
            enabled: Whether collection is enabled (allows no-op mode)
        """
        self.output_dir = Path(output_dir)
        self.logger = logger
        self.enabled = enabled

        if self.enabled:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            if self.logger:
                self.logger.info(f"📊 RAFT collector initialized: {self.output_dir}")

    def collect_example(
        self, requirement: AugmentedRequirement, generated_test_cases: str, model: str
    ) -> Path | None:
        """
        Collect a single RAFT training example.

        Args:
            requirement: Augmented requirement with context
            generated_test_cases: AI-generated test cases (to be validated)
            model: Model used for generation

        Returns:
            Path to saved example file, or None if collection is disabled
        """
        if not self.enabled:
            return None

        # Extract context for RAFT annotation
        heading = requirement.get("heading", "No Heading")
        info_list = requirement.get("info_list", [])
        interface_list = requirement.get("interface_list", [])

        # Build RAFT example structure
        raft_example: RAFTExample = {
            "requirement_id": requirement.get("id", "UNKNOWN"),
            "requirement_text": requirement.get("text", ""),
            "heading": heading,
            # Retrieved context (to be annotated as oracle/distractor)
            "retrieved_context": {
                "heading": {"id": "HEADING", "text": heading},
                "info_artifacts": [
                    {"id": info.get("id", f"INFO_{i}"), "text": info.get("text", "")}
                    for i, info in enumerate(info_list)
                ],
                "interfaces": [
                    {"id": iface.get("id", f"IF_{i}"), "text": iface.get("text", "")}
                    for i, iface in enumerate(interface_list)
                ],
            },
            # Generated output (to be validated by expert)
            "generated_test_cases": generated_test_cases,
            "model_used": model,
            "generation_timestamp": datetime.now().isoformat(),
            # RAFT annotation (to be filled by expert)
            "context_annotation": {
                "oracle_context": [],  # Expert fills: relevant context IDs
                "distractor_context": [],  # Expert fills: irrelevant context IDs
                "annotation_notes": "",  # Expert fills: optional notes
                "quality_rating": None,  # Expert fills: 1-5 scale
            },
            # Validation status
            "validation_status": "pending",  # pending|validated|rejected
            "annotated_by": None,
            "annotation_timestamp": None,
        }

        # Save to file
        req_id = requirement.get("id", "UNKNOWN").replace("/", "_")
        filename = f"raft_{req_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = self.output_dir / filename

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(raft_example, f, indent=2, ensure_ascii=False)

            if self.logger:
                self.logger.debug(f"📊 Saved RAFT example: {output_path.name}")

            return output_path

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to save RAFT example: {e}")
            return None

    def get_collection_stats(self) -> dict[str, int]:
        """Get statistics on collected RAFT examples"""
        if not self.enabled or not self.output_dir.exists():
            return {
                "total_collected": 0,
                "pending_annotation": 0,
                "validated": 0,
                "rejected": 0,
                "annotated": 0,
            }

        json_files = list(self.output_dir.glob("raft_*.json"))

        stats = {
            "total_collected": len(json_files),
            "pending_annotation": 0,
            "validated": 0,
            "rejected": 0,
            "annotated": 0,
        }

        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                    status = data.get("validation_status", "pending")

                    if status == "pending":
                        stats["pending_annotation"] += 1
                    elif status == "validated":
                        stats["validated"] += 1
                    elif status == "rejected":
                        stats["rejected"] += 1

                    # Check if context annotation is done
                    annotation = data.get("context_annotation", {})
                    if annotation.get("oracle_context") or annotation.get("distractor_context"):
                        stats["annotated"] += 1

            except Exception:
                continue

        return stats

    def clear_collected_data(self) -> int:
        """
        Clear all collected data (use with caution).

        Returns:
            Number of files deleted
        """
        if not self.enabled or not self.output_dir.exists():
            return 0

        json_files = list(self.output_dir.glob("raft_*.json"))
        count = 0

        for json_file in json_files:
            try:
                json_file.unlink()
                count += 1
            except Exception:
                continue

        if self.logger:
            self.logger.info(f"🗑️  Cleared {count} RAFT examples")

        return count
