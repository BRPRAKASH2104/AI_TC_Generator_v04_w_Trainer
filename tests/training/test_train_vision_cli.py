"""Tests for the ``train_vision_model`` CLI evaluation wiring (``--evaluate``).

``utilities/`` is not an importable package, so the script is loaded from its
file path. Only the evaluation wiring is exercised here; ``evaluate_model``
itself is covered by ``test_vision_raft_evaluate.py``.
"""

import importlib.util
import json
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "utilities" / "train_vision_model.py"


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("train_vision_model_cli", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tvm = _load_cli_module()


def _write_example(path):
    path.write_text(
        json.dumps(
            {
                "messages": [
                    {"role": "system", "content": "s"},
                    {"role": "user", "content": "u"},
                    {"role": "assistant", "content": "a"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_parse_args_accepts_evaluate(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--evaluate", "held.jsonl"])
    args = tvm.parse_args()
    assert args.evaluate == "held.jsonl"


def test_parse_args_evaluate_defaults_none(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog"])
    args = tvm.parse_args()
    assert args.evaluate is None


def test_run_evaluation_missing_file_returns_1(tmp_path):
    assert tvm.run_evaluation(str(tmp_path / "nope.jsonl"), "some-model") == 1


def test_run_evaluation_happy_path_returns_0(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)

    canned = {
        "model": "some-model",
        "evaluation_date": "now",
        "test_dataset": str(test_set),
        "metrics": {
            "text_examples_score": 1.0,
            "vision_examples_score": None,
            "overall_score": 1.0,
            "total_examples": 1,
            "text_examples": 1,
            "vision_examples": 0,
            "parse_success_rate": 1.0,
            "avg_test_cases_per_example": 2.0,
        },
        "per_example": [],
        "errors": [],
    }
    monkeypatch.setattr(
        tvm.VisionRAFTTrainer, "evaluate_model", lambda self, test_dataset=None: canned
    )

    assert tvm.run_evaluation(str(test_set), "some-model") == 0


def test_run_evaluation_all_examples_failed_returns_1(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)

    canned = {
        "model": "some-model",
        "evaluation_date": "now",
        "test_dataset": str(test_set),
        # Errored examples still count in total_examples; failed >= total means
        # nothing was actually scored.
        "metrics": {"overall_score": 0.0, "total_examples": 1},
        "per_example": [],
        "errors": ["example 0: generation failed"],
    }
    monkeypatch.setattr(
        tvm.VisionRAFTTrainer, "evaluate_model", lambda self, test_dataset=None: canned
    )

    # No examples actually scored -> the evaluation could not run meaningfully.
    assert tvm.run_evaluation(str(test_set), "some-model") == 1
