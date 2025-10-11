"""
Response and data parsers for the AI Test Case Generator.

This module provides parsers for JSON responses from AI models and HTML table parsing
for REQIF files, with performance optimizations for Python 3.13.7+.
"""


import json
import re
from typing import Any
from xml.etree import ElementTree as ET

try:
    import ujson  # Faster JSON parsing if available
    JSON_PARSER = ujson
except ImportError:
    JSON_PARSER = json

# Type aliases for better readability (PEP 695 style)
type JSONObject = dict[str, Any]
type HTMLTableData = list[dict[str, str]]


class JSONResponseParser:
    """Handles parsing JSON responses from AI models"""

    __slots__ = ()

    @staticmethod
    def extract_json_from_response(response_text: str) -> JSONObject | None:
        """
        Extract JSON from AI model response with multiple fallback strategies.
        
        This handles cases where models return JSON embedded in markdown code blocks
        or mixed with other text.
        """
        if not response_text or not response_text.strip():
            return None

        # Strategy 1: Direct JSON parsing
        try:
            return JSON_PARSER.loads(response_text.strip())
        except (json.JSONDecodeError, ValueError):
            pass

        # Strategy 2: Extract from markdown code blocks
        json_code_block_pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```"
        matches = re.findall(json_code_block_pattern, response_text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            try:
                return JSON_PARSER.loads(match.strip())
            except (json.JSONDecodeError, ValueError):
                continue

        # Strategy 3: Find JSON-like objects in text
        json_object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_object_pattern, response_text, re.DOTALL)

        for match in matches:
            try:
                return JSON_PARSER.loads(match.strip())
            except (json.JSONDecodeError, ValueError):
                continue

        # Strategy 4: Extract specific test_cases array pattern
        test_cases_pattern = r'"test_cases"\s*:\s*\[([\s\S]*?)\]'
        match = re.search(test_cases_pattern, response_text, re.IGNORECASE | re.DOTALL)

        if match:
            try:
                test_cases_json = f'{{"test_cases": [{match.group(1)}]}}'
                return JSON_PARSER.loads(test_cases_json)
            except (json.JSONDecodeError, ValueError):
                pass

        return None

    @staticmethod
    def validate_test_cases_structure(data: JSONObject) -> bool:
        """Validate that JSON contains properly structured test cases"""
        if not isinstance(data, dict):
            return False

        test_cases = data.get("test_cases", [])
        if not isinstance(test_cases, list) or not test_cases:
            return False

        # Check first test case structure
        required_fields = {"summary", "action", "data", "expected_result"}
        first_case = test_cases[0]

        if not isinstance(first_case, dict):
            return False

        return all(field in first_case for field in required_fields)


class FastJSONResponseParser(JSONResponseParser):
    """High-performance JSON parser with additional optimization for batch processing"""

    __slots__ = ()

    @staticmethod
    def extract_json_batch(responses: list[str]) -> list[JSONObject | None]:
        """Extract JSON from multiple responses in batch for better performance"""
        results = []
        for response in responses:
            results.append(JSONResponseParser.extract_json_from_response(response))
        return results

    @staticmethod
    def extract_json_from_response(response_text: str) -> JSONObject | None:
        """Optimized JSON extraction with faster regex patterns"""
        if not response_text or not response_text.strip():
            return None

        # Fast path: Direct JSON parsing
        stripped_text = response_text.strip()
        if stripped_text.startswith('{') and stripped_text.endswith('}'):
            try:
                return JSON_PARSER.loads(stripped_text)
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback to parent implementation
        return super(FastJSONResponseParser, FastJSONResponseParser).extract_json_from_response(response_text)


class HTMLTableParser:
    """Enhanced HTML table parser for REQIF XML content"""

    __slots__ = ()

    @staticmethod
    def extract_tables_from_html(html_content: str) -> HTMLTableData:
        """
        Extract structured data from HTML tables with enhanced parsing.
        
        Handles various table formats commonly found in automotive REQIF files.
        """
        if not html_content or not html_content.strip():
            return []

        try:
            # Clean and prepare HTML content
            cleaned_html = HTMLTableParser._clean_html_content(html_content)

            # Parse with ElementTree (faster than BeautifulSoup for simple tables)
            root = ET.fromstring(f"<div>{cleaned_html}</div>")
            tables = root.findall(".//table")

            all_table_data = []
            for table in tables:
                table_data = HTMLTableParser._parse_single_table(table)
                if table_data:  # Only add non-empty tables
                    all_table_data.extend(table_data)

            return all_table_data

        except (ET.ParseError, Exception):
            # Fallback: Simple regex-based parsing
            return HTMLTableParser._fallback_table_parsing(html_content)

    @staticmethod
    def _clean_html_content(html_content: str) -> str:
        """Clean HTML content for better parsing"""
        # Remove common problematic elements
        cleaned = re.sub(r'<(?:script|style)[^>]*>.*?</(?:script|style)>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

        # Fix common HTML issues
        cleaned = re.sub(r'<br\s*/?>', '<br/>', cleaned)
        cleaned = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', cleaned)

        return cleaned

    @staticmethod
    def _parse_single_table(table_element: ET.Element) -> HTMLTableData:
        """Parse a single table element into structured data"""
        rows = table_element.findall(".//tr")
        if not rows:
            return []

        # Extract headers
        header_row = rows[0]
        headers = []
        for th in header_row.findall(".//th") or header_row.findall(".//td"):
            text = ET.tostring(th, method='text', encoding='unicode').strip()
            headers.append(text or f"Column_{len(headers)}")

        # Extract data rows
        table_data = []
        for row in rows[1:]:
            cells = row.findall(".//td") or row.findall(".//th")
            if len(cells) == len(headers):
                row_data = {}
                for i, cell in enumerate(cells):
                    cell_text = ET.tostring(cell, method='text', encoding='unicode').strip()
                    row_data[headers[i]] = cell_text
                table_data.append(row_data)

        return table_data

    @staticmethod
    def _fallback_table_parsing(html_content: str) -> HTMLTableData:
        """Simple regex-based fallback for malformed HTML"""
        table_pattern = r'<table[^>]*>(.*?)</table>'
        row_pattern = r'<tr[^>]*>(.*?)</tr>'
        cell_pattern = r'<(?:td|th)[^>]*>(.*?)</(?:td|th)>'

        tables = re.findall(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
        all_data = []

        for table in tables:
            rows = re.findall(row_pattern, table, re.DOTALL | re.IGNORECASE)
            if not rows:
                continue

            # First row as headers
            first_row_cells = re.findall(cell_pattern, rows[0], re.DOTALL | re.IGNORECASE)
            headers = [re.sub(r'<[^>]+>', '', cell).strip() for cell in first_row_cells]

            # Data rows
            for row in rows[1:]:
                cells = re.findall(cell_pattern, row, re.DOTALL | re.IGNORECASE)
                if len(cells) == len(headers):
                    row_data = {}
                    for i, cell in enumerate(cells):
                        clean_cell = re.sub(r'<[^>]+>', '', cell).strip()
                        row_data[headers[i]] = clean_cell
                    all_data.append(row_data)

        return all_data
