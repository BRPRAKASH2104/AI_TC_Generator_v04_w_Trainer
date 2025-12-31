
from src.core.formatters import TestCaseFormatter


def test_excel_description_includes_confidence():
    """Test that confidence score is added to Description column"""
    formatter = TestCaseFormatter()

    test_cases = [{
        "requirement_id": "REQ-1",
        "summary": "Test Summary",
        "action": ["Step 1"],
        "expected_result": ["Pass"],
        "confidence_score": 0.987654321
    }]

    formatted = formatter._prepare_test_cases_for_excel(test_cases)

    assert len(formatted) == 1
    # Check if confidence score is formatted to 2 decimals
    assert formatted[0]["Description"] == "Confidence Score: 0.99"

def test_excel_description_handles_missing_confidence():
    """Test that Description is empty if confidence score is missing"""
    formatter = TestCaseFormatter()

    test_cases = [{
        "requirement_id": "REQ-1",
        "summary": "Test Summary"
    }]

    formatted = formatter._prepare_test_cases_for_excel(test_cases)

    assert formatted[0]["Description"] == ""
