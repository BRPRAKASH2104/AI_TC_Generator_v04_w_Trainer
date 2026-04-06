"""
Integration tests for refactored processors.

Tests complete workflows with BaseProcessor, standard and HP processors.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unittest.mock import MagicMock, patch, Mock

import pytest

from processors.hp_processor import HighPerformanceREQIFZFileProcessor
from processors.standard_processor import REQIFZFileProcessor
from tests.helpers import (
    create_test_heading,
    create_test_information,
    create_test_requirement,
)


class TestStandardProcessorIntegration:
    """Integration tests for refactored standard processor"""

    @patch('processors.standard_processor.REQIFArtifactExtractor')
    @patch('processors.standard_processor.TestCaseGenerator')
    @patch('processors.standard_processor.TestCaseFormatter')
    def test_standard_processor_complete_flow(self, MockFormatter, MockGenerator, MockExtractor):
        """Test complete standard processing flow (POSITIVE)"""
        # Setup mocks (using helpers for XHTML format)
        mock_extractor = MockExtractor.return_value
        mock_extractor.extract_reqifz_content.return_value = [
            create_test_heading("Test Heading"),
            create_test_information("Test info", info_id="INFO_001"),
            create_test_requirement("Test requirement text", requirement_id="REQ_001"),
        ]
        mock_extractor.classify_artifacts.return_value = {"System Interface": []}

        mock_generator = MockGenerator.return_value
        mock_generator.generate_test_cases_for_requirement.return_value = [
            {"test_id": "TC_001", "summary": "Test case 1"}
        ]

        mock_formatter = MockFormatter.return_value
        mock_formatter.format_to_excel.return_value = True

        # Execute
        processor = REQIFZFileProcessor()
        result = processor.process_file(
            Path("/test/file.reqifz"),
            model="llama3.1:8b"
        )

        # Verify
        assert result["success"] is True
        assert result["total_test_cases"] == 1
        assert result["requirements_processed"] == 1
        assert "output_file" in result

        # Verify context was passed (check for text within XHTML)
        call_args = mock_generator.generate_test_cases_for_requirement.call_args[0][0]
        assert "Test Heading" in call_args["heading"]  # Heading text in XHTML format
        assert len(call_args["info_list"]) == 1
        assert "Test info" in call_args["info_list"][0]["text"]  # Info text in XHTML format

    @patch('processors.standard_processor.REQIFArtifactExtractor')
    def test_standard_processor_no_artifacts(self, MockExtractor):
        """Test standard processor with no artifacts (NEGATIVE)"""
        mock_extractor = MockExtractor.return_value
        mock_extractor.extract_reqifz_content.return_value = None

        processor = REQIFZFileProcessor()
        result = processor.process_file(Path("/test/file.reqifz"))

        assert result["success"] is False
        assert "No artifacts found" in result["error"]

    @patch('processors.standard_processor.REQIFArtifactExtractor')
    @patch('processors.standard_processor.TestCaseGenerator')
    def test_standard_processor_no_test_cases_generated(self, MockGenerator, MockExtractor):
        """Test when no test cases are generated (NEGATIVE)"""
        mock_extractor = MockExtractor.return_value
        mock_extractor.extract_reqifz_content.return_value = [
            create_test_requirement("Test requirement", requirement_id="REQ_001")
        ]
        mock_extractor.classify_artifacts.return_value = {"System Interface": []}

        mock_generator = MockGenerator.return_value
        mock_generator.generate_test_cases_for_requirement.return_value = []

        processor = REQIFZFileProcessor()
        result = processor.process_file(Path("/test/file.reqifz"))

        assert result["success"] is False
        assert "No test cases were generated" in result["error"]

    @patch('processors.standard_processor.REQIFArtifactExtractor')
    @patch('processors.standard_processor.TestCaseGenerator')
    @patch('processors.standard_processor.TestCaseFormatter')
    def test_standard_processor_excel_save_failure(self, MockFormatter, MockGenerator, MockExtractor):
        """Test Excel save failure (NEGATIVE)"""
        mock_extractor = MockExtractor.return_value
        mock_extractor.extract_reqifz_content.return_value = [
            create_test_requirement("Test requirement", requirement_id="REQ_001")
        ]
        mock_extractor.classify_artifacts.return_value = {"System Interface": []}

        mock_generator = MockGenerator.return_value
        mock_generator.generate_test_cases_for_requirement.return_value = [
            {"test_id": "TC_001"}
        ]

        mock_formatter = MockFormatter.return_value
        mock_formatter.format_to_excel.return_value = False  # Save failed

        processor = REQIFZFileProcessor()
        result = processor.process_file(Path("/test/file.reqifz"))

        assert result["success"] is False
        assert "Failed to save Excel file" in result["error"]


class TestHPProcessorIntegration:
    """Integration tests for refactored HP processor"""

    @pytest.mark.asyncio
    @patch('processors.hp_processor.HighPerformanceREQIFArtifactExtractor')
    @patch('processors.hp_processor.AsyncTestCaseGenerator')
    @patch('processors.hp_processor.StreamingTestCaseFormatter')
    @patch('processors.hp_processor.AsyncOllamaClient')
    async def test_hp_processor_complete_flow(self, MockClient, MockFormatter, MockGenerator, MockExtractor):
        """Test complete HP processing flow (POSITIVE)"""
        # Setup mocks (using helpers for XHTML format)
        mock_extractor = MockExtractor.return_value
        mock_extractor.extract_reqifz_content.return_value = [
            create_test_heading("HP Test"),
            create_test_requirement("HP requirement 1", requirement_id="REQ_001"),
            create_test_requirement("HP requirement 2", requirement_id="REQ_002"),
        ]
        mock_extractor.classify_artifacts.return_value = {"System Interface": []}

        # Mock async context manager
        mock_client_instance = MagicMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance

        mock_generator_instance = MagicMock()
        MockGenerator.return_value = mock_generator_instance
        from unittest.mock import AsyncMock
        mock_generator_instance.generate_test_cases = AsyncMock()
        mock_generator_instance.generate_test_cases.side_effect = [
            [{"test_id": "TC_001"}],  # REQ_001 results
            [{"test_id": "TC_002"}],  # REQ_002 results
        ]

        mock_formatter = MockFormatter.return_value
        mock_formatter.format_to_excel_streaming.return_value = True

        # Execute
        processor = HighPerformanceREQIFZFileProcessor()
        result = await processor.process_file(
            Path("/test/file.reqifz"),
            model="llama3.1:8b"
        )

        # Verify
        assert result["success"] is True
        assert result["total_test_cases"] == 2
        assert result["requirements_processed"] == 2
        assert "performance_metrics" in result

    @pytest.mark.asyncio
    @patch('processors.hp_processor.HighPerformanceREQIFArtifactExtractor')
    async def test_hp_processor_no_artifacts(self, MockExtractor):
        """Test HP processor with no artifacts (NEGATIVE)"""
        mock_extractor = MockExtractor.return_value
        mock_extractor.extract_reqifz_content.return_value = None

        processor = HighPerformanceREQIFZFileProcessor()
        result = await processor.process_file(Path("/test/file.reqifz"))

        assert result["success"] is False
        assert "No artifacts found" in result["error"]

    @pytest.mark.asyncio
    @patch('processors.hp_processor.HighPerformanceREQIFArtifactExtractor')
    @patch('processors.hp_processor.AsyncTestCaseGenerator')
    @patch('processors.hp_processor.AsyncOllamaClient')
    async def test_hp_processor_with_errors(self, MockClient, MockGenerator, MockExtractor):
        """Test HP processor with some errors (MIXED)"""
        mock_extractor = MockExtractor.return_value
        mock_extractor.extract_reqifz_content.return_value = [
            create_test_requirement("HP requirement 1", requirement_id="REQ_001"),
            create_test_requirement("HP requirement 2", requirement_id="REQ_002"),
        ]
        mock_extractor.classify_artifacts.return_value = {"System Interface": []}

        mock_client_instance = MagicMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance

        mock_generator_instance = MagicMock()
        MockGenerator.return_value = mock_generator_instance
        # First succeeds, second fails
        from unittest.mock import AsyncMock
        mock_generator_instance.generate_test_cases = AsyncMock()
        mock_generator_instance.generate_test_cases.side_effect = [
            [{"test_id": "TC_001"}],
            {"error": True, "requirement_id": "REQ_002", "error_type": "EmptyResponse"}
        ]

        processor = HighPerformanceREQIFZFileProcessor()
        
        with patch.object(processor, 'formatter') as mock_formatter:
            mock_formatter.format_to_excel_streaming = Mock(return_value=True)

            result = await processor.process_file(Path("/tmp/file.reqifz"))

        # Should still succeed with partial results
        assert result["success"] is True
        assert result["total_test_cases"] == 1
        assert result["successful_requirements"] == 1


class TestContextPreservation:
    """Test context preservation in refactored processors"""

    @patch('processors.standard_processor.REQIFArtifactExtractor')
    @patch('processors.standard_processor.TestCaseGenerator')
    @patch('processors.standard_processor.TestCaseFormatter')
    def test_context_reset_between_requirements(self, MockFormatter, MockGenerator, MockExtractor):
        """Test that info context resets between requirements (CRITICAL)"""
        mock_extractor = MockExtractor.return_value
        mock_extractor.extract_reqifz_content.return_value = [
            create_test_heading("Section 1"),
            create_test_information("Info for REQ_001", info_id="INFO_001"),
            create_test_requirement("First requirement", requirement_id="REQ_001"),
            create_test_information("Info for REQ_002", info_id="INFO_002"),
            create_test_requirement("Second requirement", requirement_id="REQ_002"),
        ]
        mock_extractor.classify_artifacts.return_value = {"System Interface": []}

        mock_generator = MockGenerator.return_value
        mock_generator.generate_test_cases_for_requirement.return_value = [{"test_id": "TC"}]

        mock_formatter = MockFormatter.return_value
        mock_formatter.format_to_excel.return_value = True

        processor = REQIFZFileProcessor()
        processor.process_file(Path("/test/file.reqifz"))

        # Get all calls to generator
        calls = mock_generator.generate_test_cases_for_requirement.call_args_list

        # First requirement should have INFO_001
        req1 = calls[0][0][0]
        assert len(req1["info_list"]) == 1
        assert req1["info_list"][0]["id"] == "INFO_001"

        # Second requirement should have INFO_002 (not INFO_001 + INFO_002)
        req2 = calls[1][0][0]
        assert len(req2["info_list"]) == 1
        assert req2["info_list"][0]["id"] == "INFO_002"


def run_integration_tests():
    """Run integration tests"""
    print("=" * 70)
    print("INTEGRATION TESTS FOR REFACTORED PROCESSORS")
    print("=" * 70)

    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "-k", "test_"
    ]

    exit_code = pytest.main(pytest_args)

    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✅ ALL INTEGRATION TESTS PASSED")
    else:
        print(f"❌ SOME TESTS FAILED (exit code: {exit_code})")
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    run_integration_tests()
