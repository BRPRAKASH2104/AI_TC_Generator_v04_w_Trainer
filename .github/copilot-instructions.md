# Copilot Instructions for AI_TC_Generator_v04_w_Trainer

## Project Overview
This is a modular Python 3.13+ system for generating AI-powered test cases from automotive REQIFZ requirements files. It features a unified CLI (`main.py` and `ai-tc-generator`), high-performance async processing, and comprehensive error handling. The architecture is designed for maintainability, scalability, and rapid development/testing.

## Key Architecture & Patterns
- **Single Entry Point:** All workflows start from `main.py` (CLI) or the installed `ai-tc-generator` command.
- **Core Logic:** Located in `src/core/` (extractors, parsers, generators, formatters, Ollama client).
- **Workflow Orchestration:** Managed in `src/processors/` (standard and high-performance processors).
- **Config Management:** Centralized in `src/config.py` (Pydantic-based, CLI overrides).
- **Logging:** Structured, centralized logging via `src/app_logger.py`.
- **Prompt Templates:** Managed in `prompts/` (YAML), validated with CLI commands.
- **Test Suite:** All code changes must pass `python tests/run_tests.py` (unit, integration, async, config tests).

## Developer Workflow
- **Environment:** Python 3.13.7+, install with `pip install -e .[dev]`.
- **Run:** Use `ai-tc-generator <input>` or `python main.py <input>`.
- **Test:** Run `python tests/run_tests.py` for full suite; use `pytest` for granular tests.
- **Lint/Format:** Use `ruff check src/ main.py utilities/` and `ruff format ...`.
- **Type Check:** Use `mypy src/ main.py --python-version 3.13`.
- **Build:** `python -m build` for packaging; `twine check dist/*` for validation.
- **Mock Data:** Generate with `python utilities/create_mock_reqifz.py`.

## Processing & Data Flow
- **Input:** Place `.reqifz` files in `input/` (subdirectories supported).
- **Output:** Excel/JSON files saved alongside input; logs in JSON format.
- **Naming:** Output files follow `{filename}_TCD_{mode}_{model}_{timestamp}.xlsx`.
- **High-Performance:** Use `--hp` and `--max-concurrent` for async/concurrent processing.

## Error Handling & Validation
- **Structured error objects** for all failures (see `CLAUDE.md` for example).
- **Template validation:** Run `ai-tc-generator --validate-prompts` after editing YAML templates.
- **Comprehensive logging** for audit and debugging.

## AI Model Integration
- **Ollama API:** Models managed via `ollama` CLI; see `CLAUDE.md` for setup.
- **Model selection:** Use `--model <name>` CLI flag.

## Conventions & Best Practices
- **All new code must be tested and linted.**
- **Use async/await and __slots__ for performance.**
- **Centralize config and logging.**
- **Document new features in `docs/` and update relevant READMEs.**
- **Use environment variables prefixed with `AI_TG_` for secrets.**

## Key Files & Directories
- `main.py`, `src/core/`, `src/processors/`, `src/config.py`, `src/app_logger.py`, `prompts/`, `tests/`, `utilities/`, `input/`, `output/`, `docs/`

## Example Commands
- `ai-tc-generator input/your_file.reqifz --hp --model deepseek-coder-v2:16b --verbose`
- `python tests/run_tests.py`
- `ruff check src/ main.py --fix`
- `ai-tc-generator --validate-prompts`

---
For more details, see `CLAUDE.md` and `docs/README.md`. All instructions here are based on validated, discoverable project patterns as of 2025-09-29.
