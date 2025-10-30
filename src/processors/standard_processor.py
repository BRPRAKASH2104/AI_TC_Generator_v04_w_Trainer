"""
Standard processor for the AI Test Case Generator.

This module provides the standard synchronous processing workflow that orchestrates
the core components to process REQIFZ files and generate test cases.
"""

import time
from typing import TYPE_CHECKING, Any

from ..core.exceptions import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    REQIFParsingError,
)
from ..core.extractors import REQIFArtifactExtractor
from ..core.formatters import TestCaseFormatter
from ..core.generators import TestCaseGenerator
from ..core.ollama_client import OllamaClient

from .base_processor import BaseProcessor

if TYPE_CHECKING:
    from pathlib import Path

    from ..config import ConfigManager

# Type aliases
type ProcessingResult = dict[str, Any]


class REQIFZFileProcessor(BaseProcessor):
    """Standard processor for REQIFZ files using synchronous processing"""

    __slots__ = ("ollama_client",)

    def __init__(self, config: ConfigManager = None):
        super().__init__(config)
        self.ollama_client = OllamaClient(self.config.ollama)

    def process_directory(
        self,
        directory_path: Path,
        model: str = "llama3.1:8b",
        template: str = None,
        output_dir: Path = None,
    ) -> list[ProcessingResult]:
        """
        Process all REQIFZ files in a directory.
        """
        from ..app_logger import get_app_logger

        app_logger = get_app_logger()

        results = []
        reqifz_files = list(directory_path.glob("**/*.reqifz"))
        app_logger.info(f"Found {len(reqifz_files)} REQIFZ files in {directory_path.name}")

        for reqifz_path in reqifz_files:
            result = self.process_file(reqifz_path, model, template, output_dir)
            results.append(result)

        return results

    def process_file(
        self,
        reqifz_path: Path,
        model: str = "llama3.1:8b",
        template: str = None,
        output_dir: Path = None,
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

        self.extractor = REQIFArtifactExtractor(self.logger)
        self.generator = TestCaseGenerator(self.ollama_client, self.yaml_manager, self.logger)
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
            all_test_cases = []
            successful_requirements = 0

            for augmented_req in augmented_requirements:
                req_id = augmented_req.get("id", "UNKNOWN")
                heading = augmented_req.get("heading", "No Heading")

                self.logger.info(f"⚡ Processing requirement: {req_id} (heading: {heading})")

                test_cases = self.generator.generate_test_cases_for_requirement(
                    augmented_req, model, template
                )

                if test_cases:
                    all_test_cases.extend(test_cases)
                    successful_requirements += 1
                    self.logger.info(f"✅ Generated {len(test_cases)} test cases for {req_id}")

                    # RAFT: Save training example if enabled (does NOT affect core logic)
                    if self.raft_collector:
                        # Format test cases to string for RAFT storage
                        test_cases_str = "\n".join(
                            [
                                f"Test Case {i + 1}: {tc.get('summary', 'N/A')}\n"
                                f"Action: {tc.get('action', 'N/A')}\n"
                                f"Data: {tc.get('data', 'N/A')}\n"
                                f"Expected: {tc.get('expected_result', 'N/A')}\n"
                                for i, tc in enumerate(test_cases)
                            ]
                        )
                        self._save_raft_example(augmented_req, test_cases_str, model)
                else:
                    self.logger.warning(f"⚠️  No test cases generated for {req_id}")

            if not all_test_cases:
                return self._create_error_result(
                    "No test cases were generated", time.time() - start_time
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
            )

            self.logger.info("🎉 Processing complete!")
            self.logger.info(
                f"📊 Generated {len(all_test_cases)} test cases in {processing_time:.2f}s"
            )
            self.logger.info(f"📁 Saved to: {output_path.name}")

            return result

        except OllamaConnectionError as e:
            processing_time = time.time() - start_time
            self.logger.error(
                f"❌ Cannot connect to Ollama at {e.host}:{e.port}",
            )
            return self._create_error_result(
                f"Ollama connection failed. Please ensure Ollama is running:\n"
                f"  1. Start Ollama: ollama serve\n"
                f"  2. Verify: curl http://{e.host}:{e.port}/api/tags\n"
                f"Error: {e}",
                processing_time,
            )

        except OllamaTimeoutError as e:
            processing_time = time.time() - start_time
            self.logger.error(
                f"❌ Ollama timeout after {e.timeout}s",
            )
            return self._create_error_result(
                f"Ollama request timed out after {e.timeout}s.\n"
                f"Try increasing timeout in config or using a faster model.\n"
                f"Suggestions:\n"
                f"  • Use faster model: llama3.1:8b instead of deepseek-coder-v2:16b\n"
                f"  • Increase timeout: AI_TG_TIMEOUT=900",
                processing_time,
            )

        except OllamaModelNotFoundError as e:
            processing_time = time.time() - start_time
            self.logger.error(
                f"❌ Model '{e.model}' not found",
            )
            return self._create_error_result(
                f"Model '{e.model}' is not available.\n"
                f"Install it with: ollama pull {e.model}\n"
                f"Check available models: ollama list",
                processing_time,
            )

        except REQIFParsingError as e:
            processing_time = time.time() - start_time
            self.logger.error(
                f"❌ REQIF parsing failed: {e.file_path}",
            )
            return self._create_error_result(
                f"Failed to parse REQIF file: {e.file_path}\n"
                f"Error: {e}\n"
                f"Ensure the file is a valid REQIFZ archive.",
                processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(
                f"❌ Unexpected error: {e}",
            )
            return self._create_error_result(
                f"Unexpected error: {e}\n"
                f"Error type: {type(e).__name__}\n"
                f"Please report this issue with the error details.",
                processing_time,
            )

        finally:
            if self.logger and hasattr(self.logger, "close"):
                self.logger.close()
