---
name: tests
description: "Skill for the Tests area of AI_TC_Generator_v04_w_Trainer. 53 symbols across 9 files."
---

# Tests

53 symbols | 9 files | Cohesion: 87%

## When to Use

- Working with code in `tests/`
- Understanding how run_context_augmentation, test_taskgroup_available, dummy_task work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/test_refactoring.py` | test_build_augmented_requirements_with_context, test_build_augmented_requirements_no_requirements, test_build_augmented_requirements_no_heading, test_build_prompt_default_no_yaml, test_build_prompt_with_yaml_template (+12) |
| `tests/core/test_base_processor.py` | test_build_augmented_requirements_basic_flow, test_build_augmented_requirements_resets_info_after_requirement, test_build_augmented_requirements_new_heading_resets_info, test_build_augmented_requirements_skips_empty_requirements, test_build_augmented_requirements_no_heading_uses_default (+6) |
| `tests/core/test_prompt_builder.py` | _requirement, test_image_context_rendered_for_requirement_with_images, test_image_context_default_for_requirement_without_images, test_json_example_in_rendered_prompt_is_valid_json, test_template_coverage_wording_scoped_to_displayed_rows (+3) |
| `src/core/prompt_builder.py` | build_prompt, format_table, _build_from_template, _build_default, format_info_list (+2) |
| `src/processors/base_processor.py` | _clean_text_for_logging, _build_augmented_requirements, _generate_output_path |
| `tests/test_critical_improvements.py` | test_base_processor_context_aware_logic_preserved, test_context_reset_after_each_requirement |
| `tests/training/test_raft_integration.py` | test_build_augmented_requirements_unchanged_with_raft, test_context_reset_behavior_intact |
| `tests/test_python314_ollama0125.py` | test_taskgroup_available, dummy_task |
| `tests/performance/test_regression_benchmarks.py` | run_context_augmentation |

## Entry Points

Start here when exploring this area:

- **`run_context_augmentation`** (Function) — `tests/performance/test_regression_benchmarks.py:155`
- **`test_taskgroup_available`** (Function) — `tests/test_python314_ollama0125.py:91`
- **`dummy_task`** (Function) — `tests/test_python314_ollama0125.py:95`
- **`test_build_augmented_requirements_basic_flow`** (Method) — `tests/core/test_base_processor.py:166`
- **`test_build_augmented_requirements_resets_info_after_requirement`** (Method) — `tests/core/test_base_processor.py:201`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `run_context_augmentation` | Function | `tests/performance/test_regression_benchmarks.py` | 155 |
| `test_taskgroup_available` | Function | `tests/test_python314_ollama0125.py` | 91 |
| `dummy_task` | Function | `tests/test_python314_ollama0125.py` | 95 |
| `test_build_augmented_requirements_basic_flow` | Method | `tests/core/test_base_processor.py` | 166 |
| `test_build_augmented_requirements_resets_info_after_requirement` | Method | `tests/core/test_base_processor.py` | 201 |
| `test_build_augmented_requirements_new_heading_resets_info` | Method | `tests/core/test_base_processor.py` | 228 |
| `test_build_augmented_requirements_skips_empty_requirements` | Method | `tests/core/test_base_processor.py` | 249 |
| `test_build_augmented_requirements_no_heading_uses_default` | Method | `tests/core/test_base_processor.py` | 270 |
| `test_build_augmented_requirements_multiple_requirements_same_heading` | Method | `tests/core/test_base_processor.py` | 287 |
| `test_build_augmented_requirements_no_system_requirements` | Method | `tests/core/test_base_processor.py` | 306 |
| `test_base_processor_context_aware_logic_preserved` | Method | `tests/test_critical_improvements.py` | 331 |
| `test_context_reset_after_each_requirement` | Method | `tests/test_critical_improvements.py` | 393 |
| `test_build_augmented_requirements_with_context` | Method | `tests/test_refactoring.py` | 41 |
| `test_build_augmented_requirements_no_requirements` | Method | `tests/test_refactoring.py` | 81 |
| `test_build_augmented_requirements_no_heading` | Method | `tests/test_refactoring.py` | 98 |
| `test_build_augmented_requirements_unchanged_with_raft` | Method | `tests/training/test_raft_integration.py` | 92 |
| `test_context_reset_behavior_intact` | Method | `tests/training/test_raft_integration.py` | 126 |
| `build_prompt` | Method | `src/core/prompt_builder.py` | 67 |
| `test_image_context_rendered_for_requirement_with_images` | Method | `tests/core/test_prompt_builder.py` | 33 |
| `test_image_context_default_for_requirement_without_images` | Method | `tests/core/test_prompt_builder.py` | 50 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _clean_text_for_logging` | cross_community | 5 |
| `_run_standard_mode → _clean_text_for_logging` | cross_community | 4 |
| `Process_directory → _clean_text_for_logging` | cross_community | 4 |
| `Verify_prompt_generation → Format_table` | cross_community | 4 |
| `Verify_prompt_generation → Format_info_list` | cross_community | 4 |
| `Verify_prompt_generation → Format_interfaces` | cross_community | 4 |
| `Verify_prompt_generation → Format_image_context` | cross_community | 4 |

## How to Explore

1. `context({name: "run_context_augmentation"})` — see callers and callees
2. `query({search_query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
