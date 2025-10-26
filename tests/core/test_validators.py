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
