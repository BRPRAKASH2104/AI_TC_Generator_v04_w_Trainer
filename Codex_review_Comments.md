# Codex Review Comments

## Findings
- **High – HP mode fails immediately** (`src/processors/hp_processor.py:170`): the async processor calls `generator.generate_test_cases(...)`, but `AsyncTestCaseGenerator` only exposes `generate_test_cases_batch` / `_generate_test_cases_for_requirement_async`. At runtime this raises `AttributeError`, so the advertised high-performance mode never produces output.
- **High – Streaming Excel writer crashes** (`src/core/formatters.py:363-444`): the HP formatter emits a header without the `"Feature Group"`/`"LinkTest"` columns and later reads `formatted_case["Tests"]`, which the formatter never sets. This will throw a `KeyError` even if generation succeeds.
- **High – Packaging requires a non-existent interpreter** (`pyproject.toml:34`): `requires-python = ">=3.14"` cannot be satisfied today; `pip` will refuse to install on 3.12/3.13, effectively making the project un-installable.
- **High – Test suite references dead API** (`tests/integration/test_processors.py:293`): integration tests still call `HighPerformanceREQIFZFileProcessor._calculate_performance_metrics`, which no longer exists. Running the suite fails before reaching assertions.
- **Medium – Version pins target unreleased builds** (`requirements.txt:4-18`): several dependencies are pinned to versions that have not shipped yet (e.g., `pandas>=2.3.2`). Combined with the strict `<` caps, this blocks environment creation.
- **Medium – Only first .reqif entry processed** (`src/core/extractors.py:683`): `extract_reqifz_content` reads the first `.reqif` in the archive and ignores the rest, which can miss specifications in multi-document REQIFZ deliveries.

## Suggested Improvements
- Harmonise streaming and batch formatters (single source of truth for column order and keys) so future edits do not diverge again.
- Relax interpreter/dependency constraints to currently supported versions (e.g., target 3.11+/3.12+) and align `requirements.txt` with `pyproject.toml`.
- Replace direct `print` statements in `src/yaml_prompt_manager.py` with the shared logger so CLI output stays consistent and testable.
- Add regression coverage for the HP path (async generation + streaming formatter). Currently the only HP test is skipped and misses the real failure modes.
- Consider iterating every `.reqif` member in a `.reqifz` archive or exposing a configuration knob, to support OEM suppliers that bundle multiple specs.

## Testing & Coverage
- `pytest` was **not** executed as part of this review; the HP integration suite currently fails fast because of the missing `_calculate_performance_metrics` API, so CI will need fixes before reliable runs are possible.

## Follow-ups / Questions
- Which Python baseline is actually required? The code references 3.13 features, but the packaging metadata blocks installation on any released interpreter—clarifying this will unblock distribution.
- Should HP mode still surface the legacy per-second metrics? If yes, reintroduce `_calculate_performance_metrics` (or update tests/metrics consumers to the new `_get_performance_summary` output).
