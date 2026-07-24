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
    """Records calls and returns a canned raw response, no subprocess involved.

    ``response`` may be a single string (returned for every model) or a
    ``{model_name: response}`` dict, which lets A/B tests give the customized and
    base models different outputs. A per-model value may itself be:

    - a string, returned on every call;
    - an ``Exception`` instance, raised on every call (models the base model
      being unavailable); or
    - a list of the above, consumed one entry per call in order (models
      per-example transient failures).
    """

    def __init__(self, response=VALID_RESPONSE):
        self.response = response
        self.text_calls: list[dict] = []
        self.vision_calls: list[dict] = []

    def _resolve(self, model_name):
        value = self.response
        if isinstance(value, dict):
            value = value.get(model_name, UNPARSEABLE_RESPONSE)
        if isinstance(value, list):
            value = value.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

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
        return self._resolve(model_name)

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
        return self._resolve(model_name)


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
    # 07-24 review Critical 2: the raw object count is output volume, not
    # coverage, so it is exposed under an honest name alongside the
    # deduplicated canonical-valid count that is the actual decision metric.
    assert metrics["raw_test_cases_per_example"] == 1.0
    assert metrics["unique_valid_test_cases_per_example"] == 1.0
    assert "avg_test_cases_per_example" not in metrics


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


# --- Phase 2: A/B comparison against the base model --------------------------


def test_no_baseline_or_delta_by_default(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])

    result = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient())

    assert "baseline" not in result
    assert "delta" not in result


def test_compare_base_adds_baseline_and_delta(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])

    result = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(), compare_base=True
    )

    # Default base_model on VisionTrainingConfig.
    assert result["baseline"]["model"] == "llama3.2-vision:11b"
    assert "metrics" in result["baseline"]
    assert "delta" in result


def test_compare_base_runs_both_models(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])
    client = FakeOllamaClient()

    trainer.evaluate_model(test_dataset=test_set, client=client, compare_base=True)

    models_called = {call["model"] for call in client.text_calls}
    assert models_called == {"pinned-eval-model", "llama3.2-vision:11b"}


def test_delta_reflects_customized_minus_base(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])
    # Customized model emits valid canonical cases; base emits unparseable junk.
    client = FakeOllamaClient(
        {
            "pinned-eval-model": VALID_RESPONSE,
            "llama3.2-vision:11b": UNPARSEABLE_RESPONSE,
        }
    )

    result = trainer.evaluate_model(test_dataset=test_set, client=client, compare_base=True)

    assert result["metrics"]["overall_score"] == 1.0
    assert result["baseline"]["metrics"]["overall_score"] == 0.0
    assert result["delta"]["overall_score"] == 1.0


def test_delta_is_none_when_metric_absent_on_a_side(trainer, tmp_path):
    # No vision examples -> vision_examples_score is None on both sides, so the
    # delta cannot be computed and is reported as None (not 0.0).
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])

    result = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(), compare_base=True
    )

    assert result["delta"]["vision_examples_score"] is None


# --- P0 fixes (2026-07-24 review): baseline validity & paired comparison -----

BASE_MODEL = "llama3.2-vision:11b"


def test_total_baseline_failure_withholds_delta(trainer, tmp_path):
    # 07-24 review Critical 1: a dead baseline previously aggregated to all-zero
    # metrics, so the delta reported pure positive lift with no usable baseline
    # observation behind it.
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])
    client = FakeOllamaClient(
        {
            "pinned-eval-model": VALID_RESPONSE,
            BASE_MODEL: RuntimeError("base model unavailable"),
        }
    )

    result = trainer.evaluate_model(test_dataset=test_set, client=client, compare_base=True)

    assert result["delta"] is None
    assert result["comparison"]["status"] == "failed"
    assert result["comparison"]["paired_examples"] == 0
    assert result["comparison"]["baseline_failures"] == 1
    assert result["baseline"]["errors"]


def test_partial_baseline_failure_compares_paired_rows_only(trainer, tmp_path):
    # One baseline row fails, one succeeds. The delta must come from the paired
    # row only: both sides scored 1.0 there, so lift is 0.0. An unpaired
    # aggregate would report +0.5 purely from the baseline's zero-filled
    # failed row.
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example(), _text_example()])
    client = FakeOllamaClient(
        {
            "pinned-eval-model": VALID_RESPONSE,
            BASE_MODEL: [RuntimeError("transient failure"), VALID_RESPONSE],
        }
    )

    result = trainer.evaluate_model(test_dataset=test_set, client=client, compare_base=True)

    assert result["comparison"]["status"] == "partial"
    assert result["comparison"]["paired_examples"] == 1
    assert result["comparison"]["baseline_failures"] == 1
    assert result["comparison"]["custom_failures"] == 0
    assert result["delta"]["overall_score"] == 0.0


def test_customized_failures_also_excluded_from_pairing(trainer, tmp_path):
    # Pairing is symmetric: a row where the *customized* model failed must not
    # count against (or for) the baseline either.
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example(), _text_example()])
    client = FakeOllamaClient(
        {
            "pinned-eval-model": [RuntimeError("custom side died"), VALID_RESPONSE],
            BASE_MODEL: VALID_RESPONSE,
        }
    )

    result = trainer.evaluate_model(test_dataset=test_set, client=client, compare_base=True)

    assert result["comparison"]["status"] == "partial"
    assert result["comparison"]["paired_examples"] == 1
    assert result["comparison"]["custom_failures"] == 1
    assert result["delta"]["overall_score"] == 0.0


def test_full_success_comparison_is_complete(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])

    result = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(), compare_base=True
    )

    assert result["comparison"]["status"] == "complete"
    assert result["comparison"]["paired_examples"] == 1
    assert result["comparison"]["custom_failures"] == 0
    assert result["comparison"]["baseline_failures"] == 0
    assert result["delta"] is not None


# --- P0 fixes (2026-07-24 review): honest coverage metric ---------------------

# A second, clearly distinct canonical case so dedup keeps both.
VALID_TEST_CASE_B = {
    "summary_suffix": "wiper speed follows rain intensity",
    "preconditions": "vehicle running; rain sensor enabled",
    "test_steps": "1. Simulate heavy rainfall on the windshield sensor.",
    "expected_result": "Wipers switch to maximum speed within 500 ms.",
    "test_type": "functional",
}
# Five byte-identical valid cases: high raw volume, zero added coverage.
DUPLICATE_HEAVY_RESPONSE = json.dumps({"test_cases": [VALID_TEST_CASE] * 5})
# Five canonical-invalid objects: high raw volume, zero usable output.
INVALID_BULK_RESPONSE = json.dumps(
    {"test_cases": [{"summary_suffix": f"junk {i}"} for i in range(5)]}
)


def test_duplicate_heavy_output_does_not_inflate_unique_valid(trainer, tmp_path):
    # 07-24 review Critical 2, reproduction 1: five identical valid cases vs
    # one copy of the same case previously reported +4.0 "coverage" lift.
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])
    client = FakeOllamaClient(
        {
            "pinned-eval-model": DUPLICATE_HEAVY_RESPONSE,
            BASE_MODEL: VALID_RESPONSE,
        }
    )

    result = trainer.evaluate_model(test_dataset=test_set, client=client, compare_base=True)

    assert result["metrics"]["raw_test_cases_per_example"] == 5.0
    assert result["metrics"]["unique_valid_test_cases_per_example"] == 1.0
    # Raw volume still shows the difference, under its honest name...
    assert result["delta"]["raw_test_cases_per_example"] == 4.0
    # ...but the decision metric shows no added coverage.
    assert result["delta"]["unique_valid_test_cases_per_example"] == 0.0


def test_invalid_bulk_output_has_zero_unique_valid(trainer, tmp_path):
    # 07-24 review Critical 2, reproduction 2: five canonical-invalid objects
    # must contribute nothing to the decision metric.
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])
    client = FakeOllamaClient(
        {
            "pinned-eval-model": INVALID_BULK_RESPONSE,
            BASE_MODEL: VALID_RESPONSE,
        }
    )

    result = trainer.evaluate_model(test_dataset=test_set, client=client, compare_base=True)

    assert result["metrics"]["overall_score"] == 0.0
    assert result["metrics"]["unique_valid_test_cases_per_example"] == 0.0
    assert result["delta"]["unique_valid_test_cases_per_example"] == -1.0


def test_per_example_reports_invalid_and_duplicate_counts(trainer, tmp_path):
    # Two identical valid + one distinct valid + one invalid object.
    mixed = json.dumps(
        {
            "test_cases": [
                VALID_TEST_CASE,
                VALID_TEST_CASE,
                VALID_TEST_CASE_B,
                {"summary_suffix": "junk"},
            ]
        }
    )
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])

    result = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient(mixed))

    row = result["per_example"][0]
    assert row["num_test_cases"] == 4
    assert row["canonical_valid"] == 3
    assert row["unique_valid"] == 2
    assert row["invalid_test_cases"] == 1
    assert row["duplicate_test_cases"] == 1
