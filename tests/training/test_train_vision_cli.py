"""Tests for the ``train_vision_model`` CLI evaluation wiring (``--evaluate``).

``utilities/`` is not an importable package, so the script is loaded from its
file path. Only the evaluation wiring is exercised here; ``evaluate_model``
itself is covered by ``test_vision_raft_evaluate.py``.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

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


def test_parse_args_compare_base_without_evaluate_errors(monkeypatch):
    # Opt 7: --compare-base only means something in evaluation mode; accepting it
    # in model-creation mode silently ignores it. Reject it with a clear error.
    monkeypatch.setattr("sys.argv", ["prog", "--compare-base"])
    with pytest.raises(SystemExit):
        tvm.parse_args()


def test_run_evaluation_missing_file_returns_1(tmp_path):
    assert tvm.run_evaluation(str(tmp_path / "nope.jsonl"), "some-model") == 1


def test_run_evaluation_forwards_compare_base(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    captured = {}

    def fake_eval(self, test_dataset=None, compare_base=False, content_scorer=None):
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
        lambda self, test_dataset=None, compare_base=False, content_scorer=None: {
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
            "raw_test_cases_per_example": 2.0,
            "unique_valid_test_cases_per_example": 2.0,
        },
        "per_example": [],
        "errors": [],
    }
    monkeypatch.setattr(
        tvm.VisionRAFTTrainer,
        "evaluate_model",
        lambda self, test_dataset=None, compare_base=False, content_scorer=None: canned,
    )

    assert tvm.run_evaluation(str(test_set), "some-model") == 0


class _RecordingLogger:
    """Captures log lines so tests can assert on the printed summary."""

    def __init__(self):
        self.infos: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []

    def info(self, msg):
        self.infos.append(str(msg))

    def warning(self, msg):
        self.warnings.append(str(msg))

    def error(self, msg):
        self.errors.append(str(msg))


def _failed_comparison_result(test_set):
    """Result shape for a run whose baseline produced no usable observation."""
    return {
        "model": "some-model",
        "evaluation_date": "now",
        "test_dataset": str(test_set),
        "metrics": {"overall_score": 1.0, "total_examples": 1, "parse_success_rate": 1.0},
        "per_example": [],
        "errors": [],
        "baseline": {
            "model": "base-model",
            "metrics": {"overall_score": 0.0, "total_examples": 1},
            "per_example": [],
            "errors": ["example 0: generation failed: base model unavailable"],
        },
        "delta": None,
        "comparison": {
            "status": "failed",
            "paired_examples": 0,
            "total_examples": 1,
            "custom_failures": 0,
            "baseline_failures": 1,
        },
    }


def test_run_evaluation_failed_baseline_comparison_returns_1(tmp_path, monkeypatch):
    # 07-24 review Critical 1: a totally failed baseline must fail the run, not
    # exit 0 with a fabricated positive delta.
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    monkeypatch.setattr(
        tvm.VisionRAFTTrainer,
        "evaluate_model",
        lambda self,
        test_dataset=None,
        compare_base=False,
        content_scorer=None: _failed_comparison_result(test_set),
    )

    assert tvm.run_evaluation(str(test_set), "some-model", compare_base=True) == 1


def test_print_evaluation_result_reports_baseline_errors(tmp_path, monkeypatch):
    # Baseline errors were previously stored but never surfaced to the user.
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    rec = _RecordingLogger()
    monkeypatch.setattr(tvm, "logger", rec)

    tvm.print_evaluation_result(_failed_comparison_result(test_set))

    all_lines = rec.infos + rec.warnings + rec.errors
    assert any("base model unavailable" in line for line in all_lines)
    # The summary must say the delta was withheld rather than print a number.
    assert any("withheld" in line.lower() for line in all_lines)


def test_print_evaluation_result_reports_paired_sample_size(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    result = _failed_comparison_result(test_set)
    result["comparison"] = {
        "status": "partial",
        "paired_examples": 3,
        "total_examples": 4,
        "custom_failures": 0,
        "baseline_failures": 1,
    }
    result["delta"] = {"overall_score": 0.0}
    rec = _RecordingLogger()
    monkeypatch.setattr(tvm, "logger", rec)

    tvm.print_evaluation_result(result)

    all_lines = rec.infos + rec.warnings + rec.errors
    assert any("3" in line and "paired" in line.lower() for line in all_lines)


def test_print_evaluation_result_surfaces_bundle_vs_base_caveat(tmp_path, monkeypatch):
    # Rec 4: when a delta is shown, the output must warn it compares the whole
    # customized bundle against the base model's defaults, not the prompt alone.
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    result = _failed_comparison_result(test_set)
    result["comparison"] = {
        "status": "complete",
        "paired_examples": 1,
        "total_examples": 1,
        "custom_failures": 0,
        "baseline_failures": 0,
    }
    result["baseline"]["errors"] = []
    result["delta"] = {"overall_score": 0.1, "unique_valid_test_cases_per_example": 1.0}
    result["provenance"] = {
        "customized_model": {"name": "c", "kind": "bundle", "parameters": {"temperature": 0.0}},
        "base_model": {"name": "b", "kind": "base", "parameters": "defaults (NOT matched)"},
        "note": "The delta reflects the full customized model bundle ... not the system prompt alone.",
    }
    rec = _RecordingLogger()
    monkeypatch.setattr(tvm, "logger", rec)

    tvm.print_evaluation_result(result)

    all_lines = " ".join(rec.infos + rec.warnings + rec.errors).lower()
    assert "bundle" in all_lines or "not isolate" in all_lines or "not matched" in all_lines


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
        lambda self, test_dataset=None, compare_base=False, content_scorer=None: canned,
    )

    # No examples actually scored -> the evaluation could not run meaningfully.
    assert tvm.run_evaluation(str(test_set), "some-model") == 1


def test_print_shows_content_f1_when_present(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    result = _failed_comparison_result(test_set)
    result["metrics"]["content_f1"] = 0.75
    result["metrics"]["content_precision"] = 0.8
    result["metrics"]["content_recall"] = 0.7
    rec = _RecordingLogger()
    monkeypatch.setattr(tvm, "logger", rec)

    tvm.print_evaluation_result(result)

    lines = " ".join(rec.infos + rec.warnings + rec.errors).lower()
    assert "content" in lines and "0.75" in lines
    # The "meaningful signal" label moves to content F1 when it is present.
    assert "meaningful signal" in lines


def test_print_omits_content_when_absent(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    result = _failed_comparison_result(test_set)
    result["metrics"]["content_f1"] = None
    rec = _RecordingLogger()
    monkeypatch.setattr(tvm, "logger", rec)

    tvm.print_evaluation_result(result)

    lines = " ".join(rec.infos + rec.warnings + rec.errors).lower()
    assert "content f1" not in lines


def test_content_scorer_flag_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--evaluate", "x.jsonl"])
    args = tvm.parse_args()
    assert args.content_scorer == "overlap"
    assert args.judge_model is None


def test_content_scorer_flag_llm(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "--evaluate",
            "x.jsonl",
            "--content-scorer",
            "llm",
            "--judge-model",
            "llama3.1:8b",
        ],
    )
    args = tvm.parse_args()
    assert args.content_scorer == "llm"
    assert args.judge_model == "llama3.1:8b"


def test_print_shows_content_quality_when_present(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    result = _failed_comparison_result(test_set)
    result["metrics"]["content_quality"] = 0.66
    rec = _RecordingLogger()
    monkeypatch.setattr(tvm, "logger", rec)

    tvm.print_evaluation_result(result)

    lines = " ".join(rec.infos + rec.warnings + rec.errors).lower()
    assert "content quality" in lines and "0.66" in lines


def test_print_omits_content_quality_when_absent(tmp_path, monkeypatch):
    test_set = tmp_path / "held.jsonl"
    _write_example(test_set)
    result = _failed_comparison_result(test_set)
    result["metrics"]["content_quality"] = None
    rec = _RecordingLogger()
    monkeypatch.setattr(tvm, "logger", rec)

    tvm.print_evaluation_result(result)

    lines = " ".join(rec.infos + rec.warnings + rec.errors).lower()
    assert "content quality" not in lines
