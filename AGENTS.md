# Repository Guidelines

## Project Structure & Module Organization
- Application entry points live in `main.py` (CLI) and `src/main.py` (package shim). Core domain logic is under `src/`, split by responsibility (`core/` for extractors, generators, formatters; `processors/` for orchestration; `training/` for RAFT tooling).
- Configuration files and logging helpers sit alongside the code in `src/config.py`, `src/app_logger.py`, and `src/yaml_prompt_manager.py`.
- Tests mirror the source tree inside `tests/`, with `unit/`, `integration/`, `performance/`, and scenario files such as `test_critical_improvements.py`. Documentation and reference material are grouped under `docs/`; prompt assets live in `prompts/`.

## Build, Test, and Development Commands
- Install dependencies: `python3 -m pip install -r requirements.txt` (add `.[dev]` from `pyproject.toml` for linting and type checks).
- Run the CLI locally: `python3 main.py input/requirements.reqifz --hp` (omit `--hp` for the synchronous processor).
- Execute automated tests: `pytest` for the full suite; add `-k <pattern>` to target a module, or `--cov=src` to regenerate coverage.
- Lint and format: `ruff check src tests` and `ruff format src tests` (the repository targets Ruff’s `py314` profile).

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation and prefer explicit type hints (the codebase uses Python 3.13+ features such as type aliases with `type`).
- Module, function, and variable names use `snake_case`; classes use `PascalCase`.
- Keep logging consistent via `get_app_logger()` or `FileProcessingLogger` rather than raw `print`.
- Validate JSON responses and error pathways through the existing helpers (`JSONResponseParser`, `SemanticValidator`).

## Testing Guidelines
- Favor pytest-style tests with descriptive method names (`test_<feature>_<condition>`). Place async tests under `pytest.mark.asyncio`.
- Maintain parity between `src/` modules and `tests/` counterparts; stub Ollama calls with `AsyncMock` and `patch` when unit testing processors.
- Regenerate coverage reports via `pytest --cov=src --cov-report=term-missing`; keep critical paths (extractors, processors, prompt builder) covered.

## Commit & Pull Request Guidelines
- Write commits in imperative mood (`fix hp processor semaphore`) and keep them scoped to one logical change; include references to issue IDs where relevant.
- Pull requests should describe the change, outline testing performed, and flag any deviations (e.g., new CLI flags, schema updates). Attach screenshots or sample CLI output when modifying user-facing behavior, and ensure new prompts/configs are documented in `docs/` or inline comments.

## Security & Configuration Tips
- Do not hardcode secrets; rely on `ConfigManager` and environment variables (`AI_TG_*`). Run `config.save_to_file()` only to sanitized locations.
- Validate Ollama availability before invoking HP mode (`ollama serve` and `curl http://127.0.0.1:11434/api/tags`). Document any new model requirements within `docs/` and `pyproject.toml`.
