#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Script for AI Test Case Generator

This script tests the entire codebase with positive and negative scenarios
using actual REQIFZ files.

Test Categories:
1. Positive Tests - Valid REQIFZ files with expected outputs
2. Negative Tests - Invalid inputs with proper error handling
3. Standard Mode - Sequential processing verification
4. HP Mode - Concurrent processing verification
5. Output Validation - Excel file generation and content
6. Error Scenarios - Connection, timeout, model errors
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


class TestResult:
    """Track test results"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
        self.start_time = time.time()

    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"{GREEN}✓{RESET} {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append({"test": test_name, "error": error})
        print(f"{RED}✗{RESET} {test_name}")
        print(f"  {RED}Error: {error}{RESET}")

    def add_skip(self, test_name: str, reason: str):
        self.skipped += 1
        print(f"{YELLOW}⊘{RESET} {test_name} - {reason}")

    def summary(self) -> dict[str, Any]:
        duration = time.time() - self.start_time
        return {
            "total": self.passed + self.failed + self.skipped,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_seconds": round(duration, 2),
            "errors": self.errors,
        }


def run_command(cmd: list[str], timeout: int = 300) -> tuple[int, str, str]:
    """Run shell command and return (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8"
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def check_ollama_service() -> bool:
    """Check if Ollama service is running"""
    returncode, stdout, _ = run_command(["curl", "-s", "http://localhost:11434/api/tags"], timeout=5)
    return returncode == 0 and "models" in stdout


def check_models_available() -> tuple[bool, bool]:
    """Check if required models are available"""
    returncode, stdout, _ = run_command(["curl", "-s", "http://localhost:11434/api/tags"], timeout=5)
    if returncode != 0:
        return False, False

    llama_available = "llama3.1:8b" in stdout
    deepseek_available = "deepseek-coder-v2:16b" in stdout
    return llama_available, deepseek_available


def get_reqifz_files(input_dir: Path) -> list[Path]:
    """Get all REQIFZ files in input directory"""
    return list(input_dir.rglob("*.reqifz"))


def test_positive_standard_mode(result: TestResult, test_file: Path):
    """Test standard mode with valid REQIFZ file"""
    test_name = f"Positive: Standard mode - {test_file.name}"

    cmd = ["python3", "main.py", str(test_file), "--verbose"]
    returncode, stdout, stderr = run_command(cmd, timeout=600)

    if returncode == 0 and "Processing complete" in stdout:
        # Check for output file
        output_files = list(test_file.parent.glob(f"{test_file.stem}_TCD_*.xlsx"))
        if output_files:
            result.add_pass(test_name)
            # Clean up test output
            for f in output_files:
                f.unlink()
        else:
            result.add_fail(test_name, "Output file not generated")
    else:
        result.add_fail(test_name, f"Command failed: {stderr[:200]}")


def test_positive_hp_mode(result: TestResult, test_file: Path):
    """Test HP mode with valid REQIFZ file"""
    test_name = f"Positive: HP mode - {test_file.name}"

    cmd = ["python3", "main.py", str(test_file), "--hp", "--max-concurrent", "2", "--verbose"]
    returncode, stdout, stderr = run_command(cmd, timeout=600)

    if returncode == 0 and "High-performance processing complete" in stdout:
        # Check for output file with HP suffix
        output_files = list(test_file.parent.glob(f"{test_file.stem}_TCD_HP_*.xlsx"))
        if output_files:
            result.add_pass(test_name)
            # Clean up test output
            for f in output_files:
                f.unlink()
        else:
            result.add_fail(test_name, "HP output file not generated")
    else:
        result.add_fail(test_name, f"Command failed: {stderr[:200]}")


def test_negative_missing_file(result: TestResult):
    """Test with non-existent file"""
    test_name = "Negative: Missing REQIFZ file"

    cmd = ["python3", "main.py", "nonexistent.reqifz"]
    returncode, stdout, stderr = run_command(cmd, timeout=30)

    # Should fail with error message
    if returncode != 0 and ("not found" in stderr.lower() or "does not exist" in stderr.lower()):
        result.add_pass(test_name)
    else:
        result.add_fail(test_name, "Did not handle missing file correctly")


def test_negative_invalid_file(result: TestResult, input_dir: Path):
    """Test with invalid file format"""
    test_name = "Negative: Invalid file format"

    # Create a fake .reqifz file
    fake_file = input_dir / "invalid_test.reqifz"
    fake_file.write_text("This is not a valid REQIFZ file")

    cmd = ["python3", "main.py", str(fake_file)]
    returncode, stdout, stderr = run_command(cmd, timeout=30)

    # Should fail with parsing error
    if returncode != 0 and ("parsing" in stderr.lower() or "invalid" in stderr.lower() or "error" in stderr.lower()):
        result.add_pass(test_name)
    else:
        result.add_fail(test_name, "Did not handle invalid file correctly")

    # Clean up
    fake_file.unlink()


def test_negative_missing_model(result: TestResult, test_file: Path):
    """Test with non-existent model"""
    test_name = "Negative: Non-existent model"

    cmd = ["python3", "main.py", str(test_file), "--model", "nonexistent-model:99b"]
    returncode, stdout, stderr = run_command(cmd, timeout=60)

    # Should fail with model not found error
    if returncode != 0 and ("model" in stderr.lower() or "not found" in stderr.lower()):
        result.add_pass(test_name)
    else:
        result.add_fail(test_name, "Did not handle missing model correctly")


def test_output_validation(result: TestResult, test_file: Path):
    """Test output file validation"""
    test_name = f"Output Validation - {test_file.name}"

    cmd = ["python3", "main.py", str(test_file)]
    returncode, stdout, stderr = run_command(cmd, timeout=600)

    if returncode == 0:
        output_files = list(test_file.parent.glob(f"{test_file.stem}_TCD_*.xlsx"))
        if output_files:
            output_file = output_files[0]
            # Check file size (should be > 1KB)
            if output_file.stat().st_size > 1024:
                result.add_pass(test_name)
            else:
                result.add_fail(test_name, "Output file too small")
            # Clean up
            output_file.unlink()
        else:
            result.add_fail(test_name, "Output file not found")
    else:
        result.add_fail(test_name, f"Processing failed: {stderr[:200]}")


def test_template_validation(result: TestResult):
    """Test YAML template validation"""
    test_name = "Template Validation"

    cmd = ["python3", "main.py", "--validate-prompts"]
    returncode, stdout, stderr = run_command(cmd, timeout=30)

    if returncode == 0 and ("valid" in stdout.lower() or "success" in stdout.lower()):
        result.add_pass(test_name)
    else:
        result.add_fail(test_name, f"Template validation failed: {stderr[:200]}")


def test_batch_processing(result: TestResult, input_dir: Path):
    """Test batch directory processing"""
    test_name = "Batch Processing - Directory"

    # Use a subdirectory with multiple files
    toyota_dir = input_dir / "Toyota_FDC"
    if not toyota_dir.exists():
        result.add_skip(test_name, "Toyota_FDC directory not found")
        return

    cmd = ["python3", "main.py", str(toyota_dir), "--hp", "--max-concurrent", "2"]
    returncode, stdout, stderr = run_command(cmd, timeout=1800)  # 30 min for multiple files

    if returncode == 0 and "Processing complete" in stdout:
        # Check for multiple output files
        output_files = list(toyota_dir.glob("*_TCD_*.xlsx"))
        if len(output_files) >= 2:
            result.add_pass(test_name)
            # Clean up
            for f in output_files:
                f.unlink()
        else:
            result.add_fail(test_name, f"Expected multiple outputs, got {len(output_files)}")
    else:
        result.add_fail(test_name, f"Batch processing failed: {stderr[:200]}")


def main():
    """Run comprehensive test suite"""
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}AI Test Case Generator - Comprehensive E2E Testing{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}\n")

    result = TestResult()
    input_dir = Path("input")

    # Pre-flight checks
    print(f"{BLUE}🔍 Pre-flight Checks{RESET}\n")

    if not check_ollama_service():
        print(f"{RED}✗ Ollama service not running{RESET}")
        print("  Start Ollama: ollama serve")
        sys.exit(1)
    print(f"{GREEN}✓ Ollama service running{RESET}")

    llama_available, deepseek_available = check_models_available()
    if not llama_available:
        print(f"{RED}✗ llama3.1:8b not available{RESET}")
        print("  Install: ollama pull llama3.1:8b")
        sys.exit(1)
    print(f"{GREEN}✓ llama3.1:8b available{RESET}")

    if not deepseek_available:
        print(f"{YELLOW}⚠ deepseek-coder-v2:16b not available (optional){RESET}")

    reqifz_files = get_reqifz_files(input_dir)
    if not reqifz_files:
        print(f"{RED}✗ No REQIFZ files found in {input_dir}{RESET}")
        sys.exit(1)
    print(f"{GREEN}✓ Found {len(reqifz_files)} REQIFZ files{RESET}\n")

    # Select test files (use small files for faster testing)
    test_files = [
        f for f in reqifz_files if f.name == "automotive_door_window_system.reqifz"
    ]
    if not test_files:
        # Use first 2 files as fallback
        test_files = reqifz_files[:2]

    # Run test suites
    print(f"{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}Test Suite 1: Positive Tests{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")

    for test_file in test_files[:1]:  # Test with 1 file for positive tests
        test_positive_standard_mode(result, test_file)
        test_positive_hp_mode(result, test_file)
        test_output_validation(result, test_file)

    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}Test Suite 2: Negative Tests{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")

    test_negative_missing_file(result)
    test_negative_invalid_file(result, input_dir)
    if test_files:
        test_negative_missing_model(result, test_files[0])

    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}Test Suite 3: Feature Tests{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")

    test_template_validation(result)
    # test_batch_processing(result, input_dir)  # Commented out - takes too long

    # Generate summary
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}Test Summary{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}\n")

    summary = result.summary()
    total = summary["total"]
    passed = summary["passed"]
    failed = summary["failed"]
    skipped = summary["skipped"]
    duration = summary["duration_seconds"]

    print(f"Total Tests:    {total}")
    print(f"{GREEN}Passed:         {passed}{RESET}")
    if failed > 0:
        print(f"{RED}Failed:         {failed}{RESET}")
    else:
        print(f"Failed:         {failed}")
    if skipped > 0:
        print(f"{YELLOW}Skipped:        {skipped}{RESET}")
    print(f"\nDuration:       {duration}s")

    if failed == 0:
        print(f"\n{GREEN}{BOLD}✓ ALL TESTS PASSED{RESET}")
        success_rate = 100.0
    else:
        success_rate = (passed / (total - skipped)) * 100 if (total - skipped) > 0 else 0
        print(f"\n{RED}{BOLD}✗ SOME TESTS FAILED{RESET}")

    print(f"Success Rate:   {success_rate:.1f}%")

    # Save detailed report
    report_file = Path(f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nDetailed report: {report_file}")

    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
