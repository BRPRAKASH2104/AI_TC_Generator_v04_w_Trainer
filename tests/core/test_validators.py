"""Tests for semantic validation"""

from core.validators import SemanticValidator


def test_signal_name_extraction():
    """Test extraction of signal names from interface dictionary"""
    validator = SemanticValidator()

    interface_list = [
        {"id": "IF_001", "text": "CANSignal - ACCSP (Message: FCM1S39)"},
        {"id": "IF_002", "text": "InternalSignal - IgnMode"},
        {"id": "IF_003", "text": "NVM - NVM_ACCExistFlag (Dropped)"},
    ]

    signal_names = validator._extract_signal_names(interface_list)

    assert "ACCSP" in signal_names
    assert "IgnMode" in signal_names
    assert "NVM_ACCExistFlag" in signal_names


def test_valid_test_case():
    """Test validation of correct test case"""
    validator = SemanticValidator()

    test_case = {
        "action": "Send ACCSP signal with value 100",
        "data": "ACCSP=100, IgnMode=ON",
        "expected_result": "System processes signal",
    }

    requirement = {
        "interface_list": [
            {"id": "IF_001", "text": "CANSignal - ACCSP (Message: FCM1S39)"},
            {"id": "IF_002", "text": "InternalSignal - IgnMode"},
        ]
    }

    is_valid, issues = validator.validate_test_case(test_case, requirement)

    assert is_valid
    assert len(issues) == 0


def test_invalid_signal_name():
    """Test detection of hallucinated signal name"""
    validator = SemanticValidator()

    test_case = {
        "action": "Send ACC_SPEED signal with value 100",  # Wrong name
        "data": "ACC_SPEED=100, IgnMode=ON",
        "expected_result": "System processes signal",
    }

    requirement = {
        "interface_list": [
            {"id": "IF_001", "text": "CANSignal - ACCSP (Message: FCM1S39)"},
            {"id": "IF_002", "text": "InternalSignal - IgnMode"},
        ]
    }

    is_valid, issues = validator.validate_test_case(test_case, requirement)

    assert not is_valid
    assert len(issues) > 0
    assert "ACC_SPEED" in issues[0]


def test_fuzzy_matching_suggestion():
    """Test fuzzy matching suggests correct signal name"""
    validator = SemanticValidator(similarity_threshold=0.7)

    test_case = {"action": "Send ACCSP1 signal", "data": "ACCSP1=100"}  # Close to ACCSP

    requirement = {
        "interface_list": [
            {"id": "IF_001", "text": "CANSignal - ACCSP (Message: FCM1S39)"}
        ]
    }

    is_valid, issues = validator.validate_test_case(test_case, requirement)

    assert not is_valid
    assert any("Did you mean 'ACCSP'?" in issue for issue in issues)


def test_batch_validation_report():
    """Test batch validation generates correct report"""
    validator = SemanticValidator()

    test_cases = [
        {"action": "Send ACCSP=100", "data": "ACCSP=100"},  # Valid
        {"action": "Send WRONG=100", "data": "WRONG=100"},  # Invalid
        {"action": "Send IgnMode=ON", "data": "IgnMode=ON"},  # Valid
    ]

    requirement = {
        "interface_list": [
            {"id": "IF_001", "text": "CANSignal - ACCSP"},
            {"id": "IF_002", "text": "InternalSignal - IgnMode"},
        ]
    }

    report = validator.validate_batch(test_cases, requirement)

    assert report["total_test_cases"] == 3
    assert report["valid_count"] == 2
    assert report["invalid_count"] == 1
    assert abs(report["validation_rate"] - (2 / 3)) < 0.01
    assert len(report["issues"]) == 1
    assert report["issues"][0]["test_case_index"] == 2


def test_no_interface_list():
    """Test validation with no interface list returns valid"""
    validator = SemanticValidator()

    test_case = {
        "action": "Any signal name works",
        "data": "ANYTHING=100",
        "expected_result": "Something happens",
    }

    requirement = {"interface_list": []}  # Empty interface list

    is_valid, issues = validator.validate_test_case(test_case, requirement)

    assert is_valid  # Should be valid when no interfaces to validate against
    assert len(issues) == 0


def test_empty_data_field():
    """Test validation catches empty data field"""
    validator = SemanticValidator()

    test_case = {
        "action": "Send ACCSP signal",
        "data": "",  # Empty data field
        "expected_result": "System responds",
    }

    requirement = {
        "interface_list": [
            {"id": "IF_001", "text": "CANSignal - ACCSP (Message: FCM1S39)"}
        ]
    }

    is_valid, issues = validator.validate_test_case(test_case, requirement)

    assert not is_valid
    assert any("Data field is empty" in issue for issue in issues)


def test_data_format_validation():
    """Test validation of data field format"""
    validator = SemanticValidator()

    # Missing equals sign in second part
    test_case = {
        "action": "Send signals",
        "data": "ACCSP=100, IgnMode",  # Missing "=" for IgnMode
        "expected_result": "System responds",
    }

    requirement = {
        "interface_list": [
            {"id": "IF_001", "text": "CANSignal - ACCSP"},
            {"id": "IF_002", "text": "InternalSignal - IgnMode"},
        ]
    }

    is_valid, issues = validator.validate_test_case(test_case, requirement)

    assert not is_valid
    assert any("missing '=' assignment" in issue for issue in issues)


def test_multiple_invalid_signals():
    """Test detection of multiple invalid signal names"""
    validator = SemanticValidator()

    test_case = {
        "action": "Send WRONG1 and WRONG2 signals",
        "data": "WRONG1=100, WRONG2=200",
        "expected_result": "System responds",
    }

    requirement = {
        "interface_list": [
            {"id": "IF_001", "text": "CANSignal - ACCSP"},
            {"id": "IF_002", "text": "InternalSignal - IgnMode"},
        ]
    }

    is_valid, issues = validator.validate_test_case(test_case, requirement)

    assert not is_valid
    assert len(issues) >= 2  # At least 2 issues (one for each wrong signal)
    assert any("WRONG1" in issue for issue in issues)
    assert any("WRONG2" in issue for issue in issues)


def test_similarity_threshold_configuration():
    """Test that similarity threshold affects fuzzy matching"""
    # High threshold - strict matching
    strict_validator = SemanticValidator(similarity_threshold=0.9)
    test_case = {"action": "Send ACSP signal", "data": "ACSP=100"}  # Missing one C

    requirement = {
        "interface_list": [{"id": "IF_001", "text": "CANSignal - ACCSP"}]
    }

    is_valid, issues = strict_validator.validate_test_case(test_case, requirement)
    # With high threshold, "ACSP" might not match "ACCSP"
    # (depends on difflib's ratio calculation)

    # Low threshold - lenient matching
    lenient_validator = SemanticValidator(similarity_threshold=0.6)
    is_valid2, issues2 = lenient_validator.validate_test_case(test_case, requirement)

    # Both should detect the invalid signal, but lenient one more likely to suggest
    assert not is_valid or not is_valid2


def test_unknown_signal_in_test_steps_flagged_without_close_match():
    """Regression: hallucinated signals in test_steps with NO fuzzy match passed silently.

    The data/test_steps branch only reported issues when a close match
    existed, unlike the action branch which flagged unknown signals either way.
    """
    validator = SemanticValidator()

    test_case = {
        "summary_suffix": "Lock check",
        "preconditions": "1. Voltage= 12V\n2. Bat-ON",
        "test_steps": "1) Set PHANTOMSIG = 1\n2) Observe output",
        "expected_result": "Verify lock engages",
    }

    requirement = {
        "interface_list": [{"id": "IF_001", "text": "CANSignal - ACCSP"}]
    }

    is_valid, issues = validator.validate_test_case(test_case, requirement)

    assert not is_valid
    assert any("PHANTOMSIG" in issue for issue in issues)


def test_generic_words_in_test_steps_not_flagged():
    """Generic identifiers like 'Voltage' must not trigger false positives."""
    validator = SemanticValidator()

    test_case = {
        "test_steps": "1) Set Voltage = 9\n2) Set ACCSP = 100",
        "expected_result": "Verify behaviour",
    }

    requirement = {
        "interface_list": [{"id": "IF_001", "text": "CANSignal - ACCSP"}]
    }

    is_valid, issues = validator.validate_test_case(test_case, requirement)

    assert is_valid, f"Unexpected issues: {issues}"


def test_signal_names_extracted_once_per_batch():
    """Efficiency regression: the interface signal set must be built once per
    batch, not rebuilt for every test case."""
    from unittest.mock import patch

    validator = SemanticValidator()

    test_cases = [
        {"test_steps": f"1) Set ACCSP = {i}", "expected_result": "ok"} for i in range(5)
    ]
    requirement = {
        "interface_list": [{"id": "IF_001", "text": "CANSignal - ACCSP"}]
    }

    with patch.object(
        SemanticValidator, "_extract_signal_names", wraps=validator._extract_signal_names
    ) as spy:
        validator.validate_batch(test_cases, requirement)

    assert spy.call_count == 1, f"expected 1 extraction, got {spy.call_count}"


def test_signal_extraction_patterns():
    """Test various signal name extraction patterns"""
    validator = SemanticValidator()

    # Test different interface text patterns
    interface_list = [
        {"id": "IF_001", "text": "CANSignal - SIGNAL_NAME_1 (Extra Info)"},
        {"id": "IF_002", "text": "InternalSignal - SIGNAL_NAME_2"},
        {"id": "IF_003", "text": "NVM - SIGNAL_NAME_3 (Dropped)"},
        {"id": "IF_004", "text": "SIGNAL_NAME_4"},  # Simple pattern
    ]

    signal_names = validator._extract_signal_names(interface_list)

    assert "SIGNAL_NAME_1" in signal_names
    assert "SIGNAL_NAME_2" in signal_names
    assert "SIGNAL_NAME_3" in signal_names
    assert "SIGNAL_NAME_4" in signal_names
    assert len(signal_names) >= 4


class TestTruncatedTableCoverage:
    """Coverage validation must be scoped to the rows actually displayed to
    the model — format_table truncates >MAX_PROMPT_TABLE_ROWS tables to the
    first and last 10 rows and instructs displayed-rows-only coverage, so
    requiring one positive case per ORIGINAL row guarantees false failures
    (review 2026-07-17 finding 7).
    """

    @staticmethod
    def _cases(positives, negatives):
        cases = [
            {"summary_suffix": f"p{i}", "test_type": "positive"} for i in range(positives)
        ]
        cases += [
            {"summary_suffix": f"n{i}", "test_type": "negative"} for i in range(negatives)
        ]
        return cases

    def test_displayed_rows_helper(self):
        from core.prompt_builder import displayed_table_rows

        assert displayed_table_rows(5) == 5
        assert displayed_table_rows(100) == 100
        assert displayed_table_rows(150) == 20
        assert displayed_table_rows(101) == 20

    def test_large_table_coverage_scoped_to_displayed_rows(self):
        from core.validators import SemanticValidator

        validator = SemanticValidator()
        requirement = {"table": {"rows": 150}}

        issues = validator._validate_table_coverage(self._cases(20, 3), requirement)

        assert issues == []

    def test_large_table_analysis_reports_truncation(self):
        from core.validators import SemanticValidator

        validator = SemanticValidator()
        requirement = {"table": {"rows": 150}}

        analysis = validator._analyze_table_coverage(self._cases(20, 3), requirement)

        assert analysis["required_table_rows"] == 20
        assert analysis["total_table_rows"] == 150
        assert analysis["truncated"] is True
        assert analysis["adequate_coverage"] is True

    def test_small_table_still_requires_full_coverage(self):
        from core.validators import SemanticValidator

        validator = SemanticValidator()
        requirement = {"table": {"rows": 5}}

        issues = validator._validate_table_coverage(self._cases(3, 3), requirement)

        assert len(issues) >= 1  # 3 positives for 5 displayed rows is a real gap

    def test_small_table_analysis_not_truncated(self):
        from core.validators import SemanticValidator

        validator = SemanticValidator()
        requirement = {"table": {"rows": 5}}

        analysis = validator._analyze_table_coverage(self._cases(5, 3), requirement)

        assert analysis["required_table_rows"] == 5
        assert analysis["truncated"] is False
        assert analysis["adequate_coverage"] is True
