"""
Unit tests for RAFT Data Collector

Tests cover positive, negative, and corner cases to ensure RAFT collection
works correctly without affecting core logic.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock
from training.raft_collector import RAFTDataCollector


class TestRAFTDataCollector:
    """Test suite for RAFT Data Collector"""

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory for tests"""
        return tmp_path / "raft_collected"

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger"""
        return Mock()

    @pytest.fixture
    def sample_requirement(self):
        """Sample augmented requirement with context"""
        return {
            "id": "REQ_TEST_001",
            "text": "Test requirement for door lock system",
            "heading": "Door Control System",
            "info_list": [
                {"id": "INFO_001", "text": "CAN-based signal communication"},
                {"id": "INFO_002", "text": "Voltage range 9-16V"}
            ],
            "interface_list": [
                {"id": "IF_BCM_001", "text": "Body Control Module interface"}
            ]
        }

    @pytest.fixture
    def sample_test_cases(self):
        """Sample generated test cases"""
        return """Test Case 1: Verify door lock at 12V
Action: Apply 12V and send lock command
Data: Voltage=12V, Signal=LOCK
Expected: Door locks within 500ms

Test Case 2: Verify door unlock at low voltage
Action: Apply 9V and send unlock command
Data: Voltage=9V, Signal=UNLOCK
Expected: Door unlocks despite low voltage"""

    # ===== POSITIVE TESTS =====

    def test_collector_initialization_enabled(self, temp_output_dir, mock_logger):
        """Test RAFT collector initializes correctly when enabled"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        assert collector.enabled is True
        assert collector.output_dir == temp_output_dir
        assert temp_output_dir.exists()
        assert collector.logger == mock_logger

    def test_collect_example_success(self, temp_output_dir, mock_logger, sample_requirement, sample_test_cases):
        """Test successful RAFT example collection"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        output_path = collector.collect_example(
            requirement=sample_requirement,
            generated_test_cases=sample_test_cases,
            model="llama3.1:8b"
        )

        # Verify file was created
        assert output_path is not None
        assert output_path.exists()
        assert output_path.suffix == ".json"
        assert "raft_REQ_TEST_001" in output_path.name

        # Verify file content
        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["requirement_id"] == "REQ_TEST_001"
        assert data["requirement_text"] == sample_requirement["text"]
        assert data["heading"] == "Door Control System"
        assert len(data["retrieved_context"]["info_artifacts"]) == 2
        assert len(data["retrieved_context"]["interfaces"]) == 1
        assert data["generated_test_cases"] == sample_test_cases
        assert data["model_used"] == "llama3.1:8b"
        assert data["validation_status"] == "pending"
        assert data["context_annotation"]["oracle_context"] == []
        assert data["context_annotation"]["distractor_context"] == []

    def test_get_collection_stats_with_data(self, temp_output_dir, mock_logger, sample_requirement, sample_test_cases):
        """Test collection statistics retrieval with data"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        # Collect multiple examples
        for i in range(5):
            req = sample_requirement.copy()
            req["id"] = f"REQ_TEST_{i:03d}"
            collector.collect_example(req, sample_test_cases, "llama3.1:8b")

        stats = collector.get_collection_stats()

        assert stats["total_collected"] == 5
        assert stats["pending_annotation"] == 5
        assert stats["validated"] == 0
        assert stats["rejected"] == 0
        assert stats["annotated"] == 0

    def test_clear_collected_data(self, temp_output_dir, mock_logger, sample_requirement, sample_test_cases):
        """Test clearing collected data"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        # Collect examples
        collector.collect_example(sample_requirement, sample_test_cases, "llama3.1:8b")
        collector.collect_example(sample_requirement, sample_test_cases, "llama3.1:8b")

        # Verify exists
        stats_before = collector.get_collection_stats()
        assert stats_before["total_collected"] == 2

        # Clear
        count = collector.clear_collected_data()
        assert count == 2

        # Verify cleared
        stats_after = collector.get_collection_stats()
        assert stats_after["total_collected"] == 0

    # ===== NEGATIVE TESTS =====

    def test_collector_disabled_no_op(self, temp_output_dir, sample_requirement, sample_test_cases):
        """Test that disabled collector is a no-op"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=None,
            enabled=False
        )

        result = collector.collect_example(
            requirement=sample_requirement,
            generated_test_cases=sample_test_cases,
            model="llama3.1:8b"
        )

        # Should return None and not create files
        assert result is None
        assert not temp_output_dir.exists()

    def test_empty_requirement(self, temp_output_dir, mock_logger):
        """Test collection with empty requirement"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        empty_req = {}
        output_path = collector.collect_example(
            requirement=empty_req,
            generated_test_cases="Some test cases",
            model="llama3.1:8b"
        )

        assert output_path is not None
        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        # Should use defaults
        assert data["requirement_id"] == "UNKNOWN"
        assert data["requirement_text"] == ""
        assert data["heading"] == "No Heading"

    def test_missing_context_fields(self, temp_output_dir, mock_logger):
        """Test collection with missing context fields"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        req_no_context = {
            "id": "REQ_NO_CONTEXT",
            "text": "Requirement without context"
            # No heading, info_list, or interface_list
        }

        output_path = collector.collect_example(
            requirement=req_no_context,
            generated_test_cases="Test cases",
            model="llama3.1:8b"
        )

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["heading"] == "No Heading"
        assert data["retrieved_context"]["info_artifacts"] == []
        assert data["retrieved_context"]["interfaces"] == []

    def test_get_stats_no_directory(self, temp_output_dir):
        """Test getting stats when directory doesn't exist"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir / "nonexistent",
            logger=None,
            enabled=True
        )

        # Delete the directory that was created during init
        if (temp_output_dir / "nonexistent").exists():
            (temp_output_dir / "nonexistent").rmdir()

        stats = collector.get_collection_stats()

        assert stats["total_collected"] == 0
        assert stats["pending_annotation"] == 0

    def test_clear_data_when_disabled(self, temp_output_dir):
        """Test clearing data when collector is disabled"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=None,
            enabled=False
        )

        count = collector.clear_collected_data()
        assert count == 0

    # ===== CORNER CASES =====

    def test_special_characters_in_requirement_id(self, temp_output_dir, mock_logger):
        """Test handling special characters in requirement ID"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        req = {
            "id": "REQ/TEST/001:SPECIAL",  # Contains / and :
            "text": "Test requirement",
            "heading": "Test"
        }

        output_path = collector.collect_example(
            requirement=req,
            generated_test_cases="Test cases",
            model="llama3.1:8b"
        )

        # Should sanitize special characters
        assert output_path is not None
        assert "/" not in output_path.name
        assert ":" not in output_path.name or output_path.name.count(":") <= 1  # timestamp may have :

    def test_very_long_test_cases(self, temp_output_dir, mock_logger, sample_requirement):
        """Test collection with very long test case string"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        # Create very long test cases (>10KB)
        long_test_cases = "Test case " * 2000

        output_path = collector.collect_example(
            requirement=sample_requirement,
            generated_test_cases=long_test_cases,
            model="llama3.1:8b"
        )

        assert output_path is not None
        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["generated_test_cases"] == long_test_cases

    def test_unicode_characters_in_context(self, temp_output_dir, mock_logger):
        """Test collection with Unicode characters"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        req = {
            "id": "REQ_UNICODE",
            "text": "Tür-Schließ-System 🔒",  # German + emoji
            "heading": "Vehicle Access Control 车辆访问控制",  # Chinese
            "info_list": [
                {"id": "INFO_001", "text": "Temperature: -40°C to +85°C"}
            ]
        }

        output_path = collector.collect_example(
            requirement=req,
            generated_test_cases="Test cases with émojis 🚗",
            model="llama3.1:8b"
        )

        assert output_path is not None

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "🔒" in data["requirement_text"]
        assert "车辆访问控制" in data["heading"]
        assert "🚗" in data["generated_test_cases"]

    def test_empty_info_and_interface_lists(self, temp_output_dir, mock_logger):
        """Test collection with empty context lists"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        req = {
            "id": "REQ_EMPTY_LISTS",
            "text": "Test requirement",
            "heading": "Test",
            "info_list": [],
            "interface_list": []
        }

        output_path = collector.collect_example(
            requirement=req,
            generated_test_cases="Test cases",
            model="llama3.1:8b"
        )

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["retrieved_context"]["info_artifacts"] == []
        assert data["retrieved_context"]["interfaces"] == []

    def test_annotated_example_in_stats(self, temp_output_dir, mock_logger, sample_requirement, sample_test_cases):
        """Test that annotated examples are counted correctly in stats"""
        collector = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        # Collect and annotate an example
        output_path = collector.collect_example(
            requirement=sample_requirement,
            generated_test_cases=sample_test_cases,
            model="llama3.1:8b"
        )

        # Manually annotate it
        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        data["context_annotation"]["oracle_context"] = ["HEADING", "INFO_001"]
        data["context_annotation"]["distractor_context"] = ["INFO_002"]
        data["validation_status"] = "validated"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # Check stats
        stats = collector.get_collection_stats()

        assert stats["total_collected"] == 1
        assert stats["validated"] == 1
        assert stats["annotated"] == 1

    def test_multiple_collectors_same_directory(self, temp_output_dir, mock_logger, sample_requirement, sample_test_cases):
        """Test multiple collector instances using same directory"""
        collector1 = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        collector2 = RAFTDataCollector(
            output_dir=temp_output_dir,
            logger=mock_logger,
            enabled=True
        )

        # Both collect examples
        collector1.collect_example(sample_requirement, sample_test_cases, "llama3.1:8b")
        collector2.collect_example(sample_requirement, sample_test_cases, "deepseek-coder-v2:16b")

        # Both should see all examples
        stats1 = collector1.get_collection_stats()
        stats2 = collector2.get_collection_stats()

        assert stats1["total_collected"] == 2
        assert stats2["total_collected"] == 2
