# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (test coverage)

- **Direct unit coverage for three under-tested training modules** (review
  2026-07-20 Recommended finding 10(b)). Added `tests/training/test_quality_scorer.py`,
  `test_raft_annotator.py`, and `test_progressive_trainer.py` (56 tests). Coverage:
  `quality_scorer.py` 12% → 96%, `progressive_trainer.py` 21% → 80%,
  `raft_annotator.py` 13% → 80%. The tests assert **dataset influence** — that a
  content-rich RAFT example scores materially higher than a degenerate one and that
  the progressive curriculum's heuristic readiness score is a genuine function of
  the dataset (verifying the honest "does not fine-tune" contract from finding 3) —
  plus failure paths (missing/empty/corrupt dirs, insufficient examples) and the
  annotator's oracle-selection input parser (all/none/skip/numeric/invalid). No
  Ollama or subprocess is exercised. Full suite: 522 passed, 3 skipped.

- **Pinned the `VisionRAFTTrainer.evaluate_model` stub contract**
  (`tests/training/test_vision_raft_evaluate.py`). `evaluate_model` is still a
  `# TODO` stub returning hardcoded `0.0` scores; these characterization tests
  lock its shape and all-zero "not implemented" behavior so it cannot silently
  begin reporting fabricated non-zero metrics, and guard that it shells out to no
  subprocess while stubbed. To be updated when real evaluation is implemented.

### Changed (style/CI)

- **One-time repo-wide `ruff format` pass + whole-repo style gate** (review
  2026-07-20 Recommended finding 10, explicitly authorized). Reformatted 32
  drifting files (30 test modules plus `src/core/validators.py` and
  `prompts/tools/validation_and_tools.py`) — purely mechanical, no logic change;
  full suite unchanged (413 passed / 1 skipped, 52 mock-integration passed). The
  CI `lint` job now runs `ruff check .` and `ruff format --check .` (whole repo)
  instead of only `src/ main.py utilities/`, so `tests/` and `prompts/` are held
  to the same style gate and cannot drift back.

- **`utilities/` type-cleaned and added to the mypy gate** (review 2026-07-20
  Recommended finding 10, follow-up to the formatting pass). Resolved the 17
  mypy errors across 5 utility modules (`create_mock_reqifz.py`,
  `compare_v03_v04_output.py`, `verify_v03_compatibility.py`,
  `version_check.py`, `annotate_raft.py`): added missing return/parameter
  annotations, typed `parsed_requirements` as `list[tuple[str, str | None]]`
  (unversioned requirement lines legitimately carry `None`), removed a dead
  `if not version_ok:` branch that was unreachable after the early-return
  version-check guard, and marked the `sys.path.insert`-resolved
  `from config import ConfigManager` with a scoped `# type: ignore[attr-defined]`.
  The CI `type-check` job now runs `mypy src/ main.py utilities/` instead of
  only `src/`. `tests/` stays out of the gate — its pre-existing errors are a
  separate, larger effort (see CLAUDE.md).

### Fixed (test quality)

- **Scoped quality fixes toward review 2026-07-20 Recommended finding 10.**
  Replaced the `assert True` placeholder in
  `tests/integration/test_processors.py::test_calculate_performance_metrics`
  with real assertions against the current `_get_performance_summary()`
  (success rate, avg/peak CPU & memory, pass-through counts). Fixed the four
  whole-repo Ruff violations that were all in tests (unused `pathlib.Path` and
  `mock_response` — the latter also used the retired `action`/`data` schema —
  plus an import-sort and a trailing-whitespace issue); whole-repo `ruff check`
  is now clean. (The whole-repo `ruff format` drift and utility-module mypy
  errors are deliberately **not** swept here per the CLAUDE.md rule against
  mass-formatting unrelated files.)

- **Declared Pillow as a runtime dependency** (`pillow>=11.0.0,<13.0.0`).
  Image extraction is enabled by default and `image_extractor` needs Pillow, but
  it was only a silent `try/except` import — so a default install quietly
  skipped image preprocessing (and 12 vision tests skipped). Now declared and
  pinned in `constraints.txt` (`pillow==12.3.0`); the vision test suite runs
  instead of skipping.

### Security

- **Hardened REQIFZ XML parsing against XXE and entity-expansion.** REQIFZ
  archives are user-supplied, so their embedded XML is untrusted. The four
  `xml.etree.ElementTree.fromstring` call sites in `src/core/extractors.py`
  (`_parse_reqif_xml`, `parse_and_augment_relationships`),
  `src/core/image_extractor.py` (`_extract_embedded_images`), and
  `src/core/parsers.py` (`HTMLTableParser`) now use
  `defusedxml.ElementTree.fromstring`, which rejects DTD/entity definitions
  ("billion laughs") and external-entity references while returning the same
  standard `ElementTree` nodes for legitimate input. `defusedxml>=0.7.1` is now
  a declared runtime dependency, and `_parse_reqif_xml`'s handler was widened to
  `except (ET.ParseError, DefusedXmlException)`. Resolves the four Bandit B314
  findings at source (no suppression/baseline). Guarded by
  `tests/core/test_xml_hardening.py` and verified against real REQIFZ files
  (698-artifact DIAG file parses unchanged). Addresses part of review 2026-07-20
  Recommended finding 8.

### Changed (dependencies)

- **Refreshed stale dependency upper bounds to current stable majors** (review
  2026-07-20 Recommended finding 9, `pyproject.toml`). Seven caps that excluded
  current releases were raised to the next unreleased major and validated one
  family at a time against the full non-integration suite (413 passed / 1
  skipped, unchanged) plus `mypy src/` (clean) on Python 3.14.6:
  pandas `<3`→`<4` (3.0.3), rich `<14`→`<16` (15.0.0), psutil `<7`→`<8` (7.2.2),
  pytest `<9`→`<10` (9.1.1), pytest-cov `<7`→`<8` (7.1.0),
  pytest-asyncio `<0.26`→`<2` (1.4.0), mypy `<2`→`<3` (2.3.0). No cap needed to
  be retained. Added **`constraints.txt`** — a tested, fully-resolved runtime
  lock for reproducible deployment (`pip install -e . -c constraints.txt`).
  Removed a now-redundant `click.*` mypy override (click ships inline types;
  mypy 2.3 flagged it as unused).

### Changed (CI)

- **Repaired CI release/security blind spots (review 2026-07-20 Recommended
  finding 8, `.github/workflows/ci.yml`).** The integration job was permanently
  disabled with `if: false`; it is replaced by two jobs: `test-integration-mock`
  runs the mock-backed `tests/integration/` suite on every push/PR (these were
  previously never run — the unit job `--ignore`s that directory), and
  `test-integration-ollama` runs the real-Ollama-marked tests opt-in via
  `workflow_dispatch`. `pip-audit` no longer uses `continue-on-error`
  (`--strict`): known dependency vulnerabilities now fail the build under a
  documented, auditable `--ignore-vuln` policy. The Bandit job's gating policy
  is documented inline. (Wheel build+clean-venv smoke-test was already added in
  a prior session.)

### Added

- Requirement traceability relationships (parent/child/hierarchy) are now
  injected into generation prompts. `RequirementRelationshipParser` already
  parsed SPEC-RELATION elements and attached `parent_id`, `child_ids`, and
  `hierarchy_level` to each requirement (enabled by default), but the metadata
  was never surfaced to the model. A new `PromptBuilder.format_relationships()`
  renders it, wired into both the active template
  (`prompts/templates/test_generation_adaptive.yaml`, new
  `{relationship_str}` section + "use context" guidance) and the
  `_build_default` fallback (`src/core/prompt_builder.py`). Requirements with no
  relationships render `"None"`, so prompts are unchanged for flat requirement
  sets. Verified with a live `llama3.1:8b` run: the relationship section
  rendered and generation still produced canonical test cases (4/4 valid).
  Addresses the "relationship metadata parsed but never used" finding in
  `docs/reviews/Review_Comments_2026_07_20.md`.

### Changed

- **Breaking (internal API):** `REQIFArtifactExtractor` /
  `HighPerformanceREQIFArtifactExtractor` now take `config` as a **keyword-only**
  argument (`__init__(self, logger=None, *, config=None)`, `src/core/extractors.py`).
  This prevents a stale positional call from silently binding an unrelated value
  to `config` after the removals below. **Migration:** pass `config=...` by
  keyword (all in-tree callers already do). Addresses review 2026-07-20
  Recommended finding 5.

### Changed (docs)

- **Consolidated the training documentation into one accurate guide** (review
  2026-07-20 Recommended finding 7 remainder). Five overlapping/partly
  speculative guides (~3,360 lines) were replaced by a single current
  `docs/training/README.md` that documents the capability that actually
  ships — a *prompt-customization* pipeline (RAFT collect → annotate → build
  dataset → `ollama create` a Modelfile-based model), **not** weight
  fine-tuning — with verified commands, config keys, and an explicit
  "not implemented" section for the LoRA path. The old guides
  (`GETTING_STARTED_WITH_TRAINING.md`, `MODEL_TRAINING_GUIDE.md`,
  `RAFT_TECHNICAL.md`, `TRAINING_GUIDE.md`, `training_guideline.md`) were moved
  to `docs/training/archive/` (via `git mv`, preserving history) behind a
  superseded banner. Corrected the `--training` CLI message and `docs/README.md`
  link, which pointed at the (now archived, wrong-path) `MODEL_TRAINING_GUIDE.md`
  and wrongly claimed `train_vision_model.py` needs the `[training]` extra (it
  uses an Ollama Modelfile and needs no extra dependencies).

### Added (CI)

- **`scripts/verify_doc_examples.sh` + a `verify-doc-examples` CI job** (review
  2026-07-20 Recommended finding 7). Executes the documented CLI/utility
  invocations that need neither Ollama nor an input file (`--help`,
  `--validate-prompts`, `--list-templates`, the training utilities' `--help`)
  and asserts they exit 0, plus a guard that `--training` exits non-zero — so
  the documentation stays an executable, verified contract.

### Fixed

- **`--training` CLI flag no longer reports false success** (review 2026-07-20
  Archived finding 12, `main.py`). It previously printed "Training logic would
  be implemented here" and returned exit code 0, signalling success for an
  action that never ran. It now prints how to actually run the training
  pipeline — RAFT collection via `config/cli_config.yaml`, and the standalone
  `utilities/build_vision_dataset.py` / `annotate_raft.py` /
  `train_vision_model.py` scripts — and exits `1` (total failure; `2` is
  reserved for partial completion per `_resolve_exit_code`). The `--help` text
  now states the flag is not implemented in this CLI.

- User-facing documentation drift corrected (review 2026-07-20 Recommended
  finding 7). `README.md` advertised 87% test coverage and a fabricated
  "as of Nov 3, 2025" test-count breakdown — replaced with the real measured
  numbers (73% line coverage; 460 tests collected, 456 passed / 1 skipped in
  the default suite) plus the command to regenerate them. Corrected the Ollama
  minimum version (`0.17.4+` → `0.31.1+`) in both requirement blocks. Replaced
  the fictional `--profile` / `profiles/profiles.yaml` sections in `README.md`
  and `docs/USER_MANUAL.md` with the real `--preset` mechanism
  (`config/cli_config.yaml`), and removed the unsupported `--mode standard`
  example. Added a prominent "aspirational — not implemented" banner to
  `docs/training/MODEL_TRAINING_GUIDE.md`, whose LoRA/full-fine-tuning scripts
  (`src/training/lora_trainer.py`, `src/training/train_lora.py`) do not exist,
  pointing readers to the real prompt-customization workflow.

- `Design Information` requirement artifacts were misclassified as generic
  `INFORMATION`. In `_map_reqif_type_to_artifact_type`
  (`src/core/extractors.py`) the generic `"information"` branch was ordered
  before `"design information"`; since the latter contains `"information"`, the
  generic branch shadowed it and `ArtifactType.DESIGN_INFORMATION` was
  effectively dead. The `"design"` branch now precedes the generic
  `"information"` branch. Paired with a matching change in
  `BaseProcessor._build_augmented_requirements`
  (`src/processors/base_processor.py`), which now folds `Design Information`
  into the same per-heading context bucket as `Information` — without it,
  correctly typing these artifacts would have silently dropped them from
  prompts. Prompt content is unchanged for existing files (design info already
  reached context as `INFORMATION`); it is now correctly typed. Regression
  tests in `tests/core/test_artifact_type_mapping.py` and
  `tests/core/test_base_processor.py`. Addresses finding 10 in
  `docs/reviews/Review_Comments_2026_07_20.md`.

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

- **Breaking (internal API):** the `use_streaming` and `max_workers` constructor
  keyword arguments on the REQIF extractor classes, and `_max_concurrent` on
  `AsyncTestCaseGenerator`, were removed (commits `da28695` / `37088cb` and the
  later async-generator cleanup). They were previously retained only for
  interface compatibility and had no runtime effect. **Migration:** drop these
  arguments; concurrency is controlled via `--max-concurrent` / `OllamaConfig`,
  and streaming is always on where supported. Passing them now raises
  `TypeError`. Documents review 2026-07-20 Recommended finding 5.

- Unused `"analysis"` chain-of-thought output field from the prompt surfaces.
  The model was instructed to emit it on every generation, but no parser,
  validator, or the enforced Ollama `format` schema
  (`TEST_CASE_RESPONSE_JSON_SCHEMA`) ever read it, so it consumed output tokens
  and latency for a discarded result. Removed from the active template
  (`prompts/templates/test_generation_adaptive.yaml`), the `_build_default`
  fallback, and the vision instruction in `PromptBuilder.format_image_context()`
  (`src/core/prompt_builder.py`). Addresses the optional dead-surface cleanup in
  `docs/reviews/Review_Comments_2026_07_20.md`.
