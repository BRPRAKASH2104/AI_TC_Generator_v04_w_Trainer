---
name: unit
description: "Skill for the Unit area of AI_TC_Generator_v04_w_Trainer. 20 symbols across 3 files."
---

# Unit

20 symbols | 3 files | Cohesion: 79%

## When to Use

- Working with code in `src/`
- Understanding how show_banner, main, set_nested work
- Modifying unit-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/yaml_prompt_manager.py` | get_test_prompt, _auto_select_template, _validate_variables, _apply_defaults, _substitute_variables (+3) |
| `tests/unit/test_yaml_prompt_manager_fixed.py` | test_get_test_prompt_basic, test_get_test_prompt_with_template_name, test_substitute_variables_basic, test_substitute_variables_missing_variable, test_get_template_info (+2) |
| `main.py` | show_banner, main, set_nested, _validate_templates, _list_templates |

## Entry Points

Start here when exploring this area:

- **`show_banner`** (Function) — `main.py:41`
- **`main`** (Function) — `main.py:108`
- **`set_nested`** (Function) — `main.py:176`
- **`get_test_prompt`** (Method) — `src/yaml_prompt_manager.py:154`
- **`test_get_test_prompt_basic`** (Method) — `tests/unit/test_yaml_prompt_manager_fixed.py:44`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `show_banner` | Function | `main.py` | 41 |
| `main` | Function | `main.py` | 108 |
| `set_nested` | Function | `main.py` | 176 |
| `get_test_prompt` | Method | `src/yaml_prompt_manager.py` | 154 |
| `test_get_test_prompt_basic` | Method | `tests/unit/test_yaml_prompt_manager_fixed.py` | 44 |
| `test_get_test_prompt_with_template_name` | Method | `tests/unit/test_yaml_prompt_manager_fixed.py` | 61 |
| `test_substitute_variables_basic` | Method | `tests/unit/test_yaml_prompt_manager_fixed.py` | 78 |
| `test_substitute_variables_missing_variable` | Method | `tests/unit/test_yaml_prompt_manager_fixed.py` | 95 |
| `get_template_info` | Method | `src/yaml_prompt_manager.py` | 295 |
| `test_get_template_info` | Method | `tests/unit/test_yaml_prompt_manager_fixed.py` | 130 |
| `get_template_usage_summary` | Method | `src/yaml_prompt_manager.py` | 311 |
| `test_get_template_usage_summary` | Method | `tests/unit/test_yaml_prompt_manager_fixed.py` | 149 |
| `reset_template_usage` | Method | `src/yaml_prompt_manager.py` | 315 |
| `test_reset_template_usage` | Method | `tests/unit/test_yaml_prompt_manager_fixed.py` | 164 |
| `_validate_templates` | Function | `main.py` | 426 |
| `_list_templates` | Function | `main.py` | 461 |
| `_auto_select_template` | Method | `src/yaml_prompt_manager.py` | 199 |
| `_validate_variables` | Method | `src/yaml_prompt_manager.py` | 237 |
| `_apply_defaults` | Method | `src/yaml_prompt_manager.py` | 251 |
| `_substitute_variables` | Method | `src/yaml_prompt_manager.py` | 273 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _auto_select_template` | cross_community | 4 |
| `Main → _validate_variables` | cross_community | 4 |
| `Main → _apply_defaults` | cross_community | 4 |
| `Main → _substitute_variables` | cross_community | 4 |
| `Main → _log_with_extras` | cross_community | 3 |
| `Generate_sample_outputs → _validate_variables` | cross_community | 3 |
| `Generate_sample_outputs → _apply_defaults` | cross_community | 3 |
| `Generate_sample_outputs → _substitute_variables` | cross_community | 3 |
| `_validate_templates → _auto_select_template` | cross_community | 3 |
| `_validate_templates → _validate_variables` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Integration | 8 calls |
| Cluster_7 | 3 calls |

## How to Explore

1. `context({name: "show_banner"})` — see callers and callees
2. `query({search_query: "unit"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
