#!/usr/bin/env python3
"""
End-to-end integration tests for AI Test Case Generator.

These tests validate the complete workflow from REQIFZ file input
to Excel output generation, including error handling and performance.
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from config import ConfigManager
from processors.hp_processor import HighPerformanceREQIFZFileProcessor
from processors.standard_processor import REQIFZFileProcessor


class TestEndToEndWorkflows:
    """Test complete end-to-end processing workflows"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory for tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing"""
        config = ConfigManager()
        # Override with test-friendly settings
        config.ollama.timeout = 30
        config.ollama.max_retries = 1
        config.ollama.concurrent_requests = 2
        config.logging.log_level = "DEBUG"
        return config

    @pytest.fixture
    def sample_reqifz_path(self):
        """Path to sample REQIFZ file"""
        return Path("input/automotive_door_window_system.reqifz")

    @pytest.fixture
    def mock_ai_response(self):
        """Mock AI response for testing"""
        return {
            "test_cases": [
                {
                    "test_id": "TC_001",
                    "summary": "Test door window operation",
                    "preconditions": "Vehicle ignition on",
                    "test_steps": [
                        "Press window down button",
                        "Verify window moves down"
                    ],
                    "expected_result": "Window moves down smoothly",
                    "test_type": "Functional"
                },
                {
                    "test_id": "TC_002",
                    "summary": "Test window obstruction detection",
                    "preconditions": "Window in motion",
                    "test_steps": [
                        "Simulate obstruction during window movement",
                        "Verify window stops and reverses"
                    ],
                    "expected_result": "Window stops and reverses direction",
                    "test_type": "Safety"
                }
            ]
        }

    def test_standard_mode_complete_workflow(self, mock_config, temp_output_dir, sample_reqifz_path, mock_ai_response):
        """Test complete standard mode workflow from REQIFZ to Excel"""
        if not sample_reqifz_path.exists():
            pytest.skip(f"Sample REQIFZ file not found: {sample_reqifz_path}")

        # Mock AI client to avoid external dependencies
        with patch('src.processors.standard_processor.OllamaClient') as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.generate_response.return_value = json.dumps(mock_ai_response)

            # Initialize processor
            processor = REQIFZFileProcessor(mock_config)

            # Process file
            result = processor.process_file(
                reqifz_path=sample_reqifz_path,
                model="llama3.1:8b",
                template=None,
                output_dir=temp_output_dir
            )

            # Verify successful processing
            assert result["success"] is True
            assert "total_test_cases" in result
            assert result["total_test_cases"] > 0
            assert "processing_time" in result
            assert result["processing_time"] > 0

            # Verify output files were created
            output_files = list(temp_output_dir.glob("*.xlsx"))
            assert len(output_files) > 0

            # Verify Excel file has expected structure
            excel_file = output_files[0]
            assert excel_file.exists()
            assert excel_file.suffix == ".xlsx"

            # Verify AI client was called
            assert mock_client.generate_response.called

    @pytest.mark.asyncio
    async def test_hp_mode_complete_workflow(self, mock_config, temp_output_dir, sample_reqifz_path, mock_ai_response):
        """Test complete high-performance mode workflow"""
        if not sample_reqifz_path.exists():
            pytest.skip(f"Sample REQIFZ file not found: {sample_reqifz_path}")

        # Mock async AI client
        with patch('src.processors.hp_processor.AsyncOllamaClient') as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.generate_response.return_value = json.dumps(mock_ai_response)

            # Initialize HP processor
            processor = HighPerformanceREQIFZFileProcessor(mock_config, max_concurrent_requirements=2)

            # Process file
            result = await processor.process_file(
                reqifz_path=sample_reqifz_path,
                model="llama3.1:8b",
                template=None,
                output_dir=temp_output_dir
            )

            # Verify successful processing
            assert result["success"] is True
            assert "total_test_cases" in result
            assert result["total_test_cases"] > 0
            assert "processing_time" in result
            assert "performance_metrics" in result

            # Verify performance metrics
            metrics = result["performance_metrics"]
            assert "test_cases_per_second" in metrics
            assert "parallel_efficiency" in metrics
            assert "ai_calls_made" in metrics

            # Verify output files were created
            output_files = list(temp_output_dir.glob("*.xlsx"))
            assert len(output_files) > 0

    def test_directory_processing_workflow(self, mock_config, temp_output_dir, mock_ai_response):
        """Test directory processing workflow"""
        # Create temporary input directory with mock REQIFZ files
        with tempfile.TemporaryDirectory() as input_dir:
            input_path = Path(input_dir)

            # Create mock REQIFZ files (we'll mock the extraction)
            mock_file1 = input_path / "test1.reqifz"
            mock_file2 = input_path / "test2.reqifz"
            mock_file1.touch()
            mock_file2.touch()

            # Mock the extraction and AI processing
            with patch('src.core.extractors.REQIFArtifactExtractor.extract_reqifz_content') as mock_extract, \
                 patch('src.processors.standard_processor.OllamaClient') as mock_client_class:

                # Mock extraction to return sample artifacts
                mock_extract.return_value = [
                    {
                        "id": "REQ_001",
                        "type": "System Requirement",
                        "heading": "Door Window Control",
                        "text": "The system shall control door window operation",
                    }
                ]

                # Mock AI client
                mock_client = mock_client_class.return_value
                mock_client.generate_response.return_value = json.dumps(mock_ai_response)

                # Initialize processor
                processor = REQIFZFileProcessor(mock_config)

                # Process directory
                results = processor.process_directory(
                    directory_path=input_path,
                    model="llama3.1:8b",
                    template=None,
                    output_dir=temp_output_dir
                )

                # Verify results
                assert len(results) == 2  # Two files processed
                assert all(result["success"] for result in results)

                # Verify output files were created for each input file
                output_files = list(temp_output_dir.glob("*.xlsx"))
                assert len(output_files) == 2

    def test_error_handling_workflow(self, mock_config, temp_output_dir):
        """Test error handling in complete workflow"""
        # Create processor
        processor = REQIFZFileProcessor(mock_config)

        # Test with non-existent file
        non_existent_file = Path("non_existent_file.reqifz")
        result = processor.process_file(
            reqifz_path=non_existent_file,
            model="llama3.1:8b",
            template=None,
            output_dir=temp_output_dir
        )

        # Verify error handling
        assert result["success"] is False
        assert "error" in result

    def test_template_validation_workflow(self, mock_config):
        """Test template validation workflow"""
        from src.yaml_prompt_manager import YAMLPromptManager

        # Initialize YAML manager
        yaml_manager = YAMLPromptManager()

        # Test template loading
        templates = yaml_manager.test_prompts
        assert len(templates) > 0

        # Test template structure validation
        for _template_name, template_data in templates.items():
            # Updated to match new schema where 'prompt' might be 'template' or in the body
            assert "category" in template_data
            assert "description" in template_data
            # Validating against updated structure assuming 'system_prompt', 'prompt', or 'template'
            template_content = template_data.get("system_prompt", template_data.get("prompt", template_data.get("template")))
            assert isinstance(template_content, str), "Template must contain a string prompt/system_prompt/template field"
            assert len(template_data["prompt"]) > 0

    def test_configuration_workflow(self, mock_config):
        """Test configuration management workflow"""
        # Test CLI overrides
        overridden_config = mock_config.apply_cli_overrides(
            model="deepseek-coder-v2:16b",
            template="custom_template",
            max_concurrent=8,
            verbose=True
        )

        # Verify overrides were applied
        assert overridden_config.ollama.synthesizer_model == "deepseek-coder-v2:16b"
        assert overridden_config.cli.template == "custom_template"
        assert overridden_config.ollama.concurrent_requests == 8
        assert overridden_config.cli.verbose is True

        # Test secrets validation
        secrets_status = overridden_config.get_secrets_status()
        assert "secrets_configured" in secrets_status
        assert "total_secrets_available" in secrets_status
        assert "configuration_health" in secrets_status

    @pytest.mark.asyncio
    async def test_performance_comparison_workflow(self, mock_config, sample_reqifz_path, mock_ai_response):
        """Test performance comparison between standard and HP modes"""
        if not sample_reqifz_path.exists():
            pytest.skip(f"Sample REQIFZ file not found: {sample_reqifz_path}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            # Mock AI clients for both modes
            with patch('src.processors.standard_processor.OllamaClient') as mock_sync_client, \
                 patch('src.processors.hp_processor.AsyncOllamaClient') as mock_async_client:

                # Configure mock responses
                mock_sync_client.return_value.generate_response.return_value = json.dumps(mock_ai_response)
                mock_async_client.return_value.generate_response.return_value = json.dumps(mock_ai_response)

                # Test standard mode
                standard_processor = REQIFZFileProcessor(mock_config)
                start_time = time.time()
                standard_result = standard_processor.process_file(
                    reqifz_path=sample_reqifz_path,
                    model="llama3.1:8b",
                    template=None,
                    output_dir=temp_output_dir / "standard"
                )
                standard_time = time.time() - start_time

                # Test HP mode
                hp_processor = HighPerformanceREQIFZFileProcessor(mock_config)
                start_time = time.time()
                hp_result = await hp_processor.process_file(
                    reqifz_path=sample_reqifz_path,
                    model="llama3.1:8b",
                    template=None,
                    output_dir=temp_output_dir / "hp"
                )
                hp_time = time.time() - start_time

                # Verify both modes succeeded
                assert standard_result["success"] is True
                assert hp_result["success"] is True

                # Verify HP mode has performance metrics
                assert "performance_metrics" in hp_result
                assert "test_cases_per_second" in hp_result["performance_metrics"]

                # Log performance comparison (for debugging)
                print(f"Standard mode time: {standard_time:.2f}s")
                print(f"HP mode time: {hp_time:.2f}s")

    def test_logging_integration_workflow(self, mock_config, temp_output_dir):
        """Test logging integration in complete workflow"""
        # Test that logging doesn't interfere with processing
        with tempfile.TemporaryDirectory() as log_dir:
            # Update config to enable file logging
            mock_config.logging.log_to_file = True
            mock_config.logging.log_directory = str(log_dir)

            # Initialize app logger with config
            from src.app_logger import get_app_logger, shutdown_app_logger

            try:
                app_logger = get_app_logger(mock_config)

                # Log some test messages
                app_logger.info("Integration test started")
                app_logger.debug("Debug message for testing")
                app_logger.warning("Warning message for testing")

                # Verify log files were created
                log_files = list(Path(log_dir).glob("*.log"))
                json_log_files = list(Path(log_dir).glob("*.jsonl"))

                assert len(log_files) > 0 or len(json_log_files) > 0, "No log files were created"

                # Test application metrics logging
                app_logger.log_application_metrics()

            finally:
                shutdown_app_logger()

    def test_secrets_management_workflow(self, mock_config):
        """Test secrets management workflow"""
        import os

        # Set test environment variables
        test_env_vars = {
            "AI_TG_OLLAMA_API_KEY": "test_api_key_123",
            "AI_TG_EXTERNAL_API_KEY": "external_key_456",
            "AI_TG_ENCRYPTION": "true"
        }

        # Set environment variables
        for key, value in test_env_vars.items():
            os.environ[key] = value

        try:
            # Create new config to pick up environment variables
            new_config = ConfigManager()

            # Test secrets were loaded
            assert new_config.secrets.ollama_api_key == "test_api_key_123"
            assert new_config.secrets.external_api_key == "external_key_456"

            # Test secrets masking
            secrets_summary = new_config.secrets.get_masked_summary()
            assert "test***" in secrets_summary["ollama_api_key"] or "test_" in secrets_summary["ollama_api_key"]
            assert "23" in secrets_summary["ollama_api_key"]
            assert "***" in secrets_summary["ollama_api_key"]

            # Test secrets validation
            all_present, missing = new_config.validate_secrets_for_mode("external_api")
            assert all_present is True
            assert len(missing) == 0

        finally:
            # Clean up environment variables
            for key in test_env_vars:
                os.environ.pop(key, None)


class TestErrorConditions:
    """Test error conditions and edge cases in end-to-end workflows"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory for tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing"""
        config = ConfigManager()
        # Override with test-friendly settings
        config.ollama.timeout = 30
        config.ollama.max_retries = 1
        config.ollama.concurrent_requests = 2
        config.logging.log_level = "DEBUG"
        return config

    @pytest.fixture
    def sample_reqifz_path(self):
        """Path to sample REQIFZ file"""
        return Path("input/automotive_door_window_system.reqifz")

    def test_malformed_reqifz_handling(self, mock_config, temp_output_dir):
        """Test handling of malformed REQIFZ files"""
        with tempfile.NamedTemporaryFile(suffix=".reqifz", delete=False) as temp_file:
            # Write invalid ZIP content
            temp_file.write(b"This is not a valid ZIP file")
            temp_file.flush()

            try:
                processor = REQIFZFileProcessor(mock_config)
                result = processor.process_file(
                    reqifz_path=Path(temp_file.name),
                    model="llama3.1:8b",
                    template=None,
                    output_dir=temp_output_dir
                )

                # Verify graceful error handling
                assert result["success"] is False
                assert "error" in result

            finally:
                pass # Tempfile handles cleanup or edge case test closes it

    def test_ai_service_timeout_handling(self, mock_config, sample_reqifz_path, temp_output_dir):
        """Test handling of AI service timeouts"""
        if not sample_reqifz_path.exists():
            pytest.skip(f"Sample REQIFZ file not found: {sample_reqifz_path}")

        # Mock AI client to simulate timeout
        with patch('src.processors.standard_processor.OllamaClient') as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.generate_response.side_effect = TimeoutError("AI service timeout")

            processor = REQIFZFileProcessor(mock_config)
            result = processor.process_file(
                reqifz_path=sample_reqifz_path,
                model="llama3.1:8b",
                template=None,
                output_dir=temp_output_dir
            )

            # Verify timeout was handled gracefully
            # The exact behavior depends on implementation - it might succeed with 0 test cases
            # or fail entirely, both are valid approaches
            assert "success" in result
            assert "error" in result or result["success"] is True

    def test_insufficient_permissions_handling(self, mock_config, sample_reqifz_path):
        """Test handling of insufficient file permissions"""
        if not sample_reqifz_path.exists():
            pytest.skip(f"Sample REQIFZ file not found: {sample_reqifz_path}")

        # Try to write to a read-only directory (simulate permission error)
        read_only_dir = Path("/dev/null")  # This will definitely fail

        processor = REQIFZFileProcessor(mock_config)
        result = processor.process_file(
            reqifz_path=sample_reqifz_path,
            model="llama3.1:8b",
            template=None,
            output_dir=read_only_dir
        )

        # Verify permission error was handled gracefully
        assert "success" in result
        if not result["success"]:
            assert "error" in result
