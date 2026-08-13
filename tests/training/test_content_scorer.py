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


# --- Critical 3: the score must not depend on the order cases are listed in ---
#
# The review's reproduction matrix, at threshold 0.85:
#
#              reference 0   reference 1
#   generated 0    0.90          0.90
#   generated 1    1.00          0.80
#
# Only generated 1 -> reference 0 clears the threshold on reference 0's side, so
# the single optimal matching is {(0, 1), (1, 0)} — deliberately NOT the identity
# permutation, or an identity-pairing bug would satisfy the assertion by accident.
_REVIEW_MATRIX = {(0, 0): 0.90, (0, 1): 0.90, (1, 0): 1.00, (1, 1): 0.80}


class _MatrixDeduplicator:
    """Stand-in returning a fixed similarity per (generated, reference) pair."""

    def __init__(self, matrix):
        self.matrix = matrix

    def similarity(self, generated, reference):
        return self.matrix[(generated["index"], reference["index"])]


def _matrix_scorer(matrix=None, threshold=0.85):
    """A scorer whose similarities come from a fixed matrix, not real text."""
    scorer = ReferenceOverlapScorer(match_threshold=threshold)
    scorer._dedup = _MatrixDeduplicator(_REVIEW_MATRIX if matrix is None else matrix)
    return scorer


def _cases(count):
    return [{"index": i} for i in range(count)]


def test_score_is_invariant_to_generated_order():
    """Reordering the same generated cases must not change the score."""
    generated, reference = _cases(2), _cases(2)

    forward = _matrix_scorer().score(generated, reference)
    reversed_score = _matrix_scorer().score(list(reversed(generated)), reference)

    # Greedy scored 0.50 forward and 1.00 reversed; both are 1.00 now.
    assert forward["f1"] == 1.0
    assert reversed_score["f1"] == forward["f1"]
    assert reversed_score["precision"] == forward["precision"]
    assert reversed_score["recall"] == forward["recall"]


def test_score_is_invariant_to_reference_order():
    """Reordering the reference cases must not change the score either."""
    generated, reference = _cases(2), _cases(2)
    # Transpose the reference axis so index 0 and 1 swap roles.
    swapped = {(g, 1 - r): sim for (g, r), sim in _REVIEW_MATRIX.items()}

    forward = _matrix_scorer().score(generated, reference)
    swapped_score = _matrix_scorer(swapped).score(generated, list(reversed(reference)))

    assert swapped_score["f1"] == forward["f1"]


def test_matched_pairs_identify_the_unique_optimal_matching():
    """The pairing itself must be right, not merely the right size.

    This fixture has exactly one maximum matching and it is not the identity
    permutation, so a scorer that pairs the correct *number* of wrong items
    fails here.
    """
    score = _matrix_scorer().score(_cases(2), _cases(2))

    assert score["matched_pairs"] == [(0, 1), (1, 0)]


def test_matched_pairs_are_one_to_one_on_both_sides():
    """Ambiguous fixtures: assert cardinality and distinctness, not identities."""
    # Every pair clears the threshold, so several optimal matchings exist.
    all_match = {(g, r): 1.0 for g in range(3) for r in range(3)}
    score = _matrix_scorer(all_match).score(_cases(3), _cases(3))

    pairs = score["matched_pairs"]
    assert len(pairs) == 3
    assert len({g for g, _ in pairs}) == 3
    assert len({r for _, r in pairs}) == 3


def test_matched_pairs_are_sorted_by_generated_index():
    score = _matrix_scorer().score(_cases(2), _cases(2))
    generated_indices = [g for g, _ in score["matched_pairs"]]
    assert generated_indices == sorted(generated_indices)


def test_perfect_overlap_scores_one():
    """Test that perfect overlap scores 1.0 across all metrics."""
    scorer = ReferenceOverlapScorer()
    score = scorer.score([CASE_A, CASE_B], [CASE_A, CASE_B])
    # Asserted per key rather than as a whole dict: exact-dict comparisons on
    # ContentScore have broken twice as the TypedDict gained and lost fields.
    assert score["precision"] == 1.0
    assert score["recall"] == 1.0
    assert score["f1"] == 1.0
    assert score["matched_pairs"] == [(0, 0), (1, 1)]


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
    # Per key, not whole-dict — see test_perfect_overlap_scores_one.
    assert score["precision"] is None
    assert score["recall"] == 0.0
    assert score["f1"] == 0.0
    assert score["matched_pairs"] == []
