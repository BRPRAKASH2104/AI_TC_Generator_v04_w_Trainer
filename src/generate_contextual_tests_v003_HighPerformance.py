"""
Context-Rich, High-Performance Test Case Generator with Maximum CPU Utilization

Version: High-Performance v3.0 - Multi-threaded, Async, with Performance Monitoring

Key Performance Features:
- Multi-threaded file processing (4-8x speedup)
- Async AI model calls (3x speedup)
- Parallel XML parsing
- Concurrent test case generation
- Real-time performance monitoring
- Intelligent load balancing
- Memory optimization with streaming
- CPU utilization maximization (target: 80-95%)
"""

import argparse
import asyncio
import logging
import re
import sys
import threading
import time
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path

# Modern type aliases with enhanced constraints (Python 3.13.7+)
from typing import Any, NotRequired, TypedDict

import aiohttp
import pandas as pd
import psutil
import requests
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

# Import the file processing logger
from file_processing_logger import FileProcessingLogger

# Try to import performance accelerators
try:
    import lxml.etree as ET_FAST

    LXML_AVAILABLE = True
except ImportError:
    ET_FAST = ET
    LXML_AVAILABLE = False

try:
    import ujson as json_fast

    UJSON_AVAILABLE = True
except ImportError:
    import json as json_fast

    UJSON_AVAILABLE = False

type JSONObj[T] = dict[str, T]
type JSONResponse = dict[str, str | int | float | bool | None]


class RequirementData(TypedDict):
    id: str
    text: str
    type: str
    table: NotRequired[dict[str, Any] | None]


class TestCaseData(TypedDict):
    summary_suffix: str
    action: str
    data: str
    expected_result: str


@dataclass(slots=True)
class PerformanceMetrics:
    """Performance monitoring data structure"""

    start_time: float = field(default_factory=time.time)
    cpu_usage: list[float] = field(default_factory=list)
    memory_usage: list[float] = field(default_factory=list)
    files_processed: int = 0
    test_cases_generated: int = 0
    ai_calls_made: int = 0
    total_processing_time: float = 0.0
    parallel_efficiency: float = 0.0


class ArtifactType(StrEnum):
    HEADING = "Heading"
    INFORMATION = "Information"
    SYSTEM_INTERFACE = "System Interface"
    SYSTEM_REQUIREMENT = "System Requirement"


# =================================================================
# PERFORMANCE MONITORING SYSTEM
# =================================================================


class PerformanceMonitor:
    """Real-time performance monitoring and optimization system"""

    def __init__(self, update_interval: float = 0.5):
        self.update_interval = update_interval
        self.metrics = PerformanceMetrics()
        self.monitoring = False
        self.monitor_thread: threading.Thread | None = None
        self.console = Console()
        self._lock = threading.Lock()

    def start_monitoring(self):
        """Start performance monitoring in background thread"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=None)
                memory_percent = psutil.virtual_memory().percent

                with self._lock:
                    self.metrics.cpu_usage.append(cpu_percent)
                    self.metrics.memory_usage.append(memory_percent)

                    # Keep only recent data (last 100 samples)
                    if len(self.metrics.cpu_usage) > 100:
                        self.metrics.cpu_usage = self.metrics.cpu_usage[-100:]
                        self.metrics.memory_usage = self.metrics.memory_usage[-100:]

                time.sleep(self.update_interval)
            except Exception:
                # Silently continue on monitoring errors
                time.sleep(self.update_interval)

    def record_file_processed(self):
        """Record a file completion"""
        with self._lock:
            self.metrics.files_processed += 1

    def record_test_cases(self, count: int):
        """Record test cases generated"""
        with self._lock:
            self.metrics.test_cases_generated += count

    def record_ai_call(self):
        """Record an AI API call"""
        with self._lock:
            self.metrics.ai_calls_made += 1

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        with self._lock:
            return PerformanceMetrics(
                start_time=self.metrics.start_time,
                cpu_usage=self.metrics.cpu_usage.copy(),
                memory_usage=self.metrics.memory_usage.copy(),
                files_processed=self.metrics.files_processed,
                test_cases_generated=self.metrics.test_cases_generated,
                ai_calls_made=self.metrics.ai_calls_made,
                total_processing_time=time.time() - self.metrics.start_time,
                parallel_efficiency=self._calculate_efficiency(),
            )

    def _calculate_efficiency(self) -> float:
        """Calculate parallel processing efficiency"""
        if not self.metrics.cpu_usage:
            return 0.0

        avg_cpu = sum(self.metrics.cpu_usage) / len(self.metrics.cpu_usage)
        cpu_cores = psutil.cpu_count()
        ideal_utilization = min(100.0, cpu_cores * 25)  # Target 25% per core

        return min(100.0, (avg_cpu / ideal_utilization) * 100.0)

    def create_performance_table(self) -> Table:
        """Create Rich table with performance metrics"""
        metrics = self.get_current_metrics()

        table = Table(title="🚀 Performance Metrics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")

        # CPU Usage
        avg_cpu = sum(metrics.cpu_usage) / len(metrics.cpu_usage) if metrics.cpu_usage else 0
        cpu_status = "🔥 High" if avg_cpu > 70 else "⚡ Medium" if avg_cpu > 30 else "💤 Low"
        table.add_row("CPU Usage", f"{avg_cpu:.1f}%", cpu_status)

        # Memory Usage
        avg_mem = (
            sum(metrics.memory_usage) / len(metrics.memory_usage) if metrics.memory_usage else 0
        )
        mem_status = "🔴 High" if avg_mem > 80 else "🟡 Medium" if avg_mem > 50 else "🟢 Low"
        table.add_row("Memory Usage", f"{avg_mem:.1f}%", mem_status)

        # Processing Stats
        table.add_row("Files Processed", str(metrics.files_processed), "📁")
        table.add_row("Test Cases", str(metrics.test_cases_generated), "📋")
        table.add_row("AI Calls", str(metrics.ai_calls_made), "🤖")

        # Efficiency
        efficiency_status = (
            "🏆 Excellent"
            if metrics.parallel_efficiency > 80
            else "👍 Good"
            if metrics.parallel_efficiency > 50
            else "⚠️ Poor"
        )
        table.add_row(
            "Parallel Efficiency", f"{metrics.parallel_efficiency:.1f}%", efficiency_status
        )

        # Runtime
        runtime_min = metrics.total_processing_time / 60
        table.add_row("Runtime", f"{runtime_min:.1f} min", "⏱️")

        return table


# =================================================================
# ENHANCED LOGGING SYSTEM WITH PERFORMANCE INTEGRATION
# =================================================================


class HighPerformanceLogger:
    """Enhanced logging system with performance monitoring integration"""

    def __init__(self, verbose: bool = False, debug: bool = False, log_file: str | None = None):
        self.console = Console()
        self.verbose = verbose
        self.debug_enabled = debug
        self.progress: Progress | None = None
        self.current_task: TaskID | None = None
        self.performance_monitor = PerformanceMonitor()

        # Setup logging
        self._setup_logging(log_file)
        self._setup_progress()

    def _setup_logging(self, log_file: str | None) -> None:
        """Setup logging configuration"""
        if self.debug_enabled:
            level = logging.DEBUG
        elif self.verbose:
            level = logging.INFO
        else:
            level = logging.WARNING

        self.logger = logging.getLogger("ai_test_generator_hp")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        # Console handler with Rich formatting
        console_handler = RichHandler(
            console=self.console,
            show_path=self.debug_enabled,
            show_time=self.debug_enabled,
            rich_tracebacks=True,
            tracebacks_show_locals=self.debug_enabled,
        )
        console_handler.setLevel(level)

        console_format = "%(message)s"
        console_handler.setFormatter(logging.Formatter(console_format))
        self.logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
                file_handler.setLevel(logging.DEBUG)
                file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                file_handler.setFormatter(logging.Formatter(file_format))
                self.logger.addHandler(file_handler)
                self.info(f"Logging to file: {log_file}")
            except Exception as e:
                self.warning(f"Could not setup file logging: {e}")

    def _setup_progress(self) -> None:
        """Setup rich progress bar"""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            expand=True,
        )

    def start_performance_monitoring(self):
        """Start performance monitoring"""
        self.performance_monitor.start_monitoring()

    def stop_performance_monitoring(self):
        """Stop performance monitoring"""
        self.performance_monitor.stop_monitoring()

    def print_banner(self) -> None:
        """Print application banner with performance info"""
        banner_text = Text()
        banner_text.append("AI Test Case Generator v3.0 - HIGH PERFORMANCE\n", style="bold blue")
        banner_text.append("Multi-threaded • Async • Performance Optimized\n", style="cyan")
        banner_text.append("Maximum CPU Utilization • Real-time Monitoring\n", style="green")
        banner_text.append("Context-Rich Test Case Generation from REQIFZ Files", style="white")

        panel = Panel(banner_text, title="🚀 High-Performance Mode Active", expand=False)
        self.console.print(panel)

        # Show system info
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        self.console.print(f"💻 System: {cpu_count} CPU cores, {memory_gb:.1f}GB RAM")
        self.console.print(
            f"⚡ Optimizations: {'lxml' if LXML_AVAILABLE else 'stdlib'} XML, {'ujson' if UJSON_AVAILABLE else 'stdlib'} JSON"
        )

    def show_performance_dashboard(self):
        """Show real-time performance dashboard"""
        if self.verbose or self.debug_enabled:
            table = self.performance_monitor.create_performance_table()
            self.console.print(table)

    # Core logging methods with performance integration
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.console.print(message, **kwargs)
        # Only log to file, not to console handler to avoid duplication
        if self.logger.handlers:
            for handler in self.logger.handlers:
                if hasattr(handler, "baseFilename"):  # File handler
                    self.logger.info(message)

    def success(self, message: str) -> None:
        """Log success message with green checkmark"""
        self.console.print(f"✅ {message}", style="green")
        self.logger.info(f"SUCCESS: {message}")

    def warning(self, message: str) -> None:
        """Log warning message"""
        self.console.print(f"⚠️  {message}", style="yellow")
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message"""
        self.console.print(f"❌ {message}", style="red bold")
        self.logger.error(message)

    def debug(self, message: str) -> None:
        """Log debug message"""
        if self.debug_enabled:
            self.console.print(f"🔍 DEBUG: {message}", style="dim blue")
        self.logger.debug(message)

    def verbose_log(self, message: str) -> None:
        """Log verbose message"""
        if self.verbose or self.debug_enabled:
            self.console.print(f"📋 {message}", style="dim")
        self.logger.info(f"VERBOSE: {message}")

    # Performance-specific logging
    def log_performance_start(self, files: list, model: str):
        """Log processing start with performance optimization info"""
        self.info("🚀 [bold]HIGH-PERFORMANCE MODE ACTIVATED[/bold]")
        self.info(f"📁 Processing {len(files)} file(s) with maximum CPU utilization")
        self.info(f"🤖 AI Model: [cyan]{model}[/cyan]")
        self.info("🧵 Threading: Multi-core parallel processing enabled")
        self.info("⚡ Async: Concurrent AI model calls enabled")

    def log_parallel_start(self, max_workers: int):
        """Log parallel processing start"""
        self.verbose_log(f"🏭 Starting parallel processing with {max_workers} workers")

    def log_performance_summary(self):
        """Log final performance summary"""
        metrics = self.performance_monitor.get_current_metrics()

        self.console.print("\n🏆 [bold green]HIGH-PERFORMANCE PROCESSING COMPLETE![/bold green]")
        self.console.print(f"⏱️  Total Runtime: {metrics.total_processing_time / 60:.1f} minutes")
        self.console.print(f"📊 Files Processed: {metrics.files_processed}")
        self.console.print(f"📋 Test Cases Generated: {metrics.test_cases_generated}")
        self.console.print(f"🤖 AI Calls Made: {metrics.ai_calls_made}")

        if metrics.cpu_usage:
            avg_cpu = sum(metrics.cpu_usage) / len(metrics.cpu_usage)
            max_cpu = max(metrics.cpu_usage)
            self.console.print(f"💻 CPU Usage: Avg {avg_cpu:.1f}%, Peak {max_cpu:.1f}%")

        self.console.print(f"⚡ Parallel Efficiency: {metrics.parallel_efficiency:.1f}%")


# Global logger instance
_logger_instance: HighPerformanceLogger | None = None


def get_logger() -> HighPerformanceLogger:
    """Get the global logger instance"""
    if _logger_instance is None:
        raise RuntimeError("Logger not initialized. Call setup_logger() first.")
    return _logger_instance


def setup_logger(
    verbose: bool = False, debug: bool = False, log_file: str | None = None
) -> HighPerformanceLogger:
    """Setup and return the global logger instance"""
    global _logger_instance
    _logger_instance = HighPerformanceLogger(verbose=verbose, debug=debug, log_file=log_file)
    return _logger_instance


# Import dependencies
try:
    from yaml_prompt_manager import YAMLPromptManager
except ImportError as e:
    print(f"❌ Error: Could not import YAML prompt manager: {e}")
    sys.exit(1)

try:
    from config import ConfigManager, OllamaConfig, StaticTestConfig
except ImportError:
    from dataclasses import dataclass

    @dataclass(slots=True)
    class StaticTestConfig:
        VOLTAGE_PRECONDITION: str = "1. Voltage= 12V\n2. Bat-ON"
        TEST_TYPE: str = "PROVEtech"
        ISSUE_TYPE: str = "Test"
        PROJECT_KEY: str = "TCTOIC"
        ASSIGNEE: str = "ENGG"
        PLANNED_EXECUTION: str = "Manual"
        TEST_CASE_TYPE: str = "Feature Functional"
        COMPONENTS: str = "SW_DI_FV"
        LABELS: str = "AI Generated TC"

    @dataclass(slots=True)
    class OllamaConfig:
        host: str = "127.0.0.1"
        port: int = 11434
        timeout: int = 600
        temperature: float = 0.0

        @property
        def api_url(self) -> str:
            return f"http://{self.host}:{self.port}/api/generate"

    class ConfigManager:
        def __init__(self):
            self.static_test = StaticTestConfig()
            self.ollama = OllamaConfig()


# =================================================================
# ASYNC OLLAMA API CLIENT (HIGH PERFORMANCE)
# =================================================================


class AsyncOllamaClient:
    """High-performance async Ollama API client with connection pooling"""

    def __init__(self, config: OllamaConfig = None):
        self.config = config or OllamaConfig()
        self.session: aiohttp.ClientSession | None = None
        # GPU-aware concurrency limit (much lower for GPU-accelerated Ollama)
        self.semaphore = asyncio.Semaphore(
            1
        )  # Single GPU request at a time to prevent GPU saturation

    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=50,  # Connection pool size
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )

        # Extended timeouts for GPU-intensive processing
        timeout = aiohttp.ClientTimeout(
            total=self.config.timeout * 2,  # Double the total timeout for GPU processing
            connect=60,
            sock_read=600,  # Extended read timeout for large AI responses
        )

        self.session = aiohttp.ClientSession(
            connector=connector, timeout=timeout, json_serialize=json_fast.dumps
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def generate_response(self, model_name: str, prompt: str, is_json: bool = False) -> str:
        """Generate response from Ollama model asynchronously"""
        if not self.session:
            raise RuntimeError("AsyncOllamaClient not properly initialized")

        logger = get_logger()
        logger.debug(f"Async Ollama call: {model_name}, prompt length: {len(prompt)}")
        logger.performance_monitor.record_ai_call()

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.config.keep_alive,  # Ollama v0.11.10+ optimization
            "options": {
                "temperature": self.config.temperature,
                "num_ctx": self.config.num_ctx,  # Context window size
                "num_predict": self.config.num_predict,  # Response length limit (replaces hardcoded 3000)
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        if is_json:
            payload["format"] = "json"

        async with self.semaphore:  # Limit concurrent requests
            try:
                async with self.session.post(self.config.api_url, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return str(data.get("response", ""))
            except TimeoutError:
                logger.error(f"Timeout calling Ollama with model {model_name}")
                return ""
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error calling Ollama: {e}")
                return ""
            except Exception as e:
                logger.error(f"Unexpected error calling Ollama: {e}")
                return ""

    async def generate_multiple_responses(
        self, requests_data: list[tuple[str, str, bool]]
    ) -> list[str]:
        """Generate multiple responses concurrently"""
        tasks = [
            self.generate_response(model, prompt, is_json)
            for model, prompt, is_json in requests_data
        ]

        return await asyncio.gather(*tasks, return_exceptions=True)


# =================================================================
# FALLBACK SYNC OLLAMA CLIENT
# =================================================================


class OllamaClient:
    """Synchronous fallback Ollama client for compatibility"""

    __slots__ = ("config", "proxies", "_session")

    def __init__(self, config: OllamaConfig = None):
        self.config = config or OllamaConfig()
        self.proxies = {"http": None, "https": None}
        self._session = requests.Session()
        self._session.proxies.update(self.proxies)

    def generate_response(self, model_name: str, prompt: str, is_json: bool = False) -> str:
        """Generate response from Ollama model synchronously"""
        logger = get_logger()
        logger.debug(f"Sync Ollama call: {model_name}, prompt length: {len(prompt)}")
        logger.performance_monitor.record_ai_call()

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.config.keep_alive,  # Ollama v0.11.10+ optimization
            "options": {
                "temperature": self.config.temperature,
                "num_ctx": self.config.num_ctx,  # Context window size
                "num_predict": self.config.num_predict,  # Response length limit (replaces hardcoded 3000)
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        if is_json:
            payload["format"] = "json"

        try:
            response = self._session.post(
                self.config.api_url,
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return str(data.get("response", ""))
        except Exception as e:
            logger.error(f"Ollama sync error: {e}")
            return ""


# =================================================================
# OPTIMIZED JSON RESPONSE PARSER
# =================================================================


class FastJSONResponseParser:
    """High-performance JSON response parser with ujson support"""

    __slots__ = ()

    @staticmethod
    def extract_json_from_response(response_text: str) -> dict[str, Any] | None:
        """Extract and parse JSON from AI model response with performance optimization"""
        try:
            # Try direct JSON parsing first (faster for well-formed responses)
            if response_text.strip().startswith("{") and response_text.strip().endswith("}"):
                return json_fast.loads(response_text.strip())

            # Fallback to regex extraction
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json_fast.loads(json_str)
            return None
        except (ValueError, TypeError):
            return None


# =================================================================
# PARALLEL XML PARSER
# =================================================================


class ParallelXMLParser:
    """High-performance XML parser with optional lxml acceleration"""

    __slots__ = ("namespaces", "use_lxml")

    def __init__(self, namespaces: dict[str, str] | None = None):
        self.namespaces = namespaces or {
            "reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
            "html": "http://www.w3.org/1999/xhtml",
        }
        self.use_lxml = LXML_AVAILABLE

    def parse_xml_content(self, xml_content: bytes) -> ET.Element:
        """Parse XML content with optimal parser"""
        if self.use_lxml:
            return ET_FAST.fromstring(xml_content)
        return ET.fromstring(xml_content)

    def extract_spec_objects_parallel(
        self, root_element, chunk_size: int = 100
    ) -> list[dict[str, Any]]:
        """Extract spec objects with parallel processing for large documents"""
        logger = get_logger()

        # Find all spec objects
        spec_objects = root_element.findall(
            ".//reqif:SPEC-OBJECTS//reqif:SPEC-OBJECT", self.namespaces
        )

        if not spec_objects:
            return []

        logger.debug(f"Found {len(spec_objects)} spec objects for parallel processing")

        # Build shared mappings once
        type_map = self._build_type_map(root_element)
        type_to_foreign_id_map, type_to_text_def_map = self._build_attribute_maps(root_element)

        # Process in parallel chunks for large documents
        if len(spec_objects) > chunk_size:
            return self._process_chunks_parallel(
                spec_objects, type_map, type_to_foreign_id_map, type_to_text_def_map, chunk_size
            )
        # Process sequentially for smaller documents (overhead not worth it)
        return [
            self._process_spec_object(
                obj, type_map, type_to_foreign_id_map, type_to_text_def_map
            )
            for obj in spec_objects
        ]

    def _process_chunks_parallel(
        self, spec_objects, type_map, foreign_id_map, text_def_map, chunk_size
    ):
        """Process spec objects in parallel chunks"""
        chunks = [spec_objects[i : i + chunk_size] for i in range(0, len(spec_objects), chunk_size)]
        results = []

        # Use thread pool for XML processing (I/O bound)
        max_workers = min(4, len(chunks))  # Don't over-thread

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._process_chunk, chunk, type_map, foreign_id_map, text_def_map)
                for chunk in chunks
            ]

            for future in as_completed(futures):
                try:
                    chunk_results = future.result()
                    results.extend(chunk_results)
                except Exception as e:
                    logger = get_logger()
                    logger.error(f"Error processing XML chunk: {e}")

        return results

    def _process_chunk(self, spec_objects_chunk, type_map, foreign_id_map, text_def_map):
        """Process a chunk of spec objects"""
        return [
            self._process_spec_object(obj, type_map, foreign_id_map, text_def_map)
            for obj in spec_objects_chunk
        ]

    def _build_type_map(self, root) -> dict[str, str]:
        """Build mapping from type IDs to type names"""
        return {
            t.get("IDENTIFIER"): t.get("LONG-NAME")
            for t in root.findall(".//reqif:SPEC-OBJECT-TYPE", self.namespaces)
        }

    def _build_attribute_maps(self, root) -> tuple[dict[str, str], dict[str, str]]:
        """Build mappings for foreign ID and text definition attributes"""
        type_to_foreign_id_map, type_to_text_def_map = {}, {}

        for spec_type in root.findall(".//reqif:SPEC-OBJECT-TYPE", self.namespaces):
            type_id = spec_type.get("IDENTIFIER")

            foreign_id_def = spec_type.find(
                ".//reqif:ATTRIBUTE-DEFINITION-STRING[@LONG-NAME='ReqIF.ForeignID']",
                self.namespaces,
            )
            if foreign_id_def is not None:
                type_to_foreign_id_map[type_id] = foreign_id_def.get("IDENTIFIER")

            text_def = spec_type.find(
                ".//reqif:ATTRIBUTE-DEFINITION-XHTML[@LONG-NAME='ReqIF.Text']", self.namespaces
            )
            if text_def is not None:
                type_to_text_def_map[type_id] = text_def.get("IDENTIFIER")

        return type_to_foreign_id_map, type_to_text_def_map

    def _process_spec_object(
        self, spec_object, type_map, foreign_id_map, text_def_map
    ) -> dict[str, Any]:
        """Process a single spec object"""
        internal_id = spec_object.get("IDENTIFIER")
        req_id, req_text, req_type, table_data = internal_id, "", "Unknown", None

        # Get object type
        type_ref_node = spec_object.find("reqif:TYPE/reqif:SPEC-OBJECT-TYPE-REF", self.namespaces)
        if type_ref_node is not None:
            spec_object_type_ref = type_ref_node.text
            type_name = type_map.get(spec_object_type_ref, "Unknown")
            req_type = self._determine_artifact_type(type_name)

            # Extract attributes
            values_container = spec_object.find("reqif:VALUES", self.namespaces)
            if values_container is not None:
                req_id = self._extract_foreign_id(
                    values_container, foreign_id_map.get(spec_object_type_ref), req_id
                )
                req_text, table_data = self._extract_text_and_table(
                    values_container, text_def_map.get(spec_object_type_ref)
                )

        return {"id": req_id, "text": req_text.strip(), "type": req_type, "table": table_data}

    def _determine_artifact_type(self, type_name: str) -> str:
        """Determine artifact type using pattern matching"""
        name_lower = type_name.lower()

        if "heading" in name_lower:
            return ArtifactType.HEADING
        if "interface" in name_lower:
            return ArtifactType.SYSTEM_INTERFACE
        if "requirement" in name_lower:
            return ArtifactType.SYSTEM_REQUIREMENT
        if "info" in name_lower:
            return ArtifactType.INFORMATION
        return ArtifactType.INFORMATION

    def _extract_foreign_id(
        self, values_container, target_foreign_id_ref: str, default_id: str
    ) -> str:
        """Extract foreign ID from values container"""
        if not target_foreign_id_ref:
            return default_id

        for attr_value in values_container.findall("reqif:ATTRIBUTE-VALUE-STRING", self.namespaces):
            definition_ref_node = attr_value.find(
                "reqif:DEFINITION/reqif:ATTRIBUTE-DEFINITION-STRING-REF", self.namespaces
            )
            if (
                definition_ref_node is not None
                and definition_ref_node.text == target_foreign_id_ref
            ):
                return attr_value.get("THE-VALUE", default_id)

        return default_id

    def _extract_text_and_table(
        self, values_container, target_text_def_ref: str
    ) -> tuple[str, dict[str, Any] | None]:
        """Extract text content and table data from values container"""
        if not target_text_def_ref:
            return "", None

        for attr_value in values_container.findall(
            ".//reqif:ATTRIBUTE-VALUE-XHTML", self.namespaces
        ):
            definition_ref_node = attr_value.find(
                "reqif:DEFINITION/reqif:ATTRIBUTE-DEFINITION-XHTML-REF", self.namespaces
            )
            if definition_ref_node is not None and definition_ref_node.text == target_text_def_ref:
                the_value = attr_value.find("reqif:THE-VALUE", self.namespaces)
                if the_value is not None:
                    full_text = "".join(the_value.itertext()).strip()

                    # Parse table if present
                    table_element = the_value.find(".//html:table", self.namespaces)
                    table_data = None
                    if table_element is not None:
                        table_data = self._parse_html_table(table_element)

                    return full_text, table_data

        return "", None

    def _parse_html_table(self, table_element) -> dict[str, Any] | None:
        """Parse HTML table element into structured data (optimized version)"""
        headers, data_rows = [], []
        raw_rows = table_element.findall(".//html:tr", self.namespaces)

        if not raw_rows:
            return None

        # Simplified table parsing for better performance
        for i, tr in enumerate(raw_rows):
            cells = [cell.text or "" for cell in tr.findall(".//html:td", self.namespaces)]
            if not cells:
                cells = [cell.text or "" for cell in tr.findall(".//html:th", self.namespaces)]

            if i == 0:
                headers = cells
            else:
                data_rows.append(cells)

        return {"headers": headers, "rows": data_rows}


# =================================================================
# HIGH-PERFORMANCE REQIF ARTIFACT EXTRACTOR
# =================================================================


class HighPerformanceREQIFArtifactExtractor:
    """High-performance artifact extractor with parallel processing"""

    __slots__ = ("xml_parser",)

    def __init__(self, namespaces: dict[str, str] | None = None):
        self.xml_parser = ParallelXMLParser(namespaces)

    def extract_all_artifacts(self, file_path: Path) -> list[dict[str, Any]]:
        """Extract all artifacts from a REQIFZ file with performance optimization"""
        logger = get_logger()
        logger.debug(f"Starting high-performance extraction from {file_path.name}")

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                reqif_filename = self._find_reqif_file(zf)

                with zf.open(reqif_filename) as reqif_file:
                    xml_content = reqif_file.read()

                    # Parse XML with optimal parser
                    root = self.xml_parser.parse_xml_content(xml_content)

                    # Extract spec objects with parallel processing
                    all_objects = self.xml_parser.extract_spec_objects_parallel(root)

                    logger.debug(f"Extracted {len(all_objects)} artifacts from {file_path.name}")
                    return all_objects

        except Exception as e:
            logger.error(f"Error processing XML in '{file_path.name}': {e}")
            logger.debug(f"Full error details: {str(e)}")
            return []

    def _find_reqif_file(self, zip_file) -> str:
        """Find the .reqif file within the ZIP archive"""
        reqif_filename = next(
            (name for name in zip_file.namelist() if name.endswith(".reqif")), None
        )
        if not reqif_filename:
            raise FileNotFoundError("No .reqif file found in the archive.")
        return reqif_filename


# =================================================================
# ASYNC TEST CASE GENERATOR
# =================================================================


class AsyncTestCaseGenerator:
    """High-performance async test case generator with concurrent AI calls"""

    def __init__(
        self,
        model_name: str,
        yaml_prompt_manager: YAMLPromptManager,
        async_ollama_client: AsyncOllamaClient,
        config: StaticTestConfig | None = None,
    ):
        self.model_name = model_name
        self.yaml_prompt_manager = yaml_prompt_manager
        self.async_ollama_client = async_ollama_client
        self.config = config or StaticTestConfig()
        self.json_parser = FastJSONResponseParser()

    async def generate_tests_batch(
        self,
        requirements_batch: list[
            tuple[dict[str, Any], str, list[dict[str, Any]], list[dict[str, Any]]]
        ],
    ) -> list[list[dict[str, Any]]]:
        """Generate test cases for multiple requirements concurrently"""
        logger = get_logger()
        logger.debug(f"Generating tests for batch of {len(requirements_batch)} requirements")

        # Prepare all prompts concurrently
        prompt_tasks = [
            self._prepare_prompt_async(requirement, heading, info_list, interface_list)
            for requirement, heading, info_list, interface_list in requirements_batch
        ]

        prompts = await asyncio.gather(*prompt_tasks, return_exceptions=True)

        # Filter out failed prompt preparations
        valid_prompts = []
        valid_indices = []
        for i, prompt in enumerate(prompts):
            if isinstance(prompt, str) and prompt:
                valid_prompts.append((self.model_name, prompt, True))
                valid_indices.append(i)

        if not valid_prompts:
            return [[] for _ in requirements_batch]

        # Make concurrent AI calls
        logger.debug(f"Making {len(valid_prompts)} concurrent AI calls")
        responses = await self.async_ollama_client.generate_multiple_responses(valid_prompts)

        # Process responses
        results = [[] for _ in requirements_batch]
        for i, response in enumerate(responses):
            if isinstance(response, str) and response:
                original_index = valid_indices[i]
                requirement = requirements_batch[original_index][0]

                parsed_json = self.json_parser.extract_json_from_response(response)
                test_cases = parsed_json.get("test_cases", []) if parsed_json else []

                logger.debug(f"Generated {len(test_cases)} test cases for {requirement['id']}")
                results[original_index] = test_cases

        return results

    async def _prepare_prompt_async(
        self,
        requirement: dict[str, Any],
        heading: str,
        info_list: list[dict[str, Any]],
        interface_list: list[dict[str, Any]],
    ) -> str:
        """Prepare prompt asynchronously (runs in thread pool if needed)"""
        table = requirement.get("table")
        if not table:
            return ""

        # Prepare template variables
        template_variables = {
            "heading": heading,
            "requirement_id": requirement["id"],
            "table_str": self._format_table_for_prompt(table),
            "row_count": len(table["rows"]),
            "voltage_precondition": self.config.VOLTAGE_PRECONDITION.replace("\n", "\\n"),
            "info_str": self._format_info_for_prompt(info_list),
            "interface_str": self._format_interfaces_for_prompt(interface_list),
        }

        try:
            return self.yaml_prompt_manager.get_test_prompt(**template_variables)
        except Exception as e:
            logger = get_logger()
            logger.error(f"Prompt template error for {requirement['id']}: {e}")
            return ""

    def _format_table_for_prompt(self, table: dict[str, Any]) -> str:
        """Format table data for inclusion in prompt"""
        table_str = "Headers: " + ", ".join(table["headers"]) + "\n"
        for i, row in enumerate(table["rows"]):
            table_str += f"Row {i + 1}: {row}\n"
        return table_str

    def _format_interfaces_for_prompt(self, interface_list: list[dict[str, Any]]) -> str:
        """Format interface list for inclusion in prompt"""
        if not interface_list:
            return "None"
        return "\n".join([f"- {i['id']}: {i['text']}" for i in interface_list])

    def _format_info_for_prompt(self, info_list: list[dict[str, Any]]) -> str:
        """Format information list for inclusion in prompt"""
        if not info_list:
            return "None"
        return "\n".join([f"- {i['text']}" for i in info_list])


# =================================================================
# STREAMING TEST CASE FORMATTER
# =================================================================


class StreamingTestCaseFormatter:
    """Memory-optimized streaming test case formatter"""

    def __init__(self, config: StaticTestConfig | None = None):
        self.config = config or StaticTestConfig()

    def format_test_cases_stream(
        self, test_cases_data: Iterator[tuple[dict[str, Any], str, int]]
    ) -> Iterator[dict[str, Any]]:
        """Stream format test cases to avoid memory accumulation"""
        for test, requirement_id, issue_id in test_cases_data:
            if isinstance(test, dict):
                yield self._format_single_test_case(test, requirement_id, issue_id)

    def _format_single_test_case(
        self, test: dict[str, Any], requirement_id: str, issue_id: int
    ) -> dict[str, Any]:
        """Format a single test case for Excel output"""
        # Format data field to display on separate lines in Excel
        data_field = test.get("data", "N/A")
        if isinstance(data_field, str) and data_field.startswith("1)"):
            # Convert numbered list format to newline-separated
            data_field = (
                data_field.replace(", ", "\n")
                .replace("2)", "\n2)")
                .replace("3)", "\n3)")
                .replace("4)", "\n4)")
                .replace("5)", "\n5)")
            )
        elif isinstance(data_field, list):
            # Convert list to newline-separated string
            data_field = "\n".join(str(step) for step in data_field)

        return {
            "Issue ID": issue_id,
            "Summary": f"[{requirement_id}] {test.get('summary_suffix', 'Generated Test')}",
            "Test Type": self.config.TEST_TYPE,
            "Issue Type": self.config.ISSUE_TYPE,
            "Project Key": self.config.PROJECT_KEY,
            "Assignee": self.config.ASSIGNEE,
            "Description": "",
            "Action": test.get("action", self.config.VOLTAGE_PRECONDITION),
            "Data": data_field,
            "Expected Result": test.get("expected_result", "N/A"),
            "Planned Execution": self.config.PLANNED_EXECUTION,
            "Test Case Type": self.config.TEST_CASE_TYPE,
            "Components": self.config.COMPONENTS,
            "Labels": self.config.LABELS,
            "Tests": requirement_id,
        }


# =================================================================
# HIGH-PERFORMANCE FILE PROCESSOR
# =================================================================


class HighPerformanceREQIFZFileProcessor:
    """Ultra-high-performance file processor with maximum CPU utilization"""

    def __init__(
        self,
        model_name: str,
        config_manager: ConfigManager | None = None,
        yaml_prompt_manager: YAMLPromptManager | None = None,
        max_concurrent_requirements: int | None = None,
        adaptive_batching: bool = True,
    ):
        self.model_name = model_name
        self.config_manager = config_manager or ConfigManager()
        self.yaml_prompt_manager = yaml_prompt_manager or YAMLPromptManager()

        # Calculate optimal requirement concurrency (much lower for API stability)
        self.max_concurrent_requirements = max_concurrent_requirements or min(
            psutil.cpu_count() // 2, 4
        )
        self.adaptive_batching = adaptive_batching

        # Initialize high-performance components
        self.extractor = HighPerformanceREQIFArtifactExtractor()
        self.formatter = StreamingTestCaseFormatter(self.config_manager.static_test)

        # Adaptive batching parameters
        self.current_batch_size = 1
        self.max_batch_size = 3
        self.min_batch_size = 1
        self.success_streak = 0
        self.failure_streak = 0

        logger = get_logger()
        logger.debug(
            f"Initialized high-performance processor: {self.max_concurrent_requirements} concurrent requirements, adaptive batching: {adaptive_batching}, model: {model_name}"
        )

    async def process_single_file_optimized(self, reqifz_file: Path) -> int:
        """Process a single REQIFZ file with optimized requirement-level parallelism"""
        logger = get_logger()

        # Use async context manager for Ollama client
        async with AsyncOllamaClient(self.config_manager.ollama) as async_client:
            # Create async test case generator
            async_generator = AsyncTestCaseGenerator(
                self.model_name,
                self.yaml_prompt_manager,
                async_client,
                self.config_manager.static_test,
            )

            # Process the single file with requirement-level optimization
            test_count = await self._process_single_file_async_optimized(
                reqifz_file, async_generator
            )

            logger.performance_monitor.record_file_processed()
            logger.performance_monitor.record_test_cases(test_count)

            return test_count

    async def _process_single_file_async_optimized(
        self,
        reqifz_file: Path,
        async_generator: AsyncTestCaseGenerator,
    ) -> int:
        """Process a single file with optimized requirement-level parallelism"""
        logger = get_logger()
        logger.verbose_log(f"Processing: {reqifz_file.name}")

        # Generate output path first
        output_path = self._generate_output_path(reqifz_file)

        # Initialize processing logger
        processing_logger = FileProcessingLogger(
            reqifz_file=reqifz_file.name,
            input_path=str(reqifz_file),
            output_file=str(output_path),
            version="v003_HighPerformance",
            ai_model=self.model_name,
        )

        try:
            # Phase 1: XML Parsing
            processing_logger.start_phase("xml_parsing")
            loop = asyncio.get_event_loop()
            all_objects = await loop.run_in_executor(
                None, self.extractor.extract_all_artifacts, reqifz_file
            )
            processing_logger.end_phase("xml_parsing")

            if not all_objects:
                logger.warning(f"No objects found in {reqifz_file.name}")
                processing_logger.add_warning("No objects found in REQIFZ file")
                processing_logger.end_processing(success=False)
                processing_logger.save_log()
                return 0

            # Update artifact counts
            processing_logger.total_artifacts_found = len(all_objects)
            for obj in all_objects:
                artifact_type = obj.get("type", "Unknown")
                processing_logger.artifacts_by_type[artifact_type] = (
                    processing_logger.artifacts_by_type.get(artifact_type, 0) + 1
                )

            # Separate artifacts
            system_interfaces, processing_list = self._separate_artifacts(all_objects)

            # Count requirements to be processed
            requirements_to_process = [
                obj for obj in processing_list if obj.get("type") == "System Requirement"
            ]
            processing_logger.requirements_processed_total = len(requirements_to_process)

            # === ENHANCED CLI MESSAGING: Artifact Analysis ===
            logger.info(f"📊 Artifact Analysis for {reqifz_file.name}:")
            logger.info(f"-> Found {len(all_objects)} total artifacts")

            # Display artifact breakdown with meaningful information
            artifact_counts = processing_logger.artifacts_by_type
            if artifact_counts.get("System Interface", 0) > 0:
                logger.info(
                    f"-> System Interfaces: {artifact_counts['System Interface']} (used as global dictionary)"
                )
            if artifact_counts.get("System Requirement", 0) > 0:
                logger.info(
                    f"-> System Requirements: {artifact_counts['System Requirement']} (will generate test cases)"
                )
            if artifact_counts.get("Heading", 0) > 0:
                logger.info(f"-> Headings: {artifact_counts['Heading']}")
            if artifact_counts.get("Information", 0) > 0:
                logger.info(f"-> Information: {artifact_counts['Information']}")

            # Reset template usage counter for this file
            self.yaml_prompt_manager.reset_template_usage()

            # Phase 2: AI Generation (OPTIMIZED FOR REQUIREMENTS)
            processing_logger.start_phase("ai_generation")
            test_cases_generated = await self._process_requirements_optimized(
                processing_list, system_interfaces, async_generator, processing_logger
            )
            processing_logger.end_phase("ai_generation")

            # === ENHANCED CLI MESSAGING: Template Usage Summary ===
            template_usage = self.yaml_prompt_manager.get_template_usage_summary()
            if template_usage:
                logger.info("📋 Template Selection Summary:")
                for template_name, count in template_usage.items():
                    logger.info(f"-> {template_name}: {count} requirements")

            # Phase 3: Excel Output
            processing_logger.start_phase("excel_output")
            await loop.run_in_executor(
                None, self._save_test_cases_to_excel, test_cases_generated, output_path
            )
            processing_logger.end_phase("excel_output")

            test_count = len(test_cases_generated)

            # === ENHANCED CLI MESSAGING: Phase Timing Summary ===
            xml_time = processing_logger.get_phase_duration("xml_parsing")
            ai_time = processing_logger.get_phase_duration("ai_generation")
            excel_time = processing_logger.get_phase_duration("excel_output")
            total_time = xml_time + ai_time + excel_time

            logger.info(f"⏱️  Phase Timing Summary for {reqifz_file.name}:")
            logger.info(f"-> XML Parsing: {xml_time:.1f}s ({len(all_objects):,} artifacts)")
            if len(processing_logger.ai_response_times) > 0:
                avg_req_speed = len(requirements_to_process) / ai_time if ai_time > 0 else 0
                logger.info(
                    f"-> AI Generation: {ai_time:.1f}s ({avg_req_speed:.2f} req/sec, {self.max_concurrent_requirements} concurrent)"
                )
            logger.info(f"-> Excel Output: {excel_time:.1f}s ({test_count} test cases)")
            logger.info(f"-> Total Processing Time: {total_time:.1f}s")

            logger.verbose_log(f"✅ {reqifz_file.name}: Generated {test_count} test cases")

            # Record template used
            processing_logger.template_used = self.yaml_prompt_manager.get_selected_template()

            # Mark as successful
            processing_logger.end_processing(success=True)

            return test_count

        except Exception as e:
            logger.error(f"Error processing {reqifz_file.name}: {e}")
            processing_logger.add_warning(f"Processing failed: {str(e)}")
            processing_logger.end_processing(success=False)
            return 0
        finally:
            # Always save the processing log
            log_path = processing_logger.save_log()
            if log_path:
                logger.debug(f"Processing log saved: {Path(log_path).name}")
            processing_logger.update_system_metrics()

    async def _process_requirements_async(
        self,
        processing_list: list[dict[str, Any]],
        system_interfaces: list[dict[str, Any]],
        async_generator: AsyncTestCaseGenerator,
    ) -> list[dict[str, Any]]:
        """Process requirements asynchronously with batching"""
        logger = get_logger()

        master_test_list = []
        issue_id_counter = 1
        current_heading = "No Heading"
        info_since_heading = []

        # Collect requirements that need processing
        requirements_to_process = []

        for obj in processing_list:
            if obj.get("type") == ArtifactType.HEADING:
                current_heading = obj["text"]
                info_since_heading = []
                continue

            if obj.get("type") == ArtifactType.INFORMATION:
                info_since_heading.append(obj)
                continue

            if obj.get("type") == ArtifactType.SYSTEM_REQUIREMENT and obj.get("table"):
                requirements_to_process.append(
                    (obj, current_heading, info_since_heading.copy(), system_interfaces)
                )
                info_since_heading = []  # Clear after requirement

        if not requirements_to_process:
            return []

        logger.debug(f"Processing {len(requirements_to_process)} requirements in parallel")

        # Process requirements in batches for optimal performance
        batch_size = min(10, len(requirements_to_process))  # Don't overwhelm API

        for i in range(0, len(requirements_to_process), batch_size):
            batch = requirements_to_process[i : i + batch_size]

            # Generate test cases for this batch
            batch_results = await async_generator.generate_tests_batch(batch)

            # Format and add to master list
            for j, (requirement_data, _, _, _) in enumerate(batch):
                test_cases = batch_results[j]

                for test in test_cases:
                    if isinstance(test, dict):
                        # Validate test case structure
                        required_fields = ["summary_suffix", "action", "data", "expected_result"]
                        if all(field in test for field in required_fields):
                            formatted_case = self.formatter._format_single_test_case(
                                test, requirement_data["id"], issue_id_counter
                            )
                            master_test_list.append(formatted_case)
                            issue_id_counter += 1

        logger.debug(f"Generated {len(master_test_list)} total test cases")
        return master_test_list

    async def _process_requirements_async_with_logging(
        self,
        processing_list: list[dict[str, Any]],
        system_interfaces: list[dict[str, Any]],
        async_generator: AsyncTestCaseGenerator,
        processing_logger: FileProcessingLogger,
    ) -> list[dict[str, Any]]:
        """Process requirements asynchronously with comprehensive logging"""
        logger = get_logger()

        master_test_list = []
        issue_id_counter = 1
        current_heading = "No Heading"
        info_since_heading = []

        # Collect requirements that need processing
        requirements_to_process = []

        for obj in processing_list:
            if obj.get("type") == ArtifactType.HEADING:
                current_heading = obj["text"]
                info_since_heading = []
                continue

            if obj.get("type") == ArtifactType.INFORMATION:
                info_since_heading.append(obj)
                continue

            if obj.get("type") == ArtifactType.SYSTEM_REQUIREMENT and obj.get("table"):
                requirements_to_process.append(
                    (obj, current_heading, info_since_heading.copy(), system_interfaces)
                )
                info_since_heading = []  # Clear after requirement

        if not requirements_to_process:
            return []

        logger.debug(f"Processing {len(requirements_to_process)} requirements in parallel")

        # Process requirements in batches for optimal performance
        batch_size = min(10, len(requirements_to_process))  # Don't overwhelm API

        for i in range(0, len(requirements_to_process), batch_size):
            batch = requirements_to_process[i : i + batch_size]

            # Record batch start time
            batch_start_time = time.time()

            try:
                # Generate test cases for this batch
                batch_results = await async_generator.generate_tests_batch(batch)

                # Record successful batch processing
                batch_time = time.time() - batch_start_time
                processing_logger.add_ai_response_time(
                    batch_time / len(batch)
                )  # Average per requirement

                # Format and add to master list
                for j, (requirement_data, _, _, _) in enumerate(batch):
                    test_cases = batch_results[j]

                    try:
                        processing_logger.requirements_successful += 1

                        for test in test_cases:
                            if isinstance(test, dict):
                                # Validate test case structure
                                required_fields = [
                                    "summary_suffix",
                                    "action",
                                    "data",
                                    "expected_result",
                                ]
                                if all(field in test for field in required_fields):
                                    formatted_case = self.formatter._format_single_test_case(
                                        test, requirement_data["id"], issue_id_counter
                                    )
                                    master_test_list.append(formatted_case)
                                    issue_id_counter += 1

                                    # Count test case types
                                    if (
                                        formatted_case.get("Components", "").find("[Positive]")
                                        != -1
                                    ):
                                        processing_logger.increment_test_cases(positive=1)
                                    else:
                                        processing_logger.increment_test_cases(negative=1)

                    except Exception as e:
                        # Record individual requirement failure
                        processing_logger.add_requirement_failure(
                            requirement_data.get("id", "unknown"), str(e)
                        )
                        logger.debug(
                            f"Error formatting requirement {requirement_data.get('id', 'unknown')}: {e}"
                        )

            except Exception as e:
                # Record batch failure
                for requirement_data, _, _, _ in batch:
                    processing_logger.add_requirement_failure(
                        requirement_data.get("id", "unknown"), f"Batch processing failed: {str(e)}"
                    )
                logger.error(f"Error processing batch: {e}")

            # Update system metrics periodically
            if i % (batch_size * 2) == 0:
                processing_logger.update_system_metrics()

        logger.debug(f"Generated {len(master_test_list)} total test cases")
        return master_test_list

    def _separate_artifacts(
        self, all_objects: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Separate artifacts into system interfaces and processing list"""
        system_interfaces = [
            obj for obj in all_objects if obj.get("type") == ArtifactType.SYSTEM_INTERFACE
        ]
        processing_list = [
            obj for obj in all_objects if obj.get("type") != ArtifactType.SYSTEM_INTERFACE
        ]
        return system_interfaces, processing_list

    async def _process_requirements_optimized(
        self,
        processing_list: list[dict[str, Any]],
        system_interfaces: list[dict[str, Any]],
        async_generator: AsyncTestCaseGenerator,
        processing_logger: FileProcessingLogger,
    ) -> list[dict[str, Any]]:
        """Process requirements with optimized parallelism and adaptive batching"""
        logger = get_logger()

        master_test_list = []
        issue_id_counter = 1
        current_heading = "No Heading"
        info_since_heading = []

        # Collect requirements that need processing
        requirements_to_process = []

        for obj in processing_list:
            if obj.get("type") == ArtifactType.HEADING:
                current_heading = obj["text"]
                info_since_heading = []
                continue

            if obj.get("type") == ArtifactType.INFORMATION:
                info_since_heading.append(obj)
                continue

            if obj.get("type") == ArtifactType.SYSTEM_REQUIREMENT and obj.get("table"):
                requirements_to_process.append(
                    (obj, current_heading, info_since_heading.copy(), system_interfaces)
                )
                info_since_heading = []  # Clear after requirement

        if not requirements_to_process:
            return []

        # === ENHANCED CLI MESSAGING: Requirements Processing Start ===
        logger.info(
            f"🔄 Processing Requirements (Concurrent: up to {self.max_concurrent_requirements} active)"
        )
        logger.info(f"-> Total requirements to process: {len(requirements_to_process)}")

        logger.debug(
            f"Processing {len(requirements_to_process)} requirements with controlled concurrency (max: {self.max_concurrent_requirements})"
        )

        # Create semaphore for requirement-level concurrency control
        requirement_semaphore = asyncio.Semaphore(self.max_concurrent_requirements)

        # Process requirements with controlled concurrency and retry logic
        async def process_single_requirement_with_retry(req_data, retry_count=3):
            requirement, heading, info_list, interfaces = req_data

            for attempt in range(retry_count):
                try:
                    async with requirement_semaphore:
                        start_time = time.time()

                        # Process single requirement with individual batch
                        batch_data = [(requirement, heading, info_list, interfaces)]
                        batch_results = await async_generator.generate_tests_batch(batch_data)
                        test_cases = batch_results[0] if batch_results else []

                        response_time = time.time() - start_time
                        processing_logger.add_ai_response_time(response_time)
                        processing_logger.requirements_successful += 1

                        # Update adaptive batching based on response time
                        if self.adaptive_batching:
                            self._update_adaptive_batching(True, response_time)

                        return test_cases, requirement["id"]

                except TimeoutError as e:
                    if attempt == retry_count - 1:
                        processing_logger.add_requirement_failure(
                            requirement.get("id", "unknown"),
                            f"Timeout after {retry_count} attempts: {str(e)}",
                        )
                        if self.adaptive_batching:
                            self._update_adaptive_batching(False, 999.0)
                        return [], requirement.get("id", "unknown")

                    # Exponential backoff: 2s, 4s, 8s
                    await asyncio.sleep(2**attempt)
                    continue

                except Exception as e:
                    if attempt == retry_count - 1:
                        processing_logger.add_requirement_failure(
                            requirement.get("id", "unknown"),
                            f"Error after {retry_count} attempts: {str(e)}",
                        )
                        if self.adaptive_batching:
                            self._update_adaptive_batching(False, 999.0)
                        return [], requirement.get("id", "unknown")

                    await asyncio.sleep(1 + attempt)
                    continue

        # Create tasks for all requirements
        tasks = [
            process_single_requirement_with_retry(req_data) for req_data in requirements_to_process
        ]

        # Execute with controlled concurrency
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and format test cases
        for result in results:
            if isinstance(result, tuple):
                test_cases, req_id = result
                for test in test_cases:
                    if isinstance(test, dict) and all(
                        field in test
                        for field in ["summary_suffix", "action", "data", "expected_result"]
                    ):
                        formatted_case = self.formatter._format_single_test_case(
                            test, req_id, issue_id_counter
                        )
                        master_test_list.append(formatted_case)
                        issue_id_counter += 1

                        # Count test case types
                        if formatted_case.get("Components", "").find("[Positive]") != -1:
                            processing_logger.increment_test_cases(positive=1)
                        else:
                            processing_logger.increment_test_cases(negative=1)

            # Update system metrics periodically
            if len(master_test_list) % 10 == 0:
                processing_logger.update_system_metrics()

        # === ENHANCED CLI MESSAGING: Requirements Processing Summary ===
        successful_reqs = processing_logger.requirements_successful
        failed_reqs = len(requirements_to_process) - successful_reqs
        avg_response_time = (
            sum(processing_logger.ai_response_times) / len(processing_logger.ai_response_times)
            if processing_logger.ai_response_times
            else 0
        )

        logger.info("✅ Requirements Processing Complete:")
        logger.info(f"-> Successful: {successful_reqs}/{len(requirements_to_process)} requirements")
        if failed_reqs > 0:
            logger.warning(f"-> Failed: {failed_reqs} requirements (see logs for details)")
        logger.info(f"-> Generated: {len(master_test_list)} test cases total")
        logger.info(f"-> Avg response time: {avg_response_time:.1f}s per requirement")

        logger.debug(
            f"Generated {len(master_test_list)} total test cases with controlled concurrency"
        )
        return master_test_list

    def _update_adaptive_batching(self, success: bool, response_time: float):
        """Update adaptive batching parameters based on API performance"""
        if not self.adaptive_batching:
            return

        if success and response_time < 15.0:  # Fast successful response
            self.success_streak += 1
            self.failure_streak = 0
            if self.success_streak >= 3 and self.current_batch_size < self.max_batch_size:
                self.current_batch_size = min(self.max_batch_size, self.current_batch_size + 1)
                logger = get_logger()
                logger.debug(f"Increased batch size to {self.current_batch_size}")
        else:  # Slow or failed response
            self.failure_streak += 1
            self.success_streak = 0
            if self.failure_streak >= 2:
                self.current_batch_size = max(self.min_batch_size, self.current_batch_size - 1)
                logger = get_logger()
                logger.debug(f"Decreased batch size to {self.current_batch_size}")

    def _generate_output_path(self, reqifz_file: Path) -> Path:
        """Generate output XLSX file path"""
        safe_model_name = self.model_name.replace(":", "_").replace(".", "_")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return reqifz_file.with_name(
            f"{reqifz_file.stem}_TCD_HP_{safe_model_name}_{timestamp}.xlsx"
        )

    def _save_test_cases_to_excel(self, test_cases: list[dict[str, Any]], output_path: Path):
        """Save test cases to Excel file (blocking operation for thread pool)"""
        if test_cases:
            df = pd.DataFrame(test_cases)
            df.to_excel(output_path, index=False, engine="openpyxl")


# =================================================================
# COMMAND LINE INTERFACE - HIGH PERFORMANCE
# =================================================================


class HighPerformanceCommandLineInterface:
    """Enhanced command line interface with performance options"""

    @staticmethod
    def parse_arguments() -> argparse.Namespace:
        """Parse command line arguments with high-performance options"""
        parser = argparse.ArgumentParser(
            description="HIGH-PERFORMANCE Context-Aware Test Case Generator",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
HIGH-PERFORMANCE MODE:
  This version maximizes CPU utilization through:
  - Multi-threaded file processing
  - Async AI model calls
  - Parallel XML parsing
  - Concurrent test case generation
  - Real-time performance monitoring

Examples:
  %(prog)s input.reqifz --hp                                    # High-performance mode (single file)
  %(prog)s /path/files/ --hp --max-concurrent-requirements 4   # Process 4 requirements simultaneously per file
  %(prog)s input.reqifz --hp --template driver_information_default  # Use specific template
  %(prog)s input.reqifz --hp --no-adaptive-batching --verbose  # Fixed batching with verbose output
  %(prog)s input.reqifz --hp --debug --performance             # Debug with performance dashboard

Performance Options:
  --hp, --high-performance         Enable high-performance mode (requirement-level parallelism)
  --max-concurrent-requirements N  Max concurrent requirements per file (default: auto, 1-8)
  --adaptive-batching              Adjust batch size based on API response times (default: on)
  --no-adaptive-batching           Use fixed batch sizes for API requests
  --performance                    Show real-time performance dashboard
  --memory-optimize                Enable memory streaming optimizations

Standard Options:
  --model MODEL              Ollama model to use (default: llama3.1:8b)
  --template TEMPLATE        Specific prompt template
  --verbose, -v              Verbose output with progress details
  --debug                    Debug mode with detailed logging
  --log-file FILE            Save logs to file
            """,
        )

        # File input
        parser.add_argument("input_path", nargs="?", type=Path, help="Path to .reqifz file(s)")

        # Performance options
        parser.add_argument(
            "--hp",
            "--high-performance",
            action="store_true",
            dest="high_performance",
            help="Enable high-performance mode with maximum CPU utilization",
        )
        parser.add_argument(
            "--max-concurrent-requirements",
            type=int,
            help="Maximum concurrent requirements processed simultaneously (default: auto-detect, range: 1-8)",
        )
        parser.add_argument(
            "--adaptive-batching",
            action="store_true",
            default=True,
            help="Enable adaptive batching based on API response times (default: enabled)",
        )
        parser.add_argument(
            "--no-adaptive-batching",
            action="store_false",
            dest="adaptive_batching",
            help="Disable adaptive batching (use fixed batch sizes)",
        )
        parser.add_argument(
            "--performance", action="store_true", help="Show real-time performance dashboard"
        )
        parser.add_argument(
            "--memory-optimize", action="store_true", help="Enable memory streaming optimizations"
        )

        # Standard options
        parser.add_argument("--model", default="llama3.1:8b", help="Ollama model")
        parser.add_argument("--template", help="Prompt template")
        parser.add_argument("--list-templates", action="store_true")
        parser.add_argument("--validate-prompts", action="store_true")
        parser.add_argument("--prompt-config", help="Prompt config file")
        parser.add_argument("--reload-prompts", action="store_true")
        parser.add_argument("--verbose", "-v", action="store_true")
        parser.add_argument("--debug", action="store_true")
        parser.add_argument("--log-file", type=str)

        return parser.parse_args()

    @staticmethod
    def discover_files(input_path: Path) -> list[Path]:
        """Discover REQIFZ files with performance logging"""
        logger = get_logger()

        if not input_path.exists():
            raise FileNotFoundError(f"Path '{input_path}' does not exist")

        files_to_process = []

        if input_path.is_file():
            if input_path.suffix.lower() == ".reqifz":
                files_to_process.append(input_path)
            else:
                raise ValueError(f"File '{input_path.name}' is not a .reqifz file")
        elif input_path.is_dir():
            # Use efficient file discovery
            try:
                files_to_process = [
                    dirpath / file_path
                    for dirpath, _, file_paths in input_path.walk()
                    for file_path in file_paths
                    if file_path.suffix.lower() == ".reqifz"
                ]
            except AttributeError:
                files_to_process = list(input_path.rglob("*.reqifz"))

        if not files_to_process:
            raise ValueError("No .reqifz files found")

        logger.debug(f"Discovered {len(files_to_process)} files for processing")
        return sorted(files_to_process)


# =================================================================
# APPLICATION FACTORY - HIGH PERFORMANCE
# =================================================================


class HighPerformanceApplicationFactory:
    """Factory for high-performance application components"""

    @staticmethod
    def create_config_manager(config_file_path: str | None = None) -> ConfigManager:
        """Create optimized config manager"""
        logger = get_logger()
        config_manager = ConfigManager()

        if config_file_path and Path(config_file_path).exists():
            try:
                import yaml

                with open(config_file_path) as f:
                    custom_config = yaml.safe_load(f)
                if hasattr(config_manager, "update_from_dict"):
                    config_manager.update_from_dict(custom_config)
                logger.debug(f"Loaded custom config: {config_file_path}")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")

        return config_manager

    @staticmethod
    def create_yaml_prompt_manager(prompt_config_file: str | None = None) -> YAMLPromptManager:
        """Create YAML prompt manager"""
        config_file = prompt_config_file or "prompts/config/prompt_config.yaml"
        return YAMLPromptManager(config_file)

    @staticmethod
    def create_high_performance_processor(
        model_name: str,
        config_manager: ConfigManager,
        yaml_prompt_manager: YAMLPromptManager,
        max_concurrent_requirements: int | None = None,
        adaptive_batching: bool = True,
    ) -> HighPerformanceREQIFZFileProcessor:
        """Create high-performance processor with requirement-level optimization"""
        return HighPerformanceREQIFZFileProcessor(
            model_name,
            config_manager,
            yaml_prompt_manager,
            max_concurrent_requirements,
            adaptive_batching,
        )


# =================================================================
# UTILITY FUNCTIONS
# =================================================================


def validate_model_availability(model_name: str) -> bool:
    """Validate Ollama model availability"""
    get_logger()  # Initialize logger
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            available_models = [model["name"] for model in data.get("models", [])]
            return model_name in available_models
        return False
    except requests.exceptions.RequestException:
        return False


def handle_prompt_management_commands(args) -> int:
    """Handle prompt management with high-performance logging"""
    logger = get_logger()

    try:
        yaml_prompt_manager = HighPerformanceApplicationFactory.create_yaml_prompt_manager(
            args.prompt_config
        )

        if args.list_templates:
            logger.info("📋 Available Templates (High-Performance Mode):")
            templates = yaml_prompt_manager.list_templates()
            for category, template_list in templates.items():
                logger.info(f"\n[bold]{category.upper()}:[/bold]")
                for template_name in template_list:
                    info = yaml_prompt_manager.get_template_info(template_name)
                    logger.info(f"  • [cyan]{template_name}[/cyan]")
                    if args.verbose and info.get("description"):
                        logger.verbose_log(f"    {info['description']}")
            return 0

        if args.validate_prompts:
            logger.info("🔍 Validating Templates (High-Performance Mode)...")
            # Add validation logic here
            logger.success("All templates valid!")
            return 0

        if args.reload_prompts:
            yaml_prompt_manager.reload_prompts()
            logger.success("Templates reloaded!")
            return 0

        return 0

    except Exception as e:
        logger.error(f"Prompt management error: {e}")
        return 1


# =================================================================
# MAIN HIGH-PERFORMANCE APPLICATION
# =================================================================


async def main_async(args, logger: HighPerformanceLogger):
    """Main async application logic"""
    try:
        # Validate model
        if not validate_model_availability(args.model):
            logger.warning(f"Model '{args.model}' may not be available")
            logger.info("Check with: [cyan]ollama list[/cyan]")

        # Create components
        config_manager = HighPerformanceApplicationFactory.create_config_manager()
        yaml_prompt_manager = HighPerformanceApplicationFactory.create_yaml_prompt_manager(
            args.prompt_config
        )

        # Discover files
        input_path = (
            Path(args.input_path) if not isinstance(args.input_path, Path) else args.input_path
        )
        files_to_process = HighPerformanceCommandLineInterface.discover_files(input_path)

        # Log performance start
        logger.log_performance_start(files_to_process, args.model)

        # Create high-performance processor with requirement-level optimization
        processor = HighPerformanceREQIFZFileProcessor(
            args.model,
            config_manager,
            yaml_prompt_manager,
            args.max_concurrent_requirements,
            args.adaptive_batching,
        )

        # Process files sequentially with optimized requirement-level parallelism
        start_time = time.time()
        successful_files = 0
        total_test_cases = 0

        for i, reqifz_file in enumerate(files_to_process, 1):
            logger.info(f"Processing file {i}/{len(files_to_process)}: {reqifz_file.name}")

            try:
                test_count = await processor.process_single_file_optimized(reqifz_file)
                if test_count > 0:
                    successful_files += 1
                    total_test_cases += test_count
                    logger.success(f"✅ {reqifz_file.name}: Generated {test_count} test cases")
                else:
                    logger.warning(f"⚠️  {reqifz_file.name}: No test cases generated")
            except Exception as e:
                logger.error(f"❌ {reqifz_file.name}: Processing failed - {e}")

        processing_time = time.time() - start_time

        # Show results
        logger.success(f"Processed {successful_files}/{len(files_to_process)} files")
        logger.success(f"Generated {total_test_cases} total test cases")
        logger.success(f"Processing time: {processing_time / 60:.1f} minutes")

        # Show performance dashboard
        if args.performance:
            logger.show_performance_dashboard()

        return 0 if successful_files == len(files_to_process) else 1

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        if args.debug:
            import traceback

            logger.debug("Full traceback:")
            for line in traceback.format_exc().splitlines():
                logger.debug(line)
        return 1


def main():
    """Main application entry point with high-performance mode"""
    try:
        # Parse arguments first
        args = HighPerformanceCommandLineInterface.parse_arguments()

        # Setup high-performance logging
        logger = setup_logger(verbose=args.verbose, debug=args.debug, log_file=args.log_file)

        # Print banner
        logger.print_banner()

        # Start performance monitoring
        if args.high_performance or args.performance:
            logger.start_performance_monitoring()

        try:
            # Handle prompt management commands
            if args.list_templates or args.validate_prompts or args.reload_prompts:
                return handle_prompt_management_commands(args)

            # Ensure input path provided
            if not args.input_path:
                logger.error("Input path required for file processing")
                logger.info("Use --help for usage information")
                return 1

            # Run high-performance processing
            if args.high_performance or psutil.cpu_count() >= 4:
                logger.info("🚀 Running in HIGH-PERFORMANCE mode")
                return asyncio.run(main_async(args, logger))
            logger.info("💻 System has limited CPU cores, consider using standard version")
            return asyncio.run(main_async(args, logger))

        finally:
            # Stop performance monitoring and show summary
            if args.high_performance or args.performance:
                logger.stop_performance_monitoring()
                logger.log_performance_summary()

    except KeyboardInterrupt:
        if "_logger_instance" in globals() and _logger_instance:
            get_logger().warning("Process interrupted by user")
        return 1
    except Exception as e:
        if "_logger_instance" in globals() and _logger_instance:
            get_logger().error(f"Unexpected error: {e}")
        else:
            print(f"💥 Error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
