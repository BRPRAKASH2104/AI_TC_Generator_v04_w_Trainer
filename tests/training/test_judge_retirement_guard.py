"""Repository guard: the retired LLM-as-judge must not creep back in.

The LLM-as-judge scorer was retired 2026-07-26 after calibration showed it
returned a near-constant match list regardless of input (see
``docs/training/README.md``). Removing the implementation is not enough — the
2026-07-26 review found a live test still importing the deleted module, which
made the documented full test runner red.

This module asserts the retired names are absent from the maintained surface.
Historical records (the changelog, plans, reviews, archived guides) legitimately
mention them and are excluded.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Names that no longer exist in the maintained surface. The bare token "judge"
# is deliberately NOT banned: ``judge_calibration``/``judge_calibration_cases``
# and the ``--validate-judge`` CLI mode are live, and the calibration harness's
# per-scorer-kind bands still exercise an "llm" kind as a generic second kind.
RETIRED_NAMES = (
    "llm_judge_scorer",
    "LLMJudgeScorer",
    "judge_model",
    "--content-scorer",
    "content_quality",
)

# Historical records: these describe the retirement and must keep saying so.
EXCLUDED_DIRS = (
    "docs/superpowers",
    "docs/reviews",
    "docs/training/archive",
    "graphify-out",
    ".gitnexus",
)
EXCLUDED_FILES = (
    "CHANGELOG.md",
    # CLAUDE.md designates this file as the retirement's evidence record ("Full
    # evidence in docs/training/README.md"). Its mentions are all past-tense
    # narrative — "was retired", "removed" — and must survive.
    "docs/training/README.md",
    # This guard necessarily spells the banned names out.
    "tests/training/test_judge_retirement_guard.py",
)


def _maintained_files() -> list[Path]:
    """Collect the maintained Python and training-doc files to scan.

    Returns:
        Repository files that must not mention any retired name.
    """
    candidates: list[Path] = []
    for directory in ("src", "utilities", "tests"):
        candidates.extend((REPO_ROOT / directory).rglob("*.py"))
    candidates.append(REPO_ROOT / "main.py")
    # Top-level training docs only; docs/training/archive is excluded below.
    candidates.extend((REPO_ROOT / "docs" / "training").glob("*.md"))

    kept = []
    for path in candidates:
        if not path.is_file():
            continue
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative in EXCLUDED_FILES:
            continue
        if any(relative.startswith(f"{d}/") for d in EXCLUDED_DIRS):
            continue
        kept.append(path)
    return kept


@pytest.mark.parametrize("name", RETIRED_NAMES)
def test_retired_judge_name_is_absent(name: str) -> None:
    """No maintained source, test, or training doc may mention a retired name."""
    offenders = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in _maintained_files()
        if name in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert not offenders, (
        f"retired judge name {name!r} still present in: {sorted(offenders)}. "
        "The LLM judge was retired 2026-07-26; remove the reference rather than "
        "reinstating it."
    )


def test_guard_actually_scans_files() -> None:
    """The scan must cover real files, so a passing guard cannot be vacuous."""
    scanned = _maintained_files()
    assert len(scanned) > 50, f"guard scanned only {len(scanned)} files; globbing is broken"
    names = {path.name for path in scanned}
    assert "content_scorer.py" in names
    assert "train_vision_model.py" in names
