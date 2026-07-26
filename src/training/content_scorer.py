"""Reference-aware content scoring for RAFT evaluation (Phase 3).

Scores a model's generated test cases against the held-out example's reference
answer by scenario precision/recall/F1. ``ReferenceOverlapScorer`` is the only
scorer; the ``ContentScorer`` protocol remains the seam for adding another.

An LLM-as-judge implementation existed here (Phase 3b) and was retired
2026-07-26 after calibration showed it returned a near-constant match list
regardless of input. See ``docs/training/README.md`` for the evidence.
"""

from typing import Protocol, TypedDict

from src.core.deduplicator import TestCaseDeduplicator


class ContentScore(TypedDict):
    """Per-example content scores; a field is None when undefined."""

    precision: float | None
    recall: float | None
    f1: float | None


def _prf(matched: int, n_generated: int, n_reference: int) -> tuple[float | None, float, float]:
    """Precision/recall/F1 from a match count (shared by both scorers).

    Args:
        matched: Generated cases matched to a distinct reference case.
        n_generated: Total generated cases.
        n_reference: Total reference cases (caller guarantees > 0).

    Returns:
        ``(precision, recall, f1)``; precision is None when ``n_generated`` is 0
        (0/0 undefined); recall/f1 are defined against the non-empty reference.
    """
    precision = None if n_generated == 0 else matched / n_generated
    recall = matched / n_reference
    p = 0.0 if precision is None else precision
    f1 = 0.0 if (p + recall) == 0 else 2 * p * recall / (p + recall)
    return precision, recall, f1


class ContentScorer(Protocol):
    """Scores generated test cases against reference cases.

    Implementations return None when scoring is impossible (e.g. no reference).
    """

    def score(
        self,
        generated_cases: list[dict],
        reference_cases: list[dict],
    ) -> ContentScore | None:
        """Return precision/recall/F1 for the generation, or None.

        Args:
            generated_cases: Canonical, deduplicated generated test cases.
            reference_cases: Canonical, deduplicated reference test cases.
        """
        ...


class ReferenceOverlapScorer:
    """Deterministic scenario precision/recall/F1 by test-case overlap.

    A generated case "matches" a reference case when their field similarity
    (the production ``TestCaseDeduplicator`` similarity over
    ``DEFAULT_FIELDS_TO_COMPARE``) is >= ``match_threshold``. Matching is greedy
    and one-to-one: each generated case takes its highest-similarity
    still-unmatched reference case at or above the threshold (ties broken by
    reference order), so it is deterministic and order-stable.
    """

    __slots__ = ("match_threshold", "_dedup")

    def __init__(self, match_threshold: float = 0.85) -> None:
        """Initialize the scorer.

        Args:
            match_threshold: Minimum field similarity for a match (0.0–1.0);
                defaults to the deduplicator's 0.85.
        """
        self.match_threshold = match_threshold
        self._dedup = TestCaseDeduplicator(similarity_threshold=match_threshold)

    def score(
        self,
        generated_cases: list[dict],
        reference_cases: list[dict],
    ) -> ContentScore | None:
        """Score generated cases against reference cases by string overlap.

        Args:
            generated_cases: Canonical, deduplicated generated test cases.
            reference_cases: Canonical, deduplicated reference test cases.

        Returns:
            A ``ContentScore``, or None when there are no reference cases.
        """
        if not reference_cases:
            return None
        if not generated_cases:
            return {"precision": None, "recall": 0.0, "f1": 0.0}

        matched = self._count_matches(generated_cases, reference_cases)
        precision, recall, f1 = _prf(matched, len(generated_cases), len(reference_cases))
        return {"precision": precision, "recall": recall, "f1": f1}

    def _count_matches(self, generated_cases: list[dict], reference_cases: list[dict]) -> int:
        """Count greedy one-to-one matches between generated and reference."""
        matched_ref: set[int] = set()
        count = 0
        for gen in generated_cases:
            best_j: int | None = None
            best_sim = -1.0
            for j, ref in enumerate(reference_cases):
                if j in matched_ref:
                    continue
                sim = self._dedup.similarity(gen, ref)
                if sim >= self.match_threshold and sim > best_sim:
                    best_sim = sim
                    best_j = j
            if best_j is not None:
                matched_ref.add(best_j)
                count += 1
        return count
