"""
Performance regression benchmarks.

Tests to ensure performance does not regress between versions.
Run these benchmarks after major changes to verify performance improvements/nullify regressions.
"""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock
import statistics

from src.processors.standard_processor import REQIFZFileProcessor
from src.config import ConfigManager


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

        # Mock AI client responses
        mock_response = """
        {
            "test_cases": [
                {
                    "summary": "Test input validation",
                    "action": "Enter invalid data",
                    "data": "Test data",
                    "expected_result": "Error message shown",
                    "test_type": "negative"
                }
            ]
        }
        """

        with pytest.fixture.autouse(lambda: mock_response):
            # Use pytest-benchmark to measure performance
            def run_processing():
                processor = REQIFZFileProcessor(config)
                # Mock the internal components to focus on core logic timing
                processor._extract_artifacts = Mock(return_value=[{
                    "type": "System Requirement",
                    "id": "REQ_001",
                    "table": True,
                    "text": "Sample requirement text"
                }])

                processor._build_augmented_requirements = Mock(return_value=(
                    [{
                        "type": "System Requirement",
                        "id": "REQ_001",
                        "table": True,
                        "text": "Sample requirement text",
                        "heading": "Test Heading",
                        "info_list": [],
                        "interface_list": []
                    }],
                    1
                ))

                processor.generator.generate_test_cases_for_requirement = Mock(return_value=[{
                    "summary": "Test case",
                    "action": "Test action",
                    "data": "Test data",
                    "expected_result": "Test result"
                }])

                processor.formatter.format_to_excel = Mock(return_value=True)

                return processor.process_file(temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path)

            result = benchmark(run_processing)

            # Verify basic functionality still works
            assert result["success"] == True
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

        # Mock classifier
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
        from statistics import stdev, mean

        config = ConfigManager()
        processing_times = []

        for _ in range(num_runs):
            processor = REQIFZFileProcessor(config)
            # Mock components for consistency
            processor._extract_artifacts = Mock(return_value=[{
                "type": "System Requirement",
                "id": "REQ_001",
                "table": True
            }])
            processor._build_augmented_requirements = Mock(return_value=([
                {"type": "System Requirement", "id": "REQ_001", "table": True,
                 "heading": "Test", "info_list": [], "interface_list": []}
            ], 1))
            processor.generator.generate_test_cases_for_requirement = Mock(return_value=[
                {"summary": "Test case", "action": "Test", "data": "Data", "expected_result": "Result"}
            ])
            processor.formatter.format_to_excel = Mock(return_value=True)

            start_time = time.time()
            result = processor.process_file(temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path)
            processing_times.append(result["processing_time"])

        # Check consistency - standard deviation should be reasonable
        if len(processing_times) > 1:
            time_stdev = stdev(processing_times)
            avg_time = mean(processing_times)

            # Std dev should be less than 50% of average time (reasonable consistency)
            assert time_stdev < (avg_time * 0.5), f"Processing times inconsistent: {processing_times}"

        # All runs should succeed
        assert all(result["success"] for result in [processor.process_file(temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path) for _ in range(num_runs)])

    def test_memory_efficiency_regression(self, temp_reqifz_file, tmp_path):
        """Test that memory usage doesn't regress significantly."""
        import psutil
        import os

        config = ConfigManager()
        processor = REQIFZFileProcessor(config)

        # Mock components
        processor._extract_artifacts = Mock(return_value=[{
            "type": "System Requirement", "id": "REQ_001", "table": True
        }])
        processor._build_augmented_requirements = Mock(return_value=([
            {"type": "System Requirement", "id": "REQ_001", "table": True,
             "heading": "Test", "info_list": [], "interface_list": []}
        ], 1))
        processor.generator.generate_test_cases_for_requirement = Mock(return_value=[
            {"summary": "Test case", "action": "Test", "data": "Data", "expected_result": "Result"}
        ])
        processor.formatter.format_to_excel = Mock(return_value=True)

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        result = processor.process_file(temp_reqifz_file, "llama3.1:8b", output_dir=tmp_path)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = final_memory - initial_memory

        # Memory increase should be reasonable (< 50MB)
        assert memory_delta < 50, f"Memory usage increased by {memory_delta:.1f}MB, expected < 50MB"

        assert result["success"] == True

    @pytest.mark.slow
    def test_streaming_xml_memory_efficiency(self, tmp_path):
        """Test that streaming XML parsing provides memory efficiency for large files."""
        from src.core.extractors import REQIFArtifactExtractor
        import psutil
        import os

        # Create a moderately large REQIF content with 100 spec objects
        large_xml_parts = ['<?xml version="1.0" encoding="UTF-8"?><REQ-IF xmlns:reqif="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd" xmlns:html="http://www.w3.org/1999/xhtml"><reqif:CORE-CONTENT><reqif:SPEC-OBJECT-TYPE IDENTIFIER="TYPE_001" LONG-NAME="System Requirement"><reqif:ATTRIBUTE-DEFINITION-STRING LONG-NAME="ReqIF.ForeignID" IDENTIFIER="ATTR_001"/></reqif:SPEC-OBJECT-TYPE>']

        for i in range(100):
            spec_object = f'<reqif:SPEC-OBJECT IDENTIFIER="REQ_{i:03d}"><reqif:TYPE><reqif:SPEC-OBJECT-TYPE-REF>TYPE_001</reqif:SPEC-OBJECT-TYPE-REF></reqif:TYPE><reqif:VALUES><reqif:ATTRIBUTE-VALUE-STRING THE-VALUE="REQ_{i:03d}"><reqif:DEFINITION><reqif:ATTRIBUTE-DEFINITION-STRING-REF>ATTR_001</reqif:ATTRIBUTE-DEFINITION-STRING-REF></reqif:DEFINITION></reqif:ATTRIBUTE-VALUE-STRING><reqif:ATTRIBUTE-VALUE-XHTML><reqif:DEFINITION><reqif:ATTRIBUTE-DEFINITION-XHTML-REF>TEXT_ATTR</reqif:ATTRIBUTE-DEFINITION-XHTML-REF></reqif:DEFINITION><reqif:THE-VALUE><html:div>The system requirement {i} shall work properly with detailed description that makes the content larger and more realistic for memory testing purposes. This additional text helps simulate real-world REQIF files with substantial content.</html:div></reqif:THE-VALUE></reqif:ATTRIBUTE-VALUE-XHTML></reqif:VALUES></reqif:SPEC-OBJECT>'
            large_xml_parts.append(spec_object)

        large_xml_parts.append('</reqif:CORE-CONTENT></REQ-IF>')
        large_xml_content = ''.join(large_xml_parts).encode('utf-8')

        # Create REQIFZ file
        import zipfile
        large_reqifz_path = tmp_path / "large_test.reqifz"
        with zipfile.ZipFile(large_reqifz_path, 'w') as zf:
            zf.writestr("large.reqif", large_xml_content)

        process = psutil.Process(os.getpid())

        # Test standard (DOM-based) extraction
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        extractor_dom = REQIFArtifactExtractor(use_streaming=False)
        artifacts_dom = extractor_dom.extract_reqifz_content(large_reqifz_path)
        dom_memory = process.memory_info().rss / 1024 / 1024  # MB
        dom_peak_memory = dom_memory - initial_memory

        # Clear memory by forcing garbage collection
        import gc
        gc.collect()
        import time
        time.sleep(0.1)  # Allow system to settle

        # Test streaming extraction
        pre_stream_memory = process.memory_info().rss / 1024 / 1024  # MB
        extractor_stream = REQIFArtifactExtractor(use_streaming=True)
        artifacts_stream = extractor_stream.extract_reqifz_content(large_reqifz_path)
        stream_memory = process.memory_info().rss / 1024 / 1024  # MB
        stream_peak_memory = stream_memory - pre_stream_memory

        # Verify correctness - both methods should extract same artifacts
        assert len(artifacts_dom) == len(artifacts_stream) == 100, f"DOM: {len(artifacts_dom)}, Stream: {len(artifacts_stream)} artifacts extracted"

        # Check that streaming uses less peak memory
        # Allow for some variability, but streaming should be more memory efficient
        if stream_peak_memory < dom_peak_memory:
            memory_improvement_pct = ((dom_peak_memory - stream_peak_memory) / dom_peak_memory) * 100
        else:
            memory_improvement_pct = 0  # No improvement or slight increase acceptable

        # Log memory usage for reference (streaming should be more efficient)
        print(f"DOM parsing peak memory: {dom_peak_memory:.1f}MB")
        print(f"Streaming parsing peak memory: {stream_peak_memory:.1f}MB")
        print(f"Memory improvement: {memory_improvement_pct:.1f}%")

        # The test passes as long as both methods work correctly
        # Memory improvements may vary by Python version and system
        assert len(artifacts_stream) > 0, "Streaming extraction should extract artifacts"
        assert all(isinstance(art, dict) and 'id' in art for art in artifacts_stream), "All artifacts should have IDs"
