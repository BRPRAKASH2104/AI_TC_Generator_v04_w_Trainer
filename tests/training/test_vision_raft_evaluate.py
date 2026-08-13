"""Unit tests for ``VisionRAFTTrainer.evaluate_model`` (Phase 1 output-quality eval).

Phase 1 runs the *prompt-customized* model over an explicit held-out RAFT
dataset and scores each generation by the canonical-schema pass rate
(``is_canonical_test_case``) — the same gate the production pipeline applies.

These tests inject a fake Ollama client so they stay deterministic and never
shell out to ``ollama``. The live path is covered by a separate real-Ollama
check, ``test_vision_raft_evaluate_integration.py`` (marked ``integration``),
per the project's "mocks cannot catch schema/grammar regressions" lesson.
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


# --- Rec 3 (2026-07-24 review): validate & bound inputs before model calls ---


def _make_trainer(tmp_path, **config_kwargs):
    """Build a trainer whose dataset_path is a throwaway (eval uses test_dataset)."""
    seed = tmp_path / "seed.jsonl"
    _write_jsonl(seed, [_text_example()])
    config = VisionTrainingConfig(output_model="pinned-eval-model", **config_kwargs)
    return VisionRAFTTrainer(
        dataset_path=seed,
        config=config,
        output_dir=tmp_path / "models",
    )


def _client_that_must_not_be_called():
    class _Boom:
        def generate_completion(self, *a, **k):
            raise AssertionError("validation must reject the dataset before any model call")

        generate_response_with_vision = generate_completion

    return _Boom()


def test_empty_dataset_is_rejected(trainer, tmp_path):
    test_set = tmp_path / "empty.jsonl"
    test_set.write_text("\n  \n", encoding="utf-8")  # only blank lines

    with pytest.raises(ValueError, match="empty|no examples"):
        trainer.evaluate_model(test_dataset=test_set, client=_client_that_must_not_be_called())


def test_non_object_line_is_rejected_before_generation(trainer, tmp_path):
    # The exact review repro: a line containing `[]` previously aborted mid-run
    # with `AttributeError: 'list' object has no attribute 'get'`.
    test_set = tmp_path / "bad.jsonl"
    test_set.write_text("[]\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line 1|object"):
        trainer.evaluate_model(test_dataset=test_set, client=_client_that_must_not_be_called())


def test_missing_user_message_is_rejected(trainer, tmp_path):
    test_set = tmp_path / "bad.jsonl"
    _write_jsonl(test_set, [{"messages": [{"role": "system", "content": "s"}]}])

    with pytest.raises(ValueError, match="messages|user"):
        trainer.evaluate_model(test_dataset=test_set, client=_client_that_must_not_be_called())


def test_non_string_user_content_is_rejected(trainer, tmp_path):
    test_set = tmp_path / "bad.jsonl"
    _write_jsonl(
        test_set,
        [
            {
                "messages": [
                    {"role": "system", "content": "s"},
                    {"role": "user", "content": {"not": "a string"}},
                    {"role": "assistant", "content": "a"},
                ]
            }
        ],
    )

    with pytest.raises(ValueError, match="content"):
        trainer.evaluate_model(test_dataset=test_set, client=_client_that_must_not_be_called())


def test_images_field_must_be_a_list(trainer, tmp_path):
    test_set = tmp_path / "bad.jsonl"
    _write_jsonl(
        test_set,
        [
            {
                "messages": [
                    {"role": "system", "content": "s"},
                    {"role": "user", "content": "u", "images": "not-a-list"},
                    {"role": "assistant", "content": "a"},
                ]
            }
        ],
    )

    with pytest.raises(ValueError, match="images"):
        trainer.evaluate_model(test_dataset=test_set, client=_client_that_must_not_be_called())


def test_invalid_base64_image_is_rejected(trainer, tmp_path):
    test_set = tmp_path / "bad.jsonl"
    _write_jsonl(
        test_set,
        [
            {
                "messages": [
                    {"role": "system", "content": "s"},
                    {"role": "user", "content": "u", "images": ["!!!not base64!!!"]},
                    {"role": "assistant", "content": "a"},
                ]
            }
        ],
    )

    with pytest.raises(ValueError, match="base64|image"):
        trainer.evaluate_model(test_dataset=test_set, client=_client_that_must_not_be_called())


def test_oversized_image_is_rejected(tmp_path):
    trainer = _make_trainer(tmp_path, max_image_bytes=16)
    big = base64.b64encode(b"x" * 64).decode("ascii")  # 64 decoded bytes > 16 cap
    test_set = tmp_path / "big.jsonl"
    _write_jsonl(
        test_set,
        [
            {
                "messages": [
                    {"role": "system", "content": "s"},
                    {"role": "user", "content": "u", "images": [big]},
                    {"role": "assistant", "content": "a"},
                ]
            }
        ],
    )

    with pytest.raises(ValueError, match="too large|bytes|image"):
        trainer.evaluate_model(test_dataset=test_set, client=_client_that_must_not_be_called())


def test_too_many_images_per_example_is_rejected(tmp_path):
    trainer = _make_trainer(tmp_path, max_images_per_example=1)
    img = base64.b64encode(FAKE_IMAGE_BYTES).decode("ascii")
    test_set = tmp_path / "many.jsonl"
    _write_jsonl(
        test_set,
        [
            {
                "messages": [
                    {"role": "system", "content": "s"},
                    {"role": "user", "content": "u", "images": [img, img]},
                    {"role": "assistant", "content": "a"},
                ]
            }
        ],
    )

    with pytest.raises(ValueError, match="images"):
        trainer.evaluate_model(test_dataset=test_set, client=_client_that_must_not_be_called())


def test_too_many_examples_is_rejected(tmp_path):
    trainer = _make_trainer(tmp_path, max_eval_examples=1)
    test_set = tmp_path / "many.jsonl"
    _write_jsonl(test_set, [_text_example(), _text_example()])

    with pytest.raises(ValueError, match="examples|limit"):
        trainer.evaluate_model(test_dataset=test_set, client=_client_that_must_not_be_called())


def test_valid_dataset_still_passes_validation(trainer, tmp_path):
    # Regression: a well-formed text+vision dataset must not trip the new checks.
    test_set = tmp_path / "ok.jsonl"
    _write_jsonl(test_set, [_text_example(), _vision_example()])

    result = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient())

    assert result["metrics"]["total_examples"] == 2


# --- Rec 4 (2026-07-24 review): honest bundle-vs-base labeling + provenance ---


def test_compare_base_records_provenance(trainer, tmp_path):
    # The A/B compares the whole customized bundle (custom SYSTEM + PARAMETER
    # overrides) against the base model's own defaults; the result must record
    # that so no one reads the delta as an isolated prompt-only effect.
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])

    result = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(), compare_base=True
    )

    prov = result["provenance"]
    assert prov["customized_model"]["name"] == "pinned-eval-model"
    assert prov["base_model"]["name"] == "llama3.2-vision:11b"
    # Customized generation parameters are recorded explicitly...
    assert prov["customized_model"]["parameters"]["temperature"] == 0.0
    assert prov["customized_model"]["parameters"]["top_p"] == 0.9
    assert prov["customized_model"]["parameters"]["repeat_penalty"] == 1.1
    # ...and the base side is flagged as NOT parameter-matched.
    assert "not matched" in prov["base_model"]["parameters"].lower()
    # The note must not claim an isolated prompt-only effect.
    assert "system prompt" in prov["note"].lower()


def test_no_provenance_without_compare_base(trainer, tmp_path):
    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])

    result = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient())

    assert "provenance" not in result


def test_modelfile_parameters_come_from_shared_source(trainer):
    # Guards drift: the provenance parameters and the actual Modelfile PARAMETER
    # lines must be generated from one source, or the recorded provenance lies.
    params = trainer._customized_model_parameters()
    modelfile_text = trainer._prepare_modelfile().read_text(encoding="utf-8")

    for name, value in params.items():
        assert f"PARAMETER {name} {value}" in modelfile_text


# --- Phase 3: per-example content scoring -----------------------------------


def _example_with_reference(reference_cases):
    ex = _text_example()
    ex["messages"][2]["content"] = json.dumps({"test_cases": reference_cases})
    return ex


def test_per_example_content_matches_reference(trainer, tmp_path):
    # Customized model emits VALID_TEST_CASE; reference is the same case ->
    # perfect precision/recall/f1.
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_example_with_reference([VALID_TEST_CASE])])

    result = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient(VALID_RESPONSE))

    content = result["per_example"][0]["content"]
    # Per key, not whole-dict: ContentScore is a documented seam and exact-dict
    # comparisons on it have broken twice as fields were added and removed.
    assert content["precision"] == 1.0
    assert content["recall"] == 1.0
    assert content["f1"] == 1.0
    assert content["matched_pairs"] == [(0, 0)]


# --- Critical 3: the headline score must publish its own denominator ---------


def test_content_denominators_expose_partial_reference_coverage(trainer, tmp_path):
    # One parseable reference (perfect match) and one unparseable. The aggregate
    # used to report content_f1 == 1.0 with nothing revealing that only half the
    # examples contributed.
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(
        test_set,
        [
            _example_with_reference([VALID_TEST_CASE]),
            _text_example(),  # assistant content is prose, not canonical JSON
        ],
    )

    metrics = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(VALID_RESPONSE)
    )["metrics"]

    assert metrics["content_f1"] == 1.0
    assert metrics["content_reference_examples"] == 2
    assert metrics["content_scored_examples"] == 1
    assert metrics["content_scoring_errors"] == 0


def test_content_denominators_count_examples_without_a_reference(trainer, tmp_path):
    test_set = tmp_path / "held.jsonl"
    no_reference = _text_example()
    no_reference["messages"] = no_reference["messages"][:2]  # drop the assistant turn
    _write_jsonl(test_set, [_example_with_reference([VALID_TEST_CASE]), no_reference])

    metrics = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(VALID_RESPONSE)
    )["metrics"]

    assert metrics["content_reference_examples"] == 1
    assert metrics["content_scored_examples"] == 1


def test_content_scoring_errors_are_counted_not_silently_none(trainer, tmp_path):
    class _ExplodingScorer:
        def score(self, generated_cases, reference_cases):
            raise RuntimeError("scorer blew up")

    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_example_with_reference([VALID_TEST_CASE])])

    result = trainer.evaluate_model(
        test_dataset=test_set,
        client=FakeOllamaClient(VALID_RESPONSE),
        content_scorer=_ExplodingScorer(),
    )

    # A scorer fault must not abort the run, but it must be visible.
    assert result["metrics"]["content_scoring_errors"] == 1
    assert result["metrics"]["content_reference_examples"] == 1
    assert result["metrics"]["content_scored_examples"] == 0
    assert result["per_example"][0]["content_status"] == "error"


def test_content_delta_is_withheld_when_no_pair_scored_content(trainer, tmp_path):
    # Neither side can score content (the reference is prose), so a content
    # delta would compare two undefined populations.
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_text_example()])

    result = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(VALID_RESPONSE), compare_base=True
    )

    assert result["comparison"]["content_status"] == "failed"
    assert result["delta"]["content_f1"] is None


def test_per_example_content_none_without_reference(trainer, tmp_path):
    ex = _text_example()
    ex["messages"][2]["content"] = ""  # no usable reference answer
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [ex])

    result = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient())

    assert result["per_example"][0]["content"] is None


def test_aggregate_reports_content_metrics(trainer, tmp_path):
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(
        test_set,
        [_example_with_reference([VALID_TEST_CASE]), _example_with_reference([VALID_TEST_CASE])],
    )

    metrics = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(VALID_RESPONSE)
    )["metrics"]

    assert metrics["content_f1"] == 1.0
    assert metrics["content_precision"] == 1.0
    assert metrics["content_recall"] == 1.0


def test_content_metrics_none_when_no_references(trainer, tmp_path):
    # _text_example() carries a non-JSON reference ("reference answer") -> no
    # canonical reference cases -> content is None -> aggregate is None.
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_text_example()])

    metrics = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient())["metrics"]

    assert metrics["content_f1"] is None


def test_content_f1_is_in_the_delta(trainer, tmp_path):
    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_example_with_reference([VALID_TEST_CASE])])

    result = trainer.evaluate_model(
        test_dataset=test_set, client=FakeOllamaClient(VALID_RESPONSE), compare_base=True
    )

    assert "content_f1" in result["delta"]


# --- Recommended 5: the validated message must be the evaluated message -------


def _reordered_example():
    """A [system, assistant, user] example: the user turn is NOT at index 1."""
    return {
        "messages": [
            {"role": "system", "content": "s"},
            {"role": "assistant", "content": "THE REFERENCE ANSWER"},
            {"role": "user", "content": "THE ACTUAL USER PROMPT"},
        ]
    }


def test_reordered_roles_generate_from_the_user_turn(trainer, tmp_path):
    # The validator accepted this by role search while the evaluator indexed
    # messages[1], so the model was fed its own reference answer as the prompt.
    test_set = tmp_path / "reordered.jsonl"
    _write_jsonl(test_set, [_reordered_example()])
    client = FakeOllamaClient(VALID_RESPONSE)

    trainer.evaluate_model(test_dataset=test_set, client=client)

    assert len(client.text_calls) == 1
    prompt = client.text_calls[0]["prompt"]
    assert "THE ACTUAL USER PROMPT" in prompt
    assert "THE REFERENCE ANSWER" not in prompt


def test_duplicate_user_turns_use_the_first(trainer, tmp_path):
    test_set = tmp_path / "dupe.jsonl"
    _write_jsonl(
        test_set,
        [
            {
                "messages": [
                    {"role": "system", "content": "s"},
                    {"role": "user", "content": "FIRST USER TURN"},
                    {"role": "user", "content": "SECOND USER TURN"},
                    {"role": "assistant", "content": "a"},
                ]
            }
        ],
    )
    client = FakeOllamaClient(VALID_RESPONSE)

    trainer.evaluate_model(test_dataset=test_set, client=client)

    assert "FIRST USER TURN" in client.text_calls[0]["prompt"]


def test_extra_roles_do_not_break_user_selection(trainer, tmp_path):
    test_set = tmp_path / "extra.jsonl"
    _write_jsonl(
        test_set,
        [
            {
                "messages": [
                    {"role": "system", "content": "s"},
                    {"role": "tool", "content": "tool output"},
                    {"role": "user", "content": "REAL PROMPT"},
                    {"role": "assistant", "content": "a"},
                ]
            }
        ],
    )
    client = FakeOllamaClient(VALID_RESPONSE)

    trainer.evaluate_model(test_dataset=test_set, client=client)

    assert "REAL PROMPT" in client.text_calls[0]["prompt"]


def test_example_without_any_user_turn_is_rejected(trainer, tmp_path):
    test_set = tmp_path / "nouser.jsonl"
    _write_jsonl(
        test_set,
        [{"messages": [{"role": "system", "content": "s"}, ["not", "a", "dict"]]}],
    )

    with pytest.raises(ValueError, match="user message"):
        trainer.evaluate_model(test_dataset=test_set, client=_client_that_must_not_be_called())


def test_aggregate_image_payload_over_the_limit_is_rejected(tmp_path):
    # Each example is individually within max_image_bytes; together they are not.
    # Without an aggregate bound the per-example limits permit ~800 GiB.
    trainer = _make_trainer(tmp_path, max_image_bytes=1024, max_eval_total_bytes=64)
    img = base64.b64encode(b"x" * 48).decode("ascii")  # ~48 decoded bytes each
    test_set = tmp_path / "many.jsonl"
    _write_jsonl(
        test_set,
        [
            {
                "messages": [
                    {"role": "system", "content": "s"},
                    {"role": "user", "content": "u", "images": [img]},
                    {"role": "assistant", "content": "a"},
                ]
            }
        ]
        * 3,
    )

    with pytest.raises(ValueError, match="aggregate limit|max_eval_total_bytes"):
        trainer.evaluate_model(test_dataset=test_set, client=_client_that_must_not_be_called())


def test_aggregate_image_payload_within_the_limit_is_accepted(tmp_path):
    trainer = _make_trainer(tmp_path, max_image_bytes=1024, max_eval_total_bytes=10_000)
    img = base64.b64encode(FAKE_IMAGE_BYTES).decode("ascii")
    test_set = tmp_path / "ok.jsonl"
    _write_jsonl(
        test_set,
        [
            {
                "messages": [
                    {"role": "system", "content": "s"},
                    {"role": "user", "content": "u", "images": [img]},
                    {"role": "assistant", "content": "a"},
                ]
            }
        ]
        * 3,
    )

    result = trainer.evaluate_model(test_dataset=test_set, client=FakeOllamaClient(VALID_RESPONSE))

    assert result["metrics"]["total_examples"] == 3
