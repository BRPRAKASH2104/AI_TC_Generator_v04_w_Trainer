"""
Comprehensive test suite for refactored components.

Tests BaseProcessor, PromptBuilder, and refactored generators with all
positive and negative cases.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unittest.mock import Mock

import pytest

from core.generators import AsyncTestCaseGenerator, TestCaseGenerator
from core.prompt_builder import PromptBuilder
from processors.base_processor import BaseProcessor
from tests.helpers import (
    create_test_heading,
    create_test_information,
    create_test_interface,
    create_test_requirement,
)


class TestBaseProcessor:
    """Test BaseProcessor shared methods"""

    def test_initialize_logger(self):
        """Test logger initialization"""
        processor = BaseProcessor()
        reqifz_path = Path("/test/file.reqifz")

        processor._initialize_logger(reqifz_path)

        assert processor.logger is not None
        # Logger should have file info
        assert hasattr(processor.logger, 'info')

    def test_build_augmented_requirements_with_context(self):
        """Test context-aware requirement augmentation (POSITIVE)"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()

        # Mock classified artifacts
        processor.extractor.classify_artifacts.return_value = {
            "System Interface": [
                create_test_interface("Speed signal", interface_id="IF_001")
            ]
        }

        # Simulate artifact sequence with context (using helpers for XHTML format)
        artifacts = [
            create_test_heading("Door Lock System"),
            create_test_information("Safety critical", info_id="INFO_001"),
            create_test_requirement("Door shall lock when speed exceeds threshold", requirement_id="REQ_001"),
            create_test_heading("Window System"),
            create_test_requirement("Window shall close automatically", requirement_id="REQ_002")
        ]

        augmented_reqs, interface_count = processor._build_augmented_requirements(artifacts)

        # Verify context preservation
        assert len(augmented_reqs) == 2
        assert augmented_reqs[0]["id"] == "REQ_001"
        assert "Door Lock System" in augmented_reqs[0]["heading"]  # Heading text in XHTML format
        assert len(augmented_reqs[0]["info_list"]) == 1
        assert "Safety critical" in augmented_reqs[0]["info_list"][0]["text"]

        # Second requirement should have different heading, no info
        assert augmented_reqs[1]["id"] == "REQ_002"
        assert "Window System" in augmented_reqs[1]["heading"]  # Heading text in XHTML format
        assert len(augmented_reqs[1]["info_list"]) == 0

        # Both should have global interfaces
        assert len(augmented_reqs[0]["interface_list"]) == 1
        assert len(augmented_reqs[1]["interface_list"]) == 1

    def test_build_augmented_requirements_no_requirements(self):
        """Test with no system requirements (NEGATIVE)"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()
        processor.extractor.classify_artifacts.return_value = {"System Interface": []}

        artifacts = [
            create_test_heading("Test"),
            create_test_information("Info", info_id="INFO_001")
        ]

        augmented_reqs, interface_count = processor._build_augmented_requirements(artifacts)

        assert len(augmented_reqs) == 0
        assert interface_count == 0

    def test_build_augmented_requirements_no_heading(self):
        """Test requirement without heading (EDGE CASE)"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()
        processor.extractor.classify_artifacts.return_value = {"System Interface": []}

        artifacts = [
            create_test_requirement("Requirement without heading", requirement_id="REQ_001")
        ]

        augmented_reqs, _ = processor._build_augmented_requirements(artifacts)

        assert len(augmented_reqs) == 1
        assert augmented_reqs[0]["heading"] == "No Heading"  # Default

    def test_generate_output_path(self):
        """Test output path generation"""
        processor = BaseProcessor()
        reqifz_path = Path("/test/input/door_system.reqifz")
        model = "llama3.1:8b"

        output_path = processor._generate_output_path(reqifz_path, model)

        assert output_path.parent == reqifz_path.parent
        assert "door_system_TCD" in output_path.name
        assert "llama3.1_8b" in output_path.name
        assert output_path.suffix == ".xlsx"

    def test_generate_output_path_custom_dir(self):
        """Test output path with custom directory"""
        processor = BaseProcessor()
        reqifz_path = Path("/test/input/door_system.reqifz")
        model = "llama3.1:8b"
        custom_dir = Path("/test/output")

        output_path = processor._generate_output_path(reqifz_path, model, custom_dir)

        assert output_path.parent == custom_dir

    def test_create_metadata(self):
        """Test metadata creation"""
        processor = BaseProcessor()

        metadata = processor._create_metadata(
            model="llama3.1:8b",
            template="test_template",
            reqifz_path=Path("/test/file.reqifz"),
            total_cases=50,
            requirements_processed=10,
            successful_requirements=9
        )

        assert metadata["model"] == "llama3.1:8b"
        assert metadata["template"] == "test_template"
        assert metadata["total_cases"] == 50
        assert metadata["requirements_processed"] == 10
        assert metadata["successful_requirements"] == 9

    def test_create_success_result(self):
        """Test success result creation"""
        processor = BaseProcessor()

        result = processor._create_success_result(
            output_path=Path("/test/output.xlsx"),
            total_test_cases=100,
            requirements_processed=20,
            successful_requirements=18,
            artifacts_count=150,
            processing_time=45.5,
            model="llama3.1:8b",
            template="test"
        )

        assert result["success"] is True
        assert result["total_test_cases"] == 100
        assert result["processing_time"] == 45.5

    def test_create_error_result(self):
        """Test error result creation"""
        processor = BaseProcessor()

        result = processor._create_error_result("Test error", 10.5)

        assert result["success"] is False
        assert result["error"] == "Test error"
        assert result["processing_time"] == 10.5


class TestPromptBuilder:
    """Test PromptBuilder functionality"""

    def test_build_prompt_default_no_yaml(self):
        """Test default prompt building without YAML manager (POSITIVE)"""
        builder = PromptBuilder()
        requirement = {
            "id": "REQ_001",
            "heading": "Door Lock",
            "text": "System shall lock doors"
        }

        prompt = builder.build_prompt(requirement)

        assert "REQ_001" in prompt
        assert "Door Lock" in prompt
        assert "System shall lock doors" in prompt
        assert "JSON format" in prompt

    def test_build_prompt_with_yaml_template(self):
        """Test prompt building with YAML template (POSITIVE)"""
        yaml_manager = Mock()
        yaml_manager.get_test_prompt.return_value = "TEMPLATE: {requirement_id}"

        builder = PromptBuilder(yaml_manager)
        requirement = {"id": "REQ_001"}

        prompt = builder.build_prompt(requirement, "custom_template")

        yaml_manager.get_test_prompt.assert_called_once()
        assert prompt == "TEMPLATE: {requirement_id}"

    def test_build_prompt_yaml_fallback_on_error(self):
        """Test fallback to default when YAML fails (NEGATIVE)"""
        yaml_manager = Mock()
        yaml_manager.get_test_prompt.side_effect = Exception("Template error")

        builder = PromptBuilder(yaml_manager)
        requirement = {"id": "REQ_001", "heading": "Test", "text": "Text"}

        prompt = builder.build_prompt(requirement)

        # Should fallback to default
        assert "REQ_001" in prompt
        assert "JSON format" in prompt

    def test_format_table_with_data(self):
        """Test table formatting with valid data (POSITIVE)"""
        table_data = {
            "data": [
                {"col1": "value1", "col2": "value2"},
                {"col1": "value3", "col2": "value4"}
            ]
        }

        result = PromptBuilder.format_table(table_data)

        assert "Table Data:" in result
        assert "col1 | col2" in result
        assert "value1 | value2" in result

    def test_format_table_empty(self):
        """Test table formatting with empty data (NEGATIVE)"""
        assert PromptBuilder.format_table(None) == "No table data available"
        assert PromptBuilder.format_table({}) == "No table data available"
        assert PromptBuilder.format_table({"data": []}) == "Empty table"

    def test_format_table_truncation(self):
        """Test table truncation for large tables (EDGE CASE)"""
        table_data = {
            "data": [{"col": f"val{i}"} for i in range(15)]
        }

        result = PromptBuilder.format_table(table_data)

        assert "Table contains 15 rows total." in result
        assert "val9" in result  # 10th row (0-indexed)
        assert "val14" in result  # Should be preserved

    def test_format_info_list_with_data(self):
        """Test info list formatting (POSITIVE)"""
        info_list = [
            {"text": "Info 1"},
            {"text": "Info 2"},
            {"text": "Info 3"}
        ]

        result = PromptBuilder.format_info_list(info_list)

        assert "- Info 1" in result
        assert "- Info 2" in result
        assert "- Info 3" in result

    def test_format_info_list_empty(self):
        """Test info list formatting with empty list (NEGATIVE)"""
        assert PromptBuilder.format_info_list([]) == "None"
        assert PromptBuilder.format_info_list(None) == "None"

    def test_format_interfaces_with_data(self):
        """Test interface formatting (POSITIVE)"""
        interfaces = [
            {"id": "IF_001", "text": "Speed signal"},
            {"id": "IF_002", "text": "Door status"}
        ]

        result = PromptBuilder.format_interfaces(interfaces)

        assert "- IF_001: Speed signal" in result
        assert "- IF_002: Door status" in result

    def test_format_interfaces_empty(self):
        """Test interface formatting with empty list (NEGATIVE)"""
        assert PromptBuilder.format_interfaces([]) == "None"
        assert PromptBuilder.format_interfaces(None) == "None"

    def test_format_interfaces_missing_id(self):
        """Test interface formatting with missing ID (EDGE CASE)"""
        interfaces = [{"text": "Signal"}]

        result = PromptBuilder.format_interfaces(interfaces)

        assert "UNKNOWN: Signal" in result


class TestGeneratorRefactoring:
    """Test generator refactoring with PromptBuilder"""

    def test_test_case_generator_uses_prompt_builder(self):
        """Test TestCaseGenerator uses PromptBuilder (POSITIVE)"""
        client = Mock()
        yaml_manager = Mock()

        generator = TestCaseGenerator(client, yaml_manager)

        assert hasattr(generator, 'prompt_builder')
        assert generator.prompt_builder.yaml_manager == yaml_manager

    def test_async_generator_uses_prompt_builder(self):
        """Test AsyncTestCaseGenerator uses PromptBuilder (POSITIVE)"""
        client = Mock()
        yaml_manager = Mock()

        generator = AsyncTestCaseGenerator(client, yaml_manager)

        assert hasattr(generator, 'prompt_builder')
        assert generator.prompt_builder.yaml_manager == yaml_manager

    def test_test_case_generator_no_coupling(self):
        """Test TestCaseGenerator has no awkward coupling (ARCHITECTURE)"""
        client = Mock()
        generator = TestCaseGenerator(client)

        # Should NOT have methods from old implementation
        assert not hasattr(generator, '_build_prompt_from_template')
        assert not hasattr(generator, '_format_table_for_prompt')
        assert not hasattr(generator, '_format_info_for_prompt')

        # Should have PromptBuilder
        assert hasattr(generator, 'prompt_builder')

    def test_async_generator_no_sync_instantiation(self):
        """Test AsyncGenerator doesn't create sync generator (ARCHITECTURE)"""
        client = Mock()
        yaml_manager = Mock()

        # Create async generator
        async_gen = AsyncTestCaseGenerator(client, yaml_manager)

        # Verify it has its own PromptBuilder (not from sync generator)
        assert hasattr(async_gen, 'prompt_builder')
        assert isinstance(async_gen.prompt_builder, PromptBuilder)


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_base_processor_extract_artifacts_failure(self):
        """Test artifact extraction failure (NEGATIVE)"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()
        processor.extractor.extract_reqifz_content.return_value = None

        artifacts = processor._extract_artifacts(Path("/test/file.reqifz"))

        assert artifacts is None
        processor.logger.error.assert_called_once()

    def test_prompt_builder_table_format_error(self):
        """Test table formatting error handling (NEGATIVE)"""
        bad_table = {"data": "not_a_list"}  # Invalid structure

        result = PromptBuilder.format_table(bad_table)

        assert "Error formatting table" in result

    def test_generator_empty_response(self):
        """Test generator handling empty AI response (NEGATIVE)"""
        client = Mock()
        client.generate_response.return_value = ""

        generator = TestCaseGenerator(client)
        generator.json_parser = Mock()
        generator.json_parser.extract_json_from_response.return_value = None

        requirement = {"id": "REQ_001"}
        result = generator.generate_test_cases_for_requirement(requirement, "model")

        assert result == []

    def test_generator_exception_handling(self):
        """Test generator exception handling (NEGATIVE)"""
        client = Mock()
        client.generate_response.side_effect = Exception("API Error")

        generator = TestCaseGenerator(client)
        generator.logger = Mock()

        requirement = {"id": "REQ_001"}
        result = generator.generate_test_cases_for_requirement(requirement, "model")

        assert result == []
        assert generator.logger is not None


def run_tests():
    """Run all tests"""
    print("=" * 70)
    print("COMPREHENSIVE REFACTORING TEST SUITE")
    print("=" * 70)

    # Run pytest
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "-k", "test_"
    ]

    exit_code = pytest.main(pytest_args)

    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ SOME TESTS FAILED (exit code: {exit_code})")
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    run_tests()
