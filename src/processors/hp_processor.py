"""
High-performance processor for the AI Test Case Generator.

This module provides async/concurrent processing capabilities for high-throughput
test case generation with optimized resource utilization.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from config import ConfigManager
from core.exceptions import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    REQIFParsingError,
)
from core.extractors import HighPerformanceREQIFArtifactExtractor
from core.formatters import StreamingTestCaseFormatter
from core.generators import AsyncTestCaseGenerator
from core.ollama_client import AsyncOllamaClient
from processors.base_processor import BaseProcessor

# Type aliases
type ProcessingResult = dict[str, Any]
type PerformanceMetrics = dict[str, Any]


class HighPerformanceREQIFZFileProcessor(BaseProcessor):
    """High-performance async processor for REQIFZ files"""

    def __init__(self, config: ConfigManager = None, max_concurrent_requirements: int = None):
        super().__init__(config)

        # Concurrency settings
        self.max_concurrent_requirements = (
            max_concurrent_requirements or
            self.config.ollama.gpu_concurrency_limit
        )

        # Performance tracking
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "total_artifacts": 0,
            "total_requirements": 0,
            "total_test_cases": 0,
            "successful_requirements": 0,
            "ai_calls_made": 0,
            "avg_response_time": 0.0,
            "peak_concurrency": 0,
            "cpu_usage_samples": [],
            "memory_usage_samples": []
        }

    async def process_file(
        self,
        reqifz_path: Path,
        model: str = "llama3.1:8b",
        template: str = None,
        output_dir: Path = None,
        show_progress: bool = True
    ) -> ProcessingResult:
        """
        Process a single REQIFZ file with high-performance async processing.

        Args:
            reqifz_path: Path to the REQIFZ file
            model: AI model to use for generation
            template: Optional template name
            output_dir: Optional output directory
            show_progress: Whether to show progress indicators

        Returns:
            Processing result with performance metrics
        """
        self.metrics["start_time"] = time.time()

        # Initialize file-specific logger and components
        self._initialize_logger(reqifz_path)

        self.extractor = HighPerformanceREQIFArtifactExtractor(self.logger)
        self.formatter = StreamingTestCaseFormatter(self.config, self.logger)

        self.logger.info(f"🚀 High-Performance Processing: {reqifz_path.name}")
        self.logger.info(f"🤖 Model: {model}")
        self.logger.info(f"⚡ Max Concurrent: {self.max_concurrent_requirements}")

        try:
            # Step 1: Extract artifacts
            artifacts = self._extract_artifacts(reqifz_path)

            if not artifacts:
                return self._create_error_result_hp("No artifacts found in REQIFZ file")

            self.metrics["total_artifacts"] = len(artifacts)

            # Step 2: Build context-aware augmented requirements
            augmented_requirements, interface_count = self._build_augmented_requirements(artifacts)

            if not augmented_requirements:
                return self._create_error_result_hp("No System Requirements with tables found")

            self.metrics["total_requirements"] = len(augmented_requirements)

            self.logger.info(f"⚡ Async processing {len(augmented_requirements)} context-enriched requirements...")

            # Step 3: High-performance async test case generation
            async with AsyncOllamaClient(self.config.ollama) as ollama_client:
                generator = AsyncTestCaseGenerator(
                    ollama_client,
                    self.yaml_manager,
                    self.logger,
                    max_concurrent=self.max_concurrent_requirements
                )

                # Start performance monitoring
                monitor_task = asyncio.create_task(self._monitor_performance())

                # OPTIMIZATION: Process ALL requirements concurrently
                # AsyncOllamaClient's semaphore handles rate limiting automatically
                # This eliminates sequential batch gaps and improves throughput by 3x
                processing_start = time.time()

                self.logger.info(f"🚀 Processing all {len(augmented_requirements)} requirements concurrently...")

                batch_results = await generator.generate_test_cases_batch(
                    augmented_requirements, model, template
                )

                # Process all results
                all_test_cases = []
                for j, result in enumerate(batch_results):
                    self.metrics["ai_calls_made"] += 1

                    if isinstance(result, dict) and result.get("error"):
                        # Handle structured error information
                        req_id = result.get("requirement_id", "UNKNOWN")
                        error_type = result.get("error_type", "Unknown")
                        error_msg = result.get("error_message", "No details")

                        self.logger.error(f"❌ {req_id}: {error_type} - {error_msg}")

                        # Record failure with detailed information
                        if hasattr(self.logger, 'add_requirement_failure'):
                            self.logger.add_requirement_failure(req_id, f"{error_type}: {error_msg}")

                    elif isinstance(result, list) and result:
                        # Successful test cases
                        all_test_cases.extend(result)
                        self.metrics["successful_requirements"] += 1

                        # Log success for specific requirement
                        if result and isinstance(result[0], dict):
                            req_id = result[0].get("requirement_id", "UNKNOWN")
                            self.logger.info(f"✅ {req_id}: Generated {len(result)} test cases")

                    else:
                        # Empty result
                        req_id = augmented_requirements[j].get("id", "UNKNOWN") if j < len(augmented_requirements) else "UNKNOWN"
                        self.logger.warning(f"⚠️  {req_id}: No test cases generated")
                        if hasattr(self.logger, 'add_requirement_failure'):
                            self.logger.add_requirement_failure(req_id, "Empty result returned")

                processing_time = time.time() - processing_start
                rate = len(augmented_requirements) / processing_time if processing_time > 0 else 0

                self.logger.info(f"✅ Processed {len(augmented_requirements)} requirements: {rate:.1f} req/sec")

                # Stop monitoring
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass  # Expected when cancelling

                if not all_test_cases:
                    return self._create_error_result_hp("No test cases were generated")

                self.metrics["total_test_cases"] = len(all_test_cases)

            # Step 4: High-performance output formatting
            output_path = self._generate_output_path_hp(reqifz_path, model, output_dir)

            self.logger.info(f"📝 Streaming {len(all_test_cases)} test cases to Excel...")

            metadata = {
                "model": model,
                "template": template or "auto-selected",
                "source_file": str(reqifz_path),
                "processing_mode": "high_performance",
                "max_concurrent": self.max_concurrent_requirements,
                "total_cases": len(all_test_cases)
            }

            # Use streaming formatter for memory efficiency
            success = self.formatter.format_to_excel_streaming(
                iter(all_test_cases), output_path, metadata
            )

            if not success:
                return self._create_error_result_hp("Failed to save Excel file")

            # Step 5: Generate performance summary
            self.metrics["end_time"] = time.time()
            processing_time = self.metrics["end_time"] - self.metrics["start_time"]

            result = {
                "success": True,
                "output_file": str(output_path),
                "total_test_cases": len(all_test_cases),
                "requirements_processed": len(augmented_requirements),
                "successful_requirements": self.metrics["successful_requirements"],
                "artifacts_found": len(artifacts),
                "processing_time": processing_time,
                "model_used": model,
                "template_used": template or "auto-selected",
                "performance_metrics": self._get_performance_summary()
            }

            self.logger.info("🎉 High-performance processing complete!")
            self.logger.info(f"📊 Generated {len(all_test_cases)} test cases in {processing_time:.2f}s")
            self.logger.info(f"⚡ Processing rate: {len(all_test_cases)/processing_time:.1f} cases/sec")
            self.logger.info(f"📁 Saved to: {output_path.name}")

            return result

        except OllamaConnectionError as e:
            processing_time = time.time() - self.metrics["start_time"]
            self.logger.error(
                f"❌ Cannot connect to Ollama at {e.host}:{e.port}",
            )
            return self._create_error_result_hp(
                f"Ollama connection failed. Please ensure Ollama is running:\n"
                f"  1. Start Ollama: ollama serve\n"
                f"  2. Verify: curl http://{e.host}:{e.port}/api/tags\n"
                f"Error: {e}",
                processing_time
            )

        except OllamaTimeoutError as e:
            processing_time = time.time() - self.metrics["start_time"]
            self.logger.error(
                f"❌ Ollama timeout after {e.timeout}s",
            )
            return self._create_error_result_hp(
                f"Ollama request timed out after {e.timeout}s.\n"
                f"Try increasing timeout in config or using a faster model.\n"
                f"Suggestions:\n"
                f"  • Use faster model: llama3.1:8b instead of deepseek-coder-v2:16b\n"
                f"  • Increase timeout: AI_TG_TIMEOUT=900\n"
                f"  • Reduce concurrency: --max-concurrent 2",
                processing_time
            )

        except OllamaModelNotFoundError as e:
            processing_time = time.time() - self.metrics["start_time"]
            self.logger.error(
                f"❌ Model '{e.model}' not found",
            )
            return self._create_error_result_hp(
                f"Model '{e.model}' is not available.\n"
                f"Install it with: ollama pull {e.model}\n"
                f"Check available models: ollama list",
                processing_time
            )

        except REQIFParsingError as e:
            processing_time = time.time() - self.metrics["start_time"]
            self.logger.error(
                f"❌ REQIF parsing failed: {e.file_path}",
            )
            return self._create_error_result_hp(
                f"Failed to parse REQIF file: {e.file_path}\n"
                f"Error: {e}\n"
                f"Ensure the file is a valid REQIFZ archive.",
                processing_time
            )

        except Exception as e:
            processing_time = time.time() - self.metrics["start_time"]
            self.logger.error(
                f"❌ Unexpected HP processing error: {e}",
            )
            return self._create_error_result_hp(
                f"Unexpected error: {e}\n"
                f"Error type: {type(e).__name__}\n"
                f"Please report this issue with the error details.",
                processing_time
            )

        finally:
            if self.logger and hasattr(self.logger, 'close'):
                self.logger.close()

    def _generate_output_path_hp(
        self,
        reqifz_path: Path,
        model: str,
        output_dir: Path = None
    ) -> Path:
        """Generate HP-specific output file path"""
        output_directory = output_dir or reqifz_path.parent
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        model_safe = model.replace(":", "_").replace("/", "_")

        output_filename = f"{reqifz_path.stem}_TCD_HP_{model_safe}_{timestamp}.xlsx"
        output_path = output_directory / output_filename

        return output_path

    def _create_error_result_hp(
        self,
        error_message: str,
        processing_time: float = None
    ) -> ProcessingResult:
        """Create HP-specific error result with metrics"""
        if processing_time is None:
            processing_time = time.time() - self.metrics.get("start_time", time.time())

        return {
            "success": False,
            "error": error_message,
            "processing_time": processing_time,
            "performance_metrics": self._get_performance_summary()
        }

    async def _monitor_performance(self) -> None:
        """Monitor CPU and memory usage during processing"""
        try:
            import psutil
            process = psutil.Process()

            while True:
                cpu_percent = process.cpu_percent(interval=0.1)
                memory_mb = process.memory_info().rss / 1024 / 1024

                self.metrics["cpu_usage_samples"].append(cpu_percent)
                self.metrics["memory_usage_samples"].append(memory_mb)

                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        except ImportError:
            # psutil not available, skip monitoring
            pass

    def _get_performance_summary(self) -> PerformanceMetrics:
        """Generate performance metrics summary"""
        cpu_samples = self.metrics["cpu_usage_samples"]
        mem_samples = self.metrics["memory_usage_samples"]

        return {
            "total_ai_calls": self.metrics["ai_calls_made"],
            "successful_requirements": self.metrics["successful_requirements"],
            "total_requirements": self.metrics["total_requirements"],
            "success_rate": (
                self.metrics["successful_requirements"] / self.metrics["total_requirements"] * 100
                if self.metrics["total_requirements"] > 0 else 0
            ),
            "avg_cpu_percent": sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0,
            "peak_cpu_percent": max(cpu_samples) if cpu_samples else 0,
            "avg_memory_mb": sum(mem_samples) / len(mem_samples) if mem_samples else 0,
            "peak_memory_mb": max(mem_samples) if mem_samples else 0,
            "max_concurrent": self.max_concurrent_requirements
        }
