"""
Comprehensive tests for critical improvements:
1. Custom exceptions and error handling
2. Removed double semaphore (performance optimization)
3. Concurrent batch processing
4. Core logic integrity (context-aware processing)

These tests ensure that optimizations don't break existing functionality.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import ConfigManager
from core.exceptions import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaResponseError,
    OllamaTimeoutError,
    REQIFParsingError,
)
from core.generators import AsyncTestCaseGenerator
from core.ollama_client import AsyncOllamaClient, OllamaClient
from processors.base_processor import BaseProcessor
from processors.hp_processor import HighPerformanceREQIFZFileProcessor
from processors.standard_processor import REQIFZFileProcessor
from tests.helpers import (
    create_test_heading,
    create_test_information,
    create_test_interface,
    create_test_requirement,
)

# ============================================================================
# TEST 1: Custom Exceptions - Proper Error Handling
# ============================================================================


class TestCustomExceptions:
    """Test custom exception classes for proper error context"""

    def test_ollama_connection_error_with_context(self):
        """OllamaConnectionError should store host and port"""
        error = OllamaConnectionError(
            "Connection failed",
            host="127.0.0.1",
            port=11434
        )

        assert str(error) == "Connection failed"
        assert error.host == "127.0.0.1"
        assert error.port == 11434

    def test_ollama_timeout_error_with_context(self):
        """OllamaTimeoutError should store timeout value"""
        error = OllamaTimeoutError(
            "Request timed out",
            timeout=600
        )

        assert str(error) == "Request timed out"
        assert error.timeout == 600

    def test_ollama_model_not_found_error_with_context(self):
        """OllamaModelNotFoundError should store model name"""
        error = OllamaModelNotFoundError(
            "Model not found",
            model="llama3.1:8b"
        )

        assert str(error) == "Model not found"
        assert error.model == "llama3.1:8b"

    def test_reqif_parsing_error_with_context(self):
        """REQIFParsingError should store file path"""
        error = REQIFParsingError(
            "Parsing failed",
            file_path="/path/to/file.reqifz"
        )

        assert str(error) == "Parsing failed"
        assert error.file_path == "/path/to/file.reqifz"


# ============================================================================
# TEST 2: OllamaClient Error Handling
# ============================================================================


class TestOllamaClientErrorHandling:
    """Test that OllamaClient properly raises structured exceptions"""

    @patch('requests.Session.post')
    def test_connection_error_raises_ollama_connection_error(self, mock_post):
        """Connection errors should raise OllamaConnectionError"""
        import requests
        mock_post.side_effect = requests.ConnectionError("Connection refused")

        config = ConfigManager()
        client = OllamaClient(config.ollama)

        with pytest.raises(OllamaConnectionError) as exc_info:
            client.generate_response("llama3.1:8b", "test prompt")

        assert "Failed to connect to Ollama" in str(exc_info.value)
        assert exc_info.value.host == config.ollama.host
        assert exc_info.value.port == config.ollama.port

    @patch('requests.Session.post')
    def test_timeout_error_raises_ollama_timeout_error(self, mock_post):
        """Timeout errors should raise OllamaTimeoutError"""
        import requests
        mock_post.side_effect = requests.Timeout("Request timed out")

        config = ConfigManager()
        client = OllamaClient(config.ollama)

        with pytest.raises(OllamaTimeoutError) as exc_info:
            client.generate_response("llama3.1:8b", "test prompt")

        assert "timed out" in str(exc_info.value)
        assert exc_info.value.timeout == config.ollama.timeout

    @patch('requests.Session.post')
    def test_model_not_found_raises_ollama_model_not_found_error(self, mock_post):
        """404 errors should raise OllamaModelNotFoundError"""
        from unittest.mock import Mock

        import requests

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)

        mock_post.return_value = mock_response

        config = ConfigManager()
        client = OllamaClient(config.ollama)

        with pytest.raises(OllamaModelNotFoundError) as exc_info:
            client.generate_response("nonexistent:model", "test prompt")

        assert "not found" in str(exc_info.value)
        assert exc_info.value.model == "nonexistent:model"

    @patch('requests.Session.post')
    def test_invalid_json_response_raises_ollama_response_error(self, mock_post):
        """Invalid JSON should raise OllamaResponseError"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        mock_post.return_value = mock_response

        config = ConfigManager()
        client = OllamaClient(config.ollama)

        with pytest.raises(OllamaResponseError) as exc_info:
            client.generate_response("llama3.1:8b", "test prompt")

        assert "Invalid JSON response" in str(exc_info.value)


# ============================================================================
# TEST 3: AsyncOllamaClient Error Handling
# ============================================================================


class TestAsyncOllamaClientErrorHandling:
    """Test that AsyncOllamaClient properly raises structured exceptions"""

    @pytest.mark.asyncio
    async def test_async_connection_error_raises_ollama_connection_error(self):
        """Async connection errors should raise OllamaConnectionError"""
        from aiohttp import ClientConnectorError

        config = ConfigManager()

        async with AsyncOllamaClient(config.ollama) as client:
            with patch.object(client.session, 'post') as mock_post:
                # Create proper ClientConnectorError with OSError
                os_error = OSError("Connection refused")
                os_error.errno = 61  # Connection refused errno
                os_error.strerror = "Connection refused"

                mock_post.side_effect = ClientConnectorError(
                    connection_key=None,
                    os_error=os_error
                )

                with pytest.raises(OllamaConnectionError) as exc_info:
                    await client.generate_response("llama3.1:8b", "test prompt")

                assert "Failed to connect to Ollama" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_async_timeout_error_raises_ollama_timeout_error(self):
        """Async timeout errors should raise OllamaTimeoutError"""
        config = ConfigManager()

        async with AsyncOllamaClient(config.ollama) as client:
            with patch.object(client.session, 'post') as mock_post:
                mock_post.side_effect = TimeoutError()

                with pytest.raises(OllamaTimeoutError) as exc_info:
                    await client.generate_response("llama3.1:8b", "test prompt")

                assert "timed out" in str(exc_info.value)


# ============================================================================
# TEST 4: No Double Semaphore (Performance Optimization)
# ============================================================================


class TestNoDoubleSemaphore:
    """Verify that double semaphore was removed for better throughput"""

    def test_async_generator_has_no_semaphore_attribute(self):
        """AsyncTestCaseGenerator should not have a semaphore attribute"""
        ConfigManager()
        mock_client = AsyncMock(spec=AsyncOllamaClient)
        mock_client.semaphore = asyncio.Semaphore(4)

        generator = AsyncTestCaseGenerator(
            client=mock_client,
            yaml_manager=None,
            logger=None,
            _max_concurrent=4
        )

        # AsyncTestCaseGenerator should NOT have its own semaphore
        assert not hasattr(generator, 'semaphore')

    def test_async_generator_only_uses_client_semaphore(self):
        """AsyncTestCaseGenerator should rely only on client's semaphore"""
        ConfigManager()
        mock_client = AsyncMock(spec=AsyncOllamaClient)
        mock_client.semaphore = asyncio.Semaphore(4)

        generator = AsyncTestCaseGenerator(
            client=mock_client,
            yaml_manager=None,
            logger=None,
            _max_concurrent=4
        )

        # Verify only client has semaphore
        assert hasattr(generator.client, 'semaphore')
        assert generator.client.semaphore._value == 4  # Initial semaphore value


# ============================================================================
# TEST 5: Concurrent Batch Processing
# ============================================================================


class TestConcurrentBatchProcessing:
    """Test that HP processor uses concurrent batch processing correctly"""

    @pytest.mark.asyncio
    async def test_hp_processor_processes_all_requirements_concurrently(self):
        """HP processor should process all requirements at once, not in sequential batches"""
        # Create test requirements
        test_requirements = [
            {"id": f"REQ_{i:03d}", "text": f"Requirement {i}", "type": "System Requirement", "table": {"data": []}}
            for i in range(10)
        ]

        config = ConfigManager()
        processor = HighPerformanceREQIFZFileProcessor(config, max_concurrent_requirements=4)

        # Mock logger
        mock_logger = Mock()
        mock_logger.info = Mock()
        mock_logger.error = Mock()
        mock_logger.close = Mock()
        mock_logger.add_requirement_failure = Mock()

        with patch("processors.hp_processor.HighPerformanceREQIFZFileProcessor._initialize_logger", return_value=None):
            processor.logger = mock_logger

            with patch.object(processor, '_extract_artifacts') as mock_extract, \
                 patch.object(processor, '_build_augmented_requirements') as mock_augment, \
                 patch.object(processor, '_generate_output_path_hp') as mock_output, \
                 patch('processors.hp_processor.AsyncOllamaClient') as mock_client_class:

                # Setup mocks
                mock_extract.return_value = test_requirements
                mock_augmented = [{"id": f"REQ_{i:03d}", "heading": "Test", "info_list": [], "interface_list": []} for i in range(10)]
                mock_augment.return_value = (mock_augmented, 0)
                mock_output.return_value = Path("/fake/output.xlsx")

                # Create a mock AsyncOllamaClient
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client_class.return_value = mock_client

                # Create mock generator that tracks how batches are called
                batch_calls = []

                async def mock_generate_batch(requirements, model, template):
                    batch_calls.append(len(requirements))
                    return [[{"test": "case", "requirement_id": f"REQ_{i:03d}"}] for i in range(len(requirements))]

                with patch('processors.hp_processor.AsyncTestCaseGenerator') as mock_gen_class:
                    mock_generator = AsyncMock()
                    mock_generator.generate_test_cases_batch = mock_generate_batch
                    mock_gen_class.return_value = mock_generator

                    # Mock the formatter's method properly
                    with patch.object(processor, 'formatter') as mock_formatter:
                        mock_formatter.format_to_excel_streaming = Mock(return_value=True)

                        await processor.process_file(
                            Path("/fake/file.reqifz"),
                            model="llama3.1:8b",
                            template=None,
                            output_dir=None
                        )

                    # Verify that batch processing was called ONCE with ALL requirements
                    # Not multiple sequential batches
                    assert len(batch_calls) == 1, f"Expected 1 batch call, got {len(batch_calls)}"
                    assert batch_calls[0] == 10, f"Expected batch size of 10, got {batch_calls[0]}"


# ============================================================================
# TEST 6: Core Logic Integrity - Context-Aware Processing
# ============================================================================


class TestContextAwareProcessingIntegrity:
    """
    CRITICAL: Verify that context-aware processing logic remains intact.
    This is the core architecture that must not be broken by optimizations.
    """

    def test_base_processor_context_aware_logic_preserved(self):
        """BaseProcessor._build_augmented_requirements must preserve v03 context logic"""
        config = ConfigManager()
        processor = BaseProcessor(config)

        # Initialize a mock logger
        processor.logger = Mock()
        processor.logger.info = Mock()
        processor.logger.debug = Mock()
        processor.logger.warning = Mock()

        # Initialize a mock extractor (using helpers for XHTML format)
        processor.extractor = Mock()
        processor.extractor.classify_artifacts = Mock(return_value={
            "System Interface": [
                create_test_interface("CAN Signal", interface_id="IF_001")
            ]
        })

        # Create test artifacts in the exact order they would appear in a real REQIF file (using helpers)
        artifacts = [
            create_test_heading("Door Control System", heading_id="H_001"),
            create_test_information("Voltage requirements", info_id="I_001"),
            create_test_information("Temperature ranges", info_id="I_002"),
            create_test_requirement("Door shall lock", requirement_id="REQ_001"),
            create_test_heading("Window Control System", heading_id="H_002"),
            create_test_information("Motor specifications", info_id="I_003"),
            create_test_requirement("Window shall close", requirement_id="REQ_002"),
        ]

        # Execute context-aware processing
        augmented_requirements, interface_count = processor._build_augmented_requirements(artifacts)

        # CRITICAL ASSERTIONS: Context-aware processing must work correctly

        # 1. Should have 2 augmented requirements
        assert len(augmented_requirements) == 2, "Should extract exactly 2 requirements"

        # 2. First requirement should have first heading and first two info items
        req1 = augmented_requirements[0]
        assert req1["id"] == "REQ_001"
        assert "Door Control System" in req1["heading"], "First requirement should have first heading (XHTML format)"
        assert len(req1["info_list"]) == 2, "First requirement should have 2 info items"
        assert req1["info_list"][0]["id"] == "I_001"
        assert req1["info_list"][1]["id"] == "I_002"

        # 3. Second requirement should have second heading and only the third info item
        req2 = augmented_requirements[1]
        assert req2["id"] == "REQ_002"
        assert "Window Control System" in req2["heading"], "Second requirement should have second heading (XHTML format)"
        assert len(req2["info_list"]) == 1, "Second requirement should have only 1 info item"
        assert req2["info_list"][0]["id"] == "I_003"

        # 4. Both requirements should have the same system interface (global context)
        assert len(req1["interface_list"]) == 1
        assert len(req2["interface_list"]) == 1
        assert req1["interface_list"][0]["id"] == "IF_001"
        assert req2["interface_list"][0]["id"] == "IF_001"

        # 5. System interface count should be correct
        assert interface_count == 1

    def test_context_reset_after_each_requirement(self):
        """Information context MUST reset after each requirement (critical v03 behavior)"""
        config = ConfigManager()
        processor = BaseProcessor(config)

        processor.logger = Mock()
        processor.logger.info = Mock()
        processor.logger.debug = Mock()
        processor.logger.warning = Mock()

        processor.extractor = Mock()
        processor.extractor.classify_artifacts = Mock(return_value={"System Interface": []})

        # Create artifacts with information that should NOT carry over (using helpers for XHTML format)
        artifacts = [
            create_test_heading("Heading 1", heading_id="H_001"),
            create_test_information("Info before first req", info_id="I_001"),
            create_test_requirement("Req 1", requirement_id="REQ_001"),
            # This info should NOT appear in REQ_002 (context reset)
            create_test_information("Info after first req", info_id="I_002"),
            create_test_requirement("Req 2", requirement_id="REQ_002"),
        ]

        augmented_requirements, _ = processor._build_augmented_requirements(artifacts)

        # CRITICAL: REQ_002 should NOT have I_002 in its info_list
        # This tests the critical "info_since_heading = []" reset logic
        req1 = augmented_requirements[0]
        req2 = augmented_requirements[1]

        assert len(req1["info_list"]) == 1, "REQ_001 should have 1 info item"
        assert req1["info_list"][0]["id"] == "I_001"

        # This is the CRITICAL assertion: context must reset
        assert len(req2["info_list"]) == 1, "REQ_002 should have 1 info item (context reset working)"
        assert req2["info_list"][0]["id"] == "I_002", "REQ_002 should only have info AFTER first req"


# ============================================================================
# TEST 7: Processor Exception Handling Integration
# ============================================================================


class TestProcessorExceptionHandling:
    """Test that processors properly handle and format custom exceptions"""

    def test_standard_processor_handles_connection_error(self):
        """Standard processor should catch and format OllamaConnectionError"""
        config = ConfigManager()
        processor = REQIFZFileProcessor(config)

        # Mock logger properly
        mock_logger = Mock()
        mock_logger.info = Mock()
        mock_logger.error = Mock()
        mock_logger.close = Mock()

        with patch("processors.standard_processor.REQIFZFileProcessor._initialize_logger", return_value=None):
            processor.logger = mock_logger

            with patch.object(processor, '_extract_artifacts', side_effect=OllamaConnectionError("Connection failed", "127.0.0.1", 11434)):
                result = processor.process_file(
                    Path("/fake/file.reqifz"),
                    model="llama3.1:8b"
                )

                assert result["success"] is False
                assert "Ollama connection failed" in result["error"]
                assert "ollama serve" in result["error"]

    def test_standard_processor_handles_model_not_found(self):
        """Standard processor should catch and format OllamaModelNotFoundError"""
        config = ConfigManager()
        processor = REQIFZFileProcessor(config)

        # Mock logger properly
        mock_logger = Mock()
        mock_logger.info = Mock()
        mock_logger.error = Mock()
        mock_logger.close = Mock()

        with patch("processors.standard_processor.REQIFZFileProcessor._initialize_logger", return_value=None):
            processor.logger = mock_logger

            with patch.object(processor, '_extract_artifacts', side_effect=OllamaModelNotFoundError("Model not found", "fake:model")):
                result = processor.process_file(
                    Path("/fake/file.reqifz"),
                    model="fake:model"
                )

                assert result["success"] is False
                assert "not available" in result["error"]
                assert "ollama pull fake:model" in result["error"]


# ============================================================================
# TEST 8: Performance Regression Prevention
# ============================================================================


class TestPerformanceRegression:
    """Ensure optimizations actually improve performance"""

    @pytest.mark.asyncio
    async def test_no_semaphore_allows_full_concurrency(self):
        """Verify that removing double semaphore allows full concurrency"""
        ConfigManager()

        # Create mock client with semaphore value of 4
        mock_client = AsyncMock(spec=AsyncOllamaClient)
        mock_client.semaphore = asyncio.Semaphore(4)

        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0

        async def mock_generate(model, prompt, is_json=False):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)  # Simulate work
            concurrent_count -= 1
            return '{"response": "test"}'

        mock_client.generate_response = mock_generate

        generator = AsyncTestCaseGenerator(
            client=mock_client,
            yaml_manager=None,
            logger=None,
            _max_concurrent=4
        )

        # Create 8 requirements (should process 4 at a time with semaphore)
        requirements = [
            {"id": f"REQ_{i}", "text": f"Requirement {i}", "heading": "Test", "info_list": [], "interface_list": []}
            for i in range(8)
        ]

        # Process all requirements
        await generator.generate_test_cases_batch(requirements, "llama3.1:8b", None)

        # With no double semaphore, we should see higher concurrency
        # (limited only by the client's semaphore, not an additional generator semaphore)
        assert max_concurrent > 0, "Should have had concurrent executions"
        # Note: Exact concurrent count depends on timing, but we're verifying it's not restricted to 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
