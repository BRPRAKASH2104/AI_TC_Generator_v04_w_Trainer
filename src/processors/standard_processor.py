"""
Standard processor for the AI Test Case Generator.

This module provides the standard synchronous processing workflow that orchestrates
the core components to process REQIFZ files and generate test cases.
"""

import time
from typing import TYPE_CHECKING, Any

from src.core.exceptions import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    REQIFParsingError,
)
from src.core.extractors import REQIFArtifactExtractor
from src.core.formatters import TestCaseFormatter
from src.core.generators import TestCaseGenerator
from src.core.ollama_client import OllamaClient

from .base_processor import BaseProcessor

if TYPE_CHECKING:
    from pathlib import Path

    from src.config import ConfigManager

# Type aliases
type ProcessingResult = dict[str, Any]


class REQIFZFileProcessor(BaseProcessor):
    """Standard processor for REQIFZ files using synchronous processing"""

    __slots__ = ("ollama_client",)

    def __init__(self, config: ConfigManager | None = None):
        super().__init__(config)
        self.ollama_client = OllamaClient(self.config.ollama)

    def process_directory(
        self,
        directory_path: Path,
        model: str = "llama3.1:8b",
        template: str | None = None,
        output_dir: Path | None = None,
    ) -> list[ProcessingResult]:
        """
        Process all REQIFZ files in a directory.
        """
        from src.app_logger import get_app_logger

        app_logger = get_app_logger()

        results = []
        reqifz_files = list(directory_path.glob("**/*.reqifz"))
        app_logger.info(f"Found {len(reqifz_files)} REQIFZ files in {directory_path.name}")

        for reqifz_path in reqifz_files:
            result = self.process_file(reqifz_path, model, template, output_dir)
            result.setdefault("input_file", str(reqifz_path))
            results.append(result)

        return results

    def process_file(
        self,
        reqifz_path: Path,
        model: str = "llama3.1:8b",
        template: str | None = None,
        output_dir: Path | None = None,
    ) -> ProcessingResult:
        """
        Process a single REQIFZ file and generate test cases.

        Args:
            reqifz_path: Path to the REQIFZ file
            model: AI model to use for generation
            template: Optional template name
            output_dir: Optional output directory (defaults to same as input)

        Returns:
            Processing result with statistics and file paths
        """
        start_time = time.time()

        # Initialize file-specific logger and components
        self._initialize_logger(reqifz_path)
        assert self.logger is not None, "_initialize_logger() must set self.logger"

        self.extractor = REQIFArtifactExtractor(self.logger, config=self.config)
        self.generator = TestCaseGenerator(
            self.ollama_client, self.yaml_manager, self.logger, config=self.config
        )
        self.formatter = TestCaseFormatter(self.config, self.logger)

        self.logger.info(f"🔍 Processing: {reqifz_path.name}")
        self.logger.info(f"🤖 Model: {model}")

        try:
            # Step 1: Extract artifacts from REQIFZ
            artifacts = self._extract_artifacts(reqifz_path)

            if not artifacts:
                return self._create_error_result(
                    "No artifacts found in REQIFZ file", time.time() - start_time
                )

            # Step 2: Build context-aware augmented requirements
            augmented_requirements, interface_count = self._build_augmented_requirements(artifacts)

            if not augmented_requirements:
                return self._create_error_result(
                    "No System Requirements found", time.time() - start_time
                )

            self.logger.info(
                f"📋 Processing {len(augmented_requirements)} requirements sequentially..."
            )

            # Step 3: Generate test cases sequentially
            all_test_cases, successful_requirements, failed_requirements = (
                self._run_generation_loop(augmented_requirements, model, template)
            )

            if not all_test_cases:
                return self._create_error_result(
                    "No test cases were generated",
                    time.time() - start_time,
                    failed_requirements=failed_requirements,
                )

            # Step 4: Format and save to Excel
            output_path = self._generate_output_path(reqifz_path, model, output_dir)

            self.logger.info(f"📝 Formatting {len(all_test_cases)} test cases to Excel...")

            metadata = self._create_metadata(
                model,
                template,
                reqifz_path,
                len(all_test_cases),
                len(augmented_requirements),
                successful_requirements,
            )

            success = self.formatter.format_to_excel(all_test_cases, output_path, metadata)

            if not success:
                return self._create_error_result(
                    "Failed to save Excel file", time.time() - start_time
                )

            # Step 5: Generate processing summary
            processing_time = time.time() - start_time

            result = self._create_success_result(
                output_path,
                len(all_test_cases),
                len(augmented_requirements),
                successful_requirements,
                len(artifacts),
                processing_time,
                model,
                template,
                failed_requirements=failed_requirements,
            )

            if failed_requirements:
                self.logger.warning(
                    f"⚠️  Partial completion: {len(failed_requirements)} of "
                    f"{len(augmented_requirements)} requirements failed"
                )

            self.logger.info("🎉 Processing complete!")
            self.logger.info(
                f"📊 Generated {len(all_test_cases)} test cases in {processing_time:.2f}s"
            )
            self.logger.info(f"📁 Saved to: {output_path.name}")

            return result

        except Exception as e:
            return self._error_result_for_exception(e, time.time() - start_time)

        finally:
            if self.logger and hasattr(self.logger, "close"):
                self.logger.close()

    def _run_generation_loop(
        self,
        augmented_requirements: list[dict[str, Any]],
        model: str,
        template: str | None,
    ) -> tuple[list[dict[str, Any]], int, list[dict[str, str]]]:
        """Generate test cases for each requirement sequentially.

        Returns ``(all_test_cases, successful_requirements, failed_requirements)``.
        Preserves the per-requirement hybrid model selection, structured-error
        handling, logging, and RAFT side effects previously inline in
        ``process_file``.
        """
        assert self.logger is not None, "_initialize_logger() must run first"
        all_test_cases: list[dict[str, Any]] = []
        successful_requirements = 0
        failed_requirements: list[dict[str, str]] = []

        for augmented_req in augmented_requirements:
            req_id = augmented_req.get("id", "UNKNOWN")
            heading = augmented_req.get("heading", "No Heading")

            # Hybrid strategy: Use vision model for requirements with images, text model otherwise
            selected_model = self.config.get_model_for_requirement(augmented_req)

            if selected_model != model:
                # Log when switching to vision model
                self.logger.info(
                    f"⚡ Processing requirement: {req_id} (heading: {heading}) "
                    f"- Using {selected_model} (has {len(augmented_req.get('images', []))} images)"
                )
            else:
                self.logger.info(f"⚡ Processing requirement: {req_id} (heading: {heading})")

            generation_result = self.generator.generate_test_cases_for_requirement(
                augmented_req, selected_model, template
            )

            if isinstance(generation_result, dict):
                # Structured error object from the generator
                error_type = generation_result.get("error_type", "Unknown")
                error_msg = generation_result.get("error_message", "No details")
                self.logger.error(f"❌ {req_id}: {error_type} - {error_msg}")
                if hasattr(self.logger, "add_requirement_failure"):
                    self.logger.add_requirement_failure(req_id, f"{error_type}: {error_msg}")
                failed_requirements.append(
                    {
                        "requirement_id": req_id,
                        "error_type": error_type,
                        "error_message": error_msg,
                    }
                )
                continue

            test_cases = generation_result

            if test_cases:
                all_test_cases.extend(test_cases)
                successful_requirements += 1
                self.logger.info(f"✅ Generated {len(test_cases)} test cases for {req_id}")

                # RAFT: Save training example if enabled (does NOT affect core logic)
                if self.raft_collector:
                    test_cases_str = self._format_raft_test_cases(test_cases)
                    self._save_raft_example(augmented_req, test_cases_str, model)
            else:
                self.logger.warning(f"⚠️  No test cases generated for {req_id}")
                failed_requirements.append(
                    {
                        "requirement_id": req_id,
                        "error_type": "EmptyResult",
                        "error_message": "No test cases generated",
                    }
                )

        return all_test_cases, successful_requirements, failed_requirements

    def _error_result_for_exception(
        self, exc: Exception, processing_time: float
    ) -> ProcessingResult:
        """Map a processing exception to an error result.

        Same branch selection and messages as the previous inline except-ladder;
        dispatched by ``isinstance`` so ``process_file`` keeps a single
        ``except Exception``.
        """
        assert self.logger is not None, "_initialize_logger() must run first"

        if isinstance(exc, OllamaConnectionError):
            self.logger.error(f"❌ Cannot connect to Ollama at {exc.host}:{exc.port}")
            return self._create_error_result(
                f"Ollama connection failed. Please ensure Ollama is running:\n"
                f"  1. Start Ollama: ollama serve\n"
                f"  2. Verify: curl http://{exc.host}:{exc.port}/api/tags\n"
                f"Error: {exc}",
                processing_time,
            )

        if isinstance(exc, OllamaTimeoutError):
            self.logger.error(f"❌ Ollama timeout after {exc.timeout}s")
            return self._create_error_result(
                f"Ollama request timed out after {exc.timeout}s.\n"
                f"Try increasing timeout in config or using a faster model.\n"
                f"Suggestions:\n"
                f"  • Use faster model: llama3.1:8b instead of deepseek-coder-v2:16b\n"
                f"  • Increase timeout: AI_TG_TIMEOUT=900",
                processing_time,
            )

        if isinstance(exc, OllamaModelNotFoundError):
            self.logger.error(f"❌ Model '{exc.model}' not found")
            return self._create_error_result(
                f"Model '{exc.model}' is not available.\n"
                f"Install it with: ollama pull {exc.model}\n"
                f"Check available models: ollama list",
                processing_time,
            )

        if isinstance(exc, REQIFParsingError):
            self.logger.error(f"❌ REQIF parsing failed: {exc.file_path}")
            return self._create_error_result(
                f"Failed to parse REQIF file: {exc.file_path}\n"
                f"Error: {exc}\n"
                f"Ensure the file is a valid REQIFZ archive.",
                processing_time,
            )

        self.logger.error(f"❌ Unexpected error: {exc}")
        return self._create_error_result(
            f"Unexpected error: {exc}\n"
            f"Error type: {type(exc).__name__}\n"
            f"Please report this issue with the error details.",
            processing_time,
        )
