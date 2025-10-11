"""
AI Test Case Generator - Modular Architecture

A comprehensive tool for generating automotive test cases from REQIF requirements
using AI language models. Built with clean, modular components for maintainability
and extensibility.
"""

__version__ = "2.1.0"
__architecture__ = "Modular"

# Public API exports
from .app_logger import get_app_logger, shutdown_app_logger
from .config import ConfigManager
from .processors.hp_processor import HighPerformanceREQIFZFileProcessor
from .processors.standard_processor import REQIFZFileProcessor
from .yaml_prompt_manager import YAMLPromptManager

__all__ = [
    "ConfigManager",
    "REQIFZFileProcessor",
    "HighPerformanceREQIFZFileProcessor",
    "YAMLPromptManager",
    "get_app_logger",
    "shutdown_app_logger",
    "__version__",
    "__architecture__",
]
