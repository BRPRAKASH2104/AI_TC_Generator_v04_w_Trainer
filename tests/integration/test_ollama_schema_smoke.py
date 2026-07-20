"""Live-Ollama smoke test guarding the structured-output schema.

Regression guard for the empty-object schema bug (review 2026-07-20,
Critical finding 3): ``TEST_CASE_RESPONSE_JSON_SCHEMA`` once declared each
canonical field with an empty ``{}`` schema, which Ollama compiled into a
grammar that forced every field to ``{}`` — so 100% of generated test cases
failed canonical validation and no Excel was produced. The mocked unit/CI
suite never caught it because it never exercised a real backend.

This test sends the real active prompt template plus the enforced ``format``
schema through a live Ollama instance and asserts that at least one returned
test case survives ``is_canonical_test_case``. If the schema ever regresses to
emitting empty/typeless fields, this assertion fails.

It is opt-in: marked ``integration`` (excluded by ``-m "not integration"``)
and ``slow``, and it skips itself when no reachable Ollama with the required
model is available, so it is safe to leave in the default collection.
"""

import json

import pytest
import requests

from src.config import ConfigManager
from src.core.ollama_client import OllamaClient
from src.core.prompt_builder import PromptBuilder
from src.core.validators import (
    TEST_CASE_RESPONSE_JSON_SCHEMA,
    is_canonical_test_case,
)
from src.yaml_prompt_manager import YAMLPromptManager

# Project text-generation default; the model must support structured output.
TEXT_MODEL = "llama3.1:8b"


def _ollama_smoke_target() -> tuple[ConfigManager | None, str | None]:
    """Return (config, None) when a usable Ollama target exists, else (None, reason).

    The reachability/model check is performed here (inside the test call) rather
    than at import time so that running with ``-m "not integration"`` performs no
    network I/O.

    Returns:
        A tuple of the loaded ConfigManager and ``None`` when a reachable Ollama
        instance has ``TEXT_MODEL`` pulled; otherwise ``(None, reason)`` with a
        human-readable skip reason.
    """
    config = ConfigManager()
    tags_url = f"http://{config.ollama.host}:{config.ollama.port}/api/tags"
    try:
        response = requests.get(tags_url, timeout=2)
        response.raise_for_status()
        names = {model.get("name", "") for model in response.json().get("models", [])}
    except requests.RequestException as exc:
        return None, f"Ollama not reachable at {tags_url}: {exc}"

    family = TEXT_MODEL.split(":", 1)[0]
    if not any(name == TEXT_MODEL or name.startswith(family) for name in names):
        return None, f"model {TEXT_MODEL} not pulled (available: {sorted(names)})"
    return config, None


@pytest.mark.integration
@pytest.mark.slow
def test_real_ollama_yields_canonical_test_case() -> None:
    """A live generation with the enforced schema must yield a canonical case.

    Fails if the structured-output schema regresses to emitting empty/typeless
    fields (the empty ``{}`` schema bug), because such fields never satisfy
    ``is_canonical_test_case``.
    """
    config, reason = _ollama_smoke_target()
    if reason:
        pytest.skip(reason)
    assert config is not None  # narrowed for type-checkers; guaranteed by reason

    requirement = {
        "id": "REQ_SMOKE_001",
        "text": (
            "The system shall unlock all doors when the vehicle speed is 0 km/h "
            "and the driver presses the central unlock button."
        ),
        "heading": "Smoke Test - Central Locking",
        "info_list": [],
        "interface_list": [],
        "images": [],
    }
    prompt = PromptBuilder(YAMLPromptManager()).build_prompt(requirement)

    client = OllamaClient(config.ollama)
    response = client.generate_completion(
        TEXT_MODEL,
        prompt,
        return_full_response=True,
        format_schema=TEST_CASE_RESPONSE_JSON_SCHEMA,
    )
    text = response.get("response", "") if isinstance(response, dict) else str(response)

    # The `format` schema constrains the backend to valid JSON, so a plain load
    # is sufficient; a decode error here is itself a schema/backend regression.
    payload = json.loads(text)
    test_cases = payload.get("test_cases", [])
    assert test_cases, f"model returned no test_cases; raw response: {text[:300]!r}"

    canonical = [tc for tc in test_cases if is_canonical_test_case(tc)]
    assert canonical, (
        "no generated test case passed canonical validation — the structured-output "
        f"schema may be emitting empty/typeless fields. First case: {test_cases[0]!r}"
    )
