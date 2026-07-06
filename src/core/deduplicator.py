"""
Test case deduplication module for the AI Test Case Generator.

This module provides functionality to detect and remove duplicate or highly similar
test cases using various similarity metrics and clustering algorithms.
"""

from difflib import SequenceMatcher
from typing import Any

# Type aliases for better readability
type TestCase = dict[str, Any]
type TestCaseList = list[TestCase]
type SimilarityScore = float
type DuplicateGroup = list[int]  # Indices of duplicate test cases

# The active prompt schema emits preconditions/test_steps while the legacy v03
# schema used action/data; test cases from either schema must deduplicate
# against each other, so each field resolves through its alias chain.
_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "test_steps": ("test_steps", "data"),
    "data": ("data", "test_steps"),
    "preconditions": ("preconditions", "action"),
    "action": ("action", "preconditions"),
}

DEFAULT_FIELDS_TO_COMPARE = ["test_steps", "expected_result", "preconditions"]


class TestCaseDeduplicator:
    """Detects and removes duplicate or highly similar test cases"""

    __slots__ = ("similarity_threshold", "logger", "fields_to_compare")

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        logger=None,
        fields_to_compare: list[str] | None = None,
    ):
        """
        Initialize test case deduplicator.

        Args:
            similarity_threshold: Similarity threshold (0.0-1.0) for considering test cases as duplicates
            logger: Optional logger instance
            fields_to_compare: Fields to compare for similarity
                (default: test_steps, expected_result, preconditions; legacy
                action/data names are resolved via aliases)
        """
        self.similarity_threshold = similarity_threshold
        self.logger = logger
        self.fields_to_compare = fields_to_compare or list(DEFAULT_FIELDS_TO_COMPARE)

    def deduplicate(
        self, test_cases: TestCaseList, keep_strategy: str = "first"
    ) -> tuple[TestCaseList, dict[str, Any]]:
        """
        Remove duplicate test cases from a list.

        Args:
            test_cases: List of test cases to deduplicate
            keep_strategy: Strategy for keeping duplicates ("first", "last", "best")

        Returns:
            Tuple of (deduplicated_test_cases, deduplication_report)
        """
        if not test_cases:
            return [], self._create_report(0, 0, [])

        # Find duplicate groups
        duplicate_groups = self._find_duplicates(test_cases)

        # Select which test cases to keep
        indices_to_remove = set()
        for group in duplicate_groups:
            indices_to_remove.update(
                self._select_duplicates_to_remove(group, test_cases, keep_strategy)
            )

        # Build deduplicated list
        deduplicated = [tc for i, tc in enumerate(test_cases) if i not in indices_to_remove]

        # Create report
        report = self._create_report(len(test_cases), len(deduplicated), duplicate_groups)

        if self.logger and len(duplicate_groups) > 0:
            self.logger.info(
                f"Deduplication: {len(test_cases)} → {len(deduplicated)} test cases "
                f"({len(duplicate_groups)} duplicate groups removed)"
            )

        return deduplicated, report

    def _find_duplicates(self, test_cases: TestCaseList) -> list[DuplicateGroup]:
        """
        Find groups of duplicate test cases.

        Args:
            test_cases: List of test cases to analyze

        Returns:
            List of duplicate groups (each group is a list of indices)
        """
        n = len(test_cases)
        visited = set()
        duplicate_groups = []

        for i in range(n):
            if i in visited:
                continue

            # Find all test cases similar to test_cases[i]
            group = [i]
            for j in range(i + 1, n):
                if j in visited:
                    continue

                similarity = self._calculate_similarity(test_cases[i], test_cases[j])
                if similarity >= self.similarity_threshold:
                    group.append(j)
                    visited.add(j)

            # Only add groups with duplicates
            if len(group) > 1:
                duplicate_groups.append(group)
                visited.add(i)

        return duplicate_groups

    def _calculate_similarity(self, tc1: TestCase, tc2: TestCase) -> SimilarityScore:
        """
        Calculate similarity score between two test cases.

        Args:
            tc1: First test case
            tc2: Second test case

        Returns:
            Similarity score between 0.0 and 1.0
        """
        similarities = []

        for field in self.fields_to_compare:
            val1 = self._field_value(tc1, field).lower().strip()
            val2 = self._field_value(tc2, field).lower().strip()

            if not val1 and not val2:
                # Field absent from both test cases carries no signal either
                # way — skip it. (Counting it as 1.0 previously caused test
                # cases from the preconditions/test_steps schema to be merged
                # on expected_result alone.)
                continue
            elif not val1 or not val2:
                # One empty, one not - not similar
                similarities.append(0.0)
            else:
                # Calculate string similarity using SequenceMatcher
                similarity = SequenceMatcher(None, val1, val2).ratio()
                similarities.append(similarity)

        # Return average similarity across the fields that carried content
        return sum(similarities) / len(similarities) if similarities else 0.0

    @staticmethod
    def _field_value(test_case: TestCase, field: str) -> str:
        """
        Resolve a comparison field through its schema aliases.

        Returns the first non-empty value among the field's alias chain.
        List values (e.g. test_steps returned as a list of steps) are joined
        with newlines, matching the normalisation in validators.py.
        """
        for name in _FIELD_ALIASES.get(field, (field,)):
            raw = test_case.get(name)
            if raw is None or raw == "" or raw == []:
                continue
            if isinstance(raw, list):
                return "\n".join(str(item) for item in raw)
            return str(raw)
        return ""

    def _select_duplicates_to_remove(
        self, group: DuplicateGroup, test_cases: TestCaseList, keep_strategy: str
    ) -> list[int]:
        """
        Select which test cases to remove from a duplicate group.

        Args:
            group: List of indices representing duplicate test cases
            test_cases: Complete list of test cases
            keep_strategy: Strategy for keeping duplicates

        Returns:
            List of indices to remove
        """
        if keep_strategy == "first":
            # Keep the first occurrence, remove all others
            return group[1:]
        elif keep_strategy == "last":
            # Keep the last occurrence, remove all others
            return group[:-1]
        elif keep_strategy == "best":
            # Keep the one with validation_passed=True if available, or the longest
            best_idx = self._find_best_test_case(group, test_cases)
            return [idx for idx in group if idx != best_idx]
        else:
            # Default to "first" strategy
            return group[1:]

    def _find_best_test_case(self, group: DuplicateGroup, test_cases: TestCaseList) -> int:
        """
        Find the best test case in a duplicate group.

        Criteria (in order):
        1. Validation passed (if available)
        2. Longest combined field length (more detailed)
        3. First occurrence

        Args:
            group: List of indices representing duplicate test cases
            test_cases: Complete list of test cases

        Returns:
            Index of the best test case
        """
        best_idx = group[0]
        best_score = self._score_test_case(test_cases[best_idx])

        for idx in group[1:]:
            score = self._score_test_case(test_cases[idx])
            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx

    def _score_test_case(self, test_case: TestCase) -> tuple[bool, int]:
        """
        Score a test case for quality comparison.

        Returns:
            Tuple of (validation_passed, total_length) for comparison
        """
        validation_passed = test_case.get("validation_passed", False)

        # Calculate total length of compared fields (alias-aware)
        total_length = sum(
            len(self._field_value(test_case, field)) for field in self.fields_to_compare
        )

        return (validation_passed, total_length)

    def _create_report(
        self, original_count: int, deduplicated_count: int, duplicate_groups: list[DuplicateGroup]
    ) -> dict[str, Any]:
        """
        Create a deduplication report.

        Args:
            original_count: Number of test cases before deduplication
            deduplicated_count: Number of test cases after deduplication
            duplicate_groups: List of duplicate groups found

        Returns:
            Deduplication report dictionary
        """
        return {
            "original_count": original_count,
            "deduplicated_count": deduplicated_count,
            "duplicates_removed": original_count - deduplicated_count,
            "duplicate_groups_found": len(duplicate_groups),
            "duplicate_groups": duplicate_groups,
            "deduplication_rate": (
                (original_count - deduplicated_count) / original_count
                if original_count > 0
                else 0.0
            ),
        }

    def find_similar_pairs(
        self, test_cases: TestCaseList, min_similarity: float = 0.7
    ) -> list[dict[str, Any]]:
        """
        Find pairs of similar test cases without removing them.

        Useful for review and analysis.

        Args:
            test_cases: List of test cases to analyze
            min_similarity: Minimum similarity to report (default: 0.7)

        Returns:
            List of similar pairs with similarity scores
        """
        similar_pairs = []
        n = len(test_cases)

        for i in range(n):
            for j in range(i + 1, n):
                similarity = self._calculate_similarity(test_cases[i], test_cases[j])

                if similarity >= min_similarity:
                    similar_pairs.append(
                        {
                            "index1": i,
                            "index2": j,
                            "similarity": similarity,
                            "test_case1_summary": test_cases[i].get("summary_suffix", "N/A"),
                            "test_case2_summary": test_cases[j].get("summary_suffix", "N/A"),
                        }
                    )

        # Sort by similarity (highest first)
        similar_pairs.sort(key=lambda x: x["similarity"], reverse=True)

        return similar_pairs
