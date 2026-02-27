#!/usr/bin/env python3
"""
Edge case and error condition tests for AI Test Case Generator.

These tests cover malformed files, network errors, resource constraints,
and other exceptional conditions to ensure robust error handling.
"""

import asyncio
import json
import tempfile
import time
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from config import ConfigManager
from core.exceptions import OllamaConnectionError, OllamaResponseError, OllamaTimeoutError
from core.extractors import HighPerformanceREQIFArtifactExtractor, REQIFArtifactExtractor
from core.generators import AsyncTestCaseGenerator, TestCaseGenerator
from core.ollama_client import AsyncOllamaClient, OllamaClient
from core.parsers import JSONResponseParser


class TestMalformedFiles:
    """Test handling of various malformed file types"""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing"""
        config = ConfigManager()
        config.ollama.timeout = 5  # Short timeout for testing
        config.ollama.max_retries = 1
        return config

    def test_empty_reqifz_file(self, mock_config):
        """Test handling of empty REQIFZ files"""
        with tempfile.NamedTemporaryFile(suffix=".reqifz") as temp_file:
            # File is empty by default
            extractor = REQIFArtifactExtractor()
            result = extractor.extract_reqifz_content(Path(temp_file.name))

            assert isinstance(result, list)
            assert len(result) == 0

    def test_invalid_zip_structure(self, mock_config):
        """Test handling of files with invalid ZIP structure"""
        with tempfile.NamedTemporaryFile(suffix=".reqifz", delete=False) as temp_file:
            # Write random bytes that are not a valid ZIP
            temp_file.write(b"This is definitely not a ZIP file content")
            temp_file.flush()
            temp_file.close() # Close to allow extraction and unlinking

            try:
                extractor = REQIFArtifactExtractor()
                result = extractor.extract_reqifz_content(Path(temp_file.name))

                # Should handle gracefully and return empty list
                assert isinstance(result, list)
                assert len(result) == 0

            finally:
                Path(temp_file.name).unlink()

    def test_zip_without_reqif_files(self, mock_config):
        """Test handling of ZIP files without .reqif files"""
        with tempfile.NamedTemporaryFile(suffix=".reqifz", delete=False) as temp_file:
            temp_file.close() # Close so zipfile can open it
            # Create a valid ZIP file but without .reqif files
            with zipfile.ZipFile(temp_file.name, 'w') as zip_file:
                zip_file.writestr("readme.txt", "This ZIP has no REQIF files")
                zip_file.writestr("data.json", '{"message": "no reqif here"}')

            try:
                extractor = REQIFArtifactExtractor()
                result = extractor.extract_reqifz_content(Path(temp_file.name))

                assert isinstance(result, list)
                assert len(result) == 0

            finally:
                Path(temp_file.name).unlink()

    def test_malformed_xml_in_reqif(self, mock_config):
        """Test handling of malformed XML in REQIF files"""
        with tempfile.NamedTemporaryFile(suffix=".reqifz", delete=False) as temp_file:
            temp_file.close() # Close so zipfile can open it
            # Create ZIP with malformed XML
            with zipfile.ZipFile(temp_file.name, 'w') as zip_file:
                malformed_xml = """<?xml version="1.0" encoding="UTF-8"?>
                <reqif:REQ-IF xmlns:reqif="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
                    <reqif:SPEC-OBJECT>
                        <unclosed-tag>
                            <another-tag>content</another-tag>
                        <!-- Missing closing tag for unclosed-tag -->
                    </reqif:SPEC-OBJECT>
                </reqif:REQ-IF>"""
                zip_file.writestr("malformed.reqif", malformed_xml)

            try:
                extractor = REQIFArtifactExtractor()
                result = extractor.extract_reqifz_content(Path(temp_file.name))

                # Should handle XML parsing errors gracefully
                assert isinstance(result, list)

            finally:
                Path(temp_file.name).unlink()

    def test_xml_with_invalid_namespaces(self, mock_config):
        """Test handling of XML with invalid or missing namespaces"""
        with tempfile.NamedTemporaryFile(suffix=".reqifz", delete=False) as temp_file:
            temp_file.close() # Close so zipfile can open it
            # Create ZIP with XML using wrong namespaces
            with zipfile.ZipFile(temp_file.name, 'w') as zip_file:
                invalid_namespace_xml = """<?xml version="1.0" encoding="UTF-8"?>
                <wrong:REQ-IF xmlns:wrong="http://wrong.namespace.com">
                    <wrong:SPEC-OBJECT IDENTIFIER="TEST_001">
                        <wrong:VALUES>
                            <wrong:ATTRIBUTE-VALUE-STRING>
                                <wrong:THE-VALUE>Test content</wrong:THE-VALUE>
                            </wrong:ATTRIBUTE-VALUE-STRING>
                        </wrong:VALUES>
                    </wrong:SPEC-OBJECT>
                </wrong:REQ-IF>"""
                zip_file.writestr("invalid_ns.reqif", invalid_namespace_xml)

            try:
                extractor = REQIFArtifactExtractor()
                result = extractor.extract_reqifz_content(Path(temp_file.name))

                # Should handle namespace issues gracefully
                assert isinstance(result, list)

            finally:
                Path(temp_file.name).unlink()

    def test_extremely_large_reqif_file(self, mock_config):
        """Test handling of very large REQIF files"""
        with tempfile.NamedTemporaryFile(suffix=".reqifz", delete=False) as temp_file:
            temp_file.close() # Close so zipfile can open it
            # Create a large XML file (simulate many spec objects)
            with zipfile.ZipFile(temp_file.name, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
                large_xml = """<?xml version="1.0" encoding="UTF-8"?>
                <reqif:REQ-IF xmlns:reqif="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">"""

                # Add many spec objects to simulate large file
                for i in range(1000):  # 1000 spec objects
                    large_xml += f"""
                    <reqif:SPEC-OBJECT IDENTIFIER="SPEC_{i:04d}">
                        <reqif:VALUES>
                            <reqif:ATTRIBUTE-VALUE-STRING ATTRIBUTE-DEFINITION-REF="HEADING">
                                <reqif:THE-VALUE>Test Requirement {i}</reqif:THE-VALUE>
                            </reqif:ATTRIBUTE-VALUE-STRING>
                        </reqif:VALUES>
                    </reqif:SPEC-OBJECT>"""

                large_xml += "\n</reqif:REQ-IF>"
                zip_file.writestr("large.reqif", large_xml)

            try:
                # Test with high-performance extractor
                extractor = HighPerformanceREQIFArtifactExtractor(max_workers=2)
                start_time = time.time()
                result = extractor.extract_reqifz_content(Path(temp_file.name))
                processing_time = time.time() - start_time

                # Should handle large files and return results
                assert isinstance(result, list)
                assert len(result) > 0
                assert processing_time < 30  # Should complete within reasonable time

            finally:
                Path(temp_file.name).unlink()


class TestNetworkErrorConditions:
    """Test handling of network-related errors"""

    @pytest.fixture
    def mock_config(self):
        config = ConfigManager()
        config.ollama.timeout = 1  # Very short timeout
        config.ollama.max_retries = 1
        return config

    def test_connection_refused_error(self, mock_config):
        """Test handling when Ollama service is not available"""
        client = OllamaClient(mock_config.ollama)

        # Mock the session's post method to raise ConnectionError
        client._session.post = Mock(side_effect=requests.ConnectionError("Connection refused"))

        with pytest.raises(OllamaConnectionError):
            client.generate_response("test-model", "test prompt")

    def test_timeout_error(self, mock_config):
        """Test handling of request timeouts"""
        client = OllamaClient(mock_config.ollama)

        # Mock the session's post method to raise Timeout
        client._session.post = Mock(side_effect=requests.Timeout("Request timed out"))

        with pytest.raises(OllamaTimeoutError):
            client.generate_response("test-model", "test prompt")

    def test_http_error_responses(self, mock_config):
        """Test handling of various HTTP error responses"""
        error_codes = [400, 401, 403, 500, 502, 503, 504]

        for error_code in error_codes:
            client = OllamaClient(mock_config.ollama)

            # Mock the response to raise HTTPError
            mock_response = Mock()
            mock_response.status_code = error_code
            mock_response.text = f"HTTP {error_code} error"
            mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)

            # Mock the session's post method to return the mock response
            client._session.post = Mock(return_value=mock_response)

            with pytest.raises(OllamaResponseError):
                client.generate_response("test-model", "test prompt")

    @pytest.mark.asyncio
    async def test_async_connection_errors(self, mock_config):
        """Test async client error handling"""
        import aiohttp

        async with AsyncOllamaClient(mock_config.ollama) as client:
            with patch.object(client.session, 'post') as mock_post:
                # Create proper ClientConnectorError
                os_error = OSError("Connection refused")
                os_error.errno = 61
                os_error.strerror = "Connection refused"
                mock_post.side_effect = aiohttp.ClientConnectorError(
                    connection_key=Mock(),
                    os_error=os_error
                )

                with pytest.raises(OllamaConnectionError):
                    await client.generate_response("test-model", "test prompt")


class TestResourceConstraints:
    """Test behavior under resource constraints"""

    @pytest.fixture
    def mock_config(self):
        config = ConfigManager()
        config.ollama.concurrent_requests = 1  # Limit concurrency
        return config

    def test_memory_pressure_simulation(self, mock_config):
        """Test behavior under simulated memory pressure"""
        # Create a large number of requirements to process
        large_requirements = []
        for i in range(100):
            large_requirements.append({
                "id": f"REQ_{i:03d}",
                "type": "System Requirement",
                "heading": f"Requirement {i}",
                "text": "x" * 1000,  # Large text content
            })

        # Mock AI client to return responses quickly
        mock_client = Mock()
        mock_client.generate_completion.return_value = {
            "response": json.dumps({
                "test_cases": [{"test_id": "TC_001", "summary": "Test case"}]
            })
        }

        generator = TestCaseGenerator(mock_client)

        # Process all requirements (should handle memory efficiently)
        results = []
        for req in large_requirements:
            result = generator.generate_test_cases_for_requirement(req, "test-model")
            results.append(result)

        # Verify all were processed
        assert len(results) == 100

    @pytest.mark.asyncio
    async def test_concurrent_request_limiting(self, mock_config):
        """Test that concurrent request limits are delegated to client"""
        # Mock async client
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Simulate some processing time
            await asyncio.sleep(0.1)
            return {"response": json.dumps({"test_cases": []})}

        mock_client = Mock()
        mock_client.generate_completion = mock_generate

        # The generator no longer limits concurrency itself (delegates to client)
        # So we just verify it runs all tasks.
        generator = AsyncTestCaseGenerator(mock_client, _max_concurrent=2)

        # Create multiple requirements
        requirements = [
            {"id": f"REQ_{i:03d}", "type": "System Requirement", "heading": f"Req {i}", "text": "text"}
            for i in range(10)
        ]

        # Process concurrently
        time.time()
        results = await generator.generate_test_cases_batch(requirements, "test-model")

        # Verify results
        assert len(results) == 10
        assert call_count == 10


class TestMalformedResponses:
    """Test handling of malformed AI responses"""

    @pytest.fixture
    def mock_config(self):
        return ConfigManager()

    def test_invalid_json_response(self, mock_config):
        """Test handling of invalid JSON in AI response"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = {"response": "This is not valid JSON at all"}

        generator = TestCaseGenerator(mock_client)
        result = generator.generate_test_cases_for_requirement(
            {"id": "REQ_001", "type": "System Requirement", "heading": "Test", "text": "Test requirement"},
            "test-model"
        )

        # Should handle gracefully and return empty list
        assert isinstance(result, list)
        assert len(result) == 0

    def test_json_missing_test_cases_key(self, mock_config):
        """Test handling of JSON response missing expected keys"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = {
            "response": json.dumps({
                "response": "I generated some test cases",
                "metadata": {"model": "test-model"}
                # Missing "test_cases" key
            })
        }

        generator = TestCaseGenerator(mock_client)
        result = generator.generate_test_cases_for_requirement(
            {"id": "REQ_001", "type": "System Requirement", "heading": "Test", "text": "Test requirement"},
            "test-model"
        )

        # Should handle missing key gracefully
        assert isinstance(result, list)
        assert len(result) == 0

    def test_malformed_test_case_structure(self, mock_config):
        """Test handling of malformed test case structures in response"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = {
            "response": json.dumps({
                "test_cases": [
                    # Valid test case
                    {
                        "test_id": "TC_001",
                        "summary": "Valid test case",
                        "preconditions": "Valid preconditions",
                        "test_steps": ["Step 1", "Step 2"],
                        "expected_result": "Valid result"
                    },
                    # Malformed test case - missing required fields
                    {
                        "test_id": "TC_002"
                        # Missing other required fields
                    },
                    # Test case with wrong data types
                    {
                        "test_id": 123,  # Should be string
                        "summary": ["Should", "be", "string"],  # Should be string
                        "test_steps": "Should be list"  # Should be list
                    }
                ]
            })
        }

        generator = TestCaseGenerator(mock_client)
        result = generator.generate_test_cases_for_requirement(
            {"id": "REQ_001", "type": "System Requirement", "heading": "Test", "text": "Test requirement"},
            "test-model"
        )

        # Should process valid test cases and skip malformed ones
        assert isinstance(result, list)
        # At minimum should get the valid test case
        assert len(result) >= 1

    def test_extremely_large_response(self, mock_config):
        """Test handling of extremely large AI responses"""
        # Create a very large response
        large_response = {
            "test_cases": []
        }

        # Add many test cases with large content
        for i in range(1000):
            large_response["test_cases"].append({
                "test_id": f"TC_{i:04d}",
                "summary": f"Test case {i} " + "x" * 1000,  # Large summary
                "preconditions": "Large preconditions " + "y" * 500,
                "test_steps": [f"Step {j} " + "z" * 200 for j in range(10)],  # Many large steps
                "expected_result": "Large expected result " + "w" * 800
            })

        mock_client = Mock()
        mock_client.generate_completion.return_value = {"response": json.dumps(large_response)}

        generator = TestCaseGenerator(mock_client)
        result = generator.generate_test_cases_for_requirement(
            {"id": "REQ_001", "type": "System Requirement", "heading": "Test", "text": "Test requirement"},
            "test-model"
        )

        # Should handle large responses efficiently
        assert isinstance(result, list)
        # Deduplication might reduce the count, so we ensure we got at least one valid result back
        # processing 1000 entries without crashing is the main test here.
        assert len(result) >= 1


class TestJSONParserEdgeCases:
    """Test edge cases in JSON response parsing"""

    def test_nested_json_extraction(self):
        """Test extraction of JSON from nested/complex responses"""
        parser = JSONResponseParser()

        # Response with JSON embedded in markdown
        complex_response = """
        Here are the test cases you requested:

        ```json
        {
            "test_cases": [
                {
                    "test_id": "TC_001",
                    "summary": "Test embedded JSON"
                }
            ]
        }
        ```

        Additional explanation text here.
        """

        result = parser.extract_json_from_response(complex_response)
        assert result is not None
        assert "test_cases" in result
        assert len(result["test_cases"]) == 1

    def test_multiple_json_blocks(self):
        """Test handling of responses with multiple JSON blocks"""
        parser = JSONResponseParser()

        response = """
        First JSON block:
        {"metadata": {"version": "1.0"}}

        Main JSON block:
        {"test_cases": [{"test_id": "TC_001", "summary": "Test"}]}

        Another JSON block:
        {"summary": "Additional info"}
        """

        result = parser.extract_json_from_response(response)
        # Should extract the first valid JSON with test_cases
        assert result is not None

    def test_json_with_escaped_characters(self):
        """Test handling of JSON with escaped characters"""
        parser = JSONResponseParser()

        response = json.dumps({
            "test_cases": [
                {
                    "test_id": "TC_001",
                    "summary": "Test with \"quotes\" and \\backslashes\\",
                    "test_steps": ["Step with\nnewlines", "Step with\ttabs"],
                    "expected_result": "Result with special chars: !@#$%^&*()"
                }
            ]
        })

        result = parser.extract_json_from_response(response)
        assert result is not None
        assert "test_cases" in result
        assert len(result["test_cases"]) == 1
        assert "quotes" in result["test_cases"][0]["summary"]
