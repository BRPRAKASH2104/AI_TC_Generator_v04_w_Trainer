"""
Integration tests for processors.

Tests the full workflow integration between components.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from processors.standard_processor import REQIFZFileProcessor
from processors.hp_processor import HighPerformanceREQIFZFileProcessor
from config import ConfigManager


class TestREQIFZFileProcessor:
    """Integration tests for standard processor."""

    @patch('processors.standard_processor.OllamaClient')
    @patch('processors.standard_processor.YAMLPromptManager')
    def test_process_file_success(self, mock_yaml_manager, mock_ollama_client, temp_reqifz_file, tmp_path):
        """Test successful file processing end-to-end."""
        # Setup mocks
        mock_client_instance = Mock()
        mock_client_instance.generate_response.return_value = """
        {
            "test_cases": [
                {
                    "summary": "Test user input validation",
                    "action": "Enter invalid characters",
                    "data": "Special chars: @#$%",
                    "expected_result": "System shows error message",
                    "test_type": "negative"
                }
            ]
        }
        """
        mock_ollama_client.return_value = mock_client_instance
        
        mock_yaml_instance = Mock()
        mock_yaml_instance.get_test_prompt.return_value = {
            "prompt": "Generate test cases for: {requirement_text}",
            "variables": ["requirement_text"]
        }
        mock_yaml_instance.test_prompts = {"default": {}}
        mock_yaml_manager.return_value = mock_yaml_instance
        
        # Create processor
        config = ConfigManager()
        processor = REQIFZFileProcessor(config)
        
        # Process file
        result = processor.process_file(temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path)
        
        # Verify result
        assert result["success"] == True
        assert result["total_test_cases"] == 1
        assert "processing_time" in result
        assert result["artifacts_found"] == 1  # From temp file
        
        # Verify output file was created
        output_files = list(tmp_path.glob("*.xlsx"))
        assert len(output_files) == 1

    @patch('processors.standard_processor.OllamaClient')
    @patch('processors.standard_processor.YAMLPromptManager')
    def test_process_file_no_system_requirements(self, mock_yaml_manager, mock_ollama_client, tmp_path):
        """Test processing file with no System Requirements."""
        # Create REQIFZ with no System Requirements
        reqifz_content = """<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
    <THE-HEADER>
        <REQ-IF-HEADER>
            <TITLE>Empty Requirements</TITLE>
        </REQ-IF-HEADER>
    </THE-HEADER>
    <CORE-CONTENT>
        <REQ-IF-CONTENT>
            <SPEC-OBJECTS>
                <SPEC-OBJECT IDENTIFIER="INFO_001">
                    <VALUES>
                        <ATTRIBUTE-VALUE-STRING THE-VALUE="Information">
                            <DEFINITION>
                                <ATTRIBUTE-DEFINITION-STRING-REF>TYPE</ATTRIBUTE-DEFINITION-STRING-REF>
                            </DEFINITION>
                        </ATTRIBUTE-VALUE-STRING>
                    </VALUES>
                </SPEC-OBJECT>
            </SPEC-OBJECTS>
        </REQ-IF-CONTENT>
    </CORE-CONTENT>
</REQ-IF>"""
        
        # Create REQIFZ file
        import zipfile
        reqifz_path = tmp_path / "empty.reqifz"
        with zipfile.ZipFile(reqifz_path, 'w') as zf:
            zf.writestr("empty.reqif", reqifz_content)
        
        mock_yaml_instance = Mock()
        mock_yaml_instance.test_prompts = {"default": {}}
        mock_yaml_manager.return_value = mock_yaml_instance
        
        config = ConfigManager()
        processor = REQIFZFileProcessor(config)
        
        result = processor.process_file(reqifz_path, "llama3.1:8b")
        
        assert result["success"] == False
        assert "No System Requirements found" in result["error"]

    @patch('processors.standard_processor.OllamaClient')
    @patch('processors.standard_processor.YAMLPromptManager')
    def test_process_directory(self, mock_yaml_manager, mock_ollama_client, tmp_path):
        """Test processing multiple files in directory."""
        # Create multiple REQIFZ files
        for i in range(2):
            reqifz_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd" xmlns:html="http://www.w3.org/1999/xhtml">
    <CORE-CONTENT>
        <REQ-IF-CONTENT>
            <SPEC-OBJECTS>
                <SPEC-OBJECT IDENTIFIER="REQ_{i:03d}">
                    <VALUES>
                        <ATTRIBUTE-VALUE-STRING THE-VALUE="System Requirement">
                            <DEFINITION>
                                <ATTRIBUTE-DEFINITION-STRING-REF>TYPE</ATTRIBUTE-DEFINITION-STRING-REF>
                            </DEFINITION>
                        </ATTRIBUTE-VALUE-STRING>
                        <ATTRIBUTE-VALUE-XHTML>
                            <DEFINITION LONG-NAME="ReqIF.Text">
                                <ATTRIBUTE-DEFINITION-XHTML-REF>req-text</ATTRIBUTE-DEFINITION-XHTML-REF>
                            </DEFINITION>
                            <THE-VALUE><html:div>The system shall process test requirement {i}</html:div></THE-VALUE>
                        </ATTRIBUTE-VALUE-XHTML>
                    </VALUES>
                </SPEC-OBJECT>
            </SPEC-OBJECTS>
        </REQ-IF-CONTENT>
    </CORE-CONTENT>
</REQ-IF>"""
            
            import zipfile
            reqifz_path = tmp_path / f"test_{i}.reqifz"
            with zipfile.ZipFile(reqifz_path, 'w') as zf:
                zf.writestr(f"test_{i}.reqif", reqifz_content)
        
        # Setup mocks
        mock_client_instance = Mock()
        mock_client_instance.generate_response.return_value = """
        {"test_cases": [{"summary": "Test case"}]}
        """
        mock_ollama_client.return_value = mock_client_instance
        
        mock_yaml_instance = Mock()
        mock_yaml_instance.get_test_prompt.return_value = "Generate test cases"
        mock_yaml_instance.test_prompts = {"default": {}}
        mock_yaml_manager.return_value = mock_yaml_instance

        config = ConfigManager()
        processor = REQIFZFileProcessor(config)
        
        results = processor.process_directory(tmp_path, "llama3.1:8b")
        
        assert len(results) == 2
        for result in results:
            assert result["success"] == True

    def test_validate_environment(self):
        """Test environment validation."""
        with patch('processors.standard_processor.YAMLPromptManager') as mock_yaml:
            mock_yaml_instance = Mock()
            mock_yaml_instance.test_prompts = {"template1": {}}
            mock_yaml.return_value = mock_yaml_instance
            
            config = ConfigManager()
            processor = REQIFZFileProcessor(config)
            
            assert processor.validate_environment() == True

    def test_validate_environment_no_templates(self):
        """Test environment validation with no templates."""
        with patch('processors.standard_processor.YAMLPromptManager') as mock_yaml:
            mock_yaml_instance = Mock()
            mock_yaml_instance.test_prompts = {}
            mock_yaml.return_value = mock_yaml_instance
            
            config = ConfigManager()
            processor = REQIFZFileProcessor(config)
            
            assert processor.validate_environment() == False


class TestHighPerformanceREQIFZFileProcessor:
    """Integration tests for high-performance processor."""

    @pytest.mark.asyncio
    @patch('processors.hp_processor.AsyncOllamaClient')
    @patch('processors.hp_processor.YAMLPromptManager') 
    async def test_process_file_success(self, mock_yaml_manager, mock_async_ollama_client, temp_reqifz_file, tmp_path):
        """Test successful async file processing."""
        # Setup async mocks
        mock_client_instance = Mock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_async_ollama_client.return_value = mock_client_instance
        
        mock_yaml_instance = Mock()
        mock_yaml_instance.get_test_prompt.return_value = {
            "prompt": "Generate test cases for: {requirement_text}",
            "variables": ["requirement_text"]
        }
        mock_yaml_instance.test_prompts = {"default": {}}
        mock_yaml_manager.return_value = mock_yaml_instance
        
        # Mock the AsyncTestCaseGenerator
        with patch('processors.hp_processor.AsyncTestCaseGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator.generate_test_cases_batch = AsyncMock(return_value=[
                [{"summary": "Async test case", "action": "Test action"}]
            ])
            mock_generator_class.return_value = mock_generator
            
            config = ConfigManager()
            processor = HighPerformanceREQIFZFileProcessor(config, max_concurrent_requirements=2)
            
            result = await processor.process_file(temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path)
            
            assert result["success"] == True
            assert result["total_test_cases"] == 1
            assert "performance_metrics" in result

    @pytest.mark.asyncio
    @patch('processors.hp_processor.AsyncOllamaClient')
    @patch('processors.hp_processor.YAMLPromptManager')
    async def test_process_file_with_failures(self, mock_yaml_manager, mock_async_ollama_client, temp_reqifz_file, tmp_path):
        """Test async processing with some requirement failures."""
        # Setup mocks
        mock_client_instance = Mock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_async_ollama_client.return_value = mock_client_instance
        
        mock_yaml_instance = Mock()
        mock_yaml_instance.get_test_prompt.return_value = "Generate test cases"
        mock_yaml_instance.test_prompts = {"default": {}}
        mock_yaml_manager.return_value = mock_yaml_instance

        # Mock generator with mixed results - this test only has 1 requirement, so we can't test mixed results
        # Instead, let's test a pure failure case and expect the processor to handle it gracefully
        with patch('processors.hp_processor.AsyncTestCaseGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator.generate_test_cases_batch = AsyncMock(return_value=[
                {"error": True, "requirement_id": "REQ_001", "test_cases": []}  # Failed requirement
            ])
            mock_generator_class.return_value = mock_generator
            
            config = ConfigManager()
            processor = HighPerformanceREQIFZFileProcessor(config)
            
            result = await processor.process_file(temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path)
            
            assert result["success"] == False  # Processing failed due to no test cases
            assert result["error"] == "No test cases were generated"

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, tmp_path):
        """Test that performance monitoring works."""
        config = ConfigManager()
        processor = HighPerformanceREQIFZFileProcessor(config)
        
        # Start monitoring
        monitor_task = asyncio.create_task(processor._monitor_performance())
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        monitor_task.cancel()
        
        # Should have collected some metrics
        assert len(processor.metrics["cpu_usage_samples"]) > 0 or len(processor.metrics["memory_usage_samples"]) > 0

    def test_calculate_performance_metrics(self):
        """Test performance metrics calculation."""
        config = ConfigManager()
        processor = HighPerformanceREQIFZFileProcessor(config)
        
        # Set up test metrics
        processor.metrics = {
            "total_artifacts": 100,
            "total_requirements": 50, 
            "total_test_cases": 150,
            "successful_requirements": 45,
            "ai_calls_made": 50,
            "cpu_usage_samples": [50.0, 60.0, 70.0],
            "memory_usage_samples": [40.0, 45.0, 50.0]
        }
        
        metrics = processor._calculate_performance_metrics(10.0)  # 10 second processing time
        
        assert metrics["artifacts_per_second"] == 10.0
        assert metrics["requirements_per_second"] == 5.0
        assert metrics["test_cases_per_second"] == 15.0
        assert metrics["success_rate"] == 90.0
        assert metrics["avg_cpu_usage"] == 60.0
        assert metrics["peak_cpu_usage"] == 70.0