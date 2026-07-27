# AGENTS.md

This file provides guidance to Codex when working with code in this repository.

## Mandatory Protocols (from System_Instructions.md)

**Pre-Flight**: Before any complex task, search `System_Intructions.md` for relevant rules, quote them in your plan, and state how you will comply.

**Verification**: Do not mark a task done until you have checked file paths, naming conventions, and formatting against established patterns.

**Chain-of-Verification**: Answer → generate verification questions → answer them → revise original answer.

**Docstrings**: Follow Google Python Style Guide for all modules, classes, functions, and methods.

**CHANGELOG.md**: Update (Added/Changed/Fixed/Removed) for every significant change.

## Workflow: Codebase Architecture & Investigation

When asked to analyze architecture, find dependencies, or trace execution flows, YOU MUST use this synergistic two-step tool chain:

1. **Step 1 (Strict Code):** Use the **GitNexus** MCP tools (like `impact`, `trace`, or `context`) to map the strict execution paths, method resolutions, and code-level dependencies.
2. **Step 2 (Rationale & Docs):** Once the code flow is mapped, use the **Graphify** skill to query the markdown documentation, PDFs, and inline comments to find the design rationale connected to that flow.

**IMPORTANT:** Do not blindly `grep` or read raw files to understand the system architecture. Rely on GitNexus for the "how" (the code) and Graphify for the "why" (the documentation).

# Repository Instructions

## Git Practices
Read and adhere strictly to `commit.md` for all staging, committing, and GitHub PR workflows.
---

## Project

AI-powered test case generator for automotive REQIFZ requirements. Uses Ollama LLMs locally — **no cloud API calls anywhere**, including the offline evaluation and training paths. This is a hard rule, not a default; it has already cancelled planned features. Do not propose a hosted model for any purpose.

- **Python**: 3.14.6+ (no backward compatibility)
- **Ollama**: v0.31.1+
- **Models**: `llama3.1:8b` (text), `llama3.2-vision:11b` (vision)

---

## Commands

```bash
# Install
pip install -e .[dev]        # dev tools (ruff, pytest, mypy)
pip install -e .[training]   # add torch/transformers
pip install -e .[all]        # everything

# Run
ai-tc-generator input/file.reqifz --verbose
ai-tc-generator input/ --hp --max-concurrent 4   # async high-performance mode
python3 main.py input/file.reqifz --debug

# Test
python3 tests/run_tests.py                                          # full suite
python3 -m pytest tests/core/ -v                                    # fast unit tests
python3 -m pytest tests/ -v -m "not integration"
python3 -m pytest tests/core/test_generators.py::TestClass::test_method -v

# Quality — ruff check is the enforced gate and must pass before commit
ruff check src/ main.py utilities/ --fix
# CAUTION: ~11 files carry pre-existing `ruff format` drift and mypy reports ~310
# pre-existing errors. Do NOT mass-reformat or mass-fix these in an unrelated
# change — only format/type-clean the files you actually touched.
ruff format src/ main.py utilities/
mypy src/ main.py --python-version 3.14

# Packaging
python -m build
twine check dist/*

# Validation
ai-tc-generator --validate-prompts    # after editing YAML templates

# Utilities
python3 utilities/create_mock_reqifz.py    # generate mock REQIFZ for testing

# Presets — run with a named configuration (defined in config/cli_config.yaml under `presets`)
ai-tc-generator input/file.reqifz --preset qwen_vision

# Training (requires pip install -e .[training])
ai-tc-generator input/ --hp              # normal run collects RAFT examples if enabled in config/cli_config.yaml
# Enable in config/cli_config.yaml: training.enable_raft: true, training.collect_training_data: true

# Evaluation & calibration (utilities/train_vision_model.py)
python3 utilities/train_vision_model.py --evaluate val.jsonl --output-model my-model
python3 utilities/train_vision_model.py --evaluate val.jsonl --output-model my-model --compare-base
python3 utilities/train_vision_model.py --validate-judge     # calibrate the content scorer; no Ollama needed
python3 utilities/build_vision_dataset.py --val-split-ratio 0.2 --split-seed 42

# Opt-in live-Ollama tests (excluded from the default suite; self-skip without Ollama)
python3 -m pytest tests/ -m integration -rs   # -rs shows WHY a test skipped
```

---

## Architecture

```
main.py (CLI)
  -> Processor (standard_processor.py | hp_processor.py)
      -> BaseProcessor._build_augmented_requirements()   # SHARED CONTEXT LOGIC
      -> REQIFArtifactExtractor (extractors.py)
          -> RequirementRelationshipParser (relationship_parser.py)  # SPEC-RELATION parsing
          -> RequirementImageExtractor (image_extractor.py)
      -> Generator (generators.py)
          -> _GeneratorCore                    # SHARED sync/async pipeline base
          -> PromptBuilder (prompt_builder.py)
          -> OllamaClient / AsyncOllamaClient (ollama_client.py)
          -> _postprocess_test_cases(): parse -> validate -> dedup -> enrich
      -> Formatter (formatters.py)
  -> Excel output + JSON logs

src/training/                          # RAFT fine-tuning pipeline
  -> RAFTDataCollector (raft_collector.py)       # collects examples during normal runs
  -> RAFTAnnotator (raft_annotator.py)           # expert annotation support
  -> RAFTDatasetBuilder (raft_dataset_builder.py)     # also train/val split_dataset()
  -> ProgressiveRAFTTrainer (progressive_trainer.py)  # curriculum learning
  -> VisionRAFTTrainer (vision_raft_trainer.py)       # create model + evaluate_model()
  -> QualityScorer (quality_scorer.py)

src/training/  (evaluation & calibration — see docs/training/README.md)
  -> ContentScorer protocol + ReferenceOverlapScorer (content_scorer.py)
       # scores generated vs reference test cases: precision/recall/F1
  -> run_calibration / format_report (judge_calibration.py)
  -> DEFAULT_CALIBRATION_CASES (judge_calibration_cases.py)
       # 6 gold-by-construction fixtures that validate a ContentScorer itself
```

**`__slots__`**: Core classes (generators, deduplicator, clients) declare `__slots__` — adding an instance attribute requires adding it to the slots tuple first, or you get `AttributeError` at runtime.

**Config**: `src/config.py` — Pydantic-based, reads env vars automatically. Env var prefix: `AI_TG_` for app flags, `OLLAMA__` for Ollama settings (e.g. `OLLAMA__ENABLE_VISION=false`). Runtime overrides also accepted via `config/cli_config.yaml` (training/vision settings).

**Logging**: Structured JSON via `src/app_logger.py`. Logs in `output/logs/`.

**Prompt templates**: YAML in `prompts/templates/`. Validate after editing. Only `test_generation_adaptive.yaml` (template `adaptive_default`) is active; the old v3 template is archived in `prompts/backups/` — do not load it, it uses the retired `action`/`data` schema.

**Output naming**: `{filename}_TCD_{mode}_{model}_{timestamp}.xlsx`, saved alongside input file.

---

## Critical Architecture: Context-Aware Processing

**DO NOT BREAK** — `BaseProcessor._build_augmented_requirements()` (`src/processors/base_processor.py:140`):

```python
# Interface text fields normalised once before the loop
system_interfaces = [
    {**iface, "text": self._clean_text_for_logging(iface.get("text", ""))}
    for iface in raw_interfaces
]

current_heading = "No Heading"
info_since_heading = []

for obj in artifacts:
    if obj.get("type") == "Heading":
        raw_heading = obj.get("text", "No Heading")
        current_heading = self._clean_text_for_logging(raw_heading) or "No Heading"
        info_since_heading = []          # reset on new heading
    elif obj.get("type") == "Information":
        clean_info = {**obj, "text": self._clean_text_for_logging(obj.get("text", ""))}
        info_since_heading.append(clean_info)
    elif obj.get("type") == "System Requirement":
        req_text = self._clean_text_for_logging(obj.get("text", ""))
        if not req_text:
            continue
        augmented_requirement = obj.copy()
        augmented_requirement.update({
            "text": req_text,            # normalised plain string
            "heading": current_heading,
            "info_list": info_since_heading.copy(),
            "interface_list": system_interfaces
        })
        augmented_requirements.append(augmented_requirement)
        info_since_heading = []          # CRITICAL: reset after each requirement
```

Rules:
- Never filter artifacts before this loop (kills context)
- Never duplicate this logic in individual processors (use inheritance)
- Never remove `heading`, `info_list`, `interface_list` from `PromptBuilder` templates
- `_clean_text_for_logging` handles `str | list | None` — the extractor can return `text` as a Python list of XML node strings; all downstream code (validators, prompt_builder) expects plain strings

---

## Critical Architecture: Hybrid Vision Strategy

Per-requirement model selection via `ConfigManager.get_model_for_requirement()` (`src/config.py:495`):
- Requirement **has images** → `llama3.2-vision:11b` (`generate_response_with_vision()`)
- Requirement **no images** → `llama3.1:8b` (`generate_completion()`)

Never hardcode model selection in processors. Change only in `ConfigManager`.

---

## Critical Architecture: Canonical Test-Case Schema

The one true schema emitted by the active template and expected everywhere downstream: `summary_suffix`, `preconditions`, `test_steps`, `expected_result`, `test_type`.

- `TestCaseDeduplicator` compares `DEFAULT_FIELDS_TO_COMPARE = ["test_steps", "expected_result", "preconditions"]` (`src/core/deduplicator.py:30`). **Never reintroduce `action`/`data` here** — comparing fields the template doesn't produce made every pair look ~identical and silently deleted legitimate test cases (2026-07-05 review §1.1).
- `stamp_validation_results` (`src/core/generators.py:72`) stamps `validation_passed` on each test case **before** dedup runs. Keep this ordering — dedup's "best" keep-strategy reads the flag, and validating after dedup misaligns indices.
- `ValidationConfig` / `DeduplicationConfig` (`src/config.py:152,169`) are wired into their components; change thresholds there, not with hardcoded values.

---

## Critical Architecture: Content Scoring & Calibration

`evaluate_model` scores a customized model on a held-out RAFT dataset. Content
quality comes from a `ContentScorer` (`src/training/content_scorer.py`), whose
only implementation is the deterministic `ReferenceOverlapScorer`.

- **`--validate-judge` runs NO generation model.** It feeds fixed fixtures
  straight into `ContentScorer.score()`, so it measures the *scorer* in
  isolation rather than scorer-plus-model. Never "improve" it by having it
  generate — that reintroduces the confound it exists to remove.
- **Calibration bands are tolerances, not targets.** A breach means fix or
  reconsider the scorer; widening the band to get a pass destroys the signal.
  `paraphrase` is *expected* to score low on `overlap` — that is the documented
  limit of string matching, not a bug.
- **The metric counts matched *pairs*, never *which* pairs.** A scorer pairing
  the right number of wrong items is indistinguishable from a correct one.
  `mixed` catches over-claiming; closing the rest needs `ContentScore` to expose
  the pairing. Assume this ceiling before trusting any new scorer.
- **An LLM-as-judge scorer was retired 2026-07-26** after calibration showed it
  returned a near-constant match list regardless of input (a larger local model
  failed the same way). `--content-scorer`, `--judge-model`,
  `ContentScore.quality` and `content_quality` are gone. Don't reinstate a judge
  without first fixing the metric above — otherwise it cannot be validated. Full
  evidence in `docs/training/README.md`.
- Decision metric: `content_f1` when references exist, else
  `unique_valid_test_cases_per_example`. Validity scores are grammar-saturated
  and near-useless for A/B.

---

## Critical Architecture: Excel Formatter

**Exactly 16 columns**, specific names required (header list at `src/core/formatters.py:315-335`):
- Column 13: `"Feature Group"`
- Column 16: `"LinkTest"` (not `"Tests"`)

If you change columns, update **both** `TestCaseFormatter` and `StreamingTestCaseFormatter` together.

---

## Critical Architecture: REQIF Attribute Mapping

`REQIFArtifactExtractor` maps internal identifiers like `_json2reqif_XXX` to human-readable names like `"ReqIF.Text"` via `_build_attribute_definition_mapping()` (`src/core/extractors.py:244`, called at `:177`). Do not remove or bypass this.

---

## Test Infrastructure: XHTML Format

All artifact text fields use XHTML format. Tests must use helper functions from `tests/helpers/`:

```python
from tests.helpers import create_test_heading, create_test_requirement

# Wrong:
{"type": "Heading", "text": "Door System"}

# Correct:
create_test_heading("Door System", heading_id="H_001")

# Wrong:
assert artifact["heading"] == "Door System"

# Correct:
assert "Door System" in artifact["heading"]
```

See `tests/helpers/USAGE_EXAMPLES.md` for full examples.

---

## Files Not to Modify Without Full Understanding

| File | Critical symbols | Why Critical |
|------|------------------|--------------|
| `src/processors/base_processor.py` | `_build_augmented_requirements` (line 140) | Context-aware processing core |
| `src/core/extractors.py` | `_build_attribute_definition_mapping` (244), `_extract_spec_object` (292) | Attribute definition mapping |
| `src/core/formatters.py` | header list (~315-335), `StreamingTestCaseFormatter` (292) | 16-column Excel structure |
| `src/core/ollama_client.py` | `generate_response_with_vision` — sync (197), async (401); `AsyncOllamaClient.__init__` semaphore (~315) | Vision support; `--max-concurrent` wiring |
| `src/core/generators.py` | `extract_image_paths` (45), `stamp_validation_results` (72), `_GeneratorCore._postprocess_test_cases` (251) | Shared sync/async pipeline; vision path extraction; validate-before-dedup ordering |
| `src/core/deduplicator.py` | `DEFAULT_FIELDS_TO_COMPARE` (30) | Canonical-schema dedup fields (see section above) |
| `src/core/image_extractor.py` | `_validate_image` (390), `_preprocess_image` (532), `cleanup_extracted_images` (591) | Image preprocessing (applied on save) & cleanup |
| `src/config.py` | `enable_vision` (88), `get_model_for_requirement` (495) | Vision config & hybrid selection |
| `src/yaml_prompt_manager.py` | `load_all_prompts`, `_selection_rules` | Selection rules are cached at load time into `_selection_rules`; bypassing or resetting this cache causes repeated disk reads on every template selection call |
| `src/training/content_scorer.py` | `ContentScorer` protocol, `ContentScore` | Scoring seam; changing the TypedDict breaks exact-dict assertions across the eval tests |

Line numbers drift — treat the symbol name as authoritative and the number as a hint.

**Safe to modify**: `src/core/prompt_builder.py`, `prompts/templates/*.yaml`, `tests/`, `src/config.py` (follow Pydantic patterns).

---

## Test Layout

Tests are organized in `tests/core/` (unit), `tests/integration/`, `tests/training/`, `tests/unit/`, `tests/performance/`. Several test files also live directly at `tests/` root (`test_critical_improvements.py`, `test_integration_refactored.py`, `test_python314_ollama0125.py`, `test_refactoring.py`) — these are intentional, not misplaced; do not move or duplicate them into subdirectories.

## Test Markers

`unit`, `integration`, `slow`, `async_test`

---

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| "no text content" for requirements | Attribute mapping bypassed | Check `_build_attribute_definition_mapping` in `extractors.py` |
| Excel export crash in HP mode | Column count/name wrong | Verify 16 cols, "LinkTest" not "Tests" |
| Vision model OOM | Too much concurrency | Lower `--max-concurrent` or `OLLAMA__ENABLE_VISION=false` |
| Tests fail with XHTML mismatches | Not using test helpers | Use `tests/helpers/` functions |
| `generate_test_cases` AttributeError | Wrong generator class | `AsyncTestCaseGenerator` has this method |
| `TypeError: expected str` in validators on `test_steps` | AI returns `test_steps` as a list, not a string | `validators.py` normalises with `"\n".join(raw_data) if isinstance(raw_data, list)` — do not change this pattern |
| Unexpected `training_data/` files written during normal runs | RAFT collection was previously opt-out | Both `enable_raft` and `collect_training_data` default to `false` in `config/cli_config.yaml`; set both to `true` to opt in |
| Live/integration test "passes" suspiciously fast | It self-skipped (no Ollama, or model not pulled) | Run with `-rs` to see the skip reason; a skipped live test proves nothing |
| Exact-dict assertion on a `ContentScore` breaks | A key was added to or removed from the TypedDict | Tests compare the whole dict; update them together. This has broken twice, in both directions |
| `--content-scorer` / `--judge-model` not recognised | Retired 2026-07-26 with the LLM judge | Only the deterministic `overlap` scorer exists; see the Content Scoring section |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **AI_TC_Generator_v04_w_Trainer** (7002 symbols, 9680 relationships, 159 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/AI_TC_Generator_v04_w_Trainer/context` | Codebase overview, check index freshness |
| `gitnexus://repo/AI_TC_Generator_v04_w_Trainer/clusters` | All functional areas |
| `gitnexus://repo/AI_TC_Generator_v04_w_Trainer/processes` | All execution flows |
| `gitnexus://repo/AI_TC_Generator_v04_w_Trainer/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |
| Work in the Training area (261 symbols) | `.claude/skills/generated/training/SKILL.md` |
| Work in the Integration area (161 symbols) | `.claude/skills/generated/integration/SKILL.md` |
| Work in the Tests area (56 symbols) | `.claude/skills/generated/tests/SKILL.md` |
| Work in the Unit area (50 symbols) | `.claude/skills/generated/unit/SKILL.md` |
| Work in the Utilities area (46 symbols) | `.claude/skills/generated/utilities/SKILL.md` |
| Work in the Processors area (42 symbols) | `.claude/skills/generated/processors/SKILL.md` |
| Work in the Cluster_12 area (21 symbols) | `.claude/skills/generated/cluster-12/SKILL.md` |
| Work in the Tools area (15 symbols) | `.claude/skills/generated/tools/SKILL.md` |
| Work in the Cluster_11 area (14 symbols) | `.claude/skills/generated/cluster-11/SKILL.md` |
| Work in the Cluster_34 area (13 symbols) | `.claude/skills/generated/cluster-34/SKILL.md` |
| Work in the Cluster_44 area (13 symbols) | `.claude/skills/generated/cluster-44/SKILL.md` |
| Work in the Cluster_38 area (11 symbols) | `.claude/skills/generated/cluster-38/SKILL.md` |
| Work in the Cluster_53 area (11 symbols) | `.claude/skills/generated/cluster-53/SKILL.md` |
| Work in the Cluster_1 area (9 symbols) | `.claude/skills/generated/cluster-1/SKILL.md` |
| Work in the Cluster_19 area (9 symbols) | `.claude/skills/generated/cluster-19/SKILL.md` |
| Work in the Cluster_20 area (9 symbols) | `.claude/skills/generated/cluster-20/SKILL.md` |
| Work in the Cluster_37 area (9 symbols) | `.claude/skills/generated/cluster-37/SKILL.md` |
| Work in the Cluster_45 area (9 symbols) | `.claude/skills/generated/cluster-45/SKILL.md` |
| Work in the Cluster_54 area (9 symbols) | `.claude/skills/generated/cluster-54/SKILL.md` |
| Work in the Cluster_99 area (8 symbols) | `.claude/skills/generated/cluster-99/SKILL.md` |

<!-- gitnexus:end -->

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
