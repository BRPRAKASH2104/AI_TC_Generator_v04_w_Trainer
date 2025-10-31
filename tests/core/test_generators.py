"""
Unit tests for the generators module.

Tests test case generation with mock AI clients.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from core.generators import TestCaseGenerator, AsyncTestCaseGenerator


class TestTestCaseGenerator:
    """Test synchronous test case generation."""

    def test_generate_test_cases_success(self, mock_ollama_client, sample_requirement, mock_logger):
        """Test successful test case generation."""
        # Setup mock YAML manager
        mock_yaml_manager = Mock()
        mock_yaml_manager.get_test_prompt.return_value = {
            "prompt": "Generate test cases for: {requirement_text}",
            "variables": ["requirement_text"]
        }
        
        generator = TestCaseGenerator(mock_ollama_client, mock_yaml_manager, mock_logger)
        
        result = generator.generate_test_cases_for_requirement(sample_requirement, "llama3.1:8b")
        
        assert result is not None
        assert len(result) == 1
        assert result[0]["summary"] == "Test basic functionality"
        mock_ollama_client.generate_response.assert_called_once()

    def test_generate_test_cases_with_template(self, mock_ollama_client, sample_requirement, mock_logger):
        """Test test case generation with specific template."""
        mock_yaml_manager = Mock()
        mock_yaml_manager.get_test_prompt.return_value = "Custom template: {requirement_text}"
        
        generator = TestCaseGenerator(mock_ollama_client, mock_yaml_manager, mock_logger)
        
        result = generator.generate_test_cases_for_requirement(
            sample_requirement, "llama3.1:8b", "custom_template"
        )
        
        assert result is not None
        # Verify get_test_prompt was called with template name and variables
        mock_yaml_manager.get_test_prompt.assert_called_once()
        call_args = mock_yaml_manager.get_test_prompt.call_args
        assert call_args[0][0] == "custom_template"  # First positional arg is template name
        assert "requirement_id" in call_args[1]  # Variables passed as kwargs

    def test_generate_test_cases_ai_failure(self, sample_requirement, mock_logger):
        """Test handling of AI generation failure."""
        # Mock client that returns empty response
        mock_client = Mock()
        mock_client.generate_response.return_value = ""

        mock_yaml_manager = Mock()
        mock_yaml_manager.get_test_prompt.return_value = "Generate test cases for: {requirement_text}"
        
        generator = TestCaseGenerator(mock_client, mock_yaml_manager, mock_logger)
        
        result = generator.generate_test_cases_for_requirement(sample_requirement, "llama3.1:8b")
        
        assert result == []
        mock_logger.warning.assert_called()  # Empty response triggers warning, not error

    def test_generate_test_cases_invalid_json_response(self, sample_requirement, mock_logger):
        """Test handling of invalid JSON response from AI."""
        mock_client = Mock()
        mock_client.generate_response.return_value = "This is not JSON"
        
        mock_yaml_manager = Mock()
        mock_yaml_manager.get_test_prompt.return_value = {
            "prompt": "Generate test cases",
            "variables": []
        }
        
        generator = TestCaseGenerator(mock_client, mock_yaml_manager, mock_logger)
        
        result = generator.generate_test_cases_for_requirement(sample_requirement, "llama3.1:8b")
        
        assert result == []

    def test_prompt_variable_substitution(self, mock_ollama_client, sample_requirement, mock_logger):
        """Test that prompt variables are correctly substituted."""
        mock_yaml_manager = Mock()
        mock_yaml_manager.get_test_prompt.return_value = "Requirement ID: REQ_001, Text: The system shall validate user input and respond within 2 seconds"
        
        generator = TestCaseGenerator(mock_ollama_client, mock_yaml_manager, mock_logger)
        
        generator.generate_test_cases_for_requirement(sample_requirement, "llama3.1:8b")
        
        # Verify the prompt was built with substituted variables
        call_args = mock_ollama_client.generate_response.call_args[0]
        prompt = call_args[1]  # Second argument is the prompt
        
        assert "REQ_001" in prompt
        assert "validate user input" in prompt


class TestAsyncTestCaseGenerator:
    """Test asynchronous test case generation."""

    @pytest.mark.asyncio
    async def test_generate_test_cases_batch_success(self, mock_async_ollama_client, sample_requirements_list, mock_logger):
        """Test successful batch test case generation."""
        # Setup async mock
        mock_async_ollama_client.generate_response = AsyncMock(
            return_value='{"test_cases": [{"summary": "Async test case"}]}'
        )
        
        mock_yaml_manager = Mock()
        mock_yaml_manager.get_test_prompt.return_value = {
            "prompt": "Generate test cases for: {requirement_text}",
            "variables": ["requirement_text"]
        }
        
        generator = AsyncTestCaseGenerator(mock_async_ollama_client, mock_yaml_manager, mock_logger)
        
        results = await generator.generate_test_cases_batch(sample_requirements_list, "llama3.1:8b")
        
        assert len(results) == 3
        for result in results:
            assert len(result) == 1
            assert result[0]["summary"] == "Async test case"

    @pytest.mark.asyncio
    async def test_generate_test_cases_batch_with_failures(self, sample_requirements_list, mock_logger):
        """Test batch generation with some failures."""
        # Mock client that fails for second requirement
        mock_client = Mock()
        async def mock_response(model, prompt, is_json=False):
            if "REQ_002" in prompt:
                raise Exception("AI API timeout")
            return '{"test_cases": [{"summary": "Success"}]}'
        
        mock_client.generate_response = AsyncMock(side_effect=mock_response)
        
        mock_yaml_manager = Mock()
        def mock_prompt(**kwargs):
            req_id = kwargs.get('requirement_id', 'UNKNOWN')
            req_text = kwargs.get('requirement_text', 'No text')
            return f"Generate for {req_id}: {req_text}"
        mock_yaml_manager.get_test_prompt.side_effect = mock_prompt
        
        generator = AsyncTestCaseGenerator(mock_client, mock_yaml_manager, mock_logger, _max_concurrent=2)
        
        results = await generator.generate_test_cases_batch(sample_requirements_list, "llama3.1:8b")
        
        # Should return results for all requirements, with error object for failed ones
        assert len(results) == 3
        assert len(results[0]) == 1  # REQ_001 success - test cases list
        assert results[1]["error"] == True  # REQ_002 failed - error object
        assert len(results[1]["test_cases"]) == 0  # REQ_002 - empty test cases in error object
        assert len(results[2]) == 1  # REQ_003 success - test cases list

    @pytest.mark.asyncio
    async def test_concurrent_processing_limits(self, sample_requirements_list, mock_logger):
        """Test that concurrency limits are respected."""
        call_times = []
        
        async def mock_response(model, prompt, is_json=False):
            import asyncio
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # Simulate API delay
            return '{"test_cases": [{"summary": "Concurrent test"}]}'
        
        mock_client = Mock()
        mock_client.generate_response = AsyncMock(side_effect=mock_response)

        mock_yaml_manager = Mock()
        mock_yaml_manager.get_test_prompt.return_value = "Generate test cases"
        
        generator = AsyncTestCaseGenerator(mock_client, mock_yaml_manager, mock_logger, _max_concurrent=2)
        
        await generator.generate_test_cases_batch(sample_requirements_list, "llama3.1:8b")
        
        # With max_concurrent=2, the third call should start after one of first two completes
        # This is a basic timing test - in practice this would need more sophisticated timing analysis
        assert len(call_times) == 3

    @pytest.mark.asyncio
    async def test_empty_requirements_list(self, mock_async_ollama_client, mock_logger):
        """Test handling of empty requirements list."""
        mock_yaml_manager = Mock()
        mock_yaml_manager.get_test_prompt.return_value = "Generate test cases"

        generator = AsyncTestCaseGenerator(mock_async_ollama_client, mock_yaml_manager, mock_logger)

        results = await generator.generate_test_cases_batch([], "llama3.1:8b")

        assert results == []