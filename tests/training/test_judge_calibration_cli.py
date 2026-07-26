"""CLI tests for --validate-judge on train_vision_model.py.

The calibration runner is monkeypatched, so these tests pin argument handling
and exit codes without touching Ollama.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_CLI_PATH = Path(__file__).resolve().parents[2] / "utilities" / "train_vision_model.py"


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("train_vision_model_cli_calib", _CLI_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cli():
    return _load_cli_module()


def _run_argv(cli, monkeypatch, argv: list[str]):
    monkeypatch.setattr(sys, "argv", ["train_vision_model.py", *argv])
    return cli.parse_args()


def test_validate_judge_rejects_combination_with_evaluate(cli, monkeypatch):
    with pytest.raises(SystemExit):
        _run_argv(cli, monkeypatch, ["--validate-judge", "--evaluate", "some.jsonl"])


def test_compare_base_without_evaluate_still_rejected(cli, monkeypatch):
    with pytest.raises(SystemExit):
        _run_argv(cli, monkeypatch, ["--validate-judge", "--compare-base"])


def test_run_judge_calibration_returns_zero_when_all_pass(cli, monkeypatch):
    monkeypatch.setattr(
        cli,
        "run_calibration",
        lambda *a, **k: {
            "scorer_kind": "overlap",
            "results": [],
            "total": 0,
            "failed": 0,
            "errors": 0,
            "passed": True,
        },
    )

    assert cli.run_judge_calibration() == 0


def test_run_judge_calibration_returns_one_on_breach(cli, monkeypatch):
    monkeypatch.setattr(
        cli,
        "run_calibration",
        lambda *a, **k: {
            "scorer_kind": "llm",
            "results": [],
            "total": 1,
            "failed": 1,
            "errors": 0,
            "passed": False,
        },
    )

    assert cli.run_judge_calibration() == 1
