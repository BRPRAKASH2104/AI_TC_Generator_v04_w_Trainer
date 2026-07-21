"""
Base processor for the AI Test Case Generator.

This module provides the base class with shared logic for both standard
and high-performance processors, eliminating code duplication.
"""

import re
import time
from pathlib import Path
from typing import Any, Protocol, cast

from src.config import ConfigManager
from src.core.interface_matcher import build_interface_index, select_relevant_interfaces
from src.file_processing_logger import FileProcessingLogger
from src.training.raft_collector import RAFTDataCollector
from src.yaml_prompt_manager import YAMLPromptManager

# Type aliases
type ProcessingResult = dict[str, Any]
type AugmentedRequirement = dict[str, Any]


class SyncFileProcessor(Protocol):
    """Structural type for synchronous per-file processing (e.g. REQIFZFileProcessor).

    process_file has no shared declaration on BaseProcessor - sync and async
    processors define it independently with incompatible calling conventions
    (this one is not a coroutine), so a `processor` variable of unresolved
    concrete type otherwise has no static type connecting it to this method.
    """

    def process_file(
        self,
        reqifz_path: Path,
        model: str = ...,
        template: str | None = ...,
        output_dir: Path | None = ...,
    ) -> ProcessingResult: ...


class AsyncFileProcessor(Protocol):
    """Structural type for asynchronous per-file processing (e.g. HighPerformanceREQIFZFileProcessor)."""

    async def process_file(
        self,
        reqifz_path: Path,
        model: str = ...,
        template: str | None = ...,
        output_dir: Path | None = ...,
    ) -> ProcessingResult: ...


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
        config: ConfigManager | None = None,
        extractor: Any = None,  # Dependency injection: concrete type set by subclass
        generator: Any = None,  # Dependency injection: concrete type set by subclass
        formatter: Any = None,  # Dependency injection: concrete type set by subclass
    ):
        self.config = config or ConfigManager()
        self.logger: FileProcessingLogger | None = None  # Will be initialized per file
        self.yaml_manager = YAMLPromptManager()

        # Dependencies - either injected or initialized by subclasses
        self.extractor = extractor
        self.generator = generator
        self.formatter = formatter

        # RAFT data collector — created only with BOTH consent flags set:
        # enable_raft turns the feature on, collect_training_data consents to
        # writing requirement/test content to disk (review 2026-07-17 §6)
        self.raft_collector = None
        if self.config.training.enable_raft and self.config.training.collect_training_data:
            self.raft_collector = RAFTDataCollector(
                output_dir=Path(self.config.training.training_data_dir) / "collected",
                logger=None,  # Logger will be set per file
                enabled=True,
            )

    @staticmethod
    def _clean_text_for_logging(text: str | list | None) -> str:
        """Clean XML/HTML text for readable output. Handles str, list, or None."""
        if not text:
            return ""
        if isinstance(text, list):
            text = " ".join(str(item) for item in text)
        # Remove XML tags
        clean = re.sub(r"<[^>]+>", " ", text)
        # Normalize whitespace
        clean = " ".join(clean.split())
        return clean

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
        assert self.logger is not None, "_initialize_logger() must run before _extract_artifacts()"
        self.logger.info("📂 Extracting artifacts from REQIFZ file...")
        artifacts = self.extractor.extract_reqifz_content(reqifz_path)

        if not artifacts:
            self.logger.error("No artifacts found in REQIFZ file")
            return None

        # self.extractor is Any (DI target set by subclasses to one of the
        # concrete extractor classes); extract_reqifz_content is declared to
        # return ArtifactList on both.
        return cast("list[dict[str, Any]]", artifacts)

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
        assert self.logger is not None, (
            "_initialize_logger() must run before _build_augmented_requirements()"
        )
        # Classify artifacts and separate system interfaces (global context)
        classified_artifacts = self.extractor.classify_artifacts(artifacts)
        raw_interfaces = classified_artifacts.get("System Interface", [])
        # Normalise interface text fields once (shared across all requirements)
        system_interfaces = [
            {**iface, "text": self._clean_text_for_logging(iface.get("text", ""))}
            for iface in raw_interfaces
        ]
        # Pre-index interface signal names once; each requirement is then
        # attached only the interfaces it references (archived finding 8),
        # bounding prompt growth instead of fanning the full dictionary out.
        interface_index = build_interface_index(system_interfaces)
        attached_interface_total = 0

        # Context-aware artifact processing (v03 restoration)
        augmented_requirements = []
        current_heading = "No Heading"
        info_since_heading: list[dict] = []

        self.logger.info(f"🎯 Building context for {len(artifacts)} artifacts...")
        self.logger.info(f"🔌 Found {len(system_interfaces)} system interfaces (global context)")

        for obj in artifacts:
            # Update context based on artifact type
            if obj.get("type") == "Heading":
                raw_heading = obj.get("text", "No Heading")
                current_heading = self._clean_text_for_logging(raw_heading) or "No Heading"
                info_since_heading = []
                self.logger.debug(
                    f"📌 Context heading: {self._clean_text_for_logging(current_heading)}"
                )
                continue

            elif obj.get("type") in ("Information", "Design Information"):
                # Design Information (state machines, ECU architecture, etc.) is
                # design-context and is collected into the same per-heading
                # context bucket as generic Information so it still reaches the
                # prompt. Without this, correctly typing it as DESIGN_INFORMATION
                # (extractors._map_reqif_type_to_artifact_type) would silently
                # drop it from context — the paired half of that fix.
                clean_info = {**obj, "text": self._clean_text_for_logging(obj.get("text", ""))}
                info_since_heading.append(clean_info)
                self.logger.debug(f"📝 Stored information artifact: {id(obj)}")
                continue

            elif obj.get("type") == "System Requirement":
                # Augment requirement with collected context
                # FIX: Process ALL System Requirements, not just those with tables (v03 compatibility)
                req_id = obj.get("id", "UNKNOWN")
                req_text = self._clean_text_for_logging(obj.get("text", ""))

                # Skip if no text content (empty requirements)
                if not req_text:
                    self.logger.debug(f"⚠️  Skipping requirement {req_id}: no text content")
                    continue

                self.logger.debug(
                    f"⚡ Augmenting requirement: {req_id} (heading: {current_heading})"
                )

                relevant_interfaces = select_relevant_interfaces(
                    req_text,
                    [info.get("text", "") for info in info_since_heading],
                    interface_index,
                )
                attached_interface_total += len(relevant_interfaces)

                augmented_requirement = obj.copy()
                augmented_requirement.update(
                    {
                        "text": req_text,
                        "heading": current_heading,
                        "info_list": info_since_heading.copy(),
                        "interface_list": relevant_interfaces,
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
            # Report interface-scoping effect vs. the old full fan-out so the
            # prompt-size impact is observable (archived finding 8).
            full_fanout = len(augmented_requirements) * len(system_interfaces)
            if full_fanout:
                self.logger.info(
                    f"🔌 Interface scoping: attached {attached_interface_total} "
                    f"interface refs vs {full_fanout} with full fan-out "
                    f"({100 * attached_interface_total // full_fanout}% of prior size)"
                )

        return augmented_requirements, len(system_interfaces)

    def _generate_output_path(
        self, reqifz_path: Path, model: str, output_dir: Path | None = None, mode_tag: str = ""
    ) -> Path:
        """
        Generate output file path for Excel file

        Args:
            reqifz_path: Source REQIFZ file path
            model: AI model name
            output_dir: Optional output directory
            mode_tag: Optional processing-mode marker (e.g. "HP") inserted
                after the TCD token

        Returns:
            Path for output Excel file
        """
        output_directory = output_dir or reqifz_path.parent
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        model_safe = model.replace(":", "_").replace("/", "_")
        mode_part = f"{mode_tag}_" if mode_tag else ""

        output_filename = f"{reqifz_path.stem}_TCD_{mode_part}{model_safe}_{timestamp}.xlsx"
        output_path = output_directory / output_filename

        return output_path

    def _create_metadata(
        self,
        model: str,
        template: str | None,
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
        template: str | None = None,
        failed_requirements: list[dict[str, str]] | None = None,
    ) -> ProcessingResult:
        """Create success result dictionary.

        A result with failed_requirements is a *partial* completion: an
        output file exists, but not every requirement produced test cases.
        Callers must surface this and exit non-zero (review 2026-07-17 §1).
        """
        failed = failed_requirements or []
        return {
            "success": True,
            "partial": bool(failed),
            "failed_requirements": failed,
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
        self,
        error_message: str,
        processing_time: float = 0,
        failed_requirements: list[dict[str, str]] | None = None,
    ) -> ProcessingResult:
        """Create error result dictionary"""
        return {
            "success": False,
            "partial": False,
            "error": error_message,
            "processing_time": processing_time,
            "failed_requirements": failed_requirements or [],
        }

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
