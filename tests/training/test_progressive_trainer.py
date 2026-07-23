"""Unit tests for ``ProgressiveRAFTTrainer`` (curriculum assessment).

Coverage for review 2026-07-20 Recommended finding 10(b). ``progressive_trainer.py``
was at ~21%.

The module deliberately does NOT train a model (review 2026-07-17 finding 3): it
buckets a validated dataset into difficulty phases and computes a heuristic
readiness score that is "a static function of the dataset's own text." These
tests verify exactly that honest contract, including **dataset influence** (a
higher-quality dataset yields a higher readiness score) and the
insufficient-data failure path. No Ollama / subprocess is involved.
"""

import json

import pytest

from src.training.progressive_trainer import (
    CurriculumPhase,
    ProgressiveRAFTTrainer,
)


@pytest.fixture
def trainer(tmp_path):
    return ProgressiveRAFTTrainer(
        validated_dir=tmp_path / "validated",
        output_dir=tmp_path / "models",
    )


def _rich_example(req_id="R"):
    return {
        "requirement_id": req_id,
        "requirement_text": (
            "The vehicle ECU shall monitor brake pressure via CAN and must disable "
            "the ABS when it exceeds 12.5 bar, if the engine is running."
        ),
        "retrieved_context": {
            "heading": {"text": "Brake Control System"},
            "info_artifacts": [
                {"id": "I1", "text": "The brake ECU communicates over CAN with the ABS module."},
                {"id": "I2", "text": "Vehicle safety requires the engine torque to be limited."},
            ],
            "interfaces": [{"id": "IF1", "text": "CAN signal BrakePressure, range 0-20 bar"}],
        },
    }


def _simple_example(req_id="S"):
    return {
        "requirement_id": req_id,
        "requirement_text": "The system shall start.",
        "retrieved_context": {
            "heading": {"text": "Startup"},
            "info_artifacts": [{"id": "I1", "text": "Basic startup note."}],
        },
    }


def _poor_example(req_id="P"):
    return {"requirement_id": req_id, "requirement_text": "ok", "retrieved_context": {}}


def _write_validated(trainer, examples):
    trainer.validated_dir.mkdir(parents=True, exist_ok=True)
    for i, ex in enumerate(examples):
        (trainer.validated_dir / f"raft_{i:03d}_annotated.json").write_text(json.dumps(ex))


# ---------------------------------------------------------------------------
# Construction / curriculum definition
# ---------------------------------------------------------------------------


def test_init_creates_output_dir_and_curriculum(trainer):
    assert trainer.output_dir.exists()
    assert set(trainer.curriculum.keys()) == set(CurriculumPhase)


def test_define_curriculum_thresholds(trainer):
    foundation = trainer.curriculum[CurriculumPhase.FOUNDATION]
    advanced = trainer.curriculum[CurriculumPhase.ADVANCED]
    assert foundation.min_examples == 50
    assert advanced.min_examples == 150
    assert advanced.min_quality_score > foundation.min_quality_score


# ---------------------------------------------------------------------------
# Loading / organizing
# ---------------------------------------------------------------------------


def test_load_validated_examples_reads_annotated_only(trainer):
    _write_validated(trainer, [_rich_example("A"), _rich_example("B")])
    # A non-annotated file must be ignored (glob is *_annotated.json).
    (trainer.validated_dir / "raft_999.json").write_text(json.dumps(_rich_example("X")))

    loaded = trainer._load_validated_examples()
    assert len(loaded) == 2


def test_load_validated_examples_skips_corrupt(trainer):
    trainer.validated_dir.mkdir(parents=True, exist_ok=True)
    (trainer.validated_dir / "raft_000_annotated.json").write_text(json.dumps(_rich_example()))
    (trainer.validated_dir / "raft_001_annotated.json").write_text("{ broken")
    assert len(trainer._load_validated_examples()) == 1


def test_organize_examples_preserves_count_and_buckets_simple(trainer):
    examples = [_rich_example("R"), _simple_example("S"), _poor_example("P")]
    phases = trainer._organize_examples_by_phase(examples)

    total = sum(len(v) for v in phases.values())
    assert total == 3  # every example lands in exactly one phase
    # The trivially simple example belongs in FOUNDATION.
    foundation_ids = {e["requirement_id"] for e in phases[CurriculumPhase.FOUNDATION]}
    assert "S" in foundation_ids


# ---------------------------------------------------------------------------
# Heuristic scoring: dataset influence + honest contract
# ---------------------------------------------------------------------------


def test_simulate_phase_training_is_dataset_dependent(trainer):
    high = [_rich_example(f"R{i}") for i in range(5)]
    low = [_poor_example(f"P{i}") for i in range(5)]
    high_score = trainer._simulate_phase_training(CurriculumPhase.FOUNDATION, high)
    low_score = trainer._simulate_phase_training(CurriculumPhase.FOUNDATION, low)
    assert high_score > low_score
    assert 0.0 <= high_score <= 1.0
    assert 0.0 <= low_score <= 1.0


def test_simulate_phase_training_bonus_from_graduated_phases(trainer):
    examples = [_rich_example(f"R{i}") for i in range(3)]
    before = trainer._simulate_phase_training(CurriculumPhase.INTERMEDIATE, examples)
    trainer.progress.graduated_phases.append(CurriculumPhase.FOUNDATION)
    after = trainer._simulate_phase_training(CurriculumPhase.INTERMEDIATE, examples)
    assert after > before  # progressive-learning bonus applied


def test_train_phase_fails_on_insufficient_examples(trainer):
    result = trainer._train_phase(CurriculumPhase.FOUNDATION, [_rich_example()], "m")
    assert result["success"] is False
    assert any("Insufficient" in issue for issue in result["issues"])


def test_estimate_readiness_score_scales_with_graduation(trainer):
    assert trainer._estimate_readiness_score() == 0.0
    trainer.progress.graduated_phases = [CurriculumPhase.FOUNDATION, CurriculumPhase.INTERMEDIATE]
    assert trainer._estimate_readiness_score() == pytest.approx((2 / 3) * 0.9)


# ---------------------------------------------------------------------------
# End-to-end assessment run
# ---------------------------------------------------------------------------


def test_start_curriculum_training_no_examples(trainer):
    result = trainer.start_curriculum_training("run-1")
    assert result["model_name"] == "run-1"
    assert "No validated examples found" in result["issues_encountered"]
    assert result["final_readiness_score"] == 0.0


def test_start_curriculum_training_insufficient_stops_early(trainer):
    # A handful of examples is below every phase minimum -> foundation fails,
    # loop breaks, no phases completed, but the run does not crash.
    _write_validated(trainer, [_rich_example(f"R{i}") for i in range(3)])
    result = trainer.start_curriculum_training("run-2")
    assert result["phases_completed"] == []
    assert result["issues_encountered"]


# ---------------------------------------------------------------------------
# Progress persistence / status / recommendations
# ---------------------------------------------------------------------------


def test_progress_save_and_reload(trainer, tmp_path):
    trainer.progress.total_trained_examples = 7
    trainer.progress.graduated_phases = [CurriculumPhase.FOUNDATION]
    trainer._save_progress()
    assert (trainer.output_dir / "training_progress.json").exists()

    # A fresh trainer over the same output_dir restores the persisted count.
    reloaded = ProgressiveRAFTTrainer(
        validated_dir=trainer.validated_dir, output_dir=trainer.output_dir
    )
    assert reloaded.progress.total_trained_examples == 7


def test_get_training_recommendations_flags_sparse_dataset(trainer):
    _write_validated(trainer, [_rich_example()])
    recs = trainer.get_training_recommendations()
    assert any("more examples" in r for r in recs)


def test_get_curriculum_status_structure(trainer):
    _write_validated(trainer, [_rich_example(), _simple_example()])
    status = trainer.get_curriculum_status()
    assert status["total_examples"] == 2
    assert set(status["examples_per_phase"].keys()) == {p.value for p in CurriculumPhase}
    assert isinstance(status["recommendations"], list)
