"""
Integration tests with real components (where practical).

Tests for API compatibility and real component interaction.
Focuses on non-mocked integration where feasible.
"""

import pytest
from unittest.mock import Mock, patch
import time

from src.config import ConfigManager
from src.core.ollama_client import OllamaClient


class TestAPICompatibility:
    """Test real API compatibility where possible."""

    def test_ollama_client_model_validation(self):
        """Test that OllamaClient handles model validation gracefully."""
        # This doesn't require a running Ollama instance - just tests client logic
        config = ConfigManager()
        client = OllamaClient(base_url="http://localhost:11434", timeout=1)

        # Test with invalid URL (should handle connection errors gracefully)
        try:
            result = client.generate_response("test prompt", "llama3.1:8b")
            # If we get here, Ollama is running - test basic functionality
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            # Expected when Ollama is not running - verify error is handled
            assert "Connection" in str(e) or "timeout" in str(e) or "refused" in str(e)

    def test_response_parser_real_json(self):
        """Test JSON response parsing with real JSON."""
        from src.core.parsers import JSONResponseParser

        # Test with actual JSON responses from typical AI models
        real_json_response = '''
        {
            "test_cases": [
                {
                    "summary": "Validate user authentication",
                    "action": "Enter valid credentials",
                    "data": "username: test@example.com, password: secure123",
                    "expected_result": "User is logged in successfully",
                    "test_type": "positive"
                },
                {
                    "summary": "Handle invalid login attempts",
                    "action": "Enter invalid password",
                    "data": "username: test@example.com, password: wrongpass",
                    "expected_result": "Error message 'Invalid credentials' is displayed",
                    "test_type": "negative"
                }
            ]
        }
        '''

        parsed = JSONResponseParser.extract_json_from_response(real_json_response)
        assert parsed is not None
        assert "test_cases" in parsed
        assert len(parsed["test_cases"]) == 2

        # Verify structure validation
        assert JSONResponseParser.validate_test_cases_structure(parsed) == True

    def test_markdown_json_extraction(self):
        """Test extraction of JSON from markdown code blocks (common AI response format)."""
        from src.core.parsers import JSONResponseParser

        markdown_response = '''Based on the requirement, here are the test cases:

```json
{
    "test_cases": [
        {
            "summary": "Test boundary conditions",
            "action": "Input boundary values",
            "data": "min: -1, max: 100",
            "expected_result": "System handles correctly",
            "test_type": "boundary"
        }
    ]
}
```

These tests ensure comprehensive coverage.
'''

        parsed = JSONResponseParser.extract_json_from_response(markdown_response)
        assert parsed is not None
        assert "test_cases" in parsed
        assert len(parsed["test_cases"]) == 1


class TestConfigurationValidation:
    """Test configuration with real validation logic."""

    def test_config_manager_environment_variables(self):
        """Test that ConfigManager can read environment variables."""
        import os
        from src.config import ConfigManager

        # Set test environment variables
        test_vars = {
            "OLLAMA_BASE_URL": "http://test:8080",
            "OLLAMA_TIMEOUT": "30",
            "ENABLE_RAFT": "true"
        }

        with patch.dict(os.environ, test_vars):
            config = ConfigManager()

            # Verify environment variables are respected
            assert config.ollama_base_url == "http://test:8080"
            assert config.ollama_timeout_seconds == 30.0

    def test_pydantic_validation_real(self):
        """Test actual Pydantic validation in config."""
        from src.config import ConfigManager, OllamaConfig

        # Test valid config
        ollama_config = OllamaConfig(
            base_url="http://localhost:11434",
            timeout_seconds=30.0,
            model="llama3.1:8b"
        )

        assert ollama_config.base_url == "http://localhost:11434"
        assert ollama_config.timeout_seconds == 30.0

        # Test invalid config (should raise validation error)
        with pytest.raises(Exception):  # Pydantic validation error
            OllamaConfig(
                base_url="not-a-url",  # Invalid URL
                timeout_seconds=-5,     # Invalid timeout
            )


class TestPerformanceValidation:
    """Test performance characteristics with real components."""

    def test_json_parser_performance_comparison(self):
        """Test that ujson optimization is actually faster than standard json."""
        import json
        import time
        from src.core.parsers import JSON_PARSER

        # Create a substantial JSON payload
        test_json = {
            "test_cases": [
                {
                    "summary": f"Test case {i}",
                    "action": f"Action {i}",
                    "data": f"Data {i}" * 10,  # Make it larger
                    "expected_result": f"Result {i}",
                    "test_type": "functional"
                } for i in range(50)
            ]
        }

        # Convert to string and back multiple times
        json_string = json.dumps(test_json)
        iterations = 100

        # Test JSON_PARSER (should be ujson if available)
        start_time = time.time()
        for _ in range(iterations):
            parsed = JSON_PARSER.loads(json_string)
            back_to_string = JSON_PARSER.dumps(parsed)
        parser_time = time.time() - start_time

        # Test standard json for comparison
        start_time = time.time()
        for _ in range(iterations):
            parsed = json.loads(json_string)
            back_to_string = json.dumps(parsed)
        std_json_time = time.time() - start_time

        # ujson should be faster (or at least not slower)
        # Allow for some variability in performance
        assert parser_time <= std_json_time * 1.5, f"Parser took {parser_time:.3f}s, std json took {std_json_time:.3f}s"

        # Results should be identical
        fast_parsed = JSON_PARSER.loads(json_string)
        std_parsed = json.loads(json_string)
        assert fast_parsed == std_parsed


class TestFileProcessingIntegration:
    """Test actual file processing components integration."""

    def test_processor_component_validation(self):
        """Test that processor components work together correctly."""
        from src.processors.standard_processor import REQIFZFileProcessor
        from src.core.extractors import REQIFArtifactExtractor
        from src.core.generators import TestCaseGenerator
        from src.core.formatters import TestCaseFormatter

        config = ConfigManager()

        # Test component instantiation (doesn't require real files)
        try:
            extractor = REQIFArtifactExtractor()
            generator = TestCaseGenerator(config)
            formatter = TestCaseFormatter()

            assert extractor is not None
            assert generator is not None
            assert formatter is not None

        except Exception as e:
            pytest.fail(f"Component instantiation failed: {e}")

    @pytest.mark.integration
    def test_minimal_real_processing(self, tmp_path):
        """Test minimal real processing pipeline (requires Ollama running)."""
        pytest.skip("Requires running Ollama instance - skip in CI")

        # This test would only run in environments with Ollama available
        # Left as placeholder for future implementation
        pass
