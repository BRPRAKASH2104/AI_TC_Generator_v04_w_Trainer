"""
Base processor for the AI Test Case Generator.

This module provides the base class with shared logic for both standard
and high-performance processors, eliminating code duplication.
"""

import time
from pathlib import Path
from typing import Any

from ..config import ConfigManager
from ..file_processing_logger import FileProcessingLogger
from ..training.raft_collector import RAFTDataCollector
from ..yaml_prompt_manager import YAMLPromptManager

# Type aliases
type ProcessingResult = dict[str, Any]
type AugmentedRequirement = dict[str, Any]


class BaseProcessor:
    """Base processor containing shared logic for REQIFZ file processing"""

    __slots__ = (
        "config",
        "logger",
        "yaml_manager",
        "extractor",
        "generator",
        "formatter",
        "raft_collector",
    )

    def __init__(
        self,
        config: ConfigManager = None,
        extractor=None,  # Dependency injection
        generator=None,  # Dependency injection
        formatter=None,  # Dependency injection
    ):
        self.config = config or ConfigManager()
        self.logger = None  # Will be initialized per file
        self.yaml_manager = YAMLPromptManager()

        # Dependencies - either injected or initialized by subclasses
        self.extractor = extractor
        self.generator = generator
        self.formatter = formatter

        # RAFT data collector (initialized if RAFT is enabled)
        self.raft_collector = None
        if self.config.training.enable_raft:
            self.raft_collector = RAFTDataCollector(
                output_dir=Path(self.config.training.training_data_dir) / "collected",
                logger=None,  # Logger will be set per file
                enabled=True,
            )

    def _initialize_logger(self, reqifz_path: Path) -> None:
        """Initialize file-specific logger"""
        self.logger = FileProcessingLogger(
            reqifz_file=reqifz_path.name, input_path=str(reqifz_path.parent)
        )

        # Update RAFT collector logger if enabled
        if self.raft_collector:
            self.raft_collector.logger = self.logger

    def _extract_artifacts(self, reqifz_path: Path) -> list[dict[str, Any]] | None:
        """
        Extract artifacts from REQIFZ file

        Args:
            reqifz_path: Path to REQIFZ file

        Returns:
            List of artifacts or None if extraction fails
        """
        self.logger.info("📂 Extracting artifacts from REQIFZ file...")
        artifacts = self.extractor.extract_reqifz_content(reqifz_path)

        if not artifacts:
            self.logger.error("No artifacts found in REQIFZ file")
            return None

        return artifacts

    def _build_augmented_requirements(
        self, artifacts: list[dict[str, Any]]
    ) -> tuple[list[AugmentedRequirement], int]:
        """
        Build context-aware augmented requirements from artifacts.

        This method implements the core context-aware processing logic (v03 restoration):
        - Tracks current heading context
        - Collects information artifacts since last heading
        - Augments system requirements with full context

        Args:
            artifacts: Raw artifacts from REQIFZ file

        Returns:
            Tuple of (augmented_requirements, system_interfaces_count)
        """
        # Classify artifacts and separate system interfaces (global context)
        classified_artifacts = self.extractor.classify_artifacts(artifacts)
        system_interfaces = classified_artifacts.get("System Interface", [])

        # Context-aware artifact processing (v03 restoration)
        augmented_requirements = []
        current_heading = "No Heading"
        info_since_heading = []

        self.logger.info(f"🎯 Building context for {len(artifacts)} artifacts...")
        self.logger.info(f"🔌 Found {len(system_interfaces)} system interfaces (global context)")

        for obj in artifacts:
            # Update context based on artifact type
            if obj.get("type") == "Heading":
                current_heading = obj.get("text", "No Heading")
                info_since_heading = []
                self.logger.debug(f"📌 Context heading: {current_heading}")
                continue

            elif obj.get("type") == "Information":
                info_since_heading.append(obj)
                self.logger.debug(f"📝 Stored information artifact: {id(obj)}")
                continue

            elif obj.get("type") == "System Requirement":
                # Augment requirement with collected context
                # FIX: Process ALL System Requirements, not just those with tables (v03 compatibility)
                req_id = obj.get("id", "UNKNOWN")
                req_text = obj.get("text", "")

                # Skip if no text content (empty requirements)
                if not req_text or not req_text.strip():
                    self.logger.debug(f"⚠️  Skipping requirement {req_id}: no text content")
                    continue

                self.logger.debug(
                    f"⚡ Augmenting requirement: {req_id} (heading: {current_heading})"
                )

                augmented_requirement = obj.copy()
                augmented_requirement.update(
                    {
                        "heading": current_heading,
                        "info_list": info_since_heading.copy(),
                        "interface_list": system_interfaces,
                    }
                )
                augmented_requirements.append(augmented_requirement)

                # Reset information context after processing requirement
                info_since_heading = []

        if not augmented_requirements:
            self.logger.warning("No System Requirements found for test generation")
        else:
            self.logger.info(
                f"📋 Built {len(augmented_requirements)} context-enriched requirements"
            )

        return augmented_requirements, len(system_interfaces)

    def _generate_output_path(self, reqifz_path: Path, model: str, output_dir: Path = None) -> Path:
        """
        Generate output file path for Excel file

        Args:
            reqifz_path: Source REQIFZ file path
            model: AI model name
            output_dir: Optional output directory

        Returns:
            Path for output Excel file
        """
        output_directory = output_dir or reqifz_path.parent
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        model_safe = model.replace(":", "_").replace("/", "_")

        output_filename = f"{reqifz_path.stem}_TCD_{model_safe}_{timestamp}.xlsx"
        output_path = output_directory / output_filename

        return output_path

    def _create_metadata(
        self,
        model: str,
        template: str,
        reqifz_path: Path,
        total_cases: int,
        requirements_processed: int,
        successful_requirements: int,
    ) -> dict[str, Any]:
        """Create metadata dictionary for Excel output"""
        return {
            "model": model,
            "template": template or "auto-selected",
            "source_file": str(reqifz_path),
            "total_cases": total_cases,
            "requirements_processed": requirements_processed,
            "successful_requirements": successful_requirements,
        }

    def _create_success_result(
        self,
        output_path: Path,
        total_test_cases: int,
        requirements_processed: int,
        successful_requirements: int,
        artifacts_count: int,
        processing_time: float,
        model: str,
        template: str = None,
    ) -> ProcessingResult:
        """Create success result dictionary"""
        return {
            "success": True,
            "output_file": str(output_path),
            "total_test_cases": total_test_cases,
            "requirements_processed": requirements_processed,
            "successful_requirements": successful_requirements,
            "artifacts_found": artifacts_count,
            "processing_time": processing_time,
            "model_used": model,
            "template_used": template or "auto-selected",
        }

    def _create_error_result(
        self, error_message: str, processing_time: float = 0
    ) -> ProcessingResult:
        """Create error result dictionary"""
        return {"success": False, "error": error_message, "processing_time": processing_time}

    def _save_raft_example(
        self, requirement: AugmentedRequirement, test_cases: str, model: str
    ) -> None:
        """
        Save RAFT training example if collection is enabled.

        This method is a no-op if RAFT collection is disabled. It does NOT
        affect core logic - it only saves data for future training.

        Args:
            requirement: Augmented requirement with context
            test_cases: Generated test cases string
            model: Model used for generation
        """
        if self.raft_collector:
            self.raft_collector.collect_example(
                requirement=requirement, generated_test_cases=test_cases, model=model
            )
