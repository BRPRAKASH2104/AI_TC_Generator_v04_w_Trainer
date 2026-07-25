"""Live-Ollama integration test for ``VisionRAFTTrainer.evaluate_model``.

The unit tests in ``test_vision_raft_evaluate.py`` inject a fake client and so
cannot catch schema/grammar/routing regressions in the real generation path —
the same blind spot that let a base-model wiring bug ship (2026-07-24 review,
Recommended 5). This test drives the evaluator through a real ``OllamaClient``
and asserts result shape, text-example routing, canonical scoring, the paired
comparison, and the failed-baseline CLI contract.

It is opt-in: marked ``integration`` (excluded by ``-m "not integration"``) and
``slow``, and it skips itself when no reachable Ollama with the required text
model is available. The text model is used deliberately — the local
``llama.cpp`` server lacks ``mllama`` support, so live *vision* eval is not
exercised here.
"""

import importlib.util
import json
from pathlib import Path

import pytest
import requests

from src.config import ConfigManager
from src.training.vision_raft_trainer import VisionRAFTTrainer, VisionTrainingConfig

# Project text-generation default; must support structured output.
TEXT_MODEL = "llama3.1:8b"
# A model that does not exist, to force a total baseline-generation failure.
MISSING_MODEL = "definitely-not-a-real-model-zzz:0b"

_CLI_PATH = Path(__file__).resolve().parents[2] / "utilities" / "train_vision_model.py"


def _ollama_reason() -> str | None:
    """Return None when a reachable Ollama has TEXT_MODEL, else a skip reason."""
    config = ConfigManager()
    tags_url = f"http://{config.ollama.host}:{config.ollama.port}/api/tags"
    try:
        response = requests.get(tags_url, timeout=2)
        response.raise_for_status()
        names = {model.get("name", "") for model in response.json().get("models", [])}
    except requests.RequestException as exc:
        return f"Ollama not reachable at {tags_url}: {exc}"

    family = TEXT_MODEL.split(":", 1)[0]
    if not any(name == TEXT_MODEL or name.startswith(family) for name in names):
        return f"model {TEXT_MODEL} not pulled (available: {sorted(names)})"
    return None


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("train_vision_model_cli_it", _CLI_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _text_example() -> dict:
    """A well-formed text-only RAFT example that should yield canonical cases."""
    return {
        "messages": [
            {"role": "system", "content": "You generate automotive test cases."},
            {
                "role": "user",
                "content": (
                    "Relevant Context: The system shall unlock all doors when the "
                    "vehicle speed is 0 km/h and the driver presses the central "
                    "unlock button.\n\nGenerate test cases in the required JSON schema."
                ),
            },
            {"role": "assistant", "content": "reference answer"},
        ]
    }


def _write_jsonl(path: Path, examples: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(e) for e in examples) + "\n", encoding="utf-8")


@pytest.mark.integration
@pytest.mark.slow
def test_real_ollama_evaluate_with_compare_is_complete(tmp_path) -> None:
    """Live A/B (both sides = TEXT_MODEL) must complete and score canonically."""
    reason = _ollama_reason()
    if reason:
        pytest.skip(reason)

    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])
    trainer = VisionRAFTTrainer(
        dataset_path=test_set,
        config=VisionTrainingConfig(output_model=TEXT_MODEL, base_model=TEXT_MODEL),
        output_dir=tmp_path / "models",
    )

    result = trainer.evaluate_model(test_dataset=test_set, compare_base=True)

    metrics = result["metrics"]
    assert metrics["total_examples"] == 1
    # Text example routed through the text path, not the vision path.
    assert metrics["text_examples"] == 1
    assert metrics["vision_examples"] == 0
    assert 0.0 <= metrics["overall_score"] <= 1.0
    # Canonical scoring actually ran (the model returned parseable structured JSON).
    assert result["per_example"][0]["parsed"] is True
    # Both real models succeeded on the one example -> a complete, paired delta.
    assert result["comparison"]["status"] == "complete"
    assert result["comparison"]["paired_examples"] == 1
    assert result["delta"] is not None
    # Provenance records the bundle-vs-base framing.
    assert result["provenance"]["customized_model"]["name"] == TEXT_MODEL


@pytest.mark.integration
@pytest.mark.slow
def test_real_ollama_failed_baseline_makes_cli_exit_nonzero(tmp_path) -> None:
    """A missing base model must fail the comparison and return CLI exit 1."""
    reason = _ollama_reason()
    if reason:
        pytest.skip(reason)

    test_set = tmp_path / "held_out.jsonl"
    _write_jsonl(test_set, [_text_example()])
    tvm = _load_cli_module()

    exit_code = tvm.run_evaluation(
        str(test_set), TEXT_MODEL, compare_base=True, base_model=MISSING_MODEL
    )

    # The customized side generated fine, but the baseline could not, so the
    # A/B claim is unusable and the CLI must not exit 0.
    assert exit_code == 1


def _text_example_with_reference() -> dict:
    ex = _text_example()
    ex["messages"][2]["content"] = json.dumps(
        {
            "test_cases": [
                {
                    "summary_suffix": "doors unlock at standstill",
                    "preconditions": "vehicle speed 0 km/h",
                    "test_steps": "1. Press the central unlock button.",
                    "expected_result": "All doors unlock.",
                    "test_type": "functional",
                }
            ]
        }
    )
    return ex


@pytest.mark.integration
@pytest.mark.slow
def test_real_ollama_populates_content_metrics(tmp_path) -> None:
    """A live run with a reference answer must populate content metrics."""
    reason = _ollama_reason()
    if reason:
        pytest.skip(reason)

    test_set = tmp_path / "held.jsonl"
    _write_jsonl(test_set, [_text_example_with_reference()])
    trainer = VisionRAFTTrainer(
        dataset_path=test_set,
        config=VisionTrainingConfig(output_model=TEXT_MODEL),
        output_dir=tmp_path / "models",
    )

    result = trainer.evaluate_model(test_dataset=test_set)

    content = result["per_example"][0]["content"]
    assert content is not None
    assert 0.0 <= content["recall"] <= 1.0
    assert result["metrics"]["content_f1"] is not None
