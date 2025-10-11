#!/usr/bin/env python3
"""
Centralized Application Logger for AI Test Case Generator

This module provides application-level logging that complements the existing
FileProcessingLogger. It handles overall application health, debugging,
and monitoring across all operations.
"""

import json
import logging
import sys
import threading
import time
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict

import psutil
from rich.console import Console
from rich.logging import RichHandler

# Global logger instance
_app_logger_instance: AppLogger | None = None
_logger_lock = threading.Lock()


class AppLogger:
    """
    Centralized application logger with structured logging, performance monitoring,
    and multi-output support (console, file, JSON).
    """

    __slots__ = (
        "name",
        "log_level",
        "log_directory",
        "enable_json_logging",
        "enable_console_logging",
        "logger",
        "app_start_time",
        "session_id",
        "metrics",
    )

    def __init__(
        self,
        name: str = "ai_tc_generator",
        log_level: str = "INFO",
        log_to_file: bool = True,
        log_directory: Path = Path("logs"),
        enable_json_logging: bool = True,
        enable_console_logging: bool = True,
        max_log_size_mb: int = 10,
        backup_count: int = 5,
    ):
        self.name = name
        self.log_level = log_level.upper()
        self.log_directory = log_directory
        self.enable_json_logging = enable_json_logging
        self.enable_console_logging = enable_console_logging

        # Ensure log directory exists
        if log_to_file:
            self.log_directory.mkdir(exist_ok=True)

        # Create the main logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.log_level))

        # Clear any existing handlers
        self.logger.handlers.clear()

        # Console logger with Rich formatting
        if enable_console_logging:
            console = Console(stderr=True)
            console_handler = RichHandler(
                console=console,
                show_time=True,
                show_path=False,
                rich_tracebacks=True,
            )
            console_handler.setLevel(getattr(logging, self.log_level))
            console_formatter = logging.Formatter(fmt="%(message)s", datefmt="[%X]")
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # File logger for text logs
        if log_to_file:
            log_file = self.log_directory / f"{name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_log_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)  # Capture all levels in file
            file_formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        # JSON logger for structured logs
        if enable_json_logging and log_to_file:
            json_log_file = self.log_directory / f"{name}_structured.jsonl"
            json_handler = TimedRotatingFileHandler(
                json_log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8"
            )
            json_handler.setLevel(logging.DEBUG)
            json_formatter = self._JsonFormatter()
            json_handler.setFormatter(json_formatter)
            self.logger.addHandler(json_handler)

        # Application state tracking
        self.app_start_time = time.time()
        self.session_id = self._generate_session_id()
        self.metrics = {
            "files_processed": 0,
            "total_test_cases_generated": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "ai_api_calls": 0,
            "performance_stats": {
                "peak_cpu_percent": 0.0,
                "peak_memory_mb": 0.0,
                "avg_response_time": 0.0,
            },
        }

        # Performance monitoring
        self._start_performance_monitoring()

        # Log application startup
        self.info(
            "Application logger initialized",
            extra={
                "session_id": self.session_id,
                "log_level": self.log_level,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "log_directory": str(self.log_directory),
            },
        )

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}_{id(self) % 10000:04d}"

    def _start_performance_monitoring(self) -> None:
        """Start background performance monitoring"""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            self.metrics["performance_stats"]["peak_cpu_percent"] = max(
                self.metrics["performance_stats"]["peak_cpu_percent"], cpu_percent
            )
            self.metrics["performance_stats"]["peak_memory_mb"] = max(
                self.metrics["performance_stats"]["peak_memory_mb"], memory_mb
            )
        except Exception:
            pass  # Silently handle performance monitoring errors

    class _JsonFormatter(logging.Formatter):
        """Custom JSON formatter for structured logging"""

        def format(self, record: logging.LogRecord) -> str:
            """Format log record as JSON"""
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)

            # Add extra fields from logging calls
            if hasattr(record, "extra_data"):
                log_entry.update(record.extra_data)

            return json.dumps(log_entry, ensure_ascii=False)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with optional extra data"""
        self._log_with_extras(logging.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message with optional extra data"""
        self._log_with_extras(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with optional extra data"""
        self.metrics["total_warnings"] += 1
        self._log_with_extras(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message with optional extra data"""
        self.metrics["total_errors"] += 1
        self._log_with_extras(logging.ERROR, message, kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with optional extra data"""
        self.metrics["total_errors"] += 1
        self._log_with_extras(logging.CRITICAL, message, kwargs)

    def _log_with_extras(self, level: int, message: str, extra_data: Dict[str, Any]) -> None:
        """Internal method to log with extra structured data"""
        # Add session context
        extra_data.setdefault("session_id", self.session_id)
        extra_data.setdefault("uptime_seconds", time.time() - self.app_start_time)

        # Create log record with extra data
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "",  # pathname
            0,  # lineno
            message,
            (),  # args
            None,  # exc_info
        )
        record.extra_data = extra_data
        self.logger.handle(record)

    def log_file_processing_start(self, file_path: str, model: str, mode: str) -> None:
        """Log start of file processing"""
        self.info(
            f"Starting file processing: {Path(file_path).name}",
            file_path=file_path,
            model=model,
            processing_mode=mode,
            event_type="file_processing_start",
        )

    def log_file_processing_complete(
        self,
        file_path: str,
        success: bool,
        test_cases_generated: int,
        processing_time: float,
        **kwargs,
    ) -> None:
        """Log completion of file processing"""
        if success:
            self.metrics["files_processed"] += 1
            self.metrics["total_test_cases_generated"] += test_cases_generated

        level_method = self.info if success else self.error
        level_method(
            f"File processing {'completed' if success else 'failed'}: {Path(file_path).name}",
            file_path=file_path,
            success=success,
            test_cases_generated=test_cases_generated,
            processing_time_seconds=processing_time,
            event_type="file_processing_complete",
            **kwargs,
        )

    def log_ai_api_call(
        self,
        model: str,
        response_time: float,
        success: bool,
        requirement_id: str | None = None,
        **kwargs,
    ) -> None:
        """Log AI API call metrics"""
        self.metrics["ai_api_calls"] += 1

        # Update average response time
        current_avg = self.metrics["performance_stats"]["avg_response_time"]
        call_count = self.metrics["ai_api_calls"]
        new_avg = ((current_avg * (call_count - 1)) + response_time) / call_count
        self.metrics["performance_stats"]["avg_response_time"] = new_avg

        self.debug(
            f"AI API call {'successful' if success else 'failed'}: {model}",
            model=model,
            response_time_seconds=response_time,
            success=success,
            requirement_id=requirement_id,
            event_type="ai_api_call",
            **kwargs,
        )

    def log_application_metrics(self) -> None:
        """Log current application metrics"""
        # Update performance stats
        self._start_performance_monitoring()

        uptime = time.time() - self.app_start_time
        self.info(
            "Application metrics snapshot",
            event_type="metrics_snapshot",
            uptime_seconds=uptime,
            **self.metrics,
        )

    def log_environment_info(self, config_manager) -> None:
        """Log environment and configuration information"""
        try:
            import subprocess

            ollama_version = "unknown"
            try:
                result = subprocess.run(
                    ["ollama", "--version"], check=False, capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    ollama_version = (
                        result.stdout.strip().split()[-1] if result.stdout.strip() else "unknown"
                    )
            except Exception:
                pass

            self.info(
                "Environment information",
                event_type="environment_info",
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                ollama_version=ollama_version,
                ollama_host=config_manager.ollama.host,
                ollama_port=config_manager.ollama.port,
                default_model=config_manager.ollama.synthesizer_model,
                log_level=config_manager.logging.log_level,
                max_concurrent=config_manager.ollama.concurrent_requests,
            )
        except Exception as e:
            self.warning(f"Could not gather environment info: {e}")

    def shutdown(self) -> None:
        """Gracefully shutdown the logger"""
        uptime = time.time() - self.app_start_time
        self.info(
            "Application logger shutting down",
            event_type="application_shutdown",
            total_uptime_seconds=uptime,
            final_metrics=self.metrics,
        )

        # Close all handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)


def get_app_logger(config_manager=None) -> AppLogger:
    """
    Get the global application logger instance (singleton pattern).

    Args:
        config_manager: Optional ConfigManager for initial setup

    Returns:
        AppLogger instance
    """
    global _app_logger_instance

    with _logger_lock:
        if _app_logger_instance is None:
            # Initialize with default or config values
            if config_manager:
                log_config = config_manager.logging
                _app_logger_instance = AppLogger(
                    log_level=log_config.log_level,
                    log_to_file=log_config.log_to_file,
                    log_directory=Path(log_config.log_directory),
                    enable_console_logging=True,  # Always enable console for CLI app
                    enable_json_logging=True,
                )
                _app_logger_instance.log_environment_info(config_manager)
            else:
                _app_logger_instance = AppLogger()

        return _app_logger_instance


def shutdown_app_logger() -> None:
    """Shutdown the global application logger"""
    global _app_logger_instance

    with _logger_lock:
        if _app_logger_instance:
            _app_logger_instance.shutdown()
            _app_logger_instance = None


# Convenience functions for common logging operations
def log_info(message: str, **kwargs) -> None:
    """Convenience function for info logging"""
    get_app_logger().info(message, **kwargs)


def log_error(message: str, **kwargs) -> None:
    """Convenience function for error logging"""
    get_app_logger().error(message, **kwargs)


def log_warning(message: str, **kwargs) -> None:
    """Convenience function for warning logging"""
    get_app_logger().warning(message, **kwargs)


def log_debug(message: str, **kwargs) -> None:
    """Convenience function for debug logging"""
    get_app_logger().debug(message, **kwargs)
