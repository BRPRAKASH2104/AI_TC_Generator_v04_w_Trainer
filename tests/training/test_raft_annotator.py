"""Unit tests for the interactive ``RAFTAnnotator``.

Coverage for review 2026-07-20 Recommended finding 10(b). ``raft_annotator.py``
was at ~13%. The module is interactive (rich prompts), so these tests exercise:

* the pure builders and predicates (``_build_context_items_list``, ``_is_annotated``);
* the filesystem side effects (dir creation, unannotated discovery, save/reject,
  stats) against ``tmp_path``;
* the oracle-selection input parser with rich prompts patched, covering the
  all/none/skip/numeric/invalid branches.

No real terminal interaction and no Ollama are involved.
"""

import json
from unittest.mock import patch

import pytest

from src.training.raft_annotator import RAFTAnnotator


@pytest.fixture
def dirs(tmp_path):
    return {
        "collected_dir": tmp_path / "collected",
        "validated_dir": tmp_path / "validated",
        "rejected_dir": tmp_path / "rejected",
    }


@pytest.fixture
def annotator(dirs):
    dirs["collected_dir"].mkdir(parents=True, exist_ok=True)
    return RAFTAnnotator(**dirs)


def _example(req_id="REQ_001", annotated=False):
    ex = {
        "requirement_id": req_id,
        "requirement_text": "The ECU shall verify the brake signal.",
        "retrieved_context": {
            "heading": {"text": "Brake System"},
            "info_artifacts": [{"id": "INFO_1", "text": "Background info on braking."}],
            "interfaces": [{"id": "IF_1", "text": "CAN BrakePressure signal."}],
        },
    }
    if annotated:
        ex["context_annotation"] = {"oracle_context": ["IF_1"], "quality_rating": 4}
    return ex


# ---------------------------------------------------------------------------
# Construction / directory setup
# ---------------------------------------------------------------------------


def test_init_creates_output_directories(dirs):
    RAFTAnnotator(**dirs)
    assert dirs["validated_dir"].exists()
    assert dirs["rejected_dir"].exists()


# ---------------------------------------------------------------------------
# Pure builders / predicates
# ---------------------------------------------------------------------------


def test_build_context_items_list_reflects_context(annotator):
    items = annotator._build_context_items_list(_example()["retrieved_context"])
    ids = {item["id"] for item in items}
    assert ids == {"HEADING", "INFO_1", "IF_1"}
    types = {item["type"] for item in items}
    assert types == {"heading", "info", "interface"}


def test_build_context_items_list_empty_context(annotator):
    assert annotator._build_context_items_list({}) == []


def test_is_annotated(annotator):
    assert annotator._is_annotated(_example(annotated=True)) is True
    assert annotator._is_annotated(_example(annotated=False)) is False
    # oracle_context present but no rating -> not annotated.
    assert annotator._is_annotated({"context_annotation": {"oracle_context": []}}) is False


# ---------------------------------------------------------------------------
# Unannotated discovery / stats (filesystem)
# ---------------------------------------------------------------------------


def test_get_unannotated_files_filters_annotated(annotator, dirs):
    collected = dirs["collected_dir"]
    (collected / "raft_000.json").write_text(json.dumps(_example("A", annotated=False)))
    (collected / "raft_001.json").write_text(json.dumps(_example("B", annotated=True)))
    (collected / "raft_002.json").write_text(json.dumps(_example("C", annotated=False)))

    pending = annotator._get_unannotated_files()
    names = {p.name for p in pending}
    assert names == {"raft_000.json", "raft_002.json"}


def test_get_unannotated_files_skips_corrupt(annotator, dirs):
    collected = dirs["collected_dir"]
    (collected / "raft_000.json").write_text(json.dumps(_example("A")))
    (collected / "raft_001.json").write_text("{ broken json")

    pending = annotator._get_unannotated_files()
    assert [p.name for p in pending] == ["raft_000.json"]


def test_get_unannotated_files_missing_collected_dir(dirs):
    # collected_dir intentionally not created.
    annotator = RAFTAnnotator(**dirs)
    assert annotator._get_unannotated_files() == []


def test_get_annotation_stats(annotator, dirs):
    (dirs["collected_dir"] / "raft_000.json").write_text("{}")
    (dirs["collected_dir"] / "raft_001.json").write_text("{}")
    (dirs["validated_dir"] / "raft_000_annotated.json").write_text("{}")
    (dirs["rejected_dir"] / "raft_001.json").write_text("{}")

    stats = annotator.get_annotation_stats()
    assert stats["total_collected"] == 2
    assert stats["annotated_and_validated"] == 1
    assert stats["rejected"] == 1
    assert stats["pending_annotation"] == 0


# ---------------------------------------------------------------------------
# Save / reject side effects
# ---------------------------------------------------------------------------


def test_save_validated_example_writes_annotated_file(annotator, dirs, tmp_path):
    original = tmp_path / "raft_042.json"
    example = _example("REQ_042")
    annotator._save_validated_example(example, original)

    out = dirs["validated_dir"] / "raft_042_annotated.json"
    assert out.exists()
    saved = json.loads(out.read_text())
    assert saved["requirement_id"] == "REQ_042"
    # A real ISO timestamp was stamped on save.
    assert saved["annotation_timestamp"] and saved["annotation_timestamp"] != "null"


def test_move_to_rejected_copies_file(annotator, dirs):
    collected = dirs["collected_dir"]
    src = collected / "raft_009.json"
    src.write_text(json.dumps(_example("REQ_009")))

    annotator._move_to_rejected(src)
    assert (dirs["rejected_dir"] / "raft_009.json").exists()
    # copy2, not move — original is retained for the audit trail.
    assert src.exists()


# ---------------------------------------------------------------------------
# annotate_examples happy-path early return
# ---------------------------------------------------------------------------


def test_annotate_examples_no_files(annotator):
    # collected dir exists but is empty -> clean early return, no prompts.
    annotator.annotate_examples()


# ---------------------------------------------------------------------------
# Oracle-selection input parser (rich prompts patched)
# ---------------------------------------------------------------------------


@pytest.fixture
def context_items(annotator):
    return annotator._build_context_items_list(_example()["retrieved_context"])


def test_oracle_selection_empty_items_returns_empty(annotator):
    assert annotator._get_user_oracle_selection([]) == []


def test_oracle_selection_all(annotator, context_items):
    with patch("src.training.raft_annotator.Prompt.ask", return_value="all"):
        result = annotator._get_user_oracle_selection(context_items)
    assert set(result) == {item["id"] for item in context_items}


def test_oracle_selection_none(annotator, context_items):
    with patch("src.training.raft_annotator.Prompt.ask", return_value="none"):
        assert annotator._get_user_oracle_selection(context_items) == []


def test_oracle_selection_skip_returns_none(annotator, context_items):
    with patch("src.training.raft_annotator.Prompt.ask", return_value="skip"):
        assert annotator._get_user_oracle_selection(context_items) is None


def test_oracle_selection_numeric_confirmed(annotator, context_items):
    with (
        patch("src.training.raft_annotator.Prompt.ask", return_value="1,3"),
        patch("src.training.raft_annotator.Confirm.ask", return_value=True),
    ):
        result = annotator._get_user_oracle_selection(context_items)
    assert result == [context_items[0]["id"], context_items[2]["id"]]


def test_oracle_selection_invalid_then_valid(annotator, context_items):
    # First an out-of-range number (re-prompts), then a valid 'none'.
    with patch("src.training.raft_annotator.Prompt.ask", side_effect=["99", "none"]):
        assert annotator._get_user_oracle_selection(context_items) == []


# ---------------------------------------------------------------------------
# Quality rating + render smoke + full single-example annotation
# ---------------------------------------------------------------------------


def test_get_quality_rating_and_notes(annotator):
    with (
        patch("src.training.raft_annotator.IntPrompt.ask", return_value=4),
        patch("src.training.raft_annotator.Prompt.ask", return_value="clear signal"),
    ):
        rating, notes = annotator._get_quality_rating_and_notes()
    assert rating == 4
    assert notes == "clear signal"


def test_render_helpers_do_not_raise(annotator, context_items):
    # These only print to the rich console; assert they run without error.
    annotator._display_context_table(context_items)
    annotator._show_annotation_help()


def test_annotate_single_example_happy_path(annotator, dirs, tmp_path):
    example = _example("REQ_ANN")
    file_path = tmp_path / "raft_ann.json"
    file_path.write_text(json.dumps(example))

    with (
        # oracle selection prompt returns "all"; notes prompt returns text.
        patch("src.training.raft_annotator.Prompt.ask", side_effect=["all", "looks good"]),
        patch("src.training.raft_annotator.IntPrompt.ask", return_value=5),
    ):
        completed = annotator._annotate_single_example(example, file_path)

    assert completed is True
    assert example["validation_status"] == "validated"
    assert example["context_annotation"]["oracle_context"]  # all items marked oracle
    assert example["context_annotation"]["quality_rating"] == 5
    # The validated artifact was written out.
    assert (dirs["validated_dir"] / "raft_ann_annotated.json").exists()


def test_annotate_single_example_skip_moves_to_rejected(annotator, dirs, tmp_path):
    example = _example("REQ_SKIP")
    file_path = dirs["collected_dir"] / "raft_skip.json"
    file_path.write_text(json.dumps(example))

    with patch("src.training.raft_annotator.Prompt.ask", return_value="skip"):
        completed = annotator._annotate_single_example(example, file_path)

    assert completed is False
    assert (dirs["rejected_dir"] / "raft_skip.json").exists()
