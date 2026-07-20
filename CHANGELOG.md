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
