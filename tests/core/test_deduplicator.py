"""Tests for test case deduplication"""

from core.deduplicator import TestCaseDeduplicator


def test_no_duplicates():
    """Test deduplication with no duplicate test cases"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.85)

    test_cases = [
        {"action": "Send ACCSP=100", "data": "ACCSP=100", "expected_result": "System responds"},
        {"action": "Send IgnMode=ON", "data": "IgnMode=ON", "expected_result": "System activates"},
        {"action": "Send ACCSP=200", "data": "ACCSP=200", "expected_result": "System adjusts"},
    ]

    deduplicated, report = deduplicator.deduplicate(test_cases)

    assert len(deduplicated) == 3
    assert report["original_count"] == 3
    assert report["deduplicated_count"] == 3
    assert report["duplicates_removed"] == 0
    assert report["duplicate_groups_found"] == 0


def test_exact_duplicates():
    """Test deduplication with exact duplicate test cases"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.85)

    test_cases = [
        {"action": "Send ACCSP=100", "data": "ACCSP=100", "expected_result": "System responds"},
        {"action": "Send ACCSP=100", "data": "ACCSP=100", "expected_result": "System responds"},  # Exact duplicate
        {"action": "Send IgnMode=ON", "data": "IgnMode=ON", "expected_result": "System activates"},
    ]

    deduplicated, report = deduplicator.deduplicate(test_cases, keep_strategy="first")

    assert len(deduplicated) == 2
    assert report["duplicates_removed"] == 1
    assert report["duplicate_groups_found"] == 1
    assert deduplicated[0]["action"] == "Send ACCSP=100"
    assert deduplicated[1]["action"] == "Send IgnMode=ON"


def test_similar_duplicates():
    """Test deduplication with highly similar test cases"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.85)

    test_cases = [
        {"action": "Send ACCSP signal with value 100", "data": "ACCSP=100", "expected_result": "System processes signal"},
        {"action": "Send ACCSP signal with value of 100", "data": "ACCSP=100", "expected_result": "System processes the signal"},  # Very similar
        {"action": "Send IgnMode=ON", "data": "IgnMode=ON", "expected_result": "System activates"},
    ]

    deduplicated, report = deduplicator.deduplicate(test_cases)

    assert len(deduplicated) == 2
    assert report["duplicates_removed"] == 1


def test_multiple_duplicate_groups():
    """Test deduplication with multiple groups of duplicates"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.85)

    test_cases = [
        {"action": "Test A", "data": "Data A", "expected_result": "Result A"},
        {"action": "Test A", "data": "Data A", "expected_result": "Result A"},  # Duplicate of first
        {"action": "Test B", "data": "Data B", "expected_result": "Result B"},
        {"action": "Test B", "data": "Data B", "expected_result": "Result B"},  # Duplicate of third
        {"action": "Test C", "data": "Data C", "expected_result": "Result C"},
    ]

    deduplicated, report = deduplicator.deduplicate(test_cases)

    assert len(deduplicated) == 3
    assert report["duplicates_removed"] == 2
    assert report["duplicate_groups_found"] == 2


def test_keep_strategy_first():
    """Test keeping the first occurrence of duplicates"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.85)

    test_cases = [
        {"action": "First", "data": "Data", "expected_result": "Result", "index": 0},
        {"action": "First", "data": "Data", "expected_result": "Result", "index": 1},
        {"action": "First", "data": "Data", "expected_result": "Result", "index": 2},
    ]

    deduplicated, _ = deduplicator.deduplicate(test_cases, keep_strategy="first")

    assert len(deduplicated) == 1
    assert deduplicated[0]["index"] == 0


def test_keep_strategy_last():
    """Test keeping the last occurrence of duplicates"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.85)

    test_cases = [
        {"action": "Test", "data": "Data", "expected_result": "Result", "index": 0},
        {"action": "Test", "data": "Data", "expected_result": "Result", "index": 1},
        {"action": "Test", "data": "Data", "expected_result": "Result", "index": 2},
    ]

    deduplicated, _ = deduplicator.deduplicate(test_cases, keep_strategy="last")

    assert len(deduplicated) == 1
    assert deduplicated[0]["index"] == 2


def test_keep_strategy_best():
    """Test keeping the best quality test case from duplicates"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.85)

    test_cases = [
        {"action": "Test", "data": "Data", "expected_result": "Result", "validation_passed": False},
        {"action": "Test", "data": "Data", "expected_result": "Result", "validation_passed": True},  # Best (validated)
        {"action": "Test", "data": "Data", "expected_result": "Result", "validation_passed": False},
    ]

    deduplicated, _ = deduplicator.deduplicate(test_cases, keep_strategy="best")

    assert len(deduplicated) == 1
    assert deduplicated[0]["validation_passed"] is True


def test_keep_strategy_best_by_length():
    """Test keeping the longest test case when validation is equal"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.85)

    test_cases = [
        {"action": "Send ACCSP signal", "data": "ACCSP=100", "expected_result": "System responds"},
        {"action": "Send ACCSP signal with value 100", "data": "ACCSP=100", "expected_result": "System responds"},  # Longest (more detailed)
        {"action": "Send ACCSP signal", "data": "ACCSP=100", "expected_result": "System responds"},
    ]

    deduplicated, _ = deduplicator.deduplicate(test_cases, keep_strategy="best")

    assert len(deduplicated) == 1
    assert "with value" in deduplicated[0]["action"]


def test_similarity_threshold():
    """Test different similarity thresholds"""
    test_cases = [
        {"action": "Send ACCSP=100", "data": "ACCSP=100", "expected_result": "System responds"},
        {"action": "Send ACCSP=150", "data": "ACCSP=150", "expected_result": "System responds"},
    ]

    # High threshold - should not consider these as duplicates
    strict_dedup = TestCaseDeduplicator(similarity_threshold=0.95)
    deduplicated_strict, _ = strict_dedup.deduplicate(test_cases)
    assert len(deduplicated_strict) == 2

    # Low threshold - might consider these as duplicates
    lenient_dedup = TestCaseDeduplicator(similarity_threshold=0.75)
    deduplicated_lenient, _ = lenient_dedup.deduplicate(test_cases)
    # Result depends on actual similarity, but should be <= original


def test_custom_fields_to_compare():
    """Test deduplication with custom fields to compare"""
    deduplicator = TestCaseDeduplicator(
        similarity_threshold=0.85,
        fields_to_compare=["action"]  # Only compare action field
    )

    test_cases = [
        {"action": "Test A", "data": "Data 1", "expected_result": "Result 1"},
        {"action": "Test A", "data": "Data 2", "expected_result": "Result 2"},  # Same action, different data
    ]

    deduplicated, report = deduplicator.deduplicate(test_cases)

    # Should be considered duplicates because only action is compared
    assert len(deduplicated) == 1
    assert report["duplicates_removed"] == 1


def test_empty_test_cases_list():
    """Test deduplication with empty test cases list"""
    deduplicator = TestCaseDeduplicator()

    deduplicated, report = deduplicator.deduplicate([])

    assert len(deduplicated) == 0
    assert report["original_count"] == 0
    assert report["deduplicated_count"] == 0


def test_find_similar_pairs():
    """Test finding similar pairs without removing them"""
    deduplicator = TestCaseDeduplicator()

    test_cases = [
        {"action": "Test A", "data": "Data A", "expected_result": "Result A", "summary_suffix": "TC1"},
        {"action": "Test A", "data": "Data A", "expected_result": "Result A", "summary_suffix": "TC2"},  # Very similar
        {"action": "Test B", "data": "Data B", "expected_result": "Result B", "summary_suffix": "TC3"},
        {"action": "Test C", "data": "Data C", "expected_result": "Result C", "summary_suffix": "TC4"},
    ]

    similar_pairs = deduplicator.find_similar_pairs(test_cases, min_similarity=0.9)

    assert len(similar_pairs) >= 1
    assert similar_pairs[0]["similarity"] >= 0.9
    assert "index1" in similar_pairs[0]
    assert "index2" in similar_pairs[0]


def test_deduplication_report_structure():
    """Test that deduplication report has correct structure"""
    deduplicator = TestCaseDeduplicator()

    test_cases = [
        {"action": "Test", "data": "Data", "expected_result": "Result"},
        {"action": "Test", "data": "Data", "expected_result": "Result"},
    ]

    _, report = deduplicator.deduplicate(test_cases)

    assert "original_count" in report
    assert "deduplicated_count" in report
    assert "duplicates_removed" in report
    assert "duplicate_groups_found" in report
    assert "duplicate_groups" in report
    assert "deduplication_rate" in report
    assert isinstance(report["deduplication_rate"], float)


def test_case_insensitive_comparison():
    """Test that comparison is case-insensitive"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.85)

    test_cases = [
        {"action": "Send ACCSP=100", "data": "ACCSP=100", "expected_result": "System responds"},
        {"action": "SEND ACCSP=100", "data": "accsp=100", "expected_result": "SYSTEM RESPONDS"},  # Same but different case
    ]

    deduplicated, report = deduplicator.deduplicate(test_cases)

    assert len(deduplicated) == 1
    assert report["duplicates_removed"] == 1


def test_whitespace_handling():
    """Test that extra whitespace is handled properly"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.85)

    test_cases = [
        {"action": "Send ACCSP=100", "data": "ACCSP=100", "expected_result": "System responds"},
        {"action": "  Send ACCSP=100  ", "data": "  ACCSP=100  ", "expected_result": "  System responds  "},  # Extra whitespace
    ]

    deduplicated, report = deduplicator.deduplicate(test_cases)

    assert len(deduplicated) == 1
    assert report["duplicates_removed"] == 1


def test_deduplication_rate_calculation():
    """Test deduplication rate calculation"""
    deduplicator = TestCaseDeduplicator()

    test_cases = [
        {"action": "Test", "data": "Data", "expected_result": "Result"},
        {"action": "Test", "data": "Data", "expected_result": "Result"},
        {"action": "Test", "data": "Data", "expected_result": "Result"},
        {"action": "Test", "data": "Data", "expected_result": "Result"},
        {"action": "Unique", "data": "Unique", "expected_result": "Unique"},
    ]

    _, report = deduplicator.deduplicate(test_cases)

    # 5 original, 2 deduplicated (4 duplicates + 1 unique), so 3 removed
    # Deduplication rate = 3/5 = 0.6
    assert report["original_count"] == 5
    assert report["deduplicated_count"] == 2
    assert report["duplicates_removed"] == 3
    assert abs(report["deduplication_rate"] - 0.6) < 0.01
