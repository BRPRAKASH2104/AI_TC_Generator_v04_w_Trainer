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
    """Per-example content scores; a field is None when undefined.

    ``matched_pairs`` exposes *which* generated case was matched to *which*
    reference case, as ``(generated_index, reference_index)`` sorted by generated
    index. Without it the metric counts pairs but never says which ones, so a
    scorer pairing the right number of wrong items is indistinguishable from a
    correct one (the ceiling recorded in CLAUDE.md).
    """

    precision: float | None
    recall: float | None
    f1: float | None
    matched_pairs: list[tuple[int, int]]


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
    ``DEFAULT_FIELDS_TO_COMPARE``) is >= ``match_threshold``.

    Matching is one-to-one and of **maximum cardinality** over the
    at-or-above-threshold graph. An earlier greedy rule let each generated case
    take its best still-unmatched reference in turn, which made the score depend
    on the order the model happened to list its cases — the same two cases scored
    F1 0.50 or 1.00 depending on their order (2026-07-26 review, Critical 3).
    Cardinality is the numerator of both precision and recall, so maximizing it
    fixes both at once, and it is invariant under permutation of either side.

    Note the matched *count* is permutation-invariant but the specific pairing
    need not be unique: where several optimal matchings exist, ties are broken by
    index order so the result stays deterministic run to run.
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
            return {"precision": None, "recall": 0.0, "f1": 0.0, "matched_pairs": []}

        matched_pairs = self._match_pairs(generated_cases, reference_cases)
        precision, recall, f1 = _prf(len(matched_pairs), len(generated_cases), len(reference_cases))
        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "matched_pairs": matched_pairs,
        }

    def _match_pairs(
        self, generated_cases: list[dict], reference_cases: list[dict]
    ) -> list[tuple[int, int]]:
        """Maximum-cardinality one-to-one matching, as (generated, reference) pairs.

        Kuhn's augmenting-path algorithm over the at-or-above-threshold
        bipartite graph. Kept dependency-free (no scipy) in line with the
        project's dependency-light, fully local constraints; the candidate sets
        here are single-digit, so the O(V*E) bound is irrelevant in practice.

        Args:
            generated_cases: Canonical, deduplicated generated test cases.
            reference_cases: Canonical, deduplicated reference test cases.

        Returns:
            Matched ``(generated_index, reference_index)`` pairs, sorted by
            generated index.
        """
        # Adjacency in reference-index order keeps tie-breaking deterministic.
        candidates: list[list[int]] = [
            [
                j
                for j, ref in enumerate(reference_cases)
                if self._dedup.similarity(gen, ref) >= self.match_threshold
            ]
            for gen in generated_cases
        ]

        # reference index -> generated index currently matched to it
        matched_to: dict[int, int] = {}

        def augment(gen_index: int, visited: set[int]) -> bool:
            """Try to match gen_index, displacing earlier matches if needed."""
            for ref_index in candidates[gen_index]:
                if ref_index in visited:
                    continue
                visited.add(ref_index)
                holder = matched_to.get(ref_index)
                if holder is None or augment(holder, visited):
                    matched_to[ref_index] = gen_index
                    return True
            return False

        for gen_index in range(len(generated_cases)):
            augment(gen_index, set())

        return sorted((gen, ref) for ref, gen in matched_to.items())
