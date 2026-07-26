"""Unit tests for the deterministic content scorer (Phase 3)."""

from src.core.deduplicator import TestCaseDeduplicator
from src.training.content_scorer import ReferenceOverlapScorer

CASE_A = {
    "summary_suffix": "door unlocks on valid keyfob",
    "preconditions": "ignition on; keyfob paired",
    "test_steps": "1. Press the unlock button.",
    "expected_result": "Door unlocks within 200 ms.",
    "test_type": "functional",
}
CASE_B = {
    "summary_suffix": "wipers follow rain intensity",
    "preconditions": "vehicle running; rain sensor enabled",
    "test_steps": "1. Simulate heavy rainfall.",
    "expected_result": "Wipers switch to maximum speed within 500 ms.",
    "test_type": "functional",
}


def test_deduplicator_similarity_is_public_and_symmetric():
    """Test that similarity method is public and returns expected values."""
    dedup = TestCaseDeduplicator()
    assert dedup.similarity(CASE_A, CASE_A) == 1.0
    assert dedup.similarity(CASE_A, CASE_B) < 0.5


def test_perfect_overlap_scores_one():
    """Test that perfect overlap scores 1.0 across all metrics."""
    scorer = ReferenceOverlapScorer()
    score = scorer.score([CASE_A, CASE_B], [CASE_A, CASE_B])
    assert score == {"precision": 1.0, "recall": 1.0, "f1": 1.0, "quality": None}


def test_disjoint_scores_zero():
    """Test that completely disjoint cases score 0.0."""
    scorer = ReferenceOverlapScorer()
    score = scorer.score([CASE_A], [CASE_B])
    assert score["precision"] == 0.0
    assert score["recall"] == 0.0
    assert score["f1"] == 0.0


def test_partial_overlap_precision_and_recall():
    """Test partial overlap: 2 generated (1 matches), 1 reference (matched)."""
    # P = 0.5 (1 match / 2 generated)
    # R = 1.0 (1 match / 1 reference)
    # F1 ≈ 0.667
    scorer = ReferenceOverlapScorer()
    score = scorer.score([CASE_A, CASE_B], [CASE_A])
    assert score["precision"] == 0.5
    assert score["recall"] == 1.0
    assert round(score["f1"], 3) == 0.667


def test_one_reference_matched_by_at_most_one_generated():
    """Test that a reference can only be matched by one generated case."""
    # Two identical generated cases; only one should count as a match
    scorer = ReferenceOverlapScorer()
    score = scorer.score([CASE_A, CASE_A], [CASE_A])
    assert score["recall"] == 1.0
    assert score["precision"] == 0.5  # only one of the two counts as a match


def test_no_reference_returns_none():
    """Test that scoring with no reference cases returns None."""
    scorer = ReferenceOverlapScorer()
    assert scorer.score([CASE_A], []) is None


def test_no_generated_gives_zero_recall_none_precision():
    """Test scoring with no generated cases."""
    scorer = ReferenceOverlapScorer()
    score = scorer.score([], [CASE_A])
    assert score == {"precision": None, "recall": 0.0, "f1": 0.0, "quality": None}


def test_overlap_scorer_emits_quality_none():
    """Test that overlap scorer emits quality: None."""
    scorer = ReferenceOverlapScorer()
    assert scorer.score([CASE_A], [CASE_A]) == {
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
        "quality": None,
    }


def test_overlap_scorer_ignores_widened_params():
    """Test that overlap scorer ignores client and judge_model params."""
    scorer = ReferenceOverlapScorer()
    baseline = scorer.score([CASE_A, CASE_B], [CASE_A])
    widened = scorer.score([CASE_A, CASE_B], [CASE_A], client=object(), judge_model="x")
    assert widened == baseline
