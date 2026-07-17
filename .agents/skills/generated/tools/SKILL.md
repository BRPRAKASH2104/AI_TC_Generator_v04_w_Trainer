---
name: tools
description: "Skill for the Tools area of AI_TC_Generator_v04_w_Trainer. 15 symbols across 3 files."
---

# Tools

15 symbols | 3 files | Cohesion: 85%

## When to Use

- Working with code in `src/`
- Understanding how validate_all_templates, test_template_rendering, test_auto_selection work
- Modifying tools-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/yaml_prompt_manager.py` | __init__, _resolve_config_path, load_configuration, _set_default_config, load_all_prompts (+4) |
| `prompts/tools/validation_and_tools.py` | validate_all_templates, test_template_rendering, test_auto_selection, generate_sample_outputs, main |
| `tests/unit/test_yaml_prompt_manager_fixed.py` | test_list_templates |

## Entry Points

Start here when exploring this area:

- **`validate_all_templates`** (Function) — `prompts/tools/validation_and_tools.py:16`
- **`test_template_rendering`** (Function) — `prompts/tools/validation_and_tools.py:60`
- **`test_auto_selection`** (Function) — `prompts/tools/validation_and_tools.py:113`
- **`generate_sample_outputs`** (Function) — `prompts/tools/validation_and_tools.py:167`
- **`main`** (Function) — `prompts/tools/validation_and_tools.py:232`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `validate_all_templates` | Function | `prompts/tools/validation_and_tools.py` | 16 |
| `test_template_rendering` | Function | `prompts/tools/validation_and_tools.py` | 60 |
| `test_auto_selection` | Function | `prompts/tools/validation_and_tools.py` | 113 |
| `generate_sample_outputs` | Function | `prompts/tools/validation_and_tools.py` | 167 |
| `main` | Function | `prompts/tools/validation_and_tools.py` | 232 |
| `load_configuration` | Method | `src/yaml_prompt_manager.py` | 90 |
| `load_all_prompts` | Method | `src/yaml_prompt_manager.py` | 118 |
| `reload_prompts` | Method | `src/yaml_prompt_manager.py` | 319 |
| `validate_template_file` | Method | `src/yaml_prompt_manager.py` | 325 |
| `list_templates` | Method | `src/yaml_prompt_manager.py` | 288 |
| `get_selected_template` | Method | `src/yaml_prompt_manager.py` | 307 |
| `test_list_templates` | Method | `tests/unit/test_yaml_prompt_manager_fixed.py` | 110 |
| `__init__` | Method | `src/yaml_prompt_manager.py` | 33 |
| `_resolve_config_path` | Method | `src/yaml_prompt_manager.py` | 51 |
| `_set_default_config` | Method | `src/yaml_prompt_manager.py` | 104 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _resolve_config_path` | cross_community | 4 |
| `Main → _auto_select_template` | cross_community | 4 |
| `Main → _validate_variables` | cross_community | 4 |
| `Main → _apply_defaults` | cross_community | 4 |
| `Main → _substitute_variables` | cross_community | 4 |
| `Main → List_templates` | intra_community | 3 |
| `Main → Get_selected_template` | intra_community | 3 |
| `Generate_sample_outputs → _validate_variables` | cross_community | 3 |
| `Generate_sample_outputs → _apply_defaults` | cross_community | 3 |
| `Generate_sample_outputs → _substitute_variables` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Unit | 4 calls |

## How to Explore

1. `context({name: "validate_all_templates"})` — see callers and callees
2. `query({search_query: "tools"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
