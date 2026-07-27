"""Tests for the ``build_vision_dataset`` utility's user-facing summary.

``utilities/`` is not an importable package, so the script is loaded from its
file path — the same approach ``test_train_vision_cli.py`` uses.
"""

import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "utilities" / "build_vision_dataset.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_vision_dataset_cli", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bvd = _load_module()


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


def _vision_example(oracle_images=2, distractor_images=1):
    """A vision example in the shape ``_build_raft_example`` actually returns."""
    return {
        "question": "Generate comprehensive test cases for requirement REQ_1",
        "oracle_context": ["oracle doc"],
        "distractor_context": [],
        "oracle_images": [{"base64": "aaaa"}] * oracle_images,
        "distractor_images": [{"base64": "bbbb"}] * distractor_images,
        "has_images": True,
        "answer": "answer",
        "metadata": {
            "requirement_id": "REQ_1",
            "image_count": oracle_images + distractor_images,
            "oracle_image_count": oracle_images,
        },
    }


def _text_example():
    return {
        "question": "Generate comprehensive test cases for requirement REQ_2",
        "oracle_context": ["oracle doc"],
        "distractor_context": [],
        "oracle_images": [],
        "distractor_images": [],
        "has_images": False,
        "answer": "answer",
        "metadata": {"requirement_id": "REQ_2", "image_count": 0},
    }


def test_stats_report_real_image_counts(monkeypatch):
    # The summary previously summed a nonexistent "images" key, so a build
    # carrying vision examples always printed "Total images: 0".
    rec = _RecordingLogger()
    monkeypatch.setattr(bvd, "logger", rec)

    bvd.print_dataset_stats([_vision_example(), _text_example()])

    lines = " ".join(rec.infos)
    assert "Total images:         3" in lines
    assert "Total images:         0" not in lines
    assert "Avg images/example:   3.00" in lines


def test_stats_report_zero_images_for_a_text_only_build(monkeypatch):
    rec = _RecordingLogger()
    monkeypatch.setattr(bvd, "logger", rec)

    bvd.print_dataset_stats([_text_example()])

    lines = " ".join(rec.infos)
    assert "Total images:         0" in lines
    # No vision examples -> no average line at all.
    assert "Avg images/example" not in lines


def test_stats_warn_on_an_empty_dataset(monkeypatch):
    rec = _RecordingLogger()
    monkeypatch.setattr(bvd, "logger", rec)

    bvd.print_dataset_stats([])

    assert rec.warnings
    assert not rec.infos
