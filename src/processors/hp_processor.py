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
from core.extractors import HighPerformanceREQIFArtifactExtractor
from core.formatters import StreamingTestCaseFormatter
from core.generators import AsyncTestCaseGenerator
from core.ollama_client import AsyncOllamaClient
from file_processing_logger import FileProcessingLogger
from yaml_prompt_manager import YAMLPromptManager

# Type aliases
type ProcessingResult = dict[str, Any]
type PerformanceMetrics = dict[str, Any]


class HighPerformanceREQIFZFileProcessor:
    """High-performance async processor for REQIFZ files"""

    def __init__(self, config: ConfigManager = None, max_concurrent_requirements: int = None):
        self.config = config or ConfigManager()
        self.logger = None  # Will be initialized per file
        
        # Concurrency settings
        self.max_concurrent_requirements = (
            max_concurrent_requirements or 
            self.config.ollama.gpu_concurrency_limit
        )
        
        # Initialize core components (without logger for now)
        self.extractor = None  # Will be initialized per file
        self.yaml_manager = YAMLPromptManager()
        self.formatter = None  # Will be initialized per file
        
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
        self.logger = FileProcessingLogger(
            reqifz_file=reqifz_path.name,
            input_path=str(reqifz_path.parent)
        )
        
        # Initialize components with logger
        self.extractor = HighPerformanceREQIFArtifactExtractor(self.logger)
        self.formatter = StreamingTestCaseFormatter(self.config, self.logger)
        
        self.logger.info(f"🚀 High-Performance Processing: {reqifz_path.name}")
        self.logger.info(f"🤖 Model: {model}")
        self.logger.info(f"⚡ Max Concurrent: {self.max_concurrent_requirements}")
        
        try:
            # Step 1: Extract artifacts
            self.logger.info("📂 Extracting artifacts...")
            artifacts = self.extractor.extract_reqifz_content(reqifz_path)
            
            if not artifacts:
                return self._create_error_result("No artifacts found in REQIFZ file")
            
            self.metrics["total_artifacts"] = len(artifacts)

            # Step 2: Classify artifacts and separate system interfaces (global context)
            classified_artifacts = self.extractor.classify_artifacts(artifacts)
            system_interfaces = classified_artifacts.get("System Interface", [])

            # Step 3: Context-aware artifact processing preparation
            # Build augmented requirements with context (v03 restoration)
            augmented_requirements = []
            current_heading = "No Heading"
            info_since_heading = []

            self.logger.info(f"🎯 Building context for {len(artifacts)} artifacts...")

            for obj in artifacts:
                # Update context based on artifact type
                if obj.get("type") == "Heading":
                    current_heading = obj.get("text", "No Heading")
                    info_since_heading = []
                    self.logger.debug(f"📌 Context heading: {current_heading}")
                    continue

                elif obj.get("type") == "Information":
                    info_since_heading.append(obj)
                    self.logger.debug(f"📝 Stored information artifact: {obj.get('id', 'UNKNOWN')}")
                    continue

                elif obj.get("type") == "System Requirement" and obj.get("table"):
                    # Augment requirement with collected context
                    augmented_requirement = obj.copy()
                    augmented_requirement.update({
                        "heading": current_heading,
                        "info_list": info_since_heading.copy(),
                        "interface_list": system_interfaces
                    })
                    augmented_requirements.append(augmented_requirement)

                    # Reset information context after processing requirement
                    info_since_heading = []

            if not augmented_requirements:
                return self._create_error_result("No System Requirements with tables found")

            self.metrics["total_requirements"] = len(augmented_requirements)

            self.logger.info(f"⚡ Async processing {len(augmented_requirements)} context-enriched requirements...")
            self.logger.info(f"🔌 Using {len(system_interfaces)} system interfaces as global context")

            # Step 4: High-performance async test case generation
            async with AsyncOllamaClient(self.config.ollama) as ollama_client:
                generator = AsyncTestCaseGenerator(
                    ollama_client,
                    self.yaml_manager,
                    self.logger,
                    max_concurrent=self.max_concurrent_requirements
                )

                # Start performance monitoring
                monitor_task = asyncio.create_task(self._monitor_performance())

                # Process augmented requirements in batches for optimal performance
                batch_size = min(self.max_concurrent_requirements, len(augmented_requirements))
                all_test_cases = []

                for i in range(0, len(augmented_requirements), batch_size):
                    batch = augmented_requirements[i:i + batch_size]
                    batch_start = time.time()

                    self.logger.info(f"🔄 Processing batch {i//batch_size + 1} ({len(batch)} requirements)")

                    batch_results = await generator.generate_test_cases_batch(
                        batch, model, template
                    )
                    
                    # Process batch results with enhanced error tracking
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
                            # Empty result (legacy fallback)
                            req_id = batch[j].get("id", "UNKNOWN") if j < len(batch) else "UNKNOWN"
                            self.logger.warning(f"⚠️  {req_id}: No test cases generated (empty result)")
                            if hasattr(self.logger, 'add_requirement_failure'):
                                self.logger.add_requirement_failure(req_id, "Empty result returned")
                    
                    batch_time = time.time() - batch_start
                    rate = len(batch) / batch_time if batch_time > 0 else 0
                    
                    self.logger.info(f"✅ Batch completed: {rate:.1f} req/sec")
                
                # Stop monitoring
                monitor_task.cancel()
                
                if not all_test_cases:
                    return self._create_error_result("No test cases were generated")
                
                self.metrics["total_test_cases"] = len(all_test_cases)
            
            # Step 4: High-performance output formatting
            output_directory = output_dir or reqifz_path.parent
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            model_safe = model.replace(":", "_").replace("/", "_")
            
            output_filename = f"{reqifz_path.stem}_TCD_HP_{model_safe}_{timestamp}.xlsx"
            output_path = output_directory / output_filename
            
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
                return self._create_error_result("Failed to save Excel file")
            
            # Step 5: Calculate final metrics and return result
            self.metrics["end_time"] = time.time()
            processing_time = self.metrics["end_time"] - self.metrics["start_time"]
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(processing_time)
            
            # Calculate error summary
            failed_requirements = len(augmented_requirements) - self.metrics["successful_requirements"]
            error_summary = {
                "total_failures": failed_requirements,
                "failure_rate": (failed_requirements / len(augmented_requirements) * 100) if augmented_requirements else 0,
                "detailed_failures": []
            }
            
            # Extract detailed failure information from logger if available
            if hasattr(self.logger, 'failure_details'):
                error_summary["detailed_failures"] = [
                    {
                        "requirement_id": failure.requirement_id,
                        "error": failure.error,
                        "timestamp": failure.timestamp
                    }
                    for failure in self.logger.failure_details
                ]

            result = {
                "success": True,
                "output_file": str(output_path),
                "total_test_cases": len(all_test_cases),
                "requirements_processed": len(augmented_requirements),
                "successful_requirements": self.metrics["successful_requirements"],
                "failed_requirements": failed_requirements,
                "artifacts_found": len(artifacts),
                "processing_time": processing_time,
                "model_used": model,
                "template_used": template or "auto-selected",
                "performance_metrics": performance_metrics,
                "error_summary": error_summary
            }
            
            self.logger.info("🏆 High-Performance Processing Complete!")
            self.logger.info(f"📊 Generated {len(all_test_cases)} test cases in {processing_time:.2f}s")
            self.logger.info(f"⚡ Rate: {len(all_test_cases) / processing_time:.1f} test cases/sec")
            self.logger.info(f"🎯 Efficiency: {performance_metrics.get('parallel_efficiency', 0):.1f}%")
            
            return result

        except Exception as e:
            return self._create_error_result(f"Processing failed: {str(e)}")

    async def process_directory(
        self,
        input_dir: Path,
        model: str = "llama3.1:8b",
        template: str = None,
        output_dir: Path = None
    ) -> list[ProcessingResult]:
        """Process all REQIFZ files in a directory with high-performance processing"""
        self.logger.info(f"🚀 HP Directory Processing: {input_dir}")
        
        # Find all REQIFZ files
        reqifz_files = list(input_dir.glob("*.reqifz"))
        
        if not reqifz_files:
            self.logger.warning("No REQIFZ files found in directory")
            return []
        
        self.logger.info(f"📁 Found {len(reqifz_files)} REQIFZ file(s)")
        
        results = []
        overall_start = time.time()
        
        # Process files sequentially for now (could be enhanced with file-level concurrency)
        for i, reqifz_file in enumerate(reqifz_files, 1):
            self.logger.info(f"\n🔄 HP Processing file {i}/{len(reqifz_files)}: {reqifz_file.name}")
            
            result = await self.process_file(reqifz_file, model, template, output_dir)
            results.append(result)
            
            if result["success"]:
                self.logger.info(f"✅ File {i} completed successfully")
            else:
                self.logger.error(f"❌ File {i} failed: {result.get('error', 'Unknown error')}")
        
        # Overall summary
        total_time = time.time() - overall_start
        successful = sum(1 for r in results if r["success"])
        total_test_cases = sum(r.get("total_test_cases", 0) for r in results if r["success"])
        
        self.logger.info("\n🏁 HP Batch Processing Complete!")
        self.logger.info(f"📊 Files processed: {successful}/{len(reqifz_files)}")
        self.logger.info(f"📋 Total test cases: {total_test_cases}")
        self.logger.info(f"⏱️  Total time: {total_time:.2f}s")
        self.logger.info(f"⚡ Overall rate: {total_test_cases / total_time:.1f} test cases/sec")
        
        return results

    async def _monitor_performance(self) -> None:
        """Monitor system performance during processing"""
        try:
            import psutil
            
            while True:
                # Collect CPU and memory usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                
                self.metrics["cpu_usage_samples"].append(cpu_percent)
                self.metrics["memory_usage_samples"].append(memory.percent)
                
                await asyncio.sleep(1)
                
        except ImportError:
            # psutil not available, skip monitoring
            pass
        except asyncio.CancelledError:
            # Monitoring stopped
            pass

    def _calculate_performance_metrics(self, processing_time: float) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        metrics = {
            "total_processing_time": processing_time,
            "artifacts_per_second": self.metrics["total_artifacts"] / processing_time if processing_time > 0 else 0,
            "requirements_per_second": self.metrics["total_requirements"] / processing_time if processing_time > 0 else 0,
            "test_cases_per_second": self.metrics["total_test_cases"] / processing_time if processing_time > 0 else 0,
            "ai_calls_made": self.metrics["ai_calls_made"],
            "success_rate": (
                self.metrics["successful_requirements"] / self.metrics["total_requirements"] * 100
                if self.metrics["total_requirements"] > 0 else 0
            ),
            "parallel_efficiency": min(100, self.max_concurrent_requirements * 85)  # Estimate
        }
        
        # CPU/Memory stats if available
        if self.metrics["cpu_usage_samples"]:
            metrics["avg_cpu_usage"] = sum(self.metrics["cpu_usage_samples"]) / len(self.metrics["cpu_usage_samples"])
            metrics["peak_cpu_usage"] = max(self.metrics["cpu_usage_samples"])
        
        if self.metrics["memory_usage_samples"]:
            metrics["avg_memory_usage"] = sum(self.metrics["memory_usage_samples"]) / len(self.metrics["memory_usage_samples"])
            metrics["peak_memory_usage"] = max(self.metrics["memory_usage_samples"])
        
        return metrics

    def _create_error_result(self, error_message: str) -> ProcessingResult:
        """Create standardized error result"""
        if self.metrics["start_time"]:
            processing_time = time.time() - self.metrics["start_time"]
        else:
            processing_time = 0
        
        self.logger.error(error_message)
        
        return {
            "success": False,
            "error": error_message,
            "processing_time": processing_time,
            "performance_metrics": self._calculate_performance_metrics(processing_time)
        }