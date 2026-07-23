"""
Semantic validation for AI-generated test cases.

This module validates that test cases use correct signal names,
parameters, and values based on the requirement context.
"""

import re
from difflib import get_close_matches
from typing import TYPE_CHECKING, Any

from .prompt_builder import MAX_PROMPT_TABLE_ROWS, displayed_table_rows

if TYPE_CHECKING:
    from src.file_processing_logger import FileProcessingLogger

# The one true schema emitted by the active prompt template and expected by
# every downstream component (deduplicator, formatter, validators).
CANONICAL_TEST_CASE_FIELDS: tuple[str, ...] = (
    "summary_suffix",
    "preconditions",
    "test_steps",
    "expected_result",
    "test_type",
)

# JSON Schema forwarded to Ollama's `format` parameter so the model is
# constrained to the canonical schema at generation time
# (review 2026-07-17 finding 4). Each field MUST declare a concrete type:
# Ollama compiles the schema into a llama.cpp grammar, and an empty `{}`
# per-field schema compiles to "emit an empty object `{}`" rather than
# "any value", which forced every field to `{}` and made 100% of generated
# test cases fail canonical validation (verified against a live llama3.1:8b
# run, 2026-07-20). `test_steps` is authored as a newline-joined string; the
# downstream list->string normalisation in validators still tolerates a list
# if an unconstrained backend ever returns one.
TEST_CASE_RESPONSE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "test_cases": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {field: {"type": "string"} for field in CANONICAL_TEST_CASE_FIELDS},
                "required": list(CANONICAL_TEST_CASE_FIELDS),
            },
        }
    },
    "required": ["test_cases"],
}


# Retired v3 output-field directives. The archived template instructed the
# model to emit `action`/`data` fields; the active canonical schema uses
# `test_steps`/`expected_result`. An active template that still references
# these directives contradicts the schema and produces rows the downstream
# validator rejects (review 2026-07-20 finding 4). Matched as backtick-quoted
# JSON key directives so ordinary prose ("table data", "trigger action") does
# not false-positive.
RETIRED_FIELD_DIRECTIVES: tuple[str, ...] = ('`"data"`', '`"action"`')


def template_schema_issues(rendered_template: str) -> list[str]:
    """Return semantic schema problems in a rendered prompt template.

    Complements the render check in `--validate-prompts`: renderability alone
    does not catch a template that instructs a schema the pipeline rejects.

    Args:
        rendered_template: A fully rendered prompt template string.

    Returns:
        A list of human-readable issues. Empty when the template instructs the
        canonical schema and references no retired field directives.
    """
    issues: list[str] = []

    for directive in RETIRED_FIELD_DIRECTIVES:
        if directive in rendered_template:
            issues.append(f"references retired output-field directive {directive}")

    for field in CANONICAL_TEST_CASE_FIELDS:
        if f'"{field}"' not in rendered_template:
            issues.append(f'missing canonical field directive "{field}"')

    return issues


def is_canonical_test_case(test_case: Any) -> bool:
    """Check that a test case carries every canonical field with content.

    A field counts as present when it is a non-blank string or a list that
    joins to a non-blank string (the model sometimes returns test_steps as
    a list; validators normalise that downstream).

    Args:
        test_case: Parsed test-case candidate from the AI response.

    Returns:
        True when the candidate is a dict with all canonical fields filled.
    """
    if not isinstance(test_case, dict):
        return False

    for field in CANONICAL_TEST_CASE_FIELDS:
        value = test_case.get(field)
        if isinstance(value, list):
            value = "\n".join(str(item) for item in value)
        if not isinstance(value, str) or not value.strip():
            return False

    return True


class SemanticValidator:
    """Validates semantic correctness of test cases"""

    __slots__ = ("logger", "similarity_threshold", "max_prompt_table_rows")

    def __init__(
        self,
        logger: FileProcessingLogger | None = None,
        similarity_threshold: float = 0.8,
        max_prompt_table_rows: int | None = None,
    ):
        """
        Initialize semantic validator.

        Args:
            logger: Optional logger instance
            similarity_threshold: Fuzzy match threshold (0.0-1.0)
            max_prompt_table_rows: Table-truncation threshold used by the
                prompt builder; coverage checks are scoped to the rows the
                model actually saw (review 2026-07-17 finding 7)
        """
        self.logger = logger
        self.similarity_threshold = similarity_threshold
        self.max_prompt_table_rows = max_prompt_table_rows or MAX_PROMPT_TABLE_ROWS

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
        # Extract interface dictionary from requirement
        interface_list = requirement.get("interface_list", [])
        if not interface_list:
            # No interfaces to validate against
            return True, []

        # Build valid signal names from interface dictionary
        valid_signal_names = self._extract_signal_names(interface_list)

        return self._validate_with_signals(test_case, valid_signal_names)

    def _validate_with_signals(
        self, test_case: dict[str, Any], valid_signal_names: set[str]
    ) -> tuple[bool, list[str]]:
        """Validate a test case against a pre-built signal-name set.

        validate_batch builds the signal set once and reuses it for every
        test case in the batch.
        """
        issues = []

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

        # Check data field (support both 'data' and 'test_steps' formats)
        # test_steps may be a list (AI returns numbered steps as a list)
        raw_data = test_case.get("data", test_case.get("test_steps", ""))
        data = "\n".join(raw_data) if isinstance(raw_data, list) else str(raw_data)
        data_signals = re.findall(r"([A-Za-z_][A-Za-z0-9_]+)\s*=", data)

        # Only signal-shaped identifiers (ALL_CAPS or multi-part CamelCase)
        # are reported as unknown; generic words like 'Voltage' assigned in
        # preconditions/steps would otherwise flood validation with false
        # positives
        signal_like = re.compile(r"[A-Z]{3,}[A-Z0-9_]*|[A-Z][a-z]+(?:[A-Z][a-z]+)+")

        for signal in data_signals:
            if signal in valid_signals:
                continue
            close_matches = get_close_matches(
                signal, valid_signals, n=1, cutoff=self.similarity_threshold
            )
            if close_matches:
                issues.append(
                    f"Signal '{signal}' in data/test_steps not found. Did you mean '{close_matches[0]}'?"
                )
            elif signal_like.fullmatch(signal):
                issues.append(
                    f"Signal '{signal}' in data/test_steps not in interface dictionary. "
                    f"Valid signals: {', '.join(sorted(valid_signals))}"
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
        # Support both 'data' and 'test_steps' keys (may be a list)
        raw_data = test_case.get("data", test_case.get("test_steps", ""))
        data = "\n".join(raw_data) if isinstance(raw_data, list) else str(raw_data)

        if not data or not data.strip():
            issues.append("Data field is empty")
            return issues

        # Check for common formatting issues
        if "=" in str(data):
            # Should be "Signal=Value" format
            parts = str(data).split(",")
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

        # Build the signal-name set once for the whole batch
        interface_list = requirement.get("interface_list", [])
        valid_signal_names = self._extract_signal_names(interface_list) if interface_list else set()

        for idx, test_case in enumerate(test_cases, 1):
            if valid_signal_names:
                is_valid, issues = self._validate_with_signals(test_case, valid_signal_names)
            else:
                is_valid, issues = True, []

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
        issues: list[dict] = []

        # Check if this is a table-based requirement
        table_data = requirement.get("table")
        if not table_data:
            return issues  # Not table-based, skip

        total_rows = table_data.get("rows", 0)
        if total_rows == 0:
            return issues  # No table rows to cover

        # Coverage is owed only for the rows the prompt actually displayed:
        # oversized tables are truncated and the model is told to cover the
        # displayed rows only (review 2026-07-17 finding 7)
        required_rows = displayed_table_rows(total_rows, self.max_prompt_table_rows)
        truncated_note = (
            f" (table truncated in prompt: {required_rows} of {total_rows} rows displayed)"
            if required_rows < total_rows
            else ""
        )

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
                        f"Generated {positive_count} positive test cases but {required_rows} "
                        f"displayed table rows require coverage{truncated_note}. "
                        f"Required: at least one positive test per displayed row."
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

        total_rows = table_data.get("rows", 0)
        # Coverage is owed only for the displayed rows (see
        # _validate_table_coverage / review 2026-07-17 finding 7)
        required_rows = displayed_table_rows(total_rows, self.max_prompt_table_rows)
        positive_count = sum(1 for tc in test_cases if tc.get("test_type") == "positive")
        negative_count = sum(1 for tc in test_cases if tc.get("test_type") == "negative")

        coverage_percentage = (positive_count / required_rows * 100) if required_rows > 0 else 0

        return {
            "is_table_based": True,
            "required_table_rows": required_rows,
            "total_table_rows": total_rows,
            "truncated": required_rows < total_rows,
            "positive_test_cases": positive_count,
            "negative_test_cases": negative_count,
            "coverage_percentage": coverage_percentage,
            "adequate_coverage": positive_count >= required_rows and negative_count >= 3,
            "expected_min_total": required_rows + 3,
            "expected_max_total": required_rows + 8,
            "actual_total": len(test_cases),
        }
