"""
Core components for the AI Test Case Generator.

This package contains the fundamental building blocks for processing REQIFZ files
and generating test cases using Ollama AI models.
"""

from core.extractors import HighPerformanceREQIFArtifactExtractor, REQIFArtifactExtractor
from core.formatters import StreamingTestCaseFormatter, TestCaseFormatter
from core.generators import AsyncTestCaseGenerator, TestCaseGenerator
from core.ollama_client import AsyncOllamaClient, OllamaClient
from core.parsers import FastJSONResponseParser, HTMLTableParser, JSONResponseParser

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
]
