import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from src.training_data_collector import (
    TrainingDataCollector, TrainingAwareFileProcessor, TrainingExample)


@pytest.fixture
def collector(tmp_path: Path) -> TrainingDataCollector:
    """Create a TrainingDataCollector with a temporary output directory."""
    return TrainingDataCollector(output_dir=str(tmp_path))

def test_collector_init(collector: TrainingDataCollector, tmp_path: Path):
    """Test the initialization of the TrainingDataCollector."""
    assert collector.output_dir == tmp_path
    assert (tmp_path / "collected").exists()
    assert (tmp_path / "validated").exists()
    assert (tmp_path / "rejected").exists()

def test_collect_example(collector: TrainingDataCollector, tmp_path: Path):
    """Test collecting a single training example."""
    with patch.object(collector, "_save_example") as mock_save:
        collector.collect_example(
            requirement_id="REQ-001",
            requirement_text="Test requirement",
            table_data="Test table",
            generated_output={"test_cases": []},
        )
        mock_save.assert_called_once()
        assert len(collector.examples) == 1
        assert collector.examples[0].requirement_id == "REQ-001"

def test_approve_example(collector: TrainingDataCollector, tmp_path: Path):
    """Test approving a training example."""
    collector.collect_example(
        requirement_id="REQ-001",
        requirement_text="Test requirement",
        table_data="Test table",
        generated_output={"test_cases": []},
    )
    with patch.object(collector, "_move_example") as mock_move:
        result = collector.approve_example("REQ-001")
        assert result is True
        assert collector.examples[0].validation_status == "approved"
        mock_move.assert_called_with(collector.examples[0], "validated")

def test_reject_example(collector: TrainingDataCollector, tmp_path: Path):
    """Test rejecting a training example."""
    collector.collect_example(
        requirement_id="REQ-001",
        requirement_text="Test requirement",
        table_data="Test table",
        generated_output={"test_cases": []},
    )
    with patch.object(collector, "_move_example") as mock_move:
        result = collector.reject_example("REQ-001", reason="Bad example")
        assert result is True
        assert collector.examples[0].validation_status == "rejected"
        mock_move.assert_called_with(collector.examples[0], "rejected")

def test_export_training_dataset(collector: TrainingDataCollector, tmp_path: Path):
    """Test exporting a training dataset."""
    # Create a dummy validated file
    validated_dir = tmp_path / "validated"
    validated_file = validated_dir / "REQ-001_test.json"
    with open(validated_file, "w") as f:
        json.dump(
            {
                "requirement_id": "REQ-001",
                "requirement_text": "Test requirement",
                "table_data": "Test table",
                "generated_output": {"test_cases": []},
                "correction": None,
            },
            f,
        )

    output_file = collector.export_training_dataset()
    assert Path(output_file).exists()
    with open(output_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["messages"][1]["content"] is not None

def test_get_collection_stats(collector: TrainingDataCollector):
    """Test getting collection statistics."""
    collector.collect_example(
        requirement_id="REQ-001",
        requirement_text="Test requirement",
        table_data="Test table",
        generated_output={"test_cases": []},
    )
    stats = collector.get_collection_stats()
    assert stats["total_collected"] == 1
    assert stats["pending_validation"] == 1

def test_training_aware_file_processor(tmp_path: Path):
    """Test the TrainingAwareFileProcessor integration."""
    processor = TrainingAwareFileProcessor(
        reqifz_file="test.reqifz",
        input_path=str(tmp_path),
        output_file=str(tmp_path / "output.xlsx"),
        collect_training_data=True,
    )
    with patch.object(processor.training_collector, "collect_example") as mock_collect:
        processor.log_test_case_generation(
            requirement_id="REQ-001",
            requirement_text="Test requirement",
            table_data="Test table",
            generated_output={"test_cases": [{}]},
            success=True,
        )
        mock_collect.assert_called_once()
