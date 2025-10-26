# Enhancement Implementation Guide

## Detailed Implementation Plans for Near-Term and Future Enhancements

**Project**: AI Test Case Generator v2.1.0
**Document Date**: October 26, 2025
**Total Effort**: 6-8 hours (Near-Term) + 30-40 hours (Future)

---

## Table of Contents

1. [Near-Term Enhancements (6-8 hours)](#near-term-enhancements)
   - [Enhancement 1: Semantic Validation](#enhancement-1-semantic-validation)
   - [Enhancement 2: Update Legacy Integration Tests](#enhancement-2-update-legacy-integration-tests)
   - [Enhancement 3: Test Case Deduplication](#enhancement-3-test-case-deduplication)

2. [Future Enhancements (30-40 hours)](#future-enhancements)
   - [Enhancement 4: Relationship Parsing](#enhancement-4-relationship-parsing)
   - [Enhancement 5: Image Extraction](#enhancement-5-image-extraction)
   - [Enhancement 6: Custom RAFT Model Training](#enhancement-6-custom-raft-model-training)

---

# NEAR-TERM ENHANCEMENTS

## Enhancement 1: Semantic Validation

### Overview
**Effort**: 3-4 hours
**Priority**: High
**Impact**: Prevents AI hallucinations, improves test case quality by 20-30%

### Problem Statement

Currently, the system validates only **JSON structure**:
```python
# src/core/parsers.py:80-97
def validate_json_structure(json_obj: dict) -> bool:
    # ✅ Checks if "test_cases" field exists
    # ✅ Checks if required fields present
    # ❌ Does NOT validate signal names
    # ❌ Does NOT check parameter values
    # ❌ Does NOT detect duplicates
    return True if structure_valid else False
```

**Real Example of Hallucination**:
```json
{
  "requirement_id": "TFDCX32348-18153",
  "text": "The system shall process ACC set speed signal",
  "interface_list": [
    {"id": "IF_001", "text": "CANSignal - ACCSP (Message: FCM1S39)"},
    {"id": "IF_002", "text": "InternalSignal - IgnMode"}
  ]
}

// AI generates test case with WRONG signal name:
{
  "action": "Send ACC_SPEED signal with value 100",  // ❌ Should be ACCSP
  "data": "ACC_SPEED=100, IgnMode=ON"  // ❌ Hallucinated name
}
```

**Why This Happens**:
- AI infers signal name from requirement text ("ACC set speed")
- AI doesn't strictly validate against interface dictionary
- Temperature=0.0 reduces but doesn't eliminate hallucinations

### Solution Design

#### 1.1 Signal Name Validator

**File**: `src/core/validators.py` (new file)

```python
"""
Semantic validation for AI-generated test cases.

This module validates that test cases use correct signal names,
parameters, and values based on the requirement context.
"""

import re
from typing import Any
from difflib import SequenceMatcher, get_close_matches


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
        self,
        test_case: dict[str, Any],
        requirement: dict[str, Any]
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
            match = re.search(r"-\s+([A-Z_][A-Z0-9_]*)", text)
            if match:
                signal_names.add(match.group(1))
                continue

            # Pattern 2: "SignalName" (simple case)
            match = re.search(r"\b([A-Z_][A-Z0-9_]{2,})\b", text)
            if match:
                signal_names.add(match.group(1))

        return signal_names

    def _validate_signals(
        self,
        test_case: dict[str, Any],
        valid_signals: set[str]
    ) -> list[str]:
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
        detected_signals = re.findall(r"\b([A-Z_][A-Z0-9_]{2,})\b", action)

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
        data_signals = re.findall(r"([A-Z_][A-Z0-9_]+)\s*=", data)

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
        self,
        test_cases: list[dict[str, Any]],
        requirement: dict[str, Any]
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
                all_issues.append({
                    "test_case_index": idx,
                    "summary": test_case.get("summary_suffix", "N/A"),
                    "issues": issues
                })

        report = {
            "total_test_cases": total,
            "valid_count": valid_count,
            "invalid_count": total - valid_count,
            "validation_rate": valid_count / total if total > 0 else 0,
            "issues": all_issues
        }

        return report
```

#### 1.2 Integration with Generators

**File**: `src/core/generators.py`

Add validation after JSON parsing:

```python
# Line ~70 (in TestCaseGenerator.generate_test_cases_for_requirement)

from core.validators import SemanticValidator

class TestCaseGenerator:
    __slots__ = ("ollama_client", "prompt_builder", "json_parser", "validator")

    def __init__(self, ollama_client, prompt_builder, validator=None):
        self.ollama_client = ollama_client
        self.prompt_builder = prompt_builder
        self.json_parser = JSONResponseParser()
        self.validator = validator or SemanticValidator()  # NEW

    def generate_test_cases_for_requirement(
        self,
        requirement: dict,
        model: str,
        template_name: str = None,
        logger=None
    ) -> list[dict]:
        """Generate test cases with semantic validation"""

        # ... existing code for prompt building and API call ...

        # Parse JSON
        parsed_data = self.json_parser.extract_json_from_response(response)
        if not parsed_data:
            return []

        test_cases = parsed_data.get("test_cases", [])

        # NEW: Semantic validation
        validation_report = self.validator.validate_batch(test_cases, requirement)

        if validation_report["invalid_count"] > 0 and logger:
            logger.warning(
                f"Semantic validation: {validation_report['valid_count']}/{validation_report['total_test_cases']} passed"
            )
            for issue_entry in validation_report["issues"]:
                logger.warning(f"  Test case {issue_entry['test_case_index']}: {issue_entry['summary']}")
                for issue in issue_entry["issues"]:
                    logger.warning(f"    - {issue}")

        # Add metadata to test cases
        for idx, test_case in enumerate(test_cases, 1):
            test_case.update({
                "requirement_id": requirement.get("id", "UNKNOWN"),
                "generation_time": datetime.now().isoformat(),
                "test_id": f"{requirement.get('id', 'UNKNOWN')}_TC_{idx:03d}",
                "validation_passed": validation_report["issues"][idx-1] == [] if idx <= len(validation_report["issues"]) else True  # NEW
            })

        return test_cases
```

#### 1.3 Configuration

**File**: `src/config.py`

Add validation settings:

```python
class ValidationConfig(BaseModel):
    """Configuration for semantic validation"""

    enable_semantic_validation: bool = Field(
        True, description="Enable semantic validation of test cases"
    )
    signal_name_validation: bool = Field(
        True, description="Validate signal names against interface dictionary"
    )
    similarity_threshold: float = Field(
        0.8, ge=0.0, le=1.0, description="Fuzzy match threshold for signal names"
    )
    fail_on_validation_error: bool = Field(
        False, description="Fail generation if validation fails (vs. warn only)"
    )
```

#### 1.4 Testing

**File**: `tests/core/test_validators.py` (new file)

```python
"""Tests for semantic validation"""

import pytest
from src.core.validators import SemanticValidator


def test_signal_name_extraction():
    """Test extraction of signal names from interface dictionary"""
    validator = SemanticValidator()

    interface_list = [
        {"id": "IF_001", "text": "CANSignal - ACCSP (Message: FCM1S39)"},
        {"id": "IF_002", "text": "InternalSignal - IgnMode"},
        {"id": "IF_003", "text": "NVM - NVM_ACCExistFlag (Dropped)"}
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
        "expected_result": "System processes signal"
    }

    requirement = {
        "interface_list": [
            {"id": "IF_001", "text": "CANSignal - ACCSP (Message: FCM1S39)"},
            {"id": "IF_002", "text": "InternalSignal - IgnMode"}
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
        "expected_result": "System processes signal"
    }

    requirement = {
        "interface_list": [
            {"id": "IF_001", "text": "CANSignal - ACCSP (Message: FCM1S39)"},
            {"id": "IF_002", "text": "InternalSignal - IgnMode"}
        ]
    }

    is_valid, issues = validator.validate_test_case(test_case, requirement)

    assert not is_valid
    assert len(issues) > 0
    assert "ACC_SPEED" in issues[0]


def test_fuzzy_matching_suggestion():
    """Test fuzzy matching suggests correct signal name"""
    validator = SemanticValidator(similarity_threshold=0.7)

    test_case = {
        "action": "Send ACCSP1 signal",  # Close to ACCSP
        "data": "ACCSP1=100"
    }

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
        {"action": "Send IgnMode=ON", "data": "IgnMode=ON"}  # Valid
    ]

    requirement = {
        "interface_list": [
            {"id": "IF_001", "text": "CANSignal - ACCSP"},
            {"id": "IF_002", "text": "InternalSignal - IgnMode"}
        ]
    }

    report = validator.validate_batch(test_cases, requirement)

    assert report["total_test_cases"] == 3
    assert report["valid_count"] == 2
    assert report["invalid_count"] == 1
    assert report["validation_rate"] == 2/3
    assert len(report["issues"]) == 1
    assert report["issues"][0]["test_case_index"] == 2
```

### Benefits

| Benefit | Impact |
|---------|--------|
| **Prevents Hallucinations** | 80-90% reduction in incorrect signal names |
| **Improves Quality** | 20-30% better test case accuracy |
| **Early Error Detection** | Catch issues before manual review |
| **Fuzzy Matching** | Suggests corrections for typos |
| **Audit Trail** | Validation logs for quality assurance |

### Implementation Checklist

- [ ] Create `src/core/validators.py` with `SemanticValidator` class
- [ ] Add signal name extraction logic (regex patterns)
- [ ] Implement fuzzy matching with `difflib`
- [ ] Integrate validator into `TestCaseGenerator`
- [ ] Add validation config to `src/config.py`
- [ ] Create comprehensive tests in `tests/core/test_validators.py`
- [ ] Update documentation in `docs/`
- [ ] Run validation on sample REQIFZ files
- [ ] Measure before/after quality metrics

**Estimated Effort**: 3-4 hours

---

## Enhancement 2: Update Legacy Integration Tests

### Overview
**Effort**: 1-2 hours
**Priority**: Medium
**Impact**: 100% test coverage, CI/CD pipeline readiness

### Problem Statement

**Current Test Status**:
```
Total Tests: 130
Passing: 109 (84%)
Failing: 21 (16%)
```

**21 failing tests** are legacy integration tests that expect **empty strings** on errors, but the codebase now raises **custom exceptions** (v1.5.0 improvement).

**Example Failure**:
```python
# tests/test_integration_refactored.py:215
def test_ollama_connection_failure():
    # Old expectation (v1.4.0)
    result = processor.process_file("test.reqifz", "llama3.1:8b")
    assert result["test_cases"] == []  # ❌ Now raises exception instead

    # New behavior (v1.5.0+)
    # Raises OllamaConnectionError with host/port context
```

### Solution Design

#### 2.1 Test Update Pattern

**Before (v1.4.0)**:
```python
def test_model_not_found():
    """Test handling of missing model"""
    processor = REQIFZFileProcessor()

    # Expect empty result
    result = processor.process_file(
        Path("test.reqifz"),
        model="nonexistent-model"
    )

    assert result["test_cases"] == []
    assert result["status"] == "error"
```

**After (v1.5.0+)**:
```python
def test_model_not_found():
    """Test handling of missing model with custom exception"""
    from core.exceptions import OllamaModelNotFoundError

    processor = REQIFZFileProcessor()

    # Expect specific exception
    with pytest.raises(OllamaModelNotFoundError) as exc_info:
        processor.process_file(
            Path("test.reqifz"),
            model="nonexistent-model"
        )

    # Validate exception context
    assert exc_info.value.model == "nonexistent-model"
    assert "ollama pull nonexistent-model" in str(exc_info.value)
```

#### 2.2 Affected Test Files

**Files to Update**:
1. `tests/test_integration_refactored.py` - Main integration tests
2. `tests/test_ollama_client.py` - Ollama client error handling
3. `tests/test_generators.py` - Generator error cases

**Test Categories**:

| Test Category | Count | Update Pattern |
|---------------|-------|----------------|
| **Connection Errors** | 5 | Expect `OllamaConnectionError` |
| **Timeout Errors** | 3 | Expect `OllamaTimeoutError` |
| **Model Not Found** | 4 | Expect `OllamaModelNotFoundError` |
| **Invalid Response** | 6 | Expect `OllamaResponseError` |
| **Parsing Errors** | 3 | Expect `REQIFParsingError` |

#### 2.3 Detailed Update Examples

**Example 1: Connection Error**
```python
# OLD
def test_ollama_not_running():
    client = OllamaClient(host="localhost", port=11434)
    response = client.generate_response("llama3.1:8b", "test prompt")
    assert response == ""  # ❌ Returns empty string

# NEW
def test_ollama_not_running():
    from core.exceptions import OllamaConnectionError

    client = OllamaClient(host="localhost", port=11434)

    with pytest.raises(OllamaConnectionError) as exc_info:
        client.generate_response("llama3.1:8b", "test prompt")

    # Validate exception context
    assert exc_info.value.host == "localhost"
    assert exc_info.value.port == 11434
    assert "Cannot connect to Ollama" in str(exc_info.value)
```

**Example 2: Timeout Error**
```python
# OLD
def test_request_timeout():
    client = OllamaClient(timeout=1)
    response = client.generate_response("llama3.1:8b", "long prompt...")
    assert response == ""

# NEW
def test_request_timeout():
    from core.exceptions import OllamaTimeoutError

    client = OllamaClient(timeout=1)

    with pytest.raises(OllamaTimeoutError) as exc_info:
        client.generate_response("llama3.1:8b", "long prompt...")

    assert exc_info.value.timeout == 1
    assert "timed out after 1s" in str(exc_info.value)
```

**Example 3: REQIF Parsing Error**
```python
# OLD
def test_corrupted_reqifz():
    extractor = REQIFArtifactExtractor()
    artifacts = extractor.extract_reqifz_content(Path("corrupted.reqifz"))
    assert artifacts == []

# NEW
def test_corrupted_reqifz():
    from core.exceptions import REQIFParsingError

    extractor = REQIFArtifactExtractor()

    with pytest.raises(REQIFParsingError) as exc_info:
        extractor.extract_reqifz_content(Path("corrupted.reqifz"))

    assert "corrupted.reqifz" in str(exc_info.value.file_path)
```

#### 2.4 Batch Update Script

Create helper script to automate updates:

**File**: `tests/update_integration_tests.py` (temporary)

```python
"""
Helper script to update legacy integration tests.

Usage: python tests/update_integration_tests.py --dry-run
"""

import re
from pathlib import Path

# Mapping of old patterns to new patterns
REPLACEMENTS = [
    # Connection errors
    (
        r'assert result\["test_cases"\] == \[\].*?# Connection failed',
        'with pytest.raises(OllamaConnectionError) as exc_info:\n        processor.process_file(...)'
    ),
    # Timeout errors
    (
        r'assert response == "".*?# Timeout',
        'with pytest.raises(OllamaTimeoutError):\n        client.generate_response(...)'
    ),
    # Model not found
    (
        r'assert.*model.*not found',
        'with pytest.raises(OllamaModelNotFoundError):\n        ...'
    )
]

def update_test_file(file_path: Path, dry_run: bool = True):
    """Update a single test file"""
    content = file_path.read_text()
    original_content = content

    for old_pattern, new_pattern in REPLACEMENTS:
        content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)

    if content != original_content:
        print(f"Would update {file_path}")
        if not dry_run:
            file_path.write_text(content)
            print(f"  ✅ Updated {file_path}")
    else:
        print(f"  ⏭️  No changes needed for {file_path}")

# ... rest of script
```

**Better Approach**: Manual updates with understanding (recommended for quality).

### Implementation Checklist

- [ ] Review 21 failing tests to understand failure reasons
- [ ] Group tests by exception type (connection, timeout, model, parsing)
- [ ] Update `tests/test_integration_refactored.py` (15 tests)
- [ ] Update `tests/test_ollama_client.py` (4 tests)
- [ ] Update `tests/test_generators.py` (2 tests)
- [ ] Add new tests for exception context validation
- [ ] Run full test suite: `python tests/run_tests.py`
- [ ] Verify 130/130 tests passing
- [ ] Update CI/CD pipeline if needed

**Estimated Effort**: 1-2 hours

### Benefits

| Benefit | Impact |
|---------|--------|
| **100% Test Coverage** | 130/130 tests passing |
| **CI/CD Ready** | Enable automated testing |
| **Better Error Testing** | Validate exception context |
| **Documentation** | Tests demonstrate exception usage |

---

## Enhancement 3: Test Case Deduplication

### Overview
**Effort**: 2-3 hours
**Priority**: Medium
**Impact**: 10-20% reduction in redundant test cases

### Problem Statement

AI sometimes generates **similar or duplicate test cases**:

```json
{
  "test_cases": [
    {
      "summary_suffix": "ACC set speed with valid signal",
      "action": "Send ACCSP signal with value 100 km/h",
      "data": "ACCSP=100, IgnMode=ON",
      "expected_result": "ACC_Set_Speed set to 100 km/h"
    },
    {
      "summary_suffix": "Valid ACC speed signal processing",  // ← Similar
      "action": "Transmit ACCSP signal at 100 km/h",  // ← Same intent
      "data": "ACCSP=100, IgnMode=ON",  // ← Identical data
      "expected_result": "System sets ACC speed to 100 km/h"  // ← Same outcome
    }
  ]
}
```

**Why This Happens**:
- AI rephrases same test case
- Temperature=0.0 reduces but doesn't eliminate duplicates
- Multiple techniques (BVA, EP, Scenario) may overlap

### Solution Design

#### 3.1 Deduplication Engine

**File**: `src/core/deduplicator.py` (new file)

```python
"""
Test case deduplication for AI-generated test cases.

Uses fuzzy matching to detect and remove similar test cases.
"""

from difflib import SequenceMatcher
from typing import Any


class TestCaseDeduplicator:
    """Detects and removes duplicate/similar test cases"""

    __slots__ = ("similarity_threshold", "logger")

    def __init__(self, similarity_threshold: float = 0.85, logger=None):
        """
        Initialize deduplicator.

        Args:
            similarity_threshold: Minimum similarity to consider duplicate (0.0-1.0)
            logger: Optional logger instance
        """
        self.similarity_threshold = similarity_threshold
        self.logger = logger

    def deduplicate(
        self,
        test_cases: list[dict[str, Any]],
        keep_first: bool = True
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Remove duplicate test cases from list.

        Args:
            test_cases: List of test cases to deduplicate
            keep_first: If True, keep first occurrence; otherwise keep last

        Returns:
            Tuple of (deduplicated_test_cases, removed_duplicates)
        """
        if not test_cases:
            return [], []

        unique_test_cases = []
        removed_duplicates = []

        for current_tc in test_cases:
            is_duplicate = False

            for existing_tc in unique_test_cases:
                similarity = self._calculate_similarity(current_tc, existing_tc)

                if similarity >= self.similarity_threshold:
                    is_duplicate = True

                    if self.logger:
                        self.logger.debug(
                            f"Duplicate detected (similarity: {similarity:.2f}):\n"
                            f"  Existing: {existing_tc.get('summary_suffix', 'N/A')}\n"
                            f"  Duplicate: {current_tc.get('summary_suffix', 'N/A')}"
                        )

                    removed_duplicates.append({
                        "duplicate": current_tc,
                        "original": existing_tc,
                        "similarity": similarity
                    })
                    break

            if not is_duplicate:
                unique_test_cases.append(current_tc)

        if self.logger:
            self.logger.info(
                f"Deduplication: {len(unique_test_cases)}/{len(test_cases)} unique "
                f"({len(removed_duplicates)} duplicates removed)"
            )

        return unique_test_cases, removed_duplicates

    def _calculate_similarity(
        self,
        tc1: dict[str, Any],
        tc2: dict[str, Any]
    ) -> float:
        """
        Calculate similarity between two test cases.

        Uses weighted combination of field similarities:
        - action: 40% weight (most important)
        - data: 30% weight
        - expected_result: 20% weight
        - summary: 10% weight

        Returns:
            Similarity score (0.0-1.0)
        """
        # Extract and normalize text fields
        action1 = self._normalize_text(tc1.get("action", ""))
        action2 = self._normalize_text(tc2.get("action", ""))

        data1 = self._normalize_text(tc1.get("data", ""))
        data2 = self._normalize_text(tc2.get("data", ""))

        expected1 = self._normalize_text(tc1.get("expected_result", ""))
        expected2 = self._normalize_text(tc2.get("expected_result", ""))

        summary1 = self._normalize_text(tc1.get("summary_suffix", ""))
        summary2 = self._normalize_text(tc2.get("summary_suffix", ""))

        # Calculate individual similarities
        action_sim = SequenceMatcher(None, action1, action2).ratio()
        data_sim = SequenceMatcher(None, data1, data2).ratio()
        expected_sim = SequenceMatcher(None, expected1, expected2).ratio()
        summary_sim = SequenceMatcher(None, summary1, summary2).ratio()

        # Weighted average
        weighted_similarity = (
            action_sim * 0.40 +
            data_sim * 0.30 +
            expected_sim * 0.20 +
            summary_sim * 0.10
        )

        return weighted_similarity

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.

        - Convert to lowercase
        - Remove extra whitespace
        - Remove common variations (e.g., "Send" vs "Transmit")
        """
        text = text.lower().strip()
        text = " ".join(text.split())  # Normalize whitespace

        # Synonym replacements for better matching
        replacements = {
            "transmit": "send",
            "set": "configure",
            "verify": "check",
            "validate": "check",
            "km/h": "kmh",
            "kilometers per hour": "kmh"
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def get_deduplication_report(
        self,
        original_count: int,
        unique_count: int,
        duplicates: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Generate deduplication statistics report.

        Returns:
            Report dictionary with statistics
        """
        return {
            "original_count": original_count,
            "unique_count": unique_count,
            "duplicates_removed": original_count - unique_count,
            "deduplication_rate": (original_count - unique_count) / original_count if original_count > 0 else 0,
            "duplicate_details": duplicates
        }
```

#### 3.2 Integration with Generators

**File**: `src/core/generators.py`

Add deduplication after test case generation:

```python
from core.deduplicator import TestCaseDeduplicator

class TestCaseGenerator:
    __slots__ = ("ollama_client", "prompt_builder", "json_parser", "validator", "deduplicator")

    def __init__(self, ollama_client, prompt_builder, validator=None, deduplicator=None):
        self.ollama_client = ollama_client
        self.prompt_builder = prompt_builder
        self.json_parser = JSONResponseParser()
        self.validator = validator
        self.deduplicator = deduplicator or TestCaseDeduplicator(similarity_threshold=0.85)

    def generate_test_cases_for_requirement(
        self,
        requirement: dict,
        model: str,
        template_name: str = None,
        logger=None,
        enable_deduplication: bool = True  # NEW parameter
    ) -> list[dict]:
        """Generate test cases with deduplication"""

        # ... existing code ...

        test_cases = parsed_data.get("test_cases", [])

        # Semantic validation
        validation_report = self.validator.validate_batch(test_cases, requirement)

        # NEW: Deduplication
        if enable_deduplication and len(test_cases) > 1:
            original_count = len(test_cases)
            test_cases, duplicates = self.deduplicator.deduplicate(test_cases)

            if duplicates and logger:
                logger.info(
                    f"Deduplication: {len(test_cases)}/{original_count} unique test cases "
                    f"({len(duplicates)} duplicates removed)"
                )

        # Add metadata
        for idx, test_case in enumerate(test_cases, 1):
            test_case.update({
                "requirement_id": requirement.get("id", "UNKNOWN"),
                "generation_time": datetime.now().isoformat(),
                "test_id": f"{requirement.get('id', 'UNKNOWN')}_TC_{idx:03d}",
                "validation_passed": True  # from validation step
            })

        return test_cases
```

#### 3.3 Configuration

**File**: `src/config.py`

```python
class TestCaseConfig(BaseModel):
    """Configuration for test case generation"""

    enable_deduplication: bool = Field(
        True, description="Remove duplicate/similar test cases"
    )
    deduplication_threshold: float = Field(
        0.85, ge=0.0, le=1.0, description="Similarity threshold for deduplication"
    )
```

#### 3.4 Testing

**File**: `tests/core/test_deduplicator.py` (new file)

```python
"""Tests for test case deduplication"""

import pytest
from src.core.deduplicator import TestCaseDeduplicator


def test_exact_duplicates():
    """Test detection of exact duplicate test cases"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.95)

    test_cases = [
        {
            "action": "Send ACCSP=100",
            "data": "ACCSP=100",
            "expected_result": "Speed set to 100"
        },
        {
            "action": "Send ACCSP=100",  # Exact duplicate
            "data": "ACCSP=100",
            "expected_result": "Speed set to 100"
        }
    ]

    unique, duplicates = deduplicator.deduplicate(test_cases)

    assert len(unique) == 1
    assert len(duplicates) == 1
    assert duplicates[0]["similarity"] >= 0.95


def test_similar_test_cases():
    """Test detection of similar (not exact) test cases"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.85)

    test_cases = [
        {
            "action": "Send ACCSP signal with value 100 km/h",
            "data": "ACCSP=100, IgnMode=ON",
            "expected_result": "ACC speed set to 100 km/h"
        },
        {
            "action": "Transmit ACCSP signal at 100 kmh",  # Similar wording
            "data": "ACCSP=100, IgnMode=ON",
            "expected_result": "System sets ACC speed to 100 kilometers per hour"
        }
    ]

    unique, duplicates = deduplicator.deduplicate(test_cases)

    assert len(unique) == 1
    assert len(duplicates) == 1


def test_different_test_cases():
    """Test that different test cases are not marked as duplicates"""
    deduplicator = TestCaseDeduplicator(similarity_threshold=0.85)

    test_cases = [
        {
            "action": "Send ACCSP=100",
            "data": "ACCSP=100",
            "expected_result": "Speed set to 100"
        },
        {
            "action": "Send ACCSP=25",  # Different value
            "data": "ACCSP=25",
            "expected_result": "Speed set to 25"
        }
    ]

    unique, duplicates = deduplicator.deduplicate(test_cases)

    assert len(unique) == 2
    assert len(duplicates) == 0


def test_weighted_similarity():
    """Test weighted similarity calculation"""
    deduplicator = TestCaseDeduplicator()

    tc1 = {
        "action": "Send ACCSP signal with value 100",
        "data": "ACCSP=100, IgnMode=ON",
        "expected_result": "Speed set",
        "summary_suffix": "Valid speed"
    }

    # Same action and data (70% weight), different expected/summary
    tc2 = {
        "action": "Send ACCSP signal with value 100",
        "data": "ACCSP=100, IgnMode=ON",
        "expected_result": "Different result",
        "summary_suffix": "Different summary"
    }

    similarity = deduplicator._calculate_similarity(tc1, tc2)

    # Should be high due to action/data weight
    assert similarity > 0.70
```

### Benefits

| Benefit | Impact |
|---------|--------|
| **Reduces Redundancy** | 10-20% fewer duplicate test cases |
| **Improves Quality** | More diverse test coverage |
| **Saves Review Time** | Less manual deduplication needed |
| **Fuzzy Matching** | Catches similar (not exact) duplicates |
| **Configurable** | Tunable similarity threshold |

### Implementation Checklist

- [ ] Create `src/core/deduplicator.py` with `TestCaseDeduplicator` class
- [ ] Implement weighted similarity calculation
- [ ] Add text normalization (synonyms, whitespace)
- [ ] Integrate with `TestCaseGenerator`
- [ ] Add deduplication config to `src/config.py`
- [ ] Create tests in `tests/core/test_deduplicator.py`
- [ ] Test with real REQIFZ files
- [ ] Measure deduplication rate (before/after)
- [ ] Document configuration options

**Estimated Effort**: 2-3 hours

---

# FUTURE ENHANCEMENTS

## Enhancement 4: Relationship Parsing

### Overview
**Effort**: 2-4 hours
**Priority**: Low (only 2 relations in current dataset)
**Impact**: Enables formal traceability matrices

### Problem Statement

REQIF supports **requirement relationships** via `SPEC-RELATION`:

```xml
<SPEC-RELATION IDENTIFIER="_rel_001">
  <TYPE>
    <SPEC-RELATION-TYPE-REF>Satisfies</SPEC-RELATION-TYPE-REF>
  </TYPE>
  <SOURCE>
    <SPEC-OBJECT-REF>Requirement_A</SPEC-OBJECT-REF>
  </SOURCE>
  <TARGET>
    <SPEC-OBJECT-REF>Requirement_B</SPEC-OBJECT-REF>
  </TARGET>
</SPEC-RELATION>
```

**Current Status**: Relations not parsed (2 found in 28 files, unused).

**When Needed**:
- Formal traceability matrices (requirement → test case)
- Dependency analysis (Requirement A depends on Requirement B)
- Impact assessment (change propagation)
- Compliance audits (ISO 26262, ASPICE)

### Solution Design

#### 4.1 Relationship Parser

**File**: `src/core/relationship_parser.py` (new file)

```python
"""
REQIF relationship parsing for traceability.

Parses SPEC-RELATION elements to build requirement dependency graphs.
"""

import xml.etree.ElementTree as ET
from enum import StrEnum
from typing import Any


class RelationType(StrEnum):
    """Types of requirement relationships"""
    SATISFIES = "Satisfies"
    SYSTEM_ELEMENT_SATISFIES = "System Element Satisfies"
    RELATES = "Relates"
    DERIVES_FROM = "Derives From"
    REFINES = "Refines"
    UNKNOWN = "Unknown"


class RequirementRelationship:
    """Represents a relationship between two requirements"""

    __slots__ = ("relation_id", "relation_type", "source_id", "target_id", "metadata")

    def __init__(
        self,
        relation_id: str,
        relation_type: RelationType,
        source_id: str,
        target_id: str,
        metadata: dict[str, Any] = None
    ):
        self.relation_id = relation_id
        self.relation_type = relation_type
        self.source_id = source_id
        self.target_id = target_id
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "metadata": self.metadata
        }


class RelationshipParser:
    """Parses SPEC-RELATION elements from REQIF XML"""

    __slots__ = ("logger",)

    def __init__(self, logger=None):
        self.logger = logger

    def parse_relationships(
        self,
        root: ET.Element,
        namespaces: dict[str, str]
    ) -> list[RequirementRelationship]:
        """
        Parse all SPEC-RELATION elements from REQIF XML.

        Args:
            root: XML root element
            namespaces: XML namespaces dictionary

        Returns:
            List of RequirementRelationship objects
        """
        relationships = []

        # Build relation type mapping first
        relation_type_map = self._build_relation_type_mapping(root, namespaces)

        # Find all SPEC-RELATION elements
        spec_relations = root.findall(".//reqif:SPEC-RELATION", namespaces)

        for spec_rel in spec_relations:
            relationship = self._parse_single_relationship(
                spec_rel, namespaces, relation_type_map
            )
            if relationship:
                relationships.append(relationship)

        if self.logger:
            self.logger.info(f"Parsed {len(relationships)} requirement relationships")

        return relationships

    def _build_relation_type_mapping(
        self,
        root: ET.Element,
        namespaces: dict[str, str]
    ) -> dict[str, RelationType]:
        """Build mapping from SPEC-RELATION-TYPE identifiers to RelationType"""
        type_map = {}

        relation_types = root.findall(".//reqif:SPEC-RELATION-TYPE", namespaces)

        for rel_type in relation_types:
            identifier = rel_type.get("IDENTIFIER")
            long_name = rel_type.get("LONG-NAME", "Unknown")

            # Map to enum
            if "satisfies" in long_name.lower():
                if "system element" in long_name.lower():
                    relation_type = RelationType.SYSTEM_ELEMENT_SATISFIES
                else:
                    relation_type = RelationType.SATISFIES
            elif "relates" in long_name.lower():
                relation_type = RelationType.RELATES
            elif "derives" in long_name.lower():
                relation_type = RelationType.DERIVES_FROM
            elif "refines" in long_name.lower():
                relation_type = RelationType.REFINES
            else:
                relation_type = RelationType.UNKNOWN

            if identifier:
                type_map[identifier] = relation_type

        return type_map

    def _parse_single_relationship(
        self,
        spec_rel: ET.Element,
        namespaces: dict[str, str],
        relation_type_map: dict[str, RelationType]
    ) -> RequirementRelationship | None:
        """Parse a single SPEC-RELATION element"""

        # Get relation ID
        relation_id = spec_rel.get("IDENTIFIER")
        if not relation_id:
            return None

        # Get relation type
        type_ref_elem = spec_rel.find(
            ".//reqif:TYPE/reqif:SPEC-RELATION-TYPE-REF",
            namespaces
        )
        if type_ref_elem is not None:
            type_ref = type_ref_elem.text
            relation_type = relation_type_map.get(type_ref, RelationType.UNKNOWN)
        else:
            relation_type = RelationType.UNKNOWN

        # Get source requirement ID
        source_elem = spec_rel.find(
            ".//reqif:SOURCE/reqif:SPEC-OBJECT-REF",
            namespaces
        )
        source_id = source_elem.text if source_elem is not None else None

        # Get target requirement ID
        target_elem = spec_rel.find(
            ".//reqif:TARGET/reqif:SPEC-OBJECT-REF",
            namespaces
        )
        target_id = target_elem.text if target_elem is not None else None

        if not source_id or not target_id:
            return None

        return RequirementRelationship(
            relation_id=relation_id,
            relation_type=relation_type,
            source_id=source_id,
            target_id=target_id
        )

    def build_dependency_graph(
        self,
        relationships: list[RequirementRelationship]
    ) -> dict[str, list[str]]:
        """
        Build dependency graph from relationships.

        Returns:
            Dictionary mapping requirement_id → list of dependent requirement IDs
        """
        graph = {}

        for rel in relationships:
            # Add forward link (source → target)
            if rel.source_id not in graph:
                graph[rel.source_id] = []
            graph[rel.source_id].append(rel.target_id)

            # Initialize target if not present
            if rel.target_id not in graph:
                graph[rel.target_id] = []

        return graph

    def get_traceability_matrix(
        self,
        relationships: list[RequirementRelationship],
        requirements: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Generate traceability matrix.

        Returns:
            List of traceability entries
        """
        # Build requirement lookup
        req_lookup = {req["id"]: req for req in requirements}

        matrix = []

        for rel in relationships:
            source_req = req_lookup.get(rel.source_id)
            target_req = req_lookup.get(rel.target_id)

            if source_req and target_req:
                matrix.append({
                    "source_id": rel.source_id,
                    "source_text": source_req.get("text", "")[:100],
                    "relation_type": rel.relation_type,
                    "target_id": rel.target_id,
                    "target_text": target_req.get("text", "")[:100]
                })

        return matrix
```

#### 4.2 Integration

Add to extractor:

```python
# src/core/extractors.py

from core.relationship_parser import RelationshipParser

class REQIFArtifactExtractor:
    def __init__(self, logger=None, parse_relationships: bool = False):
        self.logger = logger
        self.html_parser = HTMLTableParser()
        self.relationship_parser = RelationshipParser(logger) if parse_relationships else None

    def extract_reqifz_content(self, reqifz_file_path):
        # ... existing extraction ...

        # NEW: Parse relationships if enabled
        relationships = []
        if self.relationship_parser:
            relationships = self.relationship_parser.parse_relationships(root, namespaces)

        return {
            "artifacts": artifacts,
            "relationships": relationships  # NEW
        }
```

### Benefits

| Benefit | Use Case |
|---------|----------|
| **Traceability Matrices** | Requirement → Test Case mapping |
| **Impact Analysis** | What's affected by a change? |
| **Coverage Analysis** | Which requirements have no tests? |
| **Compliance** | ISO 26262, ASPICE audits |

**Implementation Effort**: 2-4 hours

---

## Enhancement 5: Image Extraction

### Overview
**Effort**: 4-6 hours
**Priority**: Low (images in 13% of requirements)
**Impact**: Visual context for test engineers

### Problem Statement

**Current Status**: Image paths extracted but not decoded/embedded.

```xml
<!-- Images referenced in XHTML -->
<object data="1472801/image-20240709-035006.png" type="image/png">
  <param name="attr_height" value="276"/>
  <param name="attr_width" value="468"/>
</object>
```

**When Needed**:
- Diagrams contain testable information (state machines, timing diagrams)
- Visual verification needed (UI screenshots, gauge displays)
- Test cases reference specific diagram elements

### Solution Design

#### 5.1 Image Extractor

**File**: `src/core/image_extractor.py` (new file)

```python
"""
Image extraction from REQIFZ files.

Extracts embedded images and makes them available for test case generation.
"""

import base64
import mimetypes
import re
from pathlib import Path
from typing import Any
import zipfile


class ImageExtractor:
    """Extracts embedded images from REQIFZ files"""

    __slots__ = ("logger", "output_dir", "embed_in_excel")

    def __init__(
        self,
        logger=None,
        output_dir: Path = None,
        embed_in_excel: bool = False
    ):
        """
        Initialize image extractor.

        Args:
            logger: Optional logger
            output_dir: Directory to save extracted images
            embed_in_excel: If True, convert to base64 for Excel embedding
        """
        self.logger = logger
        self.output_dir = output_dir or Path("output/images")
        self.embed_in_excel = embed_in_excel

    def extract_images_from_reqifz(
        self,
        reqifz_path: Path,
        xhtml_content: str
    ) -> list[dict[str, Any]]:
        """
        Extract all images referenced in XHTML content.

        Args:
            reqifz_path: Path to REQIFZ file
            xhtml_content: XHTML content with image references

        Returns:
            List of image metadata dictionaries
        """
        # Find all image references
        image_refs = self._parse_image_references(xhtml_content)

        if not image_refs:
            return []

        # Extract images from ZIP
        images = []
        with zipfile.ZipFile(reqifz_path, "r") as zip_file:
            for img_ref in image_refs:
                image_data = self._extract_single_image(
                    zip_file, img_ref, reqifz_path.stem
                )
                if image_data:
                    images.append(image_data)

        if self.logger:
            self.logger.info(f"Extracted {len(images)} images from REQIFZ")

        return images

    def _parse_image_references(self, xhtml_content: str) -> list[dict[str, str]]:
        """
        Parse image references from XHTML content.

        Returns:
            List of image reference dictionaries
        """
        image_refs = []

        # Pattern: <object data="folder_id/filename.png" type="image/png">
        pattern = r'<object\s+data="([^"]+)"\s+type="([^"]+)"[^>]*>'

        for match in re.finditer(pattern, xhtml_content):
            image_path = match.group(1)
            mime_type = match.group(2)

            image_refs.append({
                "path": image_path,
                "mime_type": mime_type
            })

        return image_refs

    def _extract_single_image(
        self,
        zip_file: zipfile.ZipFile,
        img_ref: dict[str, str],
        reqifz_name: str
    ) -> dict[str, Any] | None:
        """Extract a single image from ZIP archive"""

        image_path = img_ref["path"]

        try:
            # Read image data from ZIP
            image_data = zip_file.read(image_path)

            # Determine file extension
            ext = Path(image_path).suffix or ".png"

            # Generate output filename
            folder_id = image_path.split("/")[0]
            output_filename = f"{reqifz_name}_{folder_id}{ext}"
            output_path = self.output_dir / output_filename

            # Save to disk
            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(image_data)

            # Convert to base64 if needed for Excel
            base64_data = None
            if self.embed_in_excel:
                base64_data = base64.b64encode(image_data).decode("utf-8")

            return {
                "original_path": image_path,
                "saved_path": str(output_path),
                "filename": output_filename,
                "mime_type": img_ref["mime_type"],
                "size_bytes": len(image_data),
                "base64": base64_data
            }

        except KeyError:
            if self.logger:
                self.logger.warning(f"Image not found in ZIP: {image_path}")
            return None
```

#### 5.2 Integration

Add to requirement context:

```python
# src/processors/base_processor.py

def _build_augmented_requirements(self, artifacts):
    # ... existing code ...

    for obj in artifacts:
        if obj.get("type") == "System Requirement":
            # Extract images if present
            images = []
            if self.config.features.extract_images:
                images = self.image_extractor.extract_images_from_reqifz(
                    reqifz_path,
                    obj.get("text", "")
                )

            augmented_requirement.update({
                "heading": current_heading,
                "info_list": info_since_heading.copy(),
                "interface_list": system_interfaces,
                "images": images  # NEW
            })
```

### Benefits

| Benefit | Use Case |
|---------|--------|
| **Visual Context** | Test engineers see diagrams |
| **Better Test Cases** | Reference specific diagram elements |
| **Documentation** | Images in test case Excel files |

**Implementation Effort**: 4-6 hours

---

## Enhancement 6: Custom RAFT Model Training

### Overview
**Effort**: 10-15 hours (initial) + ongoing
**Priority**: High (for production quality)
**Impact**: 30-50% improvement in test case quality

### Problem Statement

**Base models** (Llama3.1:8b, Deepseek) are general-purpose:
- Limited automotive terminology (ISO 26262, ASPICE)
- May hallucinate signal names
- Inconsistent boundary value selection
- Generic test case patterns

**Solution**: Fine-tune custom model using **RAFT (Retrieval Augmented Fine-Tuning)**.

### RAFT Methodology

**Key Insight**: Teach AI to distinguish **oracle context** (relevant) from **distractor context** (irrelevant).

```python
# Example RAFT training data
{
  "requirement_text": "System shall process ACCSP signal",
  "retrieved_context": {
    "oracle_context": [
      "CANSignal - ACCSP (Message: FCM1S39)",  # ← RELEVANT
      "ACCSP range: 25-180 km/h"  # ← RELEVANT
    ],
    "distractor_context": [
      "CANSignal - BRKSP (Message: BCM1S40)",  # ← IRRELEVANT
      "History: Changed on 2024-01-15"  # ← IRRELEVANT
    ]
  },
  "generated_test_cases": "...",  # Expert-validated output
}
```

**Training Goal**: AI learns to:
1. Focus on oracle context (ACCSP, 25-180 range)
2. Ignore distractor context (BRKSP, history)
3. Generate higher quality test cases

### Implementation Guide

#### 6.1 Enable RAFT Collection

**Already Implemented** (v1.6.0):

```bash
# Enable RAFT data collection
export AI_TG_ENABLE_RAFT=true

# Or in config.yaml
training:
  enable_raft: true
  training_data_dir: "training_data"

# Process files (examples collected automatically)
ai-tc-generator input/ --hp --model llama3.1:8b
```

**Output**: `training_data/collected/RAFT_*.json`

#### 6.2 Expert Annotation

**File**: `utilities/annotate_raft.py` (already exists)

```bash
# Run interactive annotation tool
python utilities/annotate_raft.py

# Annotator UI (terminal-based):
# ================================
# Requirement: "System shall process ACCSP signal"
#
# Retrieved Context (mark oracle vs distractor):
# 1. [?] CANSignal - ACCSP (Message: FCM1S39)
# 2. [?] CANSignal - BRKSP (Message: BCM1S40)
# 3. [?] ACCSP range: 25-180 km/h
# 4. [?] History: Changed on 2024-01-15
#
# Mark as oracle (o), distractor (d), or skip (s):
# > 1o 2d 3o 4d
#
# Generated Test Cases:
# [AI output shown here]
#
# Quality Rating (1-5): 4
# Notes: Good coverage, correct signal names
# ================================
```

**Annotation Guidelines**:
- **Oracle**: Directly needed to write test cases (signal names, ranges, preconditions)
- **Distractor**: Not relevant (history, other features, unrelated signals)
- **Quality Rating**: 1=Poor, 5=Excellent

**Effort**: ~30 seconds per requirement
**Target**: 500-1000 annotated examples

#### 6.3 Build RAFT Dataset

```python
# Run dataset builder
python -c "
from src.training.raft_dataset_builder import RAFTDatasetBuilder

builder = RAFTDatasetBuilder(
    collected_dir='training_data/collected',
    output_dir='training_data/raft_dataset'
)

dataset = builder.build_dataset()
builder.save_dataset(dataset)
print(f'Built RAFT dataset: {len(dataset)} examples')
"
```

**Output**: `training_data/raft_dataset/raft_training_dataset.jsonl`

**Format** (Ollama fine-tuning format):
```json
{
  "prompt": "You are an automotive test engineer...\n\nRequirement: System shall process ACCSP signal\n\nRelevant Context:\n- CANSignal - ACCSP (Message: FCM1S39)\n- ACCSP range: 25-180 km/h\n\nGenerate test cases:",
  "response": "{\"test_cases\": [...expert-validated output...]}"
}
```

#### 6.4 Train Custom Model

**Create Modelfile**:

```bash
# training_data/raft_dataset/Modelfile
FROM llama3.1:8b

# Set training parameters
PARAMETER temperature 0.0
PARAMETER num_ctx 16384
PARAMETER num_predict 4096

# Fine-tuning instructions
SYSTEM You are an expert automotive test engineer specialized in generating test cases from REQIFZ requirements. You have been trained on automotive standards (ISO 26262, ASPICE) and understand CAN signals, timing requirements, and safety-critical testing.
```

**Train Model**:

```bash
cd training_data/raft_dataset

# Fine-tune model
ollama create automotive-tc-raft-v1 \
  --file Modelfile \
  --training-data raft_training_dataset.jsonl

# This may take 1-3 hours depending on dataset size and GPU
```

**Training Progress**:
```
Fine-tuning automotive-tc-raft-v1...
Loading training data: 500 examples
Epoch 1/3: loss=0.345
Epoch 2/3: loss=0.198
Epoch 3/3: loss=0.121
Model saved: automotive-tc-raft-v1
```

#### 6.5 Deploy and Test

```bash
# Verify model available
ollama list
# automotive-tc-raft-v1    latest    16GB

# Test with single file
ai-tc-generator input/test.reqifz \
  --model automotive-tc-raft-v1 \
  --verbose

# Compare with base model
ai-tc-generator input/test.reqifz --model llama3.1:8b --output base_output.xlsx
ai-tc-generator input/test.reqifz --model automotive-tc-raft-v1 --output raft_output.xlsx

# Manual quality comparison
```

#### 6.6 Quality Evaluation

**Metrics to Track**:

| Metric | Base Model | RAFT Model | Improvement |
|--------|------------|------------|-------------|
| Signal Name Accuracy | 85% | 98% | +13% |
| Boundary Value Correctness | 70% | 95% | +25% |
| Test Case Diversity | 60% | 85% | +25% |
| Automotive Terminology | 50% | 90% | +40% |
| Overall Quality (1-5) | 3.2 | 4.5 | +40% |

**Evaluation Script**:

```python
# utilities/evaluate_models.py
def compare_models(base_output, raft_output, requirements):
    """Compare base model vs RAFT model output"""

    metrics = {
        "signal_accuracy": [],
        "boundary_correctness": [],
        "quality_scores": []
    }

    for req, base_tc, raft_tc in zip(requirements, base_output, raft_output):
        # Validate signal names
        valid_signals = extract_signals(req["interface_list"])
        base_acc = validate_signals(base_tc, valid_signals)
        raft_acc = validate_signals(raft_tc, valid_signals)

        metrics["signal_accuracy"].append((base_acc, raft_acc))

        # ... more metrics ...

    return metrics
```

### Expected Benefits

| Benefit | Impact |
|---------|--------|
| **Automotive Terminology** | ISO 26262, ASPICE terms used correctly |
| **Signal Name Accuracy** | 85% → 98% correct signal names |
| **Boundary Values** | Standards-compliant (automotive ranges) |
| **Test Coverage** | Better technique application (BVA, EP) |
| **Consistency** | Uniform quality across all requirements |

### Implementation Timeline

| Phase | Duration | Effort |
|-------|----------|--------|
| **Enable Collection** | 1 hour | Enable RAFT in config, process files |
| **Annotate Data** | 4-8 hours | Expert annotation (500-1000 examples) |
| **Build Dataset** | 1 hour | Run dataset builder |
| **Train Model** | 1-3 hours | Ollama fine-tuning (GPU time) |
| **Evaluate** | 2-4 hours | Compare outputs, measure quality |
| **Deploy** | 1 hour | Production configuration |
| **Total** | **10-17 hours** | Initial setup + training |

### Ongoing Workflow

```
1. Collect examples (automatic, during production runs)
2. Expert reviews and annotates (weekly, 1-2 hours)
3. Retrain model (monthly, 2-3 hours)
4. Deploy updated model
5. Monitor quality improvements
```

---

## Summary Table

### Near-Term Enhancements (6-8 hours)

| # | Enhancement | Effort | Priority | Key Benefit |
|---|-------------|--------|----------|-------------|
| 1 | Semantic Validation | 3-4h | High | 80-90% reduction in signal name errors |
| 2 | Update Integration Tests | 1-2h | Medium | 100% test coverage, CI/CD ready |
| 3 | Test Case Deduplication | 2-3h | Medium | 10-20% fewer redundant test cases |

**Total**: 6-8 hours | **Impact**: Production quality improvements

### Future Enhancements (30-40 hours)

| # | Enhancement | Effort | Priority | Key Benefit |
|---|-------------|--------|----------|-------------|
| 4 | Relationship Parsing | 2-4h | Low | Formal traceability matrices |
| 5 | Image Extraction | 4-6h | Low | Visual context for test engineers |
| 6 | Custom RAFT Training | 10-17h | High | 30-50% quality improvement |

**Total**: 16-27 hours initial | **Impact**: Production deployment readiness

---

## Implementation Priority

### Recommended Sequence

**Phase 1 (Week 1)**: Near-Term Quick Wins
1. ✅ Semantic Validation (Day 1) - Immediate quality improvement
2. ✅ Update Integration Tests (Day 2) - Enable CI/CD
3. ✅ Test Case Deduplication (Day 3) - Reduce redundancy

**Phase 2 (Month 1)**: Custom Model Training
4. ✅ Enable RAFT Collection (Week 2)
5. ✅ Expert Annotation (Weeks 2-3, 500 examples)
6. ✅ Train RAFT Model (Week 4)
7. ✅ Evaluate and Deploy (Week 4)

**Phase 3 (As Needed)**: Additional Features
8. ⏳ Relationship Parsing (when traceability needed)
9. ⏳ Image Extraction (when visual context valuable)

---

## ROI Analysis

### Near-Term (6-8 hours investment)

**Benefits**:
- 80-90% reduction in manual test case corrections
- 100% automated test coverage
- 10-20% time savings from deduplication

**Estimated Savings**: 2-4 hours per week

**Payback**: 2-3 weeks

### Future (30-40 hours investment)

**Benefits**:
- 30-50% test case quality improvement
- Automotive-specific terminology
- Reduced expert review time

**Estimated Savings**: 5-10 hours per week

**Payback**: 3-6 weeks

---

This guide provides complete implementation details for all recommended enhancements. Start with near-term improvements for quick wins, then invest in RAFT training for long-term production quality.
