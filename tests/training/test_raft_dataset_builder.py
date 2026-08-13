"""
Unit tests for RAFT Dataset Builder

Tests cover positive, negative, and corner cases for RAFT dataset building.
"""

import copy
import json
from unittest.mock import Mock

import pytest

from training.raft_dataset_builder import RAFTDatasetBuilder


class TestRAFTDatasetBuilder:
    """Test suite for RAFT Dataset Builder"""

    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary directories for tests"""
        validated_dir = tmp_path / "validated"
        output_dir = tmp_path / "raft_dataset"
        validated_dir.mkdir()
        return validated_dir, output_dir

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger"""
        return Mock()

    @pytest.fixture
    def annotated_example(self):
        """Sample fully annotated RAFT example"""
        return {
            "requirement_id": "REQ_001",
            "requirement_text": "Door lock shall activate within 500ms",
            "heading": "Door Control System",
            "retrieved_context": {
                "heading": {"id": "HEADING", "text": "Door Control System"},
                "info_artifacts": [
                    {"id": "INFO_001", "text": "CAN-based signals"},
                    {"id": "INFO_002", "text": "Voltage 9-16V"},
                ],
                "interfaces": [{"id": "IF_BCM_001", "text": "Body Control Module"}],
            },
            "generated_test_cases": "Test Case 1: Verify lock at 12V...",
            "model_used": "llama3.1:8b",
            "context_annotation": {
                "oracle_context": ["HEADING", "INFO_001", "IF_BCM_001"],
                "distractor_context": ["INFO_002"],
                "annotation_notes": "Voltage info not relevant for lock timing",
                "quality_rating": 4,
            },
            "validation_status": "validated",
        }

    # ===== POSITIVE TESTS =====

    def test_builder_initialization(self, temp_dirs, mock_logger):
        """Test RAFT builder initializes correctly"""
        validated_dir, output_dir = temp_dirs

        builder = RAFTDatasetBuilder(
            validated_dir=validated_dir, output_dir=output_dir, logger=mock_logger
        )

        assert builder.validated_dir == validated_dir
        assert builder.output_dir == output_dir
        assert output_dir.exists()

    def test_build_dataset_success(self, temp_dirs, mock_logger, annotated_example):
        """Test successful RAFT dataset building"""
        validated_dir, output_dir = temp_dirs

        # Create annotated example file
        example_file = validated_dir / "raft_REQ_001.json"
        with open(example_file, "w", encoding="utf-8") as f:
            json.dump(annotated_example, f)

        builder = RAFTDatasetBuilder(
            validated_dir=validated_dir, output_dir=output_dir, logger=mock_logger
        )

        raft_examples = builder.build_dataset()

        assert len(raft_examples) == 1
        example = raft_examples[0]

        # Verify RAFT structure
        assert "question" in example
        assert "oracle_context" in example
        assert "distractor_context" in example
        assert "answer" in example
        assert "metadata" in example

        # Verify content
        assert "REQ_001" in example["question"]
        assert len(example["oracle_context"]) == 3
        assert len(example["distractor_context"]) == 1
        assert example["answer"] == annotated_example["generated_test_cases"]

    def test_save_dataset_jsonl_format(self, temp_dirs, mock_logger, annotated_example):
        """Test saving RAFT dataset in JSONL format"""
        validated_dir, output_dir = temp_dirs

        # Create annotated example
        example_file = validated_dir / "raft_REQ_001.json"
        with open(example_file, "w", encoding="utf-8") as f:
            json.dump(annotated_example, f)

        builder = RAFTDatasetBuilder(validated_dir, output_dir, mock_logger)
        raft_examples = builder.build_dataset()

        jsonl_path, json_path = builder.save_dataset(raft_examples)

        # Verify JSONL file
        assert jsonl_path.exists()
        assert jsonl_path.suffix == ".jsonl"

        with open(jsonl_path, encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1

            data = json.loads(lines[0])
            assert "messages" in data
            assert len(data["messages"]) == 3
            assert data["messages"][0]["role"] == "system"
            assert data["messages"][1]["role"] == "user"
            assert data["messages"][2]["role"] == "assistant"

        # Verify JSON file
        assert json_path.exists()
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 1

    def test_filter_by_quality(self, temp_dirs, mock_logger, annotated_example):
        """Test filtering examples by quality rating"""
        validated_dir, output_dir = temp_dirs

        # Create high and low quality examples
        high_quality = copy.deepcopy(annotated_example)
        high_quality["requirement_id"] = "REQ_HIGH"
        high_quality["context_annotation"]["quality_rating"] = 5

        low_quality = copy.deepcopy(annotated_example)
        low_quality["requirement_id"] = "REQ_LOW"
        low_quality["context_annotation"]["quality_rating"] = 2

        for i, example in enumerate([high_quality, low_quality]):
            file_path = validated_dir / f"raft_REQ_{i}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(example, f)

        builder = RAFTDatasetBuilder(validated_dir, output_dir, mock_logger)

        # Build with min_quality=3
        raft_examples = builder.build_dataset(min_quality=3)

        # Should only include high quality
        assert len(raft_examples) == 1
        assert "REQ_HIGH" in raft_examples[0]["question"]

    # ===== NEGATIVE TESTS =====

    def test_build_dataset_empty_directory(self, temp_dirs, mock_logger):
        """Test building dataset from empty directory"""
        validated_dir, output_dir = temp_dirs

        builder = RAFTDatasetBuilder(validated_dir, output_dir, mock_logger)
        raft_examples = builder.build_dataset()

        assert raft_examples == []

    def test_build_dataset_nonexistent_directory(self, tmp_path, mock_logger):
        """Test building dataset when validated directory doesn't exist"""
        builder = RAFTDatasetBuilder(
            validated_dir=tmp_path / "nonexistent",
            output_dir=tmp_path / "output",
            logger=mock_logger,
        )

        raft_examples = builder.build_dataset()
        assert raft_examples == []

    def test_skip_unannotated_examples(self, temp_dirs, mock_logger):
        """Test that unannotated examples are skipped"""
        validated_dir, output_dir = temp_dirs

        # Create example without oracle context
        unannotated = {
            "requirement_id": "REQ_UNANNOTATED",
            "requirement_text": "Test",
            "heading": "Test",
            "retrieved_context": {
                "heading": {"id": "HEADING", "text": "Test"},
                "info_artifacts": [],
                "interfaces": [],
            },
            "generated_test_cases": "Test cases",
            "context_annotation": {
                "oracle_context": [],  # Empty!
                "distractor_context": [],
                "quality_rating": 4,
            },
            "validation_status": "validated",
        }

        file_path = validated_dir / "raft_UNANNOTATED.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(unannotated, f)

        builder = RAFTDatasetBuilder(validated_dir, output_dir, mock_logger)
        raft_examples = builder.build_dataset()

        assert len(raft_examples) == 0

    def test_save_empty_dataset_raises_error(self, temp_dirs, mock_logger):
        """Test that saving empty dataset raises ValueError"""
        validated_dir, output_dir = temp_dirs

        builder = RAFTDatasetBuilder(validated_dir, output_dir, mock_logger)

        with pytest.raises(ValueError, match="No RAFT examples to save"):
            builder.save_dataset([])

    # ===== CORNER CASES =====

    def test_only_oracle_context_no_distractors(self, temp_dirs, mock_logger, annotated_example):
        """Test building dataset with only oracle context (no distractors)"""
        validated_dir, output_dir = temp_dirs

        # Remove distractors
        annotated_example["context_annotation"]["distractor_context"] = []

        file_path = validated_dir / "raft_REQ_001.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(annotated_example, f)

        builder = RAFTDatasetBuilder(validated_dir, output_dir, mock_logger)
        raft_examples = builder.build_dataset()

        assert len(raft_examples) == 1
        assert len(raft_examples[0]["oracle_context"]) > 0
        assert len(raft_examples[0]["distractor_context"]) == 0

    def test_mixed_annotated_and_unannotated(self, temp_dirs, mock_logger, annotated_example):
        """Test dataset building with mix of annotated and unannotated examples"""
        validated_dir, output_dir = temp_dirs

        # Create annotated example
        file1 = validated_dir / "raft_annotated.json"
        with open(file1, "w", encoding="utf-8") as f:
            json.dump(annotated_example, f)

        # Create unannotated example
        unannotated = annotated_example.copy()
        unannotated["context_annotation"]["oracle_context"] = []

        file2 = validated_dir / "raft_unannotated.json"
        with open(file2, "w", encoding="utf-8") as f:
            json.dump(unannotated, f)

        builder = RAFTDatasetBuilder(validated_dir, output_dir, mock_logger)
        raft_examples = builder.build_dataset()

        # Should only include annotated
        assert len(raft_examples) == 1

    def test_validate_dataset_format(self, temp_dirs, mock_logger, annotated_example):
        """Test dataset validation functionality"""
        validated_dir, output_dir = temp_dirs

        file_path = validated_dir / "raft_REQ_001.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(annotated_example, f)

        builder = RAFTDatasetBuilder(validated_dir, output_dir, mock_logger)
        raft_examples = builder.build_dataset()
        jsonl_path, _ = builder.save_dataset(raft_examples)

        # Validate the dataset
        validation_result = builder.validate_dataset(jsonl_path)

        assert validation_result["valid"] is True
        assert len(validation_result["issues"]) == 0
        assert validation_result["stats"]["total_examples"] == 1
        assert validation_result["stats"]["with_oracle_context"] == 1

    def test_unicode_in_context(self, temp_dirs, mock_logger, annotated_example):
        """Test handling Unicode characters in context"""
        validated_dir, output_dir = temp_dirs

        # Add Unicode to context
        annotated_example["retrieved_context"]["info_artifacts"][0]["text"] = (
            "Temperature: -40°C to +85°C 🌡️"
        )

        file_path = validated_dir / "raft_REQ_001.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(annotated_example, f, ensure_ascii=False)

        builder = RAFTDatasetBuilder(validated_dir, output_dir, mock_logger)
        raft_examples = builder.build_dataset()
        jsonl_path, _ = builder.save_dataset(raft_examples)

        # Verify Unicode preserved
        with open(jsonl_path, encoding="utf-8") as f:
            data = json.loads(f.readline())
            user_msg = data["messages"][1]["content"]
            assert "°C" in user_msg
            assert "🌡️" in user_msg

    def test_get_dataset_stats(self, temp_dirs, mock_logger, annotated_example):
        """Test getting dataset statistics"""
        validated_dir, output_dir = temp_dirs

        file_path = validated_dir / "raft_REQ_001.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(annotated_example, f)

        builder = RAFTDatasetBuilder(validated_dir, output_dir, mock_logger)
        raft_examples = builder.build_dataset()
        builder.save_dataset(raft_examples)

        stats = builder.get_dataset_stats()

        assert stats["jsonl_files"] == 1
        assert stats["json_files"] == 1
        assert stats["total_examples"] == 1
        assert stats["latest_dataset"] is not None


def _examples(n):
    """Build n *intermediate* RAFT examples, the shape ``build_dataset`` returns.

    ``save_split`` converts these to the evaluator's conversation contract on
    write, so the fixture must match ``_build_raft_example``'s output rather than
    the already-converted ``{"messages": [...]}`` shape.
    """
    return [
        {
            "question": f"Generate comprehensive test cases for requirement REQ_{i}",
            "oracle_context": [f"oracle doc {i}"],
            "distractor_context": [],
            "oracle_images": [],
            "distractor_images": [],
            "has_images": False,
            "answer": f"answer {i}",
            "metadata": {"requirement_id": f"REQ_{i}", "image_count": 0},
        }
        for i in range(n)
    ]


def test_split_is_deterministic_for_a_seed():
    builder = RAFTDatasetBuilder.__new__(RAFTDatasetBuilder)  # no __init__ side effects
    train_a, val_a = builder.split_dataset(_examples(10), val_ratio=0.2, seed=7)
    train_b, val_b = builder.split_dataset(_examples(10), val_ratio=0.2, seed=7)
    assert (train_a, val_a) == (train_b, val_b)
    assert len(val_a) == 2 and len(train_a) == 8


def test_split_keeps_at_least_one_val_and_one_train():
    builder = RAFTDatasetBuilder.__new__(RAFTDatasetBuilder)
    train, val = builder.split_dataset(_examples(2), val_ratio=0.01, seed=1)
    assert len(val) == 1 and len(train) == 1


def test_split_rejects_too_few_examples():
    builder = RAFTDatasetBuilder.__new__(RAFTDatasetBuilder)
    with pytest.raises(ValueError, match="at least 2"):
        builder.split_dataset(_examples(1))


def test_save_split_writes_two_jsonl_files(tmp_path):
    builder = RAFTDatasetBuilder.__new__(RAFTDatasetBuilder)
    train_path, val_path = builder.save_split(_examples(10), tmp_path, val_ratio=0.2, seed=7)
    assert train_path.name == "train.jsonl" and val_path.name == "val.jsonl"
    assert len(val_path.read_text().strip().splitlines()) == 2
    assert len(train_path.read_text().strip().splitlines()) == 8


def test_save_split_refuses_overwrite_without_force(tmp_path):
    builder = RAFTDatasetBuilder.__new__(RAFTDatasetBuilder)
    builder.save_split(_examples(10), tmp_path)
    with pytest.raises(FileExistsError):
        builder.save_split(_examples(10), tmp_path)
    # force overwrites cleanly
    builder.save_split(_examples(10), tmp_path, force=True)


def test_save_split_writes_the_evaluator_contract(tmp_path):
    """Both halves must be conversation-shaped, not raw intermediate rows."""
    builder = RAFTDatasetBuilder.__new__(RAFTDatasetBuilder)
    train_path, val_path = builder.save_split(_examples(10), tmp_path, val_ratio=0.2, seed=7)

    for path in (train_path, val_path):
        for line in path.read_text(encoding="utf-8").strip().splitlines():
            row = json.loads(line)
            assert "question" not in row, "intermediate RAFT fields must not be written"
            roles = [message["role"] for message in row["messages"]]
            assert roles == ["system", "user", "assistant"]


def test_split_val_file_loads_through_the_evaluator(tmp_path):
    """The advertised build -> split -> evaluate workflow must actually run.

    The prior split tests stopped at line counts, so nothing caught that
    ``val.jsonl`` was rejected by the evaluator's own loader
    (2026-07-26 review, Critical 1).
    """
    from training.vision_raft_trainer import VisionRAFTTrainer, VisionTrainingConfig

    builder = RAFTDatasetBuilder.__new__(RAFTDatasetBuilder)
    _, val_path = builder.save_split(_examples(10), tmp_path, val_ratio=0.2, seed=7)

    trainer = VisionRAFTTrainer(
        dataset_path=val_path,
        config=VisionTrainingConfig(),
        output_dir=tmp_path / "models",
    )
    loaded = trainer._load_and_validate_examples(val_path)

    assert len(loaded) == 2
    assert all(example["messages"][1]["role"] == "user" for example in loaded)
