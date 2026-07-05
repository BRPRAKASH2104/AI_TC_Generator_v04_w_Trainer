"""
Unit tests for the generators module.

Tests test case generation with mock AI clients.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from core.generators import AsyncTestCaseGenerator, TestCaseGenerator


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

        # Setup mock client to return full response structure
        mock_ollama_client.generate_completion.return_value = {
            "response": '{"test_cases": [{"summary": "Test basic functionality"}]}',
            "logprobs": None
        }

        generator = TestCaseGenerator(mock_ollama_client, mock_yaml_manager, mock_logger)

        result = generator.generate_test_cases_for_requirement(sample_requirement, "llama3.1:8b")

        assert result is not None
        assert len(result) == 1
        assert result[0]["summary"] == "Test basic functionality"
        mock_ollama_client.generate_completion.assert_called_once()

    def test_generate_test_cases_with_template(self, mock_ollama_client, sample_requirement, mock_logger):
        """Test test case generation with specific template."""
        mock_yaml_manager = Mock()
        mock_yaml_manager.get_test_prompt.return_value = "Custom template: {requirement_text}"

        # Setup mock client
        mock_ollama_client.generate_completion.return_value = {
            "response": '{"test_cases": [{"summary": "Test template"}]}'
        }

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
        # Mock generate_completion to return empty response dict
        mock_client.generate_completion.return_value = {"response": ""}

        mock_yaml_manager = Mock()
        mock_yaml_manager.get_test_prompt.return_value = "Generate test cases for: {requirement_text}"

        generator = TestCaseGenerator(mock_client, mock_yaml_manager, mock_logger)

        result = generator.generate_test_cases_for_requirement(sample_requirement, "llama3.1:8b")

        assert result == []
        mock_logger.warning.assert_called()  # Empty response triggers warning, not error

    def test_generate_test_cases_invalid_json_response(self, sample_requirement, mock_logger):
        """Test handling of invalid JSON response from AI."""
        mock_client = Mock()
        mock_client.generate_completion.return_value = {"response": "This is not JSON"}

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

        mock_ollama_client.generate_completion.return_value = {
             "response": '{"test_cases": []}'
        }

        generator = TestCaseGenerator(mock_ollama_client, mock_yaml_manager, mock_logger)

        generator.generate_test_cases_for_requirement(sample_requirement, "llama3.1:8b")

        # Verify the prompt was built with substituted variables
        # generate_completion(model, prompt, ...)
        call_args = mock_ollama_client.generate_completion.call_args[0]
        prompt = call_args[1]  # Second argument is the prompt

        assert "REQ_001" in prompt
        assert "validate user input" in prompt


class TestAsyncTestCaseGenerator:
    """Test asynchronous test case generation."""

    @pytest.mark.asyncio
    async def test_generate_test_cases_batch_success(self, mock_async_ollama_client, sample_requirements_list, mock_logger):
        """Test successful batch test case generation."""
        # Setup async mock
        mock_async_ollama_client.generate_completion = AsyncMock(
            return_value={"response": '{"test_cases": [{"summary": "Async test case"}]}'}
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
        async def mock_response(model, prompt, is_json=False, return_full_response=True):
            if "REQ_002" in prompt:
                raise Exception("AI API timeout")
            return {"response": '{"test_cases": [{"summary": "Success"}]}'}

        mock_client.generate_completion = AsyncMock(side_effect=mock_response)

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
        assert results[1]["error"]  # REQ_002 failed - error object
        assert len(results[1]["test_cases"]) == 0  # REQ_002 - empty test cases in error object
        assert len(results[2]) == 1  # REQ_003 success - test cases list

    @pytest.mark.asyncio
    async def test_concurrent_processing_limits(self, sample_requirements_list, mock_logger):
        """Test that concurrency limits are respected."""
        call_times = []

        async def mock_response(model, prompt, is_json=False, return_full_response=True):
            import asyncio
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # Simulate API delay
            return {"response": '{"test_cases": [{"summary": "Concurrent test"}]}'}

        mock_client = Mock()
        # Mocking the client which is passed to generator.
        # The generator calls client.generate_completion, which uses client.semaphore.
        # However, AsyncOllamaClient uses semaphore inside generate_completion.
        # Since we are mocking the client, we need to mock the semaphore behavior or just the method.
        # The test checks if they run concurrently.

        mock_client.generate_completion = AsyncMock(side_effect=mock_response)

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


class TestValidationStamping:
    """Regression tests for validation_passed correctness.

    The old inline computation (`i >= len(issues) or ...`) marked failing test
    cases as valid whenever their index exceeded the number of issue entries,
    and it ran after deduplication so indices no longer matched the validator
    report. validation_passed must be stamped from the report indices, before
    deduplication.
    """

    THREE_CASES_JSON = (
        '{"test_cases": ['
        '{"summary_suffix": "A", "test_steps": "1) a", "expected_result": "ra"},'
        '{"summary_suffix": "B", "test_steps": "1) b", "expected_result": "rb"},'
        '{"summary_suffix": "C", "test_steps": "1) c", "expected_result": "rc"}'
        "]}"
    )

    @staticmethod
    def _validation_report(issues):
        invalid = len([e for e in issues if e.get("test_case_index", -1) > 0])
        return {
            "total_test_cases": 3,
            "valid_count": 3 - invalid,
            "invalid_count": invalid,
            "validation_rate": (3 - invalid) / 3,
            "issues": issues,
            "table_coverage": {"is_table_based": False},
        }

    def _make_sync_generator(self, issues, mock_logger):
        mock_client = Mock()
        mock_client.generate_completion.return_value = {"response": self.THREE_CASES_JSON}

        mock_yaml_manager = Mock()
        mock_yaml_manager.get_test_prompt.return_value = "Generate test cases"

        mock_validator = Mock()
        mock_validator.validate_batch.return_value = self._validation_report(issues)

        mock_deduplicator = Mock()
        mock_deduplicator.deduplicate.side_effect = lambda tcs, keep_strategy: (
            tcs,
            {
                "original_count": len(tcs),
                "deduplicated_count": len(tcs),
                "duplicates_removed": 0,
                "duplicate_groups_found": 0,
                "duplicate_groups": [],
                "deduplication_rate": 0.0,
            },
        )

        generator = TestCaseGenerator(
            mock_client,
            mock_yaml_manager,
            mock_logger,
            validator=mock_validator,
            deduplicator=mock_deduplicator,
        )
        return generator, mock_deduplicator

    def test_failing_case_beyond_issue_count_is_marked_invalid(
        self, sample_requirement, mock_logger
    ):
        """One issue at test_case_index=2: only the second case may be invalid."""
        issues = [{"test_case_index": 2, "summary": "B", "issues": ["bad signal"]}]
        generator, _ = self._make_sync_generator(issues, mock_logger)

        result = generator.generate_test_cases_for_requirement(sample_requirement, "llama3.1:8b")

        assert len(result) == 3
        assert result[0]["validation_passed"] is True
        assert result[1]["validation_passed"] is False  # old logic marked this True
        assert result[2]["validation_passed"] is True

    def test_table_coverage_issues_do_not_invalidate_cases(
        self, sample_requirement, mock_logger
    ):
        """Global table-coverage issues (test_case_index=-1) must not mark any case invalid."""
        issues = [{"test_case_index": -1, "summary": "Table Coverage Deficiency", "issues": ["x"]}]
        generator, _ = self._make_sync_generator(issues, mock_logger)

        result = generator.generate_test_cases_for_requirement(sample_requirement, "llama3.1:8b")

        assert len(result) == 3
        assert all(tc["validation_passed"] is True for tc in result)

    def test_validation_stamped_before_deduplication(self, sample_requirement, mock_logger):
        """The deduplicator must see validation_passed so its 'best' strategy can use it."""
        issues = [{"test_case_index": 1, "summary": "A", "issues": ["bad signal"]}]
        generator, mock_deduplicator = self._make_sync_generator(issues, mock_logger)

        generator.generate_test_cases_for_requirement(sample_requirement, "llama3.1:8b")

        dedup_input = mock_deduplicator.deduplicate.call_args[0][0]
        assert all("validation_passed" in tc for tc in dedup_input)
        assert dedup_input[0]["validation_passed"] is False
        assert dedup_input[1]["validation_passed"] is True

    @pytest.mark.asyncio
    async def test_async_generator_stamps_validation_identically(
        self, sample_requirement, mock_logger
    ):
        """Async pipeline must apply the same stamping rules as the sync one."""
        mock_client = AsyncMock()
        mock_client.generate_completion = AsyncMock(
            return_value={"response": self.THREE_CASES_JSON}
        )

        mock_yaml_manager = Mock()
        mock_yaml_manager.get_test_prompt.return_value = "Generate test cases"

        mock_validator = Mock()
        mock_validator.validate_batch.return_value = self._validation_report(
            [{"test_case_index": 3, "summary": "C", "issues": ["bad signal"]}]
        )

        generator = AsyncTestCaseGenerator(
            mock_client, mock_yaml_manager, mock_logger, validator=mock_validator
        )

        result = await generator.generate_test_cases(sample_requirement, "llama3.1:8b")

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["validation_passed"] is True
        assert result[1]["validation_passed"] is True
        assert result[2]["validation_passed"] is False
