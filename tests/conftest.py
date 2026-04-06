"""
Pytest configuration and shared fixtures for AI Test Case Generator tests.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.helpers import create_test_requirement


@pytest.fixture
def mock_ollama_client():
    """Mock OllamaClient for testing without API calls."""
    mock_client = Mock()
    mock_client.generate_response.return_value = """
    {
        "test_cases": [
            {
                "summary": "Test basic functionality",
                "action": "Execute basic test",
                "data": "Test data",
                "expected_result": "Expected outcome"
            }
        ]
    }
    """
    return mock_client


@pytest.fixture
def mock_async_ollama_client():
    """Mock AsyncOllamaClient for testing async functionality."""
    mock_client = AsyncMock()
    _response = """
    {
        "test_cases": [
            {
                "summary": "Test async functionality",
                "action": "Execute async test",
                "data": "Async test data",
                "expected_result": "Async expected outcome"
            }
        ]
    }
    """
    mock_client.generate_response = AsyncMock(return_value=_response)
    mock_client.generate_response_with_vision = AsyncMock(return_value=_response)
    # Context-manager support (async with client as c:)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


@pytest.fixture
def sample_requirement():
    """Sample requirement artifact for testing (XHTML-formatted text)."""
    return create_test_requirement(
        "The system shall validate user input and respond within 2 seconds",
        requirement_id="REQ_001",
    )


@pytest.fixture
def sample_requirements_list():
    """List of sample requirements for batch testing (XHTML-formatted text)."""
    return [
        create_test_requirement(
            "The system shall validate user input",
            requirement_id="REQ_001",
        ),
        create_test_requirement(
            "The system shall handle errors gracefully",
            requirement_id="REQ_002",
        ),
        create_test_requirement(
            "The system shall log all transactions",
            requirement_id="REQ_003",
        ),
    ]


@pytest.fixture
def sample_test_cases():
    """Sample test cases for formatter testing."""
    return [
        {
            "issue_id": "TC_001",
            "summary": "Test input validation",
            "action": "Enter invalid data",
            "data": "Special characters: @#$%",
            "expected_result": "System displays error message",
            "test_type": "negative",
            "requirement_id": "REQ_001"
        },
        {
            "issue_id": "TC_002",
            "summary": "Test valid input",
            "action": "Enter valid data",
            "data": "Normal user input",
            "expected_result": "System processes successfully",
            "test_type": "positive",
            "requirement_id": "REQ_001"
        }
    ]


@pytest.fixture
def temp_reqifz_file(tmp_path):
    """Create a temporary REQIFZ file for testing."""
    reqifz_content = """<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd" xmlns:html="http://www.w3.org/1999/xhtml">
    <THE-HEADER>
        <REQ-IF-HEADER>
            <COMMENT>Test REQIF file</COMMENT>
            <CREATION-TIME>2025-01-15T10:00:00.000Z</CREATION-TIME>
            <REPOSITORY-ID>test-repo</REPOSITORY-ID>
            <REQ-IF-TOOL-ID>test-tool</REQ-IF-TOOL-ID>
            <REQ-IF-VERSION>1.0</REQ-IF-VERSION>
            <SOURCE-TOOL-ID>test-source</SOURCE-TOOL-ID>
            <TITLE>Test Requirements</TITLE>
        </REQ-IF-HEADER>
    </THE-HEADER>
    <CORE-CONTENT>
        <REQ-IF-CONTENT>
            <SPEC-OBJECTS>
                <SPEC-OBJECT IDENTIFIER="REQ_001" LAST-CHANGE="2025-01-15T10:00:00.000Z">
                    <VALUES>
                        <ATTRIBUTE-VALUE-STRING THE-VALUE="System Requirement">
                            <DEFINITION>
                                <ATTRIBUTE-DEFINITION-STRING-REF>TYPE</ATTRIBUTE-DEFINITION-STRING-REF>
                            </DEFINITION>
                        </ATTRIBUTE-VALUE-STRING>
                        <ATTRIBUTE-VALUE-XHTML>
                            <DEFINITION LONG-NAME="ReqIF.Text">
                                <ATTRIBUTE-DEFINITION-XHTML-REF>req-text</ATTRIBUTE-DEFINITION-XHTML-REF>
                            </DEFINITION>
                            <THE-VALUE><html:div>The system shall validate user input</html:div></THE-VALUE>
                        </ATTRIBUTE-VALUE-XHTML>
                    </VALUES>
                </SPEC-OBJECT>
            </SPEC-OBJECTS>
        </REQ-IF-CONTENT>
    </CORE-CONTENT>
</REQ-IF>"""

    # Create REQIFZ (ZIP) file
    import zipfile
    reqifz_path = tmp_path / "test.reqifz"
    with zipfile.ZipFile(reqifz_path, 'w') as zf:
        zf.writestr("test.reqif", reqifz_content)

    return reqifz_path


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    mock = Mock()
    mock.info = Mock()
    mock.warning = Mock()
    mock.error = Mock()
    mock.add_requirement_failure = Mock()
    mock.add_ai_response_time = Mock()
    return mock
