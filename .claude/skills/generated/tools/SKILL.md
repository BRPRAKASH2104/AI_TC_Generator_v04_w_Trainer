---
name: tools
description: "Skill for the Tools area of AI_TC_Generator_v04_w_Trainer. 6 symbols across 2 files."
---

# Tools

6 symbols | 2 files | Cohesion: 59%

## When to Use

- Working with code in `prompts/`
- Understanding how get_selected_template, validate_template_file, validate_all_templates work
- Modifying tools-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `prompts/tools/validation_and_tools.py` | validate_all_templates, test_auto_selection, generate_sample_outputs, main |
| `src/yaml_prompt_manager.py` | get_selected_template, validate_template_file |

## Entry Points

Start here when exploring this area:

- **`get_selected_template`** (Function) — `src/yaml_prompt_manager.py:312`
- **`validate_template_file`** (Function) — `src/yaml_prompt_manager.py:329`
- **`validate_all_templates`** (Function) — `prompts/tools/validation_and_tools.py:16`
- **`test_auto_selection`** (Function) — `prompts/tools/validation_and_tools.py:113`
- **`generate_sample_outputs`** (Function) — `prompts/tools/validation_and_tools.py:167`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `get_selected_template` | Function | `src/yaml_prompt_manager.py` | 312 |
| `validate_template_file` | Function | `src/yaml_prompt_manager.py` | 329 |
| `validate_all_templates` | Function | `prompts/tools/validation_and_tools.py` | 16 |
| `test_auto_selection` | Function | `prompts/tools/validation_and_tools.py` | 113 |
| `generate_sample_outputs` | Function | `prompts/tools/validation_and_tools.py` | 167 |
| `main` | Function | `prompts/tools/validation_and_tools.py` | 232 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _resolve_config_path` | cross_community | 4 |
| `Main → _validate_variables` | cross_community | 4 |
| `Main → _apply_defaults` | cross_community | 4 |
| `Main → _substitute_variables` | cross_community | 4 |
| `Test_auto_selection → _resolve_config_path` | cross_community | 4 |
| `Generate_sample_outputs → _resolve_config_path` | cross_community | 4 |
| `Main → YAMLPromptManager` | cross_community | 3 |
| `Main → List_templates` | cross_community | 3 |
| `Main → Get_selected_template` | intra_community | 3 |
| `Test_auto_selection → _substitute_variables` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Unit | 6 calls |
| Cluster_39 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "get_selected_template"})` — see callers and callees
2. `gitnexus_query({query: "tools"})` — find related execution flows
3. Read key files listed above for implementation details
