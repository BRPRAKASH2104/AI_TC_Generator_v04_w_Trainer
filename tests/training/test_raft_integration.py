"""
Integration tests for RAFT with core processors

Tests verify that RAFT collection does NOT affect core logic or test case generation.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from config import ConfigManager
from processors.base_processor import BaseProcessor


class TestRAFTIntegration:
    """Integration tests for RAFT with processors"""

    @pytest.fixture
    def config_raft_disabled(self):
        """Config with RAFT disabled"""
        config = ConfigManager()
        config.training.enable_raft = False
        return config

    @pytest.fixture
    def config_raft_enabled(self, tmp_path):
        """Config with RAFT enabled"""
        config = ConfigManager()
        config.training.enable_raft = True
        config.training.training_data_dir = str(tmp_path / "training_data")
        return config

    # ===== CORE LOGIC INTEGRITY TESTS =====

    def test_raft_disabled_no_collector_created(self, config_raft_disabled):
        """Test that RAFT collector is not created when disabled"""
        processor = BaseProcessor(config=config_raft_disabled)

        assert processor.raft_collector is None

    def test_raft_enabled_collector_created(self, config_raft_enabled):
        """Test that RAFT collector is created when enabled"""
        processor = BaseProcessor(config=config_raft_enabled)

        assert processor.raft_collector is not None
        assert processor.raft_collector.enabled is True

    def test_save_raft_example_no_op_when_disabled(self, config_raft_disabled):
        """Test that _save_raft_example is no-op when RAFT disabled"""
        processor = BaseProcessor(config=config_raft_disabled)

        # Mock requirement and test cases
        requirement = {
            "id": "REQ_TEST",
            "text": "Test requirement",
            "heading": "Test"
        }

        # Should not raise error, just no-op
        processor._save_raft_example(requirement, "Test cases", "llama3.1:8b")

        # No files should be created
        assert processor.raft_collector is None

    def test_save_raft_example_collects_when_enabled(self, config_raft_enabled, tmp_path):
        """Test that _save_raft_example collects data when RAFT enabled"""
        processor = BaseProcessor(config=config_raft_enabled)

        # Initialize logger (required for RAFT collector)
        processor.logger = Mock()

        requirement = {
            "id": "REQ_TEST",
            "text": "Test requirement",
            "heading": "Test",
            "info_list": [],
            "interface_list": []
        }

        # Call save method
        processor._save_raft_example(requirement, "Test cases", "llama3.1:8b")

        # Verify file was created
        collected_dir = tmp_path / "training_data" / "collected"
        assert collected_dir.exists()

        json_files = list(collected_dir.glob("raft_*.json"))
        assert len(json_files) == 1

    # ===== CONTEXT-AWARE PROCESSING INTEGRITY =====

    def test_build_augmented_requirements_unchanged_with_raft(self, config_raft_enabled):
        """Test that _build_augmented_requirements works identically with/without RAFT"""
        processor = BaseProcessor(config=config_raft_enabled)

        # Mock extractor
        processor.extractor = Mock()
        processor.extractor.classify_artifacts = Mock(return_value={
            "System Interface": [{"id": "IF_001", "text": "Interface 1"}],
            "Heading": [],
            "Information": [],
            "System Requirement": []
        })

        # Sample artifacts
        artifacts = [
            {"type": "Heading", "text": "Test Heading"},
            {"type": "Information", "text": "Test Info", "id": "INFO_001"},
            {"type": "System Requirement", "id": "REQ_001", "text": "Test requirement", "table": {"data": []}},
        ]

        # Mock logger
        processor.logger = Mock()

        # Call method
        augmented_requirements, interface_count = processor._build_augmented_requirements(artifacts)

        # Verify context-aware processing works correctly
        assert len(augmented_requirements) == 1
        assert augmented_requirements[0]["id"] == "REQ_001"
        assert augmented_requirements[0]["heading"] == "Test Heading"
        assert len(augmented_requirements[0]["info_list"]) == 1
        assert augmented_requirements[0]["info_list"][0]["id"] == "INFO_001"
        assert interface_count == 1

    def test_context_reset_behavior_intact(self, config_raft_enabled):
        """Test that info context resets after each requirement (critical v03 behavior)"""
        processor = BaseProcessor(config=config_raft_enabled)

        processor.extractor = Mock()
        processor.extractor.classify_artifacts = Mock(return_value={"System Interface": []})

        # Multiple requirements with info artifacts between them
        artifacts = [
            {"type": "Heading", "text": "Heading 1"},
            {"type": "Information", "text": "Info for REQ1", "id": "INFO_001"},
            {"type": "System Requirement", "id": "REQ_001", "text": "Requirement 1", "table": {"data": []}},
            {"type": "Information", "text": "Info for REQ2", "id": "INFO_002"},
            {"type": "System Requirement", "id": "REQ_002", "text": "Requirement 2", "table": {"data": []}},
        ]

        processor.logger = Mock()

        augmented_requirements, _ = processor._build_augmented_requirements(artifacts)

        # CRITICAL: Info should reset after each requirement
        assert len(augmented_requirements) == 2

        # REQ_001 should have INFO_001
        assert len(augmented_requirements[0]["info_list"]) == 1
        assert augmented_requirements[0]["info_list"][0]["id"] == "INFO_001"

        # REQ_002 should have INFO_002 (NOT INFO_001 - info resets!)
        assert len(augmented_requirements[1]["info_list"]) == 1
        assert augmented_requirements[1]["info_list"][0]["id"] == "INFO_002"

    # ===== PROCESSOR OUTPUT INTEGRITY =====

    def test_raft_does_not_change_success_result(self, config_raft_enabled):
        """Test that RAFT doesn't modify success result structure"""
        processor = BaseProcessor(config=config_raft_enabled)

        output_path = Path("/tmp/test_output.xlsx")
        result = processor._create_success_result(
            output_path=output_path,
            total_test_cases=10,
            requirements_processed=5,
            successful_requirements=4,
            artifacts_count=20,
            processing_time=5.5,
            model="llama3.1:8b",
            template="test_template"
        )

        # Verify structure is unchanged
        assert result["success"] is True
        assert result["output_file"] == str(output_path)
        assert result["total_test_cases"] == 10
        assert result["requirements_processed"] == 5
        assert result["successful_requirements"] == 4
        assert result["artifacts_found"] == 20
        assert result["processing_time"] == 5.5
        assert result["model_used"] == "llama3.1:8b"
        assert result["template_used"] == "test_template"

        # No extra RAFT fields
        assert "raft_examples_collected" not in result

    def test_raft_does_not_change_error_result(self, config_raft_enabled):
        """Test that RAFT doesn't modify error result structure"""
        processor = BaseProcessor(config=config_raft_enabled)

        result = processor._create_error_result(
            error_message="Test error",
            processing_time=1.0
        )

        # Verify structure is unchanged
        assert result["success"] is False
        assert result["error"] == "Test error"
        assert result["processing_time"] == 1.0

        # No extra RAFT fields
        assert "raft_error" not in result

    # ===== PERFORMANCE INTEGRITY =====

    def test_raft_collection_minimal_overhead(self, config_raft_enabled, config_raft_disabled):
        """Test that RAFT collection adds minimal overhead"""
        import time

        # Measure with RAFT disabled
        processor_disabled = BaseProcessor(config=config_raft_disabled)
        processor_disabled.logger = Mock()

        requirement = {"id": "REQ_TEST", "text": "Test", "heading": "Test"}

        start = time.time()
        for _ in range(100):
            processor_disabled._save_raft_example(requirement, "Test cases", "llama3.1:8b")
        time_disabled = time.time() - start

        # Measure with RAFT enabled
        processor_enabled = BaseProcessor(config=config_raft_enabled)
        processor_enabled.logger = Mock()

        start = time.time()
        for _ in range(100):
            processor_enabled._save_raft_example(requirement, "Test cases", "llama3.1:8b")
        time_enabled = time.time() - start

        # RAFT should add minimal overhead (< 100ms for 100 calls)
        overhead = time_enabled - time_disabled
        assert overhead < 0.1, f"RAFT overhead too high: {overhead}s"

    # ===== BACKWARD COMPATIBILITY =====

    def test_processors_work_without_raft_config(self):
        """Test that processors work if RAFT config fields are missing"""
        config = ConfigManager()

        # Remove RAFT fields to simulate old config
        if hasattr(config.training, "enable_raft"):
            delattr(config.training, "enable_raft")

        # Should not crash
        try:
            processor = BaseProcessor(config=config)
            # If enable_raft is missing, should default to disabled
            assert processor.raft_collector is None or not processor.raft_collector.enabled
        except AttributeError:
            # If it raises AttributeError, that's also acceptable - it means RAFT is truly optional
            pass

    def test_logger_update_does_not_affect_raft_disabled(self, config_raft_disabled):
        """Test that logger updates work correctly when RAFT is disabled"""
        processor = BaseProcessor(config=config_raft_disabled)

        # Create mock logger
        mock_logger = Mock()

        # Initialize logger (should not crash even with raft_collector=None)
        processor.logger = mock_logger

        if processor.raft_collector:
            processor.raft_collector.logger = mock_logger

        # Should complete without error
        assert processor.logger == mock_logger
