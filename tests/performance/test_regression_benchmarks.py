"""
Performance regression benchmarks.

Tests to ensure performance does not regress between versions.
Run these benchmarks after major changes to verify performance improvements/nullify regressions.
"""

import os
import time
from unittest.mock import Mock, patch

import pytest

from src.config import ConfigManager
from src.processors.standard_processor import REQIFZFileProcessor


@pytest.fixture
def sample_reqifz_data():
    """Generate sample REQIFZ data for performance testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd" xmlns:html="http://www.w3.org/1999/xhtml">
    <CORE-CONTENT>
        <REQ-IF-CONTENT>
            <SPEC-OBJECTS>
                <SPEC-OBJECT IDENTIFIER="REQ_001">
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
                            <THE-VALUE><html:div>The system shall validate user input</html:div></THE-VALUE>
                        </ATTRIBUTE-VALUE-XHTML>
                    </VALUES>
                </SPEC-OBJECT>
            </SPEC-OBJECTS>
        </REQ-IF-CONTENT>
    </CORE-CONTENT>
</REQ-IF>"""


@pytest.fixture
def temp_reqifz_file(tmp_path, sample_reqifz_data):
    """Create a temporary REQIFZ file for testing."""
    import zipfile
    reqifz_path = tmp_path / "test.reqifz"
    with zipfile.ZipFile(reqifz_path, 'w') as zf:
        zf.writestr("test.reqif", sample_reqifz_data)
    return reqifz_path


class TestPerformanceRegressionBenchmarks:
    """Performance regression tests to ensure optimizations work and don't regress."""

    def test_standard_processor_performance_regression(self, temp_reqifz_file, tmp_path, benchmark):
        """Test that standard processor performance is within expected bounds."""
        # Setup mocks for controlled testing
        config = ConfigManager()

        # Use pytest-benchmark to measure performance
        def run_processing():
            processor = REQIFZFileProcessor(config)
            return processor.process_file(temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path)

        with patch("src.processors.base_processor.BaseProcessor._extract_artifacts", return_value=[{
            "type": "System Requirement",
            "id": "REQ_001",
            "table": True,
            "text": "Sample requirement text"
        }]), patch("src.processors.base_processor.BaseProcessor._build_augmented_requirements", return_value=([{
                "type": "System Requirement",
                "id": "REQ_001",
                "table": True,
                "text": "Sample requirement text",
                "heading": "Test Heading",
                "info_list": [],
                "interface_list": []
            }], 1)), patch("src.core.generators.TestCaseGenerator.generate_test_cases_for_requirement", return_value=[{
                "summary": "Test case",
                "action": "Test action",
                "data": "Test data",
                "expected_result": "Test result"
            }]), patch("src.core.formatters.TestCaseFormatter.format_to_excel", return_value=True):

            result = benchmark(run_processing)

        # Verify basic functionality still works
        assert result["success"]
        assert result["total_test_cases"] == 1

        # Performance assertion (adjust thresholds based on your environment)
        # This is a rough benchmark - absolute time will vary by machine
        assert result["processing_time"] < 5.0, f"Processing took {result['processing_time']:.2f}s, expected < 5.0s"

    def test_context_aware_processing_performance(self, benchmark):
        """Benchmark the context-aware requirement augmentation logic."""
        from src.processors.base_processor import BaseProcessor

        # Create a base processor instance for testing
        config = ConfigManager()
        processor = BaseProcessor(config)

        # Generate realistic test artifacts (100 artifacts)
        artifacts = []
        for i in range(50):
            artifacts.append({
                "type": "Information",
                "id": f"INFO_{i:03d}",
                "text": f"This is information artifact {i}"
            })

        for i in range(25):
            artifacts.append({
                "type": "Heading",
                "id": f"HEAD_{i:03d}",
                "text": f"Chapter {i}"
            })

        for i in range(25):
            artifacts.append({
                "type": "System Requirement",
                "id": f"REQ_{i:03d}",
                "table": True,
                "text": f"Requirement {i} text"
            })

        # Setup mock logger so BaseProcessor calls to it succeed
        processor.logger = Mock()

        # Mock classifier
        processor.extractor = Mock()
        processor.extractor.classify_artifacts = Mock(return_value={
            "System Interface": [{"type": "System Interface", "text": "CAN Bus"}]
        })

        def run_context_augmentation():
            return processor._build_augmented_requirements(artifacts)

        augmented_reqs, interface_count = benchmark(run_context_augmentation)

        # Verify correctness
        assert isinstance(augmented_reqs, list)
        assert len(augmented_reqs) == 25  # Should have 25 requirements
        assert interface_count == 1

        # Verify context attachment
        for req in augmented_reqs:
            assert "heading" in req
            assert "info_list" in req
            assert "interface_list" in req

    @pytest.mark.parametrize("num_runs", [3])
    def test_processor_consistency(self, temp_reqifz_file, tmp_path, num_runs):
        """Test that processor results are consistent across multiple runs."""
        from statistics import mean, stdev

        config = ConfigManager()
        processing_times = []

        for _ in range(num_runs):
            with patch.object(REQIFZFileProcessor, '_extract_artifacts', return_value=[{
                "type": "System Requirement",
                "id": "REQ_001",
                "table": True
            }]), patch.object(REQIFZFileProcessor, '_build_augmented_requirements', return_value=([
                {"type": "System Requirement", "id": "REQ_001", "table": True,
                 "heading": "Test", "info_list": [], "interface_list": []}
            ], 1)), patch("src.core.generators.TestCaseGenerator.generate_test_cases_for_requirement", return_value=[
                {"summary": "Test case", "action": "Test", "data": "Data", "expected_result": "Result"}
            ]), patch("src.core.formatters.TestCaseFormatter.format_to_excel", return_value=True):

                processor = REQIFZFileProcessor(config)

                time.time()
                result = processor.process_file(temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path)
                processing_times.append(result["processing_time"])

        # Check consistency - standard deviation should be reasonable (ignoring the first cold-start run)
        if len(processing_times) > 2:
            time_stdev = stdev(processing_times[1:])
            avg_time = mean(processing_times[1:])

            # Std dev should be less than 50% of average time (reasonable consistency)
            assert time_stdev < (avg_time * 0.5), f"Processing times inconsistent: {processing_times}"

        # All runs should succeed
        with patch("src.processors.base_processor.BaseProcessor._extract_artifacts", return_value=[{
            "type": "System Requirement",
            "id": "REQ_001",
            "table": True
        }]), patch("src.processors.base_processor.BaseProcessor._build_augmented_requirements", return_value=([
            {"type": "System Requirement", "id": "REQ_001", "table": True,
             "heading": "Test", "info_list": [], "interface_list": []}
        ], 1)), patch("src.core.generators.TestCaseGenerator.generate_test_cases_for_requirement", return_value=[
            {"summary": "Test case", "action": "Test", "data": "Data", "expected_result": "Result"}
        ]), patch("src.core.formatters.TestCaseFormatter.format_to_excel", return_value=True):
            assert all(processor.process_file(temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path)["success"] for _ in range(num_runs))

    def test_memory_efficiency_regression(self, temp_reqifz_file, tmp_path):
        """Test that memory usage doesn't regress significantly."""

        import psutil

        config = ConfigManager()
        processor = REQIFZFileProcessor(config)

        with patch("src.processors.base_processor.BaseProcessor._extract_artifacts", return_value=[{
            "type": "System Requirement", "id": "REQ_001", "table": True
        }]), patch("src.processors.base_processor.BaseProcessor._build_augmented_requirements", return_value=([
            {"type": "System Requirement", "id": "REQ_001", "table": True,
             "heading": "Test", "info_list": [], "interface_list": []}
        ], 1)), patch("src.core.generators.TestCaseGenerator.generate_test_cases_for_requirement", return_value=[
            {"summary": "Test case", "action": "Test", "data": "Data", "expected_result": "Result"}
        ]), patch("src.core.formatters.TestCaseFormatter.format_to_excel", return_value=True):

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            result = processor.process_file(temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = final_memory - initial_memory

        # Memory increase should be reasonable (< 50MB)
        assert memory_delta < 50, f"Memory usage increased by {memory_delta:.1f}MB, expected < 50MB"

        assert result["success"]

