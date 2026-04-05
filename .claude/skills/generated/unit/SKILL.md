---
name: unit
description: "Skill for the Unit area of AI_TC_Generator_v04_w_Trainer. 24 symbols across 4 files."
---

# Unit

24 symbols | 4 files | Cohesion: 67%

## When to Use

- Working with code in `tests/`
- Understanding how list_templates, get_template_info, get_template_usage_summary work
- Modifying unit-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/unit/test_yaml_prompt_manager_fixed.py` | test_initialization_success, test_load_configuration_success, test_list_templates, test_get_template_info, test_get_template_usage_summary (+7) |
| `src/yaml_prompt_manager.py` | YAMLPromptManager, list_templates, get_template_info, get_template_usage_summary, reset_template_usage (+5) |
| `tests/integration/test_end_to_end.py` | test_template_validation_workflow |
| `prompts/tools/validation_and_tools.py` | test_template_rendering |

## Entry Points

Start here when exploring this area:

- **`list_templates`** (Function) — `src/yaml_prompt_manager.py:293`
- **`get_template_info`** (Function) — `src/yaml_prompt_manager.py:300`
- **`get_template_usage_summary`** (Function) — `src/yaml_prompt_manager.py:316`
- **`reset_template_usage`** (Function) — `src/yaml_prompt_manager.py:320`
- **`test_initialization_success`** (Function) — `tests/unit/test_yaml_prompt_manager_fixed.py:15`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `YAMLPromptManager` | Class | `src/yaml_prompt_manager.py` | 15 |
| `list_templates` | Function | `src/yaml_prompt_manager.py` | 293 |
| `get_template_info` | Function | `src/yaml_prompt_manager.py` | 300 |
| `get_template_usage_summary` | Function | `src/yaml_prompt_manager.py` | 316 |
| `reset_template_usage` | Function | `src/yaml_prompt_manager.py` | 320 |
| `test_initialization_success` | Function | `tests/unit/test_yaml_prompt_manager_fixed.py` | 15 |
| `test_load_configuration_success` | Function | `tests/unit/test_yaml_prompt_manager_fixed.py` | 29 |
| `test_list_templates` | Function | `tests/unit/test_yaml_prompt_manager_fixed.py` | 110 |
| `test_get_template_info` | Function | `tests/unit/test_yaml_prompt_manager_fixed.py` | 130 |
| `test_get_template_usage_summary` | Function | `tests/unit/test_yaml_prompt_manager_fixed.py` | 149 |
| `test_reset_template_usage` | Function | `tests/unit/test_yaml_prompt_manager_fixed.py` | 164 |
| `test_load_configuration_file_not_found` | Function | `tests/unit/test_yaml_prompt_manager_fixed.py` | 176 |
| `test_load_configuration_yaml_error` | Function | `tests/unit/test_yaml_prompt_manager_fixed.py` | 188 |
| `test_template_validation_workflow` | Function | `tests/integration/test_end_to_end.py` | 222 |
| `test_template_rendering` | Function | `prompts/tools/validation_and_tools.py` | 60 |
| `get_test_prompt` | Function | `src/yaml_prompt_manager.py` | 145 |
| `get_error_prompt` | Function | `src/yaml_prompt_manager.py` | 190 |
| `test_get_test_prompt_basic` | Function | `tests/unit/test_yaml_prompt_manager_fixed.py` | 44 |
| `test_get_test_prompt_with_template_name` | Function | `tests/unit/test_yaml_prompt_manager_fixed.py` | 61 |
| `test_substitute_variables_basic` | Function | `tests/unit/test_yaml_prompt_manager_fixed.py` | 78 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _resolve_config_path` | cross_community | 5 |
| `Main → _validate_variables` | cross_community | 4 |
| `Main → _apply_defaults` | cross_community | 4 |
| `Main → _substitute_variables` | cross_community | 4 |
| `Main → _validate_variables` | cross_community | 4 |
| `Main → _apply_defaults` | cross_community | 4 |
| `Main → _substitute_variables` | cross_community | 4 |
| `Main → YAMLPromptManager` | cross_community | 4 |
| `Test_template_rendering → _resolve_config_path` | cross_community | 4 |
| `Test_auto_selection → _resolve_config_path` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_39 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "list_templates"})` — see callers and callees
2. `gitnexus_query({query: "unit"})` — find related execution flows
3. Read key files listed above for implementation details
