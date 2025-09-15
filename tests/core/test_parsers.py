"""
Unit tests for the parsers module.

Tests JSON response parsing with multiple fallback strategies and HTML table parsing.
"""

import pytest

from core.parsers import JSONResponseParser, FastJSONResponseParser, HTMLTableParser


class TestJSONResponseParser:
    """Test JSON response parsing with fallback strategies."""

    def test_extract_direct_json(self):
        """Test direct JSON parsing from clean response."""
        response = '{"test_cases": [{"summary": "Test case 1"}]}'
        result = JSONResponseParser.extract_json_from_response(response)
        
        assert result is not None
        assert "test_cases" in result
        assert len(result["test_cases"]) == 1
        assert result["test_cases"][0]["summary"] == "Test case 1"

    def test_extract_json_from_markdown_block(self):
        """Test JSON extraction from markdown code blocks."""
        response = """Some text before
```json
{"test_cases": [{"summary": "Test case from markdown"}]}
```
Some text after"""
        
        result = JSONResponseParser.extract_json_from_response(response)
        
        assert result is not None
        assert "test_cases" in result
        assert result["test_cases"][0]["summary"] == "Test case from markdown"

    def test_extract_json_from_code_block_without_language(self):
        """Test JSON extraction from code blocks without language specifier."""
        response = """Here's the response:
```
{"test_cases": [{"summary": "Test without language"}]}
```"""
        
        result = JSONResponseParser.extract_json_from_response(response)
        
        assert result is not None
        assert "test_cases" in result
        assert result["test_cases"][0]["summary"] == "Test without language"

    def test_extract_json_with_curly_braces_fallback(self):
        """Test JSON extraction using curly braces pattern matching."""
        response = """The AI model responded with this data:
        {"test_cases": [{"summary": "Extracted with braces"}]}
        Additional text here"""
        
        result = JSONResponseParser.extract_json_from_response(response)
        
        assert result is not None
        assert "test_cases" in result
        assert result["test_cases"][0]["summary"] == "Extracted with braces"

    def test_invalid_json_returns_none(self):
        """Test that invalid JSON returns None."""
        response = "This is not JSON at all"
        result = JSONResponseParser.extract_json_from_response(response)
        
        assert result is None

    def test_empty_response_returns_none(self):
        """Test that empty response returns None."""
        result = JSONResponseParser.extract_json_from_response("")
        assert result is None
        
        result = JSONResponseParser.extract_json_from_response(None)
        assert result is None

    def test_malformed_json_in_code_block(self):
        """Test handling of malformed JSON in code blocks."""
        response = """```json
{"test_cases": [{"summary": "Missing closing brace"}
```"""

        result = JSONResponseParser.extract_json_from_response(response)
        # Parser should extract the valid JSON portion that exists
        assert result is not None
        assert result == {"summary": "Missing closing brace"}

    def test_multiple_json_blocks_returns_first_valid(self):
        """Test that first valid JSON block is returned when multiple exist."""
        response = """First block:
```json
{"test_cases": [{"summary": "First valid"}]}
```
Second block:
```json
{"test_cases": [{"summary": "Second valid"}]}
```"""
        
        result = JSONResponseParser.extract_json_from_response(response)
        
        assert result is not None
        assert result["test_cases"][0]["summary"] == "First valid"


class TestFastJSONResponseParser:
    """Test the fast JSON response parser."""

    def test_fast_parser_basic_functionality(self):
        """Test that FastJSONResponseParser works with basic JSON."""
        response = '{"test_cases": [{"summary": "Fast parser test"}]}'
        result = FastJSONResponseParser.extract_json_from_response(response)
        
        assert result is not None
        assert "test_cases" in result
        assert result["test_cases"][0]["summary"] == "Fast parser test"

    def test_fast_parser_fallback_behavior(self):
        """Test that FastJSONResponseParser handles fallback scenarios."""
        # This should work the same as regular parser for fallback cases
        response = """```json
{"test_cases": [{"summary": "Fast fallback test"}]}
```"""
        
        result = FastJSONResponseParser.extract_json_from_response(response)
        
        assert result is not None
        assert "test_cases" in result


class TestHTMLTableParser:
    """Test HTML table parsing functionality."""

    def test_parse_simple_table(self):
        """Test parsing a simple HTML table."""
        html = """
        <table>
            <tr>
                <th>Header 1</th>
                <th>Header 2</th>
            </tr>
            <tr>
                <td>Value 1</td>
                <td>Value 2</td>
            </tr>
        </table>
        """
        
        result = HTMLTableParser.extract_tables_from_html(html)
        
        assert len(result) == 1
        assert result[0]["Header 1"] == "Value 1"
        assert result[0]["Header 2"] == "Value 2"

    def test_parse_table_with_multiple_rows(self):
        """Test parsing table with multiple data rows."""
        html = """
        <table>
            <tr><th>ID</th><th>Name</th></tr>
            <tr><td>1</td><td>Test 1</td></tr>
            <tr><td>2</td><td>Test 2</td></tr>
        </table>
        """
        
        result = HTMLTableParser.extract_tables_from_html(html)
        
        assert len(result) == 2
        assert result[0]["ID"] == "1"
        assert result[0]["Name"] == "Test 1"
        assert result[1]["ID"] == "2" 
        assert result[1]["Name"] == "Test 2"

    def test_parse_empty_table(self):
        """Test parsing an empty table."""
        html = "<table></table>"
        
        result = HTMLTableParser.extract_tables_from_html(html)
        
        assert result == []

    def test_parse_malformed_html(self):
        """Test handling of malformed HTML."""
        html = "<table><tr><th>Header</th><tr><td>Unclosed tags"
        
        # Should not raise exception, return empty or partial result
        result = HTMLTableParser.extract_tables_from_html(html)
        
        assert isinstance(result, list)

    def test_parse_table_with_nested_elements(self):
        """Test parsing table with nested HTML elements."""
        html = """
        <table>
            <tr>
                <th>Requirement</th>
                <th>Description</th>
            </tr>
            <tr>
                <td><strong>REQ-001</strong></td>
                <td>The system <em>shall</em> validate input</td>
            </tr>
        </table>
        """
        
        result = HTMLTableParser.extract_tables_from_html(html)
        
        assert len(result) == 1
        assert "REQ-001" in result[0]["Requirement"]
        assert "shall" in result[0]["Description"]