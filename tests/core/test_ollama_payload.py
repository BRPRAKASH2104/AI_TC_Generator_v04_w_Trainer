"""Unit tests for the shared Ollama request-payload builder.

Covers JSON-schema structured output support (review 2026-07-17 finding 4):
a format_schema dict must be forwarded as the Ollama `format` object so the
model is constrained to the canonical test-case schema.
"""

from config import OllamaConfig
from core.ollama_client import _build_generate_payload


def _payload(**kwargs):
    defaults = {
        "config": OllamaConfig(),
        "model_name": "llama3.1:8b",
        "prompt": "Generate",
        "is_json": False,
        "images_base64": None,
        "context_window": 4096,
    }
    defaults.update(kwargs)
    return _build_generate_payload(**defaults)


class TestFormatSchema:
    def test_schema_dict_is_sent_as_format(self):
        schema = {"type": "object", "required": ["test_cases"]}

        payload = _payload(is_json=True, format_schema=schema)

        assert payload["format"] == schema

    def test_is_json_without_schema_sends_json_string(self):
        payload = _payload(is_json=True)

        assert payload["format"] == "json"

    def test_no_json_no_schema_sends_no_format(self):
        payload = _payload(is_json=False)

        assert "format" not in payload
