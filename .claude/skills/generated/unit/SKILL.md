---
name: unit
description: "Skill for the Unit area of AI_TC_Generator_v04_w_Trainer. 50 symbols across 8 files."
---

# Unit

50 symbols | 8 files | Cohesion: 88%

## When to Use

- Working with code in `tests/`
- Understanding how template_schema_issues, get_test_prompt, test_get_test_prompt_basic work
- Modifying unit-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/unit/test_main_helpers.py` | _effective_for_preset, test_production_preset_mode_and_flags_survive, test_production_preset_concurrency_not_clobbered_by_model_defaults, test_development_preset_verbose_survives_absent_cli_flag, test_all_files_succeeded (+13) |
| `src/yaml_prompt_manager.py` | get_test_prompt, _auto_select_template, _validate_variables, _apply_defaults, _substitute_variables (+3) |
| `tests/unit/test_yaml_prompt_manager_fixed.py` | test_get_test_prompt_basic, test_get_test_prompt_with_template_name, test_substitute_variables_basic, test_substitute_variables_missing_variable, test_get_template_info (+2) |
| `tests/unit/test_training_consent.py` | test_training_section_is_loaded, test_unknown_training_keys_are_ignored, _processor_with, test_both_flags_enabled_creates_collector, test_enable_raft_alone_is_not_consent (+2) |
| `main.py` | _aggregate_directory_results, _resolve_exit_code, _resolve_processing_mode, _validate_templates |
| `tests/unit/test_config_export.py` | _config_with_secrets, test_secret_values_not_written, test_secrets_section_absent_and_config_still_valid, test_export_has_owner_only_permissions |
| `src/config.py` | load_cli_config |
| `src/core/validators.py` | template_schema_issues |

## Entry Points

Start here when exploring this area:

- **`template_schema_issues`** (Function) — `src/core/validators.py:64`
- **`get_test_prompt`** (Method) — `src/yaml_prompt_manager.py:154`
- **`test_get_test_prompt_basic`** (Method) — `tests/unit/test_yaml_prompt_manager_fixed.py:44`
- **`test_get_test_prompt_with_template_name`** (Method) — `tests/unit/test_yaml_prompt_manager_fixed.py:61`
- **`test_substitute_variables_basic`** (Method) — `tests/unit/test_yaml_prompt_manager_fixed.py:78`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `template_schema_issues` | Function | `src/core/validators.py` | 64 |
| `get_test_prompt` | Method | `src/yaml_prompt_manager.py` | 154 |
| `test_get_test_prompt_basic` | Method | `tests/unit/test_yaml_prompt_manager_fixed.py` | 44 |
| `test_get_test_prompt_with_template_name` | Method | `tests/unit/test_yaml_prompt_manager_fixed.py` | 61 |
| `test_substitute_variables_basic` | Method | `tests/unit/test_yaml_prompt_manager_fixed.py` | 78 |
| `test_substitute_variables_missing_variable` | Method | `tests/unit/test_yaml_prompt_manager_fixed.py` | 95 |
| `load_cli_config` | Method | `src/config.py` | 560 |
| `test_production_preset_mode_and_flags_survive` | Method | `tests/unit/test_main_helpers.py` | 118 |
| `test_production_preset_concurrency_not_clobbered_by_model_defaults` | Method | `tests/unit/test_main_helpers.py` | 125 |
| `test_development_preset_verbose_survives_absent_cli_flag` | Method | `tests/unit/test_main_helpers.py` | 131 |
| `test_training_section_is_loaded` | Method | `tests/unit/test_training_consent.py` | 43 |
| `test_unknown_training_keys_are_ignored` | Method | `tests/unit/test_training_consent.py` | 60 |
| `test_all_files_succeeded` | Method | `tests/unit/test_main_helpers.py` | 12 |
| `test_one_file_failed_means_partial_not_success` | Method | `tests/unit/test_main_helpers.py` | 25 |
| `test_partial_file_propagates_partial` | Method | `tests/unit/test_main_helpers.py` | 37 |
| `test_all_files_failed` | Method | `tests/unit/test_main_helpers.py` | 48 |
| `test_empty_results_is_failure` | Method | `tests/unit/test_main_helpers.py` | 60 |
| `test_complete_success_is_zero` | Method | `tests/unit/test_main_helpers.py` | 70 |
| `test_partial_success_is_two` | Method | `tests/unit/test_main_helpers.py` | 73 |
| `test_partial_directory_failure_is_two` | Method | `tests/unit/test_main_helpers.py` | 76 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _auto_select_template` | cross_community | 4 |
| `Main → _validate_variables` | cross_community | 4 |
| `Main → _apply_defaults` | cross_community | 4 |
| `Main → _substitute_variables` | cross_community | 4 |
| `Generate_sample_outputs → _validate_variables` | cross_community | 3 |
| `Generate_sample_outputs → _apply_defaults` | cross_community | 3 |
| `Generate_sample_outputs → _substitute_variables` | cross_community | 3 |
| `_validate_templates → _auto_select_template` | cross_community | 3 |
| `_validate_templates → _validate_variables` | cross_community | 3 |
| `_validate_templates → _apply_defaults` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_1 | 1 calls |

## How to Explore

1. `context({name: "template_schema_issues"})` — see callers and callees
2. `query({search_query: "unit"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
