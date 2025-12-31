import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
def test_run_comprehensive_e2e_script():
    """Run the comprehensive E2E script as a subprocess."""
    project_root = Path(__file__).parent.parent.parent
    script_path = project_root / "tests" / "integration" / "e2e_runner_script.py"

    # Ensure environment has src in PYTHONPATH
    env = os.environ.copy()
    src_path = project_root / "src"
    # Prepend src to PYTHONPATH
    env["PYTHONPATH"] = str(src_path) + os.pathsep + env.get("PYTHONPATH", "")

    # Run the script
    # We use sys.executable to ensure we use the same python interpreter
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(project_root),
        env=env,
        capture_output=True,
        text=True
    )

    # Debug info on failure
    if result.returncode != 0:
        print("\n=== E2E Script STDOUT ===")
        print(result.stdout)
        print("\n=== E2E Script STDERR ===")
        print(result.stderr)

    assert result.returncode == 0, f"E2E script failed with return code {result.returncode}"
