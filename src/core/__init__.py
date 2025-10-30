"""
Core components for the AI Test Case Generator.

This package contains the fundamental building blocks for processing REQIFZ files
and generating test cases using Ollama AI models.
"""

from .extractors import HighPerformanceREQIFArtifactExtractor, REQIFArtifactExtractor
from .formatters import StreamingTestCaseFormatter, TestCaseFormatter
from .generators import AsyncTestCaseGenerator, TestCaseGenerator
from .ollama_client import AsyncOllamaClient, OllamaClient
from .parsers import FastJSONResponseParser, HTMLTableParser, JSONResponseParser
from .prompt_builder import PromptBuilder

__all__ = [
    "OllamaClient",
    "AsyncOllamaClient",
    "HTMLTableParser",
    "JSONResponseParser",
    "FastJSONResponseParser",
    "REQIFArtifactExtractor",
    "HighPerformanceREQIFArtifactExtractor",
    "TestCaseGenerator",
    "AsyncTestCaseGenerator",
    "TestCaseFormatter",
    "StreamingTestCaseFormatter",
    "PromptBuilder",
]
