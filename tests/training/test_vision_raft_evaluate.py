"""Characterization test pinning ``VisionRAFTTrainer.evaluate_model`` behavior.

``evaluate_model`` is currently a **stub** (see the ``# TODO: Implement actual
evaluation`` in ``src/training/vision_raft_trainer.py``): it returns a
fixed-shape metrics dict with hardcoded ``0.0`` scores and does not run the
model. This test documents that honest contract so the stub cannot silently
start reporting fabricated non-zero scores, and so the intended structure is
locked in for whoever implements real evaluation later.

**When real evaluation is implemented, update this test** — the all-zero /
"not implemented" assertions are the pin, not the goal.
"""

import json

import pytest

from src.training.vision_raft_trainer import VisionRAFTTrainer, VisionTrainingConfig


@pytest.fixture
def trainer(tmp_path):
    dataset = tmp_path / "raft.jsonl"
    dataset.write_text(
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
    config = VisionTrainingConfig(output_model="pinned-eval-model")
    return VisionRAFTTrainer(
        dataset_path=dataset,
        config=config,
        output_dir=tmp_path / "models",
    )


def test_evaluate_model_returns_stub_shape(trainer):
    result = trainer.evaluate_model()

    assert set(result) == {"model", "evaluation_date", "test_dataset", "metrics", "errors"}
    assert result["model"] == "pinned-eval-model"
    assert result["errors"] == []
    # Default (no test_dataset) reports the validation-split label.
    assert result["test_dataset"] == "validation_split"


def test_evaluate_model_scores_are_stubbed_zero(trainer):
    # The stub reports 0.0 for every score — no real evaluation happens yet.
    metrics = trainer.evaluate_model()["metrics"]
    assert metrics == {
        "text_examples_score": 0.0,
        "vision_examples_score": 0.0,
        "overall_score": 0.0,
    }


def test_evaluate_model_records_provided_dataset_path(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    test_set.write_text("{}\n", encoding="utf-8")

    result = trainer.evaluate_model(test_dataset=test_set)
    assert result["test_dataset"] == str(test_set)


def test_evaluate_model_needs_no_ollama(trainer, monkeypatch):
    # The stub must not shell out to `ollama` — guard against a future edit that
    # wires evaluation in without updating this pinning test.
    import subprocess

    def _boom(*args, **kwargs):
        raise AssertionError("evaluate_model must not invoke a subprocess while stubbed")

    monkeypatch.setattr(subprocess, "run", _boom)
    result = trainer.evaluate_model()
    assert result["metrics"]["overall_score"] == 0.0
