#!/usr/bin/env python3
"""
Test runner for AI Test Case Generator.

Runs the complete test suite with coverage reporting.
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run the test suite with pytest."""
    print("🧪 Running AI Test Case Generator Test Suite")
    print("=" * 60)

    # Run pytest with coverage
    cmd = [
        "python3", "-m", "pytest",
        ".",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--cov=src",  # Coverage for src directory
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html:htmlcov",  # HTML coverage report
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest pytest-cov")
        return False

def run_specific_test(test_path):
    """Run a specific test file or test function."""
    print(f"🧪 Running specific test: {test_path}")

    cmd = ["python3", "-m", "pytest", test_path, "-v", "--tb=short"]

    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Test passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Test failed with exit code {e.returncode}")
        return False

if __name__ == "__main__":
    # Add src to path for direct execution (from tests/ directory)
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    if len(sys.argv) > 1:
        # Run specific test
        test_path = sys.argv[1]
        success = run_specific_test(test_path)
    else:
        # Run all tests
        success = run_tests()

    sys.exit(0 if success else 1)
