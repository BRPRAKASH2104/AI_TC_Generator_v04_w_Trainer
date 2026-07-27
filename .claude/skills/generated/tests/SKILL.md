---
name: tests
description: "Skill for the Tests area of AI_TC_Generator_v04_w_Trainer. 56 symbols across 9 files."
---

# Tests

56 symbols | 9 files | Cohesion: 86%

## When to Use

- Working with code in `tests/`
- Understanding how run_context_augmentation, test_taskgroup_available, dummy_task work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/test_refactoring.py` | test_build_augmented_requirements_with_context, test_build_augmented_requirements_no_requirements, test_build_augmented_requirements_no_heading, test_build_prompt_default_no_yaml, test_build_prompt_with_yaml_template (+12) |
| `tests/core/test_base_processor.py` | test_build_augmented_requirements_basic_flow, test_build_augmented_requirements_includes_design_information_in_context, test_build_augmented_requirements_resets_info_after_requirement, test_build_augmented_requirements_new_heading_resets_info, test_build_augmented_requirements_skips_empty_requirements (+7) |
| `tests/core/test_prompt_builder.py` | _requirement, test_image_context_rendered_for_requirement_with_images, test_image_context_default_for_requirement_without_images, test_relationships_rendered_for_requirement_with_parent_and_children, test_relationships_default_none_for_unrelated_requirement (+5) |
| `src/core/prompt_builder.py` | build_prompt, format_table, _build_from_template, _build_default, format_info_list (+2) |
| `src/processors/base_processor.py` | _clean_text_for_logging, _build_augmented_requirements, _generate_output_path |
| `tests/test_critical_improvements.py` | test_base_processor_context_aware_logic_preserved, test_context_reset_after_each_requirement |
| `tests/training/test_raft_integration.py` | test_build_augmented_requirements_unchanged_with_raft, test_context_reset_behavior_intact |
| `tests/test_python314_ollama0125.py` | test_taskgroup_available, dummy_task |
| `tests/performance/test_regression_benchmarks.py` | run_context_augmentation |

## Entry Points

Start here when exploring this area:

- **`run_context_augmentation`** (Function) — `tests/performance/test_regression_benchmarks.py:165`
- **`test_taskgroup_available`** (Function) — `tests/test_python314_ollama0125.py:90`
- **`dummy_task`** (Function) — `tests/test_python314_ollama0125.py:94`
- **`test_build_augmented_requirements_basic_flow`** (Method) — `tests/core/test_base_processor.py:167`
- **`test_build_augmented_requirements_includes_design_information_in_context`** (Method) — `tests/core/test_base_processor.py:202`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `run_context_augmentation` | Function | `tests/performance/test_regression_benchmarks.py` | 165 |
| `test_taskgroup_available` | Function | `tests/test_python314_ollama0125.py` | 90 |
| `dummy_task` | Function | `tests/test_python314_ollama0125.py` | 94 |
| `test_build_augmented_requirements_basic_flow` | Method | `tests/core/test_base_processor.py` | 167 |
| `test_build_augmented_requirements_includes_design_information_in_context` | Method | `tests/core/test_base_processor.py` | 202 |
| `test_build_augmented_requirements_resets_info_after_requirement` | Method | `tests/core/test_base_processor.py` | 233 |
| `test_build_augmented_requirements_new_heading_resets_info` | Method | `tests/core/test_base_processor.py` | 260 |
| `test_build_augmented_requirements_skips_empty_requirements` | Method | `tests/core/test_base_processor.py` | 281 |
| `test_build_augmented_requirements_no_heading_uses_default` | Method | `tests/core/test_base_processor.py` | 302 |
| `test_build_augmented_requirements_multiple_requirements_same_heading` | Method | `tests/core/test_base_processor.py` | 319 |
| `test_build_augmented_requirements_no_system_requirements` | Method | `tests/core/test_base_processor.py` | 338 |
| `test_base_processor_context_aware_logic_preserved` | Method | `tests/test_critical_improvements.py` | 328 |
| `test_context_reset_after_each_requirement` | Method | `tests/test_critical_improvements.py` | 394 |
| `test_build_augmented_requirements_with_context` | Method | `tests/test_refactoring.py` | 41 |
| `test_build_augmented_requirements_no_requirements` | Method | `tests/test_refactoring.py` | 81 |
| `test_build_augmented_requirements_no_heading` | Method | `tests/test_refactoring.py` | 98 |
| `test_build_augmented_requirements_unchanged_with_raft` | Method | `tests/training/test_raft_integration.py` | 90 |
| `test_context_reset_behavior_intact` | Method | `tests/training/test_raft_integration.py` | 131 |
| `build_prompt` | Method | `src/core/prompt_builder.py` | 67 |
| `test_image_context_rendered_for_requirement_with_images` | Method | `tests/core/test_prompt_builder.py` | 33 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _clean_text_for_logging` | cross_community | 5 |
| `_run_standard_mode → _clean_text_for_logging` | cross_community | 4 |
| `Process_directory → _clean_text_for_logging` | cross_community | 4 |
| `Verify_prompt_generation → Format_table` | cross_community | 4 |
| `Verify_prompt_generation → Format_info_list` | cross_community | 4 |
| `Verify_prompt_generation → Format_interfaces` | cross_community | 4 |
| `Verify_prompt_generation → Format_relationships` | cross_community | 4 |
| `Verify_prompt_generation → Format_image_context` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_50 | 2 calls |
| Cluster_36 | 1 calls |
| Cluster_37 | 1 calls |

## How to Explore

1. `context({name: "run_context_augmentation"})` — see callers and callees
2. `query({search_query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
