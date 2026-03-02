"""
Semantic validation for AI-generated test cases.

This module validates that test cases use correct signal names,
parameters, and values based on the requirement context.
"""

import re
from difflib import get_close_matches
from typing import Any


class SemanticValidator:
    """Validates semantic correctness of test cases"""

    __slots__ = ("logger", "similarity_threshold")

    def __init__(self, logger=None, similarity_threshold: float = 0.8):
        """
        Initialize semantic validator.

        Args:
            logger: Optional logger instance
            similarity_threshold: Fuzzy match threshold (0.0-1.0)
        """
        self.logger = logger
        self.similarity_threshold = similarity_threshold

    def validate_test_case(
        self, test_case: dict[str, Any], requirement: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """
        Validate a single test case against requirement context.

        Args:
            test_case: Generated test case
            requirement: Original requirement with context

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Extract interface dictionary from requirement
        interface_list = requirement.get("interface_list", [])
        if not interface_list:
            # No interfaces to validate against
            return True, []

        # Build valid signal names from interface dictionary
        valid_signal_names = self._extract_signal_names(interface_list)

        # Validate signal names in test case
        signal_issues = self._validate_signals(test_case, valid_signal_names)
        issues.extend(signal_issues)

        # Validate data field format
        data_issues = self._validate_data_format(test_case)
        issues.extend(data_issues)

        is_valid = len(issues) == 0

        if not is_valid and self.logger:
            self.logger.warning(
                f"Semantic validation failed for test case: {test_case.get('summary_suffix', 'N/A')}"
            )
            for issue in issues:
                self.logger.warning(f"  - {issue}")

        return is_valid, issues

    def _extract_signal_names(self, interface_list: list[dict[str, Any]]) -> set[str]:
        """
        Extract valid signal names from interface dictionary.

        Examples:
          "CANSignal - ACCSP (Message: FCM1S39)" → "ACCSP"
          "InternalSignal - IgnMode" → "IgnMode"
          "NVM - NVM_ACCExistFlag (Dropped)" → "NVM_ACCExistFlag"
        """
        signal_names = set()

        for interface in interface_list:
            text = interface.get("text", "")

            # Pattern 1: "SignalType - SignalName (extra info)"
            match = re.search(r"-\s+([A-Za-z_][A-Za-z0-9_]*)", text)
            if match:
                signal_names.add(match.group(1))
                continue

            # Pattern 2: "SignalName" (simple case)
            match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]{2,})\b", text)
            if match:
                signal_names.add(match.group(1))

        return signal_names

    def _validate_signals(self, test_case: dict[str, Any], valid_signals: set[str]) -> list[str]:
        """
        Validate signal names in test case action and data fields.

        Returns:
            List of validation issues
        """
        if not valid_signals:
            return []

        issues = []

        # Check action field
        action = test_case.get("action", "")
        # Match signal names: ALL_CAPS (3+ chars to avoid ON/OFF) or CamelCase (multiple parts)
        detected_signals = re.findall(
            r"\b([A-Z]{3,}[A-Z0-9_]*|[A-Z][a-z]+(?:[A-Z][a-z]+)+)\b", action
        )

        for signal in detected_signals:
            if signal not in valid_signals:
                # Try fuzzy matching
                close_matches = get_close_matches(
                    signal, valid_signals, n=1, cutoff=self.similarity_threshold
                )
                if close_matches:
                    issues.append(
                        f"Signal '{signal}' in action not found. Did you mean '{close_matches[0]}'?"
                    )
                else:
                    issues.append(
                        f"Signal '{signal}' in action not in interface dictionary. "
                        f"Valid signals: {', '.join(sorted(valid_signals))}"
                    )

        # Check data field
        data = test_case.get("data", "")
        data_signals = re.findall(r"([A-Za-z_][A-Za-z0-9_]+)\s*=", data)

        for signal in data_signals:
            if signal not in valid_signals:
                close_matches = get_close_matches(
                    signal, valid_signals, n=1, cutoff=self.similarity_threshold
                )
                if close_matches:
                    issues.append(
                        f"Signal '{signal}' in data not found. Did you mean '{close_matches[0]}'?"
                    )

        return issues

    def _validate_data_format(self, test_case: dict[str, Any]) -> list[str]:
        """
        Validate data field follows expected format.

        Expected formats:
          - "Signal1=value1, Signal2=value2"
          - "1. Step one\n2. Step two"
        """
        issues = []
        data = test_case.get("data", "")

        if not data or not data.strip():
            issues.append("Data field is empty")
            return issues

        # Check for common formatting issues
        if "=" in data:
            # Should be "Signal=Value" format
            parts = data.split(",")
            for part in parts:
                part = part.strip()
                if "=" not in part:
                    issues.append(f"Data part '{part}' missing '=' assignment")

        return issues

    def validate_batch(
        self, test_cases: list[dict[str, Any]], requirement: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate a batch of test cases for a single requirement.

        Returns:
            Validation report with statistics and issues
        """
        total = len(test_cases)
        valid_count = 0
        all_issues = []

        for idx, test_case in enumerate(test_cases, 1):
            is_valid, issues = self.validate_test_case(test_case, requirement)

            if is_valid:
                valid_count += 1
            else:
                all_issues.append(
                    {
                        "test_case_index": idx,
                        "summary": test_case.get("summary_suffix", "N/A"),
                        "issues": issues,
                    }
                )

        # Check table coverage for table-based requirements
        table_issues = self._validate_table_coverage(test_cases, requirement)
        all_issues.extend(table_issues)

        report = {
            "total_test_cases": total,
            "valid_count": valid_count,
            "invalid_count": total - valid_count + len(table_issues),
            "validation_rate": valid_count / total if total > 0 else 0,
            "issues": all_issues,
            "table_coverage": self._analyze_table_coverage(test_cases, requirement),
        }

        return report

    def _validate_table_coverage(
        self, test_cases: list[dict[str, Any]], requirement: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Validate that table-based requirements have adequate test coverage.

        For table-based requirements, ensure:
        1. At least one positive test case per table row
        2. At least 3 negative test cases
        3. Total test cases reasonable for table size

        Args:
            test_cases: Generated test cases
            requirement: Requirement with table data

        Returns:
            List of coverage validation issues
        """
        issues = []

        # Check if this is a table-based requirement
        table_data = requirement.get("table")
        if not table_data:
            return issues  # Not table-based, skip

        required_rows = table_data.get("rows", 0)
        if required_rows == 0:
            return issues  # No table rows to cover

        # Count positive and negative test cases
        positive_count = sum(1 for tc in test_cases if tc.get("test_type") == "positive")
        negative_count = sum(1 for tc in test_cases if tc.get("test_type") == "negative")

        # Validate coverage
        if positive_count < required_rows:
            issues.append(
                {
                    "test_case_index": -1,  # Global issue, not specific to one test case
                    "summary": "Table Coverage Deficiency",
                    "issues": [
                        f"Generated {positive_count} positive test cases but table has {required_rows} rows. "
                        f"Required: at least one positive test per table row."
                    ],
                }
            )

        if negative_count < 3:
            issues.append(
                {
                    "test_case_index": -1,
                    "summary": "Negative Test Deficiency",
                    "issues": [
                        f"Generated {negative_count} negative test cases but minimum 3 required for table-based requirements."
                    ],
                }
            )

        total_expected_min = required_rows + 3  # At least one per row + 3 negative
        total_expected_max = required_rows + 8  # Reasonable maximum for negatives

        if len(test_cases) < total_expected_min:
            issues.append(
                {
                    "test_case_index": -1,
                    "summary": "Total Test Case Count",
                    "issues": [
                        f"Generated {len(test_cases)} test cases. Expected minimum: {total_expected_min} "
                        f"({required_rows} positive + 3 negative). Expected maximum: {total_expected_max}."
                    ],
                }
            )

        return issues

    def _analyze_table_coverage(
        self, test_cases: list[dict[str, Any]], requirement: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze table coverage and return statistics.

        Args:
            test_cases: Generated test cases
            requirement: Requirement with table data

        Returns:
            Coverage analysis statistics
        """
        table_data = requirement.get("table")

        if not table_data:
            return {"is_table_based": False}

        required_rows = table_data.get("rows", 0)
        positive_count = sum(1 for tc in test_cases if tc.get("test_type") == "positive")
        negative_count = sum(1 for tc in test_cases if tc.get("test_type") == "negative")

        coverage_percentage = (positive_count / required_rows * 100) if required_rows > 0 else 0

        return {
            "is_table_based": True,
            "required_table_rows": required_rows,
            "positive_test_cases": positive_count,
            "negative_test_cases": negative_count,
            "coverage_percentage": coverage_percentage,
            "adequate_coverage": positive_count >= required_rows and negative_count >= 3,
            "expected_min_total": required_rows + 3,
            "expected_max_total": required_rows + 8,
            "actual_total": len(test_cases),
        }
