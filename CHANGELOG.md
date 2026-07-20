# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Structured-output schema forced every generated test-case field to an empty
  object, so 100% of test cases failed canonical validation and no Excel output
  was produced on a real Ollama backend. `TEST_CASE_RESPONSE_JSON_SCHEMA`
  (`src/core/validators.py`) declared each canonical field with an empty `{}`
  schema; Ollama compiles that into a llama.cpp grammar meaning "emit `{}`",
  not "any value". Each field now declares `{"type": "string"}`. Verified with a
  live `llama3.1:8b` run: the door/window sample went from 0 valid cases to 7,
  written to Excel. The bug was never caught because CI/unit tests mock Ollama
  and the review's real-integration check was skipped (no server available).

### Removed

- Unused `"analysis"` chain-of-thought output field from the prompt surfaces.
  The model was instructed to emit it on every generation, but no parser,
  validator, or the enforced Ollama `format` schema
  (`TEST_CASE_RESPONSE_JSON_SCHEMA`) ever read it, so it consumed output tokens
  and latency for a discarded result. Removed from the active template
  (`prompts/templates/test_generation_adaptive.yaml`), the `_build_default`
  fallback, and the vision instruction in `PromptBuilder.format_image_context()`
  (`src/core/prompt_builder.py`). Addresses the optional dead-surface cleanup in
  `docs/reviews/Review_Comments_2026_07_20.md`.
