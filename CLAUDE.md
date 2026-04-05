# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Mandatory Protocols (from System_Instructions.md)

**Pre-Flight**: Before any complex task, search `System_Intructions.md` for relevant rules, quote them in your plan, and state how you will comply.

**Verification**: Do not mark a task done until you have checked file paths, naming conventions, and formatting against established patterns.

**Chain-of-Verification**: Answer → generate verification questions → answer them → revise original answer.

**Review Reports**: Always save to `docs/reviews/Review_Comments_YYYY_MM_DD.md`.

**Docstrings**: Follow Google Python Style Guide for all modules, classes, functions, and methods.

**CHANGELOG.md**: Update `[Unreleased]` section (Added/Changed/Fixed/Removed) for every significant change.

---

## Project

AI-powered test case generator for automotive REQIFZ requirements. Uses Ollama LLMs locally — no cloud API calls.

- **Python**: 3.14+ (no backward compatibility)
- **Ollama**: v0.17.4+
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

# Quality (must pass before commit)
ruff check src/ main.py utilities/ --fix
ruff format src/ main.py utilities/
mypy src/ main.py --python-version 3.14

# Validation
ai-tc-generator --validate-prompts    # after editing YAML templates

# Utilities
python3 utilities/create_mock_reqifz.py    # generate mock REQIFZ for testing

# Training (requires pip install -e .[training])
ai-tc-generator input/ --hp              # normal run collects RAFT examples if enabled in config/cli_config.yaml
# Enable in config/cli_config.yaml: training.enable_raft: true, training.collect_training_data: true
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
          -> PromptBuilder (prompt_builder.py)
          -> OllamaClient / AsyncOllamaClient (ollama_client.py)
          -> FastJSONResponseParser -> SemanticValidator -> TestCaseDeduplicator
      -> Formatter (formatters.py)
  -> Excel output + JSON logs

src/training/                          # RAFT fine-tuning pipeline
  -> RAFTDataCollector (raft_collector.py)       # collects examples during normal runs
  -> RAFTAnnotator (raft_annotator.py)           # expert annotation support
  -> RAFTDatasetBuilder (raft_dataset_builder.py)
  -> ProgressiveRAFTTrainer (progressive_trainer.py)  # curriculum learning
  -> VisionRAFTTrainer (vision_raft_trainer.py)
  -> QualityScorer (quality_scorer.py)
```

**Config**: `src/config.py` — Pydantic-based, reads env vars automatically. Env var prefix: `AI_TG_` for app flags, `OLLAMA__` for Ollama settings (e.g. `OLLAMA__ENABLE_VISION=false`). Runtime overrides also accepted via `config/cli_config.yaml` (training/vision settings).

**Logging**: Structured JSON via `src/app_logger.py`. Logs in `output/logs/`.

**Prompt templates**: YAML in `prompts/templates/`. Validate after editing.

**Output naming**: `{filename}_TCD_{mode}_{model}_{timestamp}.xlsx`, saved alongside input file.

---

## Critical Architecture: Context-Aware Processing

**DO NOT BREAK** — `BaseProcessor._build_augmented_requirements()` (`src/processors/base_processor.py:62-126`):

```python
current_heading = "No Heading"
info_since_heading = []

for obj in artifacts:
    if obj.get("type") == "Heading":
        current_heading = obj.get("text", "No Heading")
        info_since_heading = []          # reset on new heading
    elif obj.get("type") == "Information":
        info_since_heading.append(obj)
    elif obj.get("type") == "System Requirement":
        augmented_requirement = obj.copy()
        augmented_requirement.update({
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

---

## Critical Architecture: Hybrid Vision Strategy

Per-requirement model selection via `ConfigManager.get_model_for_requirement()`:
- Requirement **has images** → `llama3.2-vision:11b` (`generate_response_with_vision()`)
- Requirement **no images** → `llama3.1:8b` (`generate_response()`)

Never hardcode model selection in processors. Change only in `ConfigManager`.

---

## Critical Architecture: Excel Formatter

**Exactly 16 columns**, specific names required (`src/core/formatters.py:363-447`):
- Column 13: `"Feature Group"`
- Column 16: `"LinkTest"` (not `"Tests"`)

If you change columns, update **both** `TestCaseFormatter` and `StreamingTestCaseFormatter` together.

---

## Critical Architecture: REQIF Attribute Mapping

`REQIFArtifactExtractor` (`src/core/extractors.py:151-172,191,235`) maps internal identifiers like `_json2reqif_XXX` to human-readable names like `"ReqIF.Text"` via `_build_attribute_definition_mapping()`. Do not remove or bypass this.

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

| File | Lines | Why Critical |
|------|-------|--------------|
| `src/processors/base_processor.py` | 62-126 | Context-aware processing core |
| `src/core/extractors.py` | 151-172, 191, 235 | Attribute definition mapping |
| `src/core/formatters.py` | 363-447 | 16-column Excel structure |
| `src/core/ollama_client.py` | 146-266, 578-689 | Vision model support |
| `src/core/image_extractor.py` | 203-244, 354-395, 415-454 | Image preprocessing & cleanup |
| `src/core/generators.py` | 41-62, 85-98, 200-221, 351-367 | Vision path extraction |
| `src/config.py` | 79-92, 211, 378, 475-498 | Vision config & hybrid selection |

**Safe to modify**: `src/core/prompt_builder.py`, `prompts/templates/*.yaml`, `tests/`, `src/config.py` (follow Pydantic patterns).

---

## Test Markers

`unit`, `integration`, `slow`, `async_test`

---

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| "no text content" for requirements | Attribute mapping bypassed | Check extractor lines 151-172 |
| Excel export crash in HP mode | Column count/name wrong | Verify 16 cols, "LinkTest" not "Tests" |
| Vision model OOM | Too much concurrency | Lower `--max-concurrent` or `OLLAMA__ENABLE_VISION=false` |
| Tests fail with XHTML mismatches | Not using test helpers | Use `tests/helpers/` functions |
| `generate_test_cases` AttributeError | Wrong generator class | `AsyncTestCaseGenerator` has this method |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **AI_TC_Generator_v04_w_Trainer** (4618 symbols, 7924 relationships, 207 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/AI_TC_Generator_v04_w_Trainer/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/AI_TC_Generator_v04_w_Trainer/context` | Codebase overview, check index freshness |
| `gitnexus://repo/AI_TC_Generator_v04_w_Trainer/clusters` | All functional areas |
| `gitnexus://repo/AI_TC_Generator_v04_w_Trainer/processes` | All execution flows |
| `gitnexus://repo/AI_TC_Generator_v04_w_Trainer/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |
| Work in the Tests area (181 symbols) | `.claude/skills/generated/tests/SKILL.md` |
| Work in the Integration area (111 symbols) | `.claude/skills/generated/integration/SKILL.md` |
| Work in the Training area (94 symbols) | `.claude/skills/generated/training/SKILL.md` |
| Work in the Utilities area (58 symbols) | `.claude/skills/generated/utilities/SKILL.md` |
| Work in the Processors area (24 symbols) | `.claude/skills/generated/processors/SKILL.md` |
| Work in the Unit area (24 symbols) | `.claude/skills/generated/unit/SKILL.md` |
| Work in the Cluster_89 area (21 symbols) | `.claude/skills/generated/cluster-89/SKILL.md` |
| Work in the Cluster_74 area (17 symbols) | `.claude/skills/generated/cluster-74/SKILL.md` |
| Work in the Cluster_86 area (11 symbols) | `.claude/skills/generated/cluster-86/SKILL.md` |
| Work in the Cluster_105 area (9 symbols) | `.claude/skills/generated/cluster-105/SKILL.md` |
| Work in the Cluster_44 area (8 symbols) | `.claude/skills/generated/cluster-44/SKILL.md` |
| Work in the Cluster_79 area (8 symbols) | `.claude/skills/generated/cluster-79/SKILL.md` |
| Work in the Cluster_39 area (7 symbols) | `.claude/skills/generated/cluster-39/SKILL.md` |
| Work in the Cluster_75 area (7 symbols) | `.claude/skills/generated/cluster-75/SKILL.md` |
| Work in the Cluster_77 area (7 symbols) | `.claude/skills/generated/cluster-77/SKILL.md` |
| Work in the Cluster_78 area (7 symbols) | `.claude/skills/generated/cluster-78/SKILL.md` |
| Work in the Cluster_83 area (7 symbols) | `.claude/skills/generated/cluster-83/SKILL.md` |
| Work in the Tools area (6 symbols) | `.claude/skills/generated/tools/SKILL.md` |
| Work in the Cluster_76 area (6 symbols) | `.claude/skills/generated/cluster-76/SKILL.md` |
| Work in the Cluster_84 area (6 symbols) | `.claude/skills/generated/cluster-84/SKILL.md` |

<!-- gitnexus:end -->
