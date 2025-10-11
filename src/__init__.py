"""
AI Test Case Generator - Modular Architecture

A comprehensive tool for generating automotive test cases from REQIF requirements
using AI language models. Built with clean, modular components for maintainability
and extensibility.
"""

__version__ = "2.1.0"
__architecture__ = "Modular"

# Public API exports
from .config import ConfigManager
from .processors.standard_processor import REQIFZFileProcessor
from .processors.hp_processor import HighPerformanceREQIFZFileProcessor
from .yaml_prompt_manager import YAMLPromptManager
from .app_logger import get_app_logger, shutdown_app_logger

__all__ = [
    "ConfigManager",
    "REQIFZFileProcessor",
    "HighPerformanceREQIFZFileProcessor",
    "YAMLPromptManager",
    "get_app_logger",
    "shutdown_app_logger",
    "__version__",
    "__architecture__"
]