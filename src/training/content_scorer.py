"""Reference-aware content scoring for RAFT evaluation (Phase 3).

Scores a model's generated test cases against the held-out example's reference
answer by scenario precision/recall/F1. ``ReferenceOverlapScorer`` is the
deterministic first scorer; the ``ContentScorer`` protocol is the seam for a
future LLM-as-judge (Phase 3b).
"""

from typing import Protocol, TypedDict

from src.core.deduplicator import TestCaseDeduplicator


class ContentScore(TypedDict):
    """Per-example content-quality scores; a field is None when undefined."""

    precision: float | None
    recall: float | None
    f1: float | None


class ContentScorer(Protocol):
    """Scores generated test cases against reference cases.

    Implementations return None when scoring is impossible (e.g. no reference).
    """

    def score(
        self, generated_cases: list[dict], reference_cases: list[dict]
    ) -> ContentScore | None:
        """Return precision/recall/F1 for the generation, or None."""
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
        self, generated_cases: list[dict], reference_cases: list[dict]
    ) -> ContentScore | None:
        """Score generated cases against reference cases.

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
        precision = matched / len(generated_cases)
        recall = matched / len(reference_cases)
        f1 = 0.0 if (precision + recall) == 0 else 2 * precision * recall / (precision + recall)
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
