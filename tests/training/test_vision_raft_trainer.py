"""Failure-path tests for VisionRAFTTrainer.train().

Regression coverage for review 2026-07-20 finding 3: a failed `ollama create`
must be recorded as `failed` (not `completed`), and its underlying error must
be surfaced in the top-level `result["errors"]` list the CLI printer reads.
"""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.training.vision_raft_trainer import VisionRAFTTrainer


@pytest.fixture
def dataset(tmp_path):
    """A minimal one-line RAFT JSONL dataset."""
    path = tmp_path / "raft.jsonl"
    path.write_text(
        json.dumps(
            {
                "messages": [
                    {"role": "system", "content": "sys"},
                    {"role": "user", "content": "Relevant Context: x"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _trainer(dataset, tmp_path):
    return VisionRAFTTrainer(dataset_path=dataset, output_dir=tmp_path / "models")


@patch("src.training.vision_raft_trainer.subprocess.run")
def test_nonzero_returncode_is_failed_with_error(mock_run, dataset, tmp_path):
    mock_run.return_value = MagicMock(returncode=1, stderr="simulated ollama failure")
    trainer = _trainer(dataset, tmp_path)

    result = trainer.train()

    assert result["success"] is False
    assert trainer.progress.status == "failed"
    assert result["errors"], "top-level errors must not be empty on failure"
    assert "simulated ollama failure" in result["errors"][0]


@patch("src.training.vision_raft_trainer.subprocess.run")
def test_timeout_is_failed_with_error(mock_run, dataset, tmp_path):
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="ollama", timeout=600)
    trainer = _trainer(dataset, tmp_path)

    result = trainer.train()

    assert result["success"] is False
    assert trainer.progress.status == "failed"
    assert result["errors"]
    assert "timed out" in result["errors"][0].lower()


@patch("src.training.vision_raft_trainer.subprocess.run")
def test_command_not_found_is_failed_with_error(mock_run, dataset, tmp_path):
    mock_run.side_effect = FileNotFoundError("ollama: command not found")
    trainer = _trainer(dataset, tmp_path)

    result = trainer.train()

    assert result["success"] is False
    assert trainer.progress.status == "failed"
    assert result["errors"]
    assert "command not found" in result["errors"][0]


@patch("src.training.vision_raft_trainer.subprocess.run")
def test_success_is_completed_without_errors(mock_run, dataset, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stderr="")
    trainer = _trainer(dataset, tmp_path)

    result = trainer.train()

    assert result["success"] is True
    assert trainer.progress.status == "completed"
    assert result["errors"] == []
    assert result["training_completed"] is not None
