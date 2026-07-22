"""
Integration tests for processors.

Tests the full workflow integration between components.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from config import ConfigManager
from processors.hp_processor import HighPerformanceREQIFZFileProcessor
from processors.standard_processor import REQIFZFileProcessor
from tests.helpers import (
    create_test_heading,
    create_test_requirement,
)


class TestREQIFZFileProcessor:
    """Integration tests for standard processor."""

    @patch('processors.standard_processor.REQIFArtifactExtractor')
    @patch('processors.standard_processor.TestCaseGenerator')
    @patch('processors.standard_processor.TestCaseFormatter')
    def test_process_file_success(self, mock_formatter_class, mock_generator_class, mock_extractor_class, temp_reqifz_file, tmp_path):
        """Test successful file processing end-to-end."""
        # Setup mocks using mock objects
        mock_extractor = Mock()
        mock_extractor.extract_reqifz_content.return_value = [{"type": "System Requirement", "id": "REQ_001", "table": True, "req_text": "Sample text", "text": "Sample text", "heading": "Heading"}]
        mock_extractor.classify_artifacts.return_value = {}
        mock_extractor_class.return_value = mock_extractor

        mock_generator = Mock()
        mock_generator.generate_test_cases_for_requirement.return_value = [{"summary": "Test case"}]
        mock_generator_class.return_value = mock_generator

        mock_formatter = Mock()
        def mock_format(*args, **kwargs):
            # args[1] in format_to_excel(test_cases, output_dir, ...) is the output directory
            out_dir = kwargs.get('output_dir')
            if not out_dir and len(args) > 1:
                out_dir = args[1]
            if not out_dir:
                out_dir = tmp_path

            # Ensure the directory exists before touching a file in it
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "test_output.xlsx").touch()
            return True
        mock_formatter.format_to_excel.side_effect = mock_format
        mock_formatter_class.return_value = mock_formatter

        config = ConfigManager()
        processor = REQIFZFileProcessor(config)

        # Process file
        result = processor.process_file(temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path)

        # Verify result
        assert result["success"]
        assert result["total_test_cases"] == 1
        assert "processing_time" in result
        assert result["artifacts_found"] == 1

        # Verify mocks were called
        mock_extractor.extract_reqifz_content.assert_called_once()
        mock_generator.generate_test_cases_for_requirement.assert_called_once()
        mock_formatter.format_to_excel.assert_called_once()

        # Verify output file was created
        output_files = list(tmp_path.glob("*.xlsx"))
        assert len(output_files) == 1

    @patch('processors.standard_processor.OllamaClient')
    @patch('processors.base_processor.YAMLPromptManager')
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

        assert not result["success"]
        assert "No System Requirements found" in result["error"]

    @patch('processors.standard_processor.OllamaClient')
    @patch('processors.base_processor.YAMLPromptManager')
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
        with patch('processors.standard_processor.TestCaseGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator.generate_test_cases_for_requirement.return_value = [{"summary": "Test case"}]
            mock_generator_class.return_value = mock_generator

            mock_yaml_instance = Mock()
            mock_yaml_instance.get_test_prompt.return_value = "Generate test cases"
            mock_yaml_instance.test_prompts = {"default": {}}
            mock_yaml_manager.return_value = mock_yaml_instance

            config = ConfigManager()
            processor = REQIFZFileProcessor(config)

            results = processor.process_directory(tmp_path, "llama3.1:8b")

        assert len(results) == 2
        for result in results:
            assert result["success"]




class TestHPProcessorIsolation:
    """Regression tests for per-file state isolation in the HP processor.

    process_file reassigns self.logger/self.extractor/self.formatter and
    mutates self.metrics, so files must not be processed concurrently on one
    instance, and metrics must be reset between files.
    """

    @pytest.mark.asyncio
    async def test_process_directory_runs_files_sequentially(self, tmp_path):
        """Two files in a directory must never be in flight at the same time."""
        config = ConfigManager()
        processor = HighPerformanceREQIFZFileProcessor(config)

        for i in range(2):
            (tmp_path / f"file_{i}.reqifz").write_bytes(b"")

        active = 0
        max_active = 0

        async def fake_process_file(*args, **kwargs):
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(0.02)
            active -= 1
            return {"success": True}

        with patch.object(
            HighPerformanceREQIFZFileProcessor, "process_file", side_effect=fake_process_file
        ):
            results = await processor.process_directory(tmp_path)

        assert len(results) == 2
        assert all(r["success"] for r in results)
        assert max_active == 1  # shared per-file state forbids overlap

    def test_metrics_reset_between_files(self):
        """Counters from a previous file must not leak into the next one."""
        config = ConfigManager()
        processor = HighPerformanceREQIFZFileProcessor(config)

        processor.metrics["successful_requirements"] = 7
        processor.metrics["ai_calls_made"] = 12
        processor.metrics["cpu_usage_samples"].append(55.0)

        processor._reset_metrics()

        assert processor.metrics["successful_requirements"] == 0
        assert processor.metrics["ai_calls_made"] == 0
        assert processor.metrics["cpu_usage_samples"] == []


class TestHighPerformanceREQIFZFileProcessor:
    """Integration tests for high-performance processor."""

    @pytest.mark.asyncio
    @patch('processors.hp_processor.HighPerformanceREQIFArtifactExtractor')
    @patch('processors.hp_processor.AsyncTestCaseGenerator')
    @patch('processors.hp_processor.StreamingTestCaseFormatter')
    @patch('processors.hp_processor.AsyncOllamaClient')
    async def test_process_file_success(
        self,
        MockClient,
        MockFormatter,
        MockGenerator,
        MockExtractor,
        tmp_path,
    ):
        """Test successful async file processing."""
        # Setup extractor mock with XHTML-formatted artifacts
        mock_extractor = MockExtractor.return_value
        mock_extractor.extract_reqifz_content.return_value = [
            create_test_heading("HP Test Section"),
            create_test_requirement("HP requirement 1", requirement_id="REQ_001"),
            create_test_requirement("HP requirement 2", requirement_id="REQ_002"),
        ]
        mock_extractor.classify_artifacts.return_value = {"System Interface": []}

        # Async context-manager for OllamaClient
        mock_client_instance = MagicMock()
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        # Generator mock — generate_test_cases is an async method
        mock_generator_instance = MagicMock()
        MockGenerator.return_value = mock_generator_instance
        mock_generator_instance.generate_test_cases = AsyncMock(
            side_effect=[
                [{"test_id": "TC_001", "summary": "Test case 1"}],
                [{"test_id": "TC_002", "summary": "Test case 2"}],
            ]
        )

        mock_formatter = MockFormatter.return_value
        mock_formatter.format_to_excel_streaming.return_value = True

        config = ConfigManager()
        processor = HighPerformanceREQIFZFileProcessor(config)

        result = await processor.process_file(
            Path("/test/file.reqifz"),
            model="llama3.1:8b",
            output_dir=tmp_path,
        )

        assert result["success"] is True
        assert result["total_test_cases"] == 2
        assert result["requirements_processed"] == 2

    @pytest.mark.asyncio
    @patch('processors.hp_processor.HighPerformanceREQIFArtifactExtractor')
    @patch('processors.hp_processor.AsyncTestCaseGenerator')
    @patch('processors.hp_processor.AsyncOllamaClient')
    async def test_process_file_no_test_cases_generated(
        self,
        MockClient,
        MockGenerator,
        MockExtractor,
        tmp_path,
    ):
        """Test HP processor returns failure when generator produces no test cases."""
        mock_extractor = MockExtractor.return_value
        mock_extractor.extract_reqifz_content.return_value = [
            create_test_requirement("Sample requirement", requirement_id="REQ_001"),
        ]
        mock_extractor.classify_artifacts.return_value = {"System Interface": []}

        mock_client_instance = MagicMock()
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_generator_instance = MagicMock()
        MockGenerator.return_value = mock_generator_instance
        # Generator returns an empty list — no test cases produced
        mock_generator_instance.generate_test_cases = AsyncMock(return_value=[])

        config = ConfigManager()
        processor = HighPerformanceREQIFZFileProcessor(config)

        result = await processor.process_file(
            Path("/test/file.reqifz"),
            model="llama3.1:8b",
            output_dir=tmp_path,
        )

        assert not result["success"]
        assert "No test cases were generated" in result["error"]

    @pytest.mark.asyncio
    @patch('processors.hp_processor.HighPerformanceREQIFArtifactExtractor')
    @patch('processors.hp_processor.AsyncTestCaseGenerator')
    @patch('processors.hp_processor.AsyncOllamaClient')
    async def test_process_file_with_generator_exception(
        self,
        MockClient,
        MockGenerator,
        MockExtractor,
        tmp_path,
    ):
        """Test HP processor returns failure when generator raises an exception."""
        mock_extractor = MockExtractor.return_value
        mock_extractor.extract_reqifz_content.return_value = [
            create_test_requirement("Sample requirement", requirement_id="REQ_001"),
        ]
        mock_extractor.classify_artifacts.return_value = {"System Interface": []}

        mock_client_instance = MagicMock()
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_generator_instance = MagicMock()
        MockGenerator.return_value = mock_generator_instance
        # Generator raises so the TaskGroup propagates an error
        mock_generator_instance.generate_test_cases = AsyncMock(
            side_effect=RuntimeError("Simulated generation failure")
        )

        config = ConfigManager()
        processor = HighPerformanceREQIFZFileProcessor(config)

        result = await processor.process_file(
            Path("/test/file.reqifz"),
            model="llama3.1:8b",
            output_dir=tmp_path,
        )

        assert not result["success"]

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, tmp_path):
        """Test that performance monitoring works."""
        config = ConfigManager()
        processor = HighPerformanceREQIFZFileProcessor(config)

        # Start monitoring
        monitor_task = asyncio.create_task(processor._monitor_performance())

        # The monitor samples non-blockingly every 0.5s (a blocking
        # cpu_percent(interval=0.1) call previously stalled the event loop),
        # so wait for at least one sampling cycle
        await asyncio.sleep(0.6)

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
            "memory_usage_samples": [40.0, 45.0, 50.0],
        }

        summary = processor._get_performance_summary()

        # Pass-through counts
        assert summary["total_ai_calls"] == 50
        assert summary["successful_requirements"] == 45
        assert summary["total_requirements"] == 50
        # Derived rates and aggregates
        assert summary["success_rate"] == 90.0  # 45 / 50 * 100
        assert summary["avg_cpu_percent"] == 60.0  # mean(50, 60, 70)
        assert summary["peak_cpu_percent"] == 70.0
        assert summary["avg_memory_mb"] == 45.0  # mean(40, 45, 50)
        assert summary["peak_memory_mb"] == 50.0
        assert summary["max_concurrent"] == processor.max_concurrent_requirements


class TestPartialCompletionReporting:
    """Partial generation failures must be visible in processor results
    (review 2026-07-17 finding 1).
    """

    @staticmethod
    def _make_extractor_mock(mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor.extract_reqifz_content.return_value = [
            create_test_requirement("The door shall lock", requirement_id="REQ_001"),
            create_test_requirement("The door shall unlock", requirement_id="REQ_002"),
        ]
        mock_extractor.classify_artifacts.return_value = {}
        mock_extractor_class.return_value = mock_extractor
        return mock_extractor

    @staticmethod
    def _make_formatter_mock(mock_formatter_class, tmp_path):
        mock_formatter = Mock()

        def mock_format(*args, **kwargs):
            out_dir = kwargs.get("output_dir") or tmp_path
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "test_output.xlsx").touch()
            return True

        mock_formatter.format_to_excel.side_effect = mock_format
        mock_formatter_class.return_value = mock_formatter
        return mock_formatter

    @patch("processors.standard_processor.REQIFArtifactExtractor")
    @patch("processors.standard_processor.TestCaseGenerator")
    @patch("processors.standard_processor.TestCaseFormatter")
    def test_process_file_reports_partial_failure(
        self,
        mock_formatter_class,
        mock_generator_class,
        mock_extractor_class,
        temp_reqifz_file,
        tmp_path,
    ):
        """One failed requirement out of two: success, but marked partial."""
        self._make_extractor_mock(mock_extractor_class)
        self._make_formatter_mock(mock_formatter_class, tmp_path)

        mock_generator = Mock()
        mock_generator.generate_test_cases_for_requirement.side_effect = [
            [{"summary_suffix": "locks", "requirement_id": "REQ_001"}],
            {
                "error": True,
                "requirement_id": "REQ_002",
                "error_type": "OllamaConnectionError",
                "error_message": "connection refused",
                "test_cases": [],
            },
        ]
        mock_generator_class.return_value = mock_generator

        processor = REQIFZFileProcessor(ConfigManager())
        result = processor.process_file(
            temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path
        )

        assert result["success"] is True
        assert result["partial"] is True
        assert len(result["failed_requirements"]) == 1
        assert result["failed_requirements"][0]["requirement_id"] == "REQ_002"
        assert result["failed_requirements"][0]["error_type"] == "OllamaConnectionError"

    @patch("processors.standard_processor.REQIFArtifactExtractor")
    @patch("processors.standard_processor.TestCaseGenerator")
    @patch("processors.standard_processor.TestCaseFormatter")
    def test_process_file_all_succeeded_is_not_partial(
        self,
        mock_formatter_class,
        mock_generator_class,
        mock_extractor_class,
        temp_reqifz_file,
        tmp_path,
    ):
        """No failures: partial must be False and failed_requirements empty."""
        self._make_extractor_mock(mock_extractor_class)
        self._make_formatter_mock(mock_formatter_class, tmp_path)

        mock_generator = Mock()
        mock_generator.generate_test_cases_for_requirement.return_value = [
            {"summary_suffix": "works", "requirement_id": "REQ"}
        ]
        mock_generator_class.return_value = mock_generator

        processor = REQIFZFileProcessor(ConfigManager())
        result = processor.process_file(
            temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path
        )

        assert result["success"] is True
        assert result["partial"] is False
        assert result["failed_requirements"] == []

    @patch("processors.standard_processor.REQIFArtifactExtractor")
    @patch("processors.standard_processor.TestCaseGenerator")
    @patch("processors.standard_processor.TestCaseFormatter")
    def test_process_file_all_failed_is_error(
        self,
        mock_formatter_class,
        mock_generator_class,
        mock_extractor_class,
        temp_reqifz_file,
        tmp_path,
    ):
        """Every requirement failing must produce an unsuccessful result."""
        self._make_extractor_mock(mock_extractor_class)
        self._make_formatter_mock(mock_formatter_class, tmp_path)

        mock_generator = Mock()
        mock_generator.generate_test_cases_for_requirement.return_value = {
            "error": True,
            "requirement_id": "REQ_001",
            "error_type": "OllamaConnectionError",
            "error_message": "connection refused",
            "test_cases": [],
        }
        mock_generator_class.return_value = mock_generator

        processor = REQIFZFileProcessor(ConfigManager())
        result = processor.process_file(
            temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path
        )

        assert result["success"] is False
        assert len(result["failed_requirements"]) == 2
