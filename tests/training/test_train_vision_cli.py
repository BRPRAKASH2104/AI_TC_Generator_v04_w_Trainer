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


def test_parse_args_accepts_compare_base(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--evaluate", "held.jsonl", "--compare-base"])
    args = tvm.parse_args()
    assert args.compare_base is True


def test_parse_args_compare_base_defaults_false(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog"])
    args = tvm.parse_args()
    assert args.compare_base is False


def test_run_evaluation_missing_file_returns_1(tmp_path):
    assert tvm.run_evaluation(str(tmp_path / "nope.jsonl"), "some-model") == 1


def test_run_evaluation_forwards_compare_base(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    captured = {}

    def fake_eval(self, test_dataset=None, compare_base=False):
        captured["compare_base"] = compare_base
        return {
            "model": "m",
            "test_dataset": str(test_set),
            "metrics": {"total_examples": 1, "overall_score": 1.0},
            "per_example": [],
            "errors": [],
        }

    monkeypatch.setattr(tvm.VisionRAFTTrainer, "evaluate_model", fake_eval)

    tvm.run_evaluation(str(test_set), "m", compare_base=True)

    assert captured["compare_base"] is True


def test_run_evaluation_threads_base_model_into_config(tmp_path, monkeypatch):
    # Guards the wiring: --base-model must reach VisionTrainingConfig, or the
    # A/B comparison silently runs against the default base model.
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    captured = {}
    real_config = tvm.VisionTrainingConfig

    def spy_config(**kwargs):
        captured.update(kwargs)
        return real_config(**kwargs)

    monkeypatch.setattr(tvm, "VisionTrainingConfig", spy_config)
    monkeypatch.setattr(
        tvm.VisionRAFTTrainer,
        "evaluate_model",
        lambda self, test_dataset=None, compare_base=False: {
            "model": "out-model",
            "test_dataset": str(test_set),
            "metrics": {"total_examples": 1, "overall_score": 1.0},
            "per_example": [],
            "errors": [],
        },
    )

    tvm.run_evaluation(
        str(test_set), "out-model", compare_base=True, base_model="deepseek-coder-v2:16b"
    )

    assert captured.get("output_model") == "out-model"
    assert captured.get("base_model") == "deepseek-coder-v2:16b"


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
        tvm.VisionRAFTTrainer,
        "evaluate_model",
        lambda self, test_dataset=None, compare_base=False: canned,
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
        tvm.VisionRAFTTrainer,
        "evaluate_model",
        lambda self, test_dataset=None, compare_base=False: canned,
    )

    # No examples actually scored -> the evaluation could not run meaningfully.
    assert tvm.run_evaluation(str(test_set), "some-model") == 1
