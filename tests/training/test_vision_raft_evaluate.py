"""Unit tests for ``VisionRAFTTrainer.evaluate_model`` (Phase 1 output-quality eval).

Phase 1 runs the *prompt-customized* model over an explicit held-out RAFT
dataset and scores each generation by the canonical-schema pass rate
(``is_canonical_test_case``) — the same gate the production pipeline applies.

These tests inject a fake Ollama client so they stay deterministic and never
shell out to ``ollama``. A separate real-Ollama check (marked ``integration``)
covers the live path, per the project's "mocks cannot catch schema/grammar
regressions" lesson.
"""

import base64
import json

import pytest

from src.core.validators import TEST_CASE_RESPONSE_JSON_SCHEMA
from src.training.vision_raft_trainer import VisionRAFTTrainer, VisionTrainingConfig

# A test case carrying every canonical field with content -> passes the gate.
VALID_TEST_CASE = {
    "summary_suffix": "door opens on valid keyfob",
    "preconditions": "ignition on; keyfob paired",
    "test_steps": "1. Press the unlock button.",
    "expected_result": "Door unlocks within 200 ms.",
    "test_type": "functional",
}
VALID_RESPONSE = json.dumps({"test_cases": [VALID_TEST_CASE]})
# Missing four of the five canonical fields -> fails the gate.
INVALID_RESPONSE = json.dumps({"test_cases": [{"summary_suffix": "only one field"}]})
UNPARSEABLE_RESPONSE = "the model rambled and produced no JSON at all"

FAKE_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n fake image payload"


class FakeOllamaClient:
    """Records calls and returns a canned raw response, no subprocess involved."""

    def __init__(self, response: str = VALID_RESPONSE):
        self.response = response
        self.text_calls: list[dict] = []
        self.vision_calls: list[dict] = []

    def generate_completion(
        self,
        model_name,
        prompt,
        is_json=False,
        return_full_response=True,
        format_schema=None,
    ):
        self.text_calls.append(
            {"model": model_name, "prompt": prompt, "format_schema": format_schema}
        )
        return self.response

    def generate_response_with_vision(
        self,
        model_name,
        prompt,
        image_paths=None,
        is_json=False,
        return_full_response=False,
        format_schema=None,
    ):
        # Read the bytes now to prove the base64 was decoded to a real file that
        # existed during the call (temp files may be cleaned up afterwards).
        image_bytes = [p.read_bytes() for p in (image_paths or [])]
        self.vision_calls.append({"model": model_name, "image_bytes": image_bytes})
        return self.response


def _write_jsonl(path, examples):
    path.write_text("\n".join(json.dumps(e) for e in examples) + "\n", encoding="utf-8")


def _text_example(content="Relevant Context: door system\n\nGenerate test cases."):
    return {
        "messages": [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": content},
            {"role": "assistant", "content": "reference answer"},
        ]
    }


def _vision_example():
    img_b64 = base64.b64encode(FAKE_IMAGE_BYTES).decode("ascii")
    return {
        "messages": [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "Analyze the diagram.", "images": [img_b64]},
            {"role": "assistant", "content": "reference answer"},
        ]
    }


@pytest.fixture
def trainer(tmp_path):
    dataset = tmp_path / "raft.jsonl"
    _write_jsonl(dataset, [_text_example()])
    config = VisionTrainingConfig(output_model="pinned-eval-model")
    return VisionRAFTTrainer(
        dataset_path=dataset,
        config=config,
        output_dir=tmp_path / "models",
    )


def test_requires_explicit_test_dataset(trainer):
    # No held-out split exists yet; refuse rather than silently evaluate on the
    # training data or fabricate a split.
    with pytest.raises(ValueError, match="test_dataset"):
        trainer.evaluate_model()


def test_result_shape(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])

    result = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient())

    assert set(result) >= {
        "model",
        "evaluation_date",
        "test_dataset",
        "metrics",
        "per_example",
        "errors",
    }
    assert result["model"] == "pinned-eval-model"
    assert result["test_dataset"] == str(test_set)
    assert result["errors"] == []


def test_valid_output_scores_one(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example(), _text_example()])

    metrics = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(VALID_RESPONSE)
    )["metrics"]

    assert metrics["overall_score"] == 1.0
    assert metrics["text_examples_score"] == 1.0
    assert metrics["parse_success_rate"] == 1.0
    assert metrics["total_examples"] == 2
    assert metrics["avg_test_cases_per_example"] == 1.0


def test_invalid_schema_output_scores_zero(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])

    metrics = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(INVALID_RESPONSE)
    )["metrics"]

    assert metrics["overall_score"] == 0.0
    # Parsing succeeded (valid JSON), the test cases just fail the canonical gate.
    assert metrics["parse_success_rate"] == 1.0


def test_unparseable_output_scores_zero(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])

    metrics = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(UNPARSEABLE_RESPONSE)
    )["metrics"]

    assert metrics["overall_score"] == 0.0
    assert metrics["parse_success_rate"] == 0.0


def test_vision_score_is_none_without_vision_examples(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])

    metrics = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient())["metrics"]

    # No fabricated 0.0 — a metric with nothing behind it is reported as absent.
    assert metrics["vision_examples_score"] is None
    assert metrics["vision_examples"] == 0
    assert metrics["text_examples"] == 1


def test_routes_vision_examples_through_vision_method(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_vision_example()])
    client = FakeOllamaClient(VALID_RESPONSE)

    metrics = trainer.evaluate_model(test_dataset=test_set, client=client)["metrics"]

    assert len(client.vision_calls) == 1
    # base64 image was decoded to a real file and passed to the vision method.
    assert client.vision_calls[0]["image_bytes"] == [FAKE_IMAGE_BYTES]
    assert metrics["vision_examples"] == 1
    assert metrics["vision_examples_score"] == 1.0


def test_forwards_canonical_schema_to_model(trainer, tmp_path):
    # Guards the schema-sensitive path: generation must request the canonical
    # JSON schema, or output silently fails the gate (the 2026-07-20 grammar bug).
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])
    client = FakeOllamaClient()

    trainer.evaluate_model(test_dataset=test_set, client=client)

    assert client.text_calls[0]["format_schema"] is TEST_CASE_RESPONSE_JSON_SCHEMA


def test_injected_client_never_shells_out(trainer, tmp_path, monkeypatch):
    import subprocess

    def _boom(*args, **kwargs):
        raise AssertionError("evaluate_model must not invoke a subprocess")

    monkeypatch.setattr(subprocess, "run", _boom)
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])

    metrics = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient())["metrics"]

    assert metrics["overall_score"] == 1.0
