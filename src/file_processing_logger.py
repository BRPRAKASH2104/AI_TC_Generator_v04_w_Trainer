#!/usr/bin/env python3
"""
File Processing Logger - Per-file processing log generation
Automatically generates detailed logs for each REQIFZ file processed.
"""

import json
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil


@dataclass
class ProcessingPhase:
    """Track timing for individual processing phases"""

    name: str
    start_time: float | None = None
    end_time: float | None = None

    def start(self):
        """Start timing this phase"""
        self.start_time = time.time()

    def end(self):
        """End timing this phase"""
        self.end_time = time.time()

    @property
    def duration(self) -> float:
        """Get phase duration in seconds"""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time


@dataclass
class RequirementFailure:
    """Details about a failed requirement"""

    requirement_id: str
    error: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class FileProcessingLogger:
    """Comprehensive logging for REQIFZ file processing"""

    # File information
    reqifz_file: str
    input_path: str
    output_file: str = ""

    # Processing metadata
    version: str = "unknown"
    ai_model: str = "unknown"
    template_used: str = "unknown"

    # Timing
    start_time: float | None = None
    end_time: float | None = None
    phases: dict[str, ProcessingPhase] = field(default_factory=dict)

    # Requirements analysis
    total_artifacts_found: int = 0
    artifacts_by_type: dict[str, int] = field(default_factory=dict)
    requirements_processed_total: int = 0
    requirements_successful: int = 0
    requirements_failed: int = 0
    requirements_skipped: int = 0
    failure_details: list[RequirementFailure] = field(default_factory=list)

    # Test case generation
    total_test_cases_generated: int = 0
    positive_tests: int = 0
    negative_tests: int = 0

    # Performance metrics
    peak_cpu_usage: float = 0.0
    peak_memory_mb: float = 0.0
    ai_response_times: list[float] = field(default_factory=list)

    # Status and warnings
    status: str = "IN_PROGRESS"
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize logger"""
        self.start_processing()

        # Get system info
        self.python_version = (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )

        # Try to get Ollama version
        self.ollama_version = "unknown"
        try:
            import subprocess

            result = subprocess.run(
                ["ollama", "--version"], check=False, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                self.ollama_version = (
                    result.stdout.strip().split()[-1] if result.stdout.strip() else "unknown"
                )
        except Exception:
            pass

    def start_processing(self):
        """Mark start of processing"""
        self.start_time = time.time()
        self.status = "IN_PROGRESS"

    def end_processing(self, success: bool = True):
        """Mark end of processing"""
        self.end_time = time.time()
        self.status = "SUCCESS" if success else "FAILED"

    def start_phase(self, phase_name: str):
        """Start timing a processing phase"""
        if phase_name not in self.phases:
            self.phases[phase_name] = ProcessingPhase(phase_name)
        self.phases[phase_name].start()

    def end_phase(self, phase_name: str):
        """End timing a processing phase"""
        if phase_name in self.phases:
            self.phases[phase_name].end()

    def get_phase_duration(self, phase_name: str) -> float:
        """Get duration of a specific phase in seconds"""
        if phase_name in self.phases:
            return self.phases[phase_name].duration
        return 0.0

    def add_requirement_failure(self, requirement_id: str, error: str):
        """Record a requirement processing failure"""
        self.failure_details.append(RequirementFailure(requirement_id, error))
        self.requirements_failed += 1

    def add_ai_response_time(self, response_time: float):
        """Record AI response time"""
        self.ai_response_times.append(response_time)

    def add_warning(self, warning: str):
        """Add a warning message"""
        if warning not in self.warnings:
            self.warnings.append(warning)

    def update_system_metrics(self):
        """Update peak system usage metrics"""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent()
            memory_mb = process.memory_info().rss / 1024 / 1024

            self.peak_cpu_usage = max(self.peak_cpu_usage, cpu_percent)
            self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)
        except Exception:
            pass

    def increment_test_cases(self, positive: int = 0, negative: int = 0):
        """Increment test case counters"""
        self.positive_tests += positive
        self.negative_tests += negative
        self.total_test_cases_generated = self.positive_tests + self.negative_tests

    def to_dict(self) -> dict[str, Any]:
        """Convert logger to dictionary for JSON serialization"""

        # Calculate derived metrics
        total_duration = 0.0
        if self.start_time and self.end_time:
            total_duration = self.end_time - self.start_time

        avg_ai_response_time = 0.0
        if self.ai_response_times:
            avg_ai_response_time = sum(self.ai_response_times) / len(self.ai_response_times)

        requirements_per_second = 0.0
        if total_duration > 0:
            requirements_per_second = self.requirements_successful / total_duration

        avg_tests_per_requirement = 0.0
        if self.requirements_successful > 0:
            avg_tests_per_requirement = (
                self.total_test_cases_generated / self.requirements_successful
            )

        generation_success_rate = 0.0
        if self.requirements_processed_total > 0:
            generation_success_rate = (
                self.requirements_successful / self.requirements_processed_total
            ) * 100

        return {
            "file_info": {
                "reqifz_file": self.reqifz_file,
                "input_path": self.input_path,
                "output_file": self.output_file,
            },
            "processing_metadata": {
                "version": self.version,
                "ai_model": self.ai_model,
                "template_used": self.template_used,
                "python_version": self.python_version,
                "ollama_version": self.ollama_version,
            },
            "timing": {
                "start_time": datetime.fromtimestamp(self.start_time, UTC).isoformat()
                if self.start_time
                else None,
                "end_time": datetime.fromtimestamp(self.end_time, UTC).isoformat()
                if self.end_time
                else None,
                "total_duration_seconds": round(total_duration, 3),
                "phases": {name: round(phase.duration, 3) for name, phase in self.phases.items()},
            },
            "requirements_analysis": {
                "total_artifacts_found": self.total_artifacts_found,
                "artifacts_by_type": self.artifacts_by_type,
                "requirements_processed": {
                    "total": self.requirements_processed_total,
                    "successful": self.requirements_successful,
                    "failed": self.requirements_failed,
                    "skipped": self.requirements_skipped,
                },
                "failure_details": [
                    {
                        "requirement_id": failure.requirement_id,
                        "error": failure.error,
                        "timestamp": failure.timestamp,
                    }
                    for failure in self.failure_details
                ],
            },
            "test_case_generation": {
                "total_generated": self.total_test_cases_generated,
                "positive_tests": self.positive_tests,
                "negative_tests": self.negative_tests,
                "avg_tests_per_requirement": round(avg_tests_per_requirement, 2),
                "generation_success_rate": round(generation_success_rate, 1),
            },
            "performance_metrics": {
                "peak_cpu_usage_percent": round(self.peak_cpu_usage, 1),
                "peak_memory_mb": round(self.peak_memory_mb, 1),
                "avg_ai_response_time_seconds": round(avg_ai_response_time, 2),
                "requirements_per_second": round(requirements_per_second, 2),
            },
            "status": self.status,
            "warnings": self.warnings,
        }

    def save_log(self, output_dir: str | None = None):
        """Save processing log to JSON file with same naming pattern as Excel output"""
        try:
            # Determine output directory (same as Excel output by default)
            if output_dir is None:
                if self.output_file:
                    output_dir = str(Path(self.output_file).parent)
                else:
                    output_dir = str(Path(self.input_path).parent)

            # Create log filename based on Excel output filename pattern
            if self.output_file:
                # Use the exact same name as Excel file but with .json extension
                excel_path = Path(self.output_file)
                log_filename = excel_path.stem + ".json"
            else:
                # Fallback to original pattern if no output file specified
                reqifz_name = Path(self.reqifz_file).stem
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                log_filename = f"{reqifz_name}_processing_log_{timestamp}.json"

            log_path = Path(output_dir) / log_filename

            # Ensure directory exists
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Save log
            with log_path.open("w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

            return str(log_path)

        except Exception as e:
            # If logging fails, don't break the main process
            print(f"Warning: Could not save processing log: {e}")
            return None
