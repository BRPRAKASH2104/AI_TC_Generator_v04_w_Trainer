---
name: cluster-39
description: "Skill for the Cluster_39 area of AI_TC_Generator_v04_w_Trainer. 7 symbols across 1 files."
---

# Cluster_39

7 symbols | 1 files | Cohesion: 88%

## When to Use

- Working with code in `src/`
- Understanding how load_configuration, load_all_prompts, reload_prompts work
- Modifying cluster_39-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/yaml_prompt_manager.py` | __init__, _resolve_config_path, load_configuration, _set_default_config, load_all_prompts (+2) |

## Entry Points

Start here when exploring this area:

- **`load_configuration`** (Function) — `src/yaml_prompt_manager.py:83`
- **`load_all_prompts`** (Function) — `src/yaml_prompt_manager.py:111`
- **`reload_prompts`** (Function) — `src/yaml_prompt_manager.py:324`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `load_configuration` | Function | `src/yaml_prompt_manager.py` | 83 |
| `load_all_prompts` | Function | `src/yaml_prompt_manager.py` | 111 |
| `reload_prompts` | Function | `src/yaml_prompt_manager.py` | 324 |
| `__init__` | Function | `src/yaml_prompt_manager.py` | 27 |
| `_resolve_config_path` | Function | `src/yaml_prompt_manager.py` | 44 |
| `_set_default_config` | Function | `src/yaml_prompt_manager.py` | 97 |
| `_auto_select_template` | Function | `src/yaml_prompt_manager.py` | 203 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _resolve_config_path` | cross_community | 5 |
| `Main → _resolve_config_path` | cross_community | 4 |
| `Test_template_rendering → _resolve_config_path` | cross_community | 4 |
| `Test_auto_selection → _resolve_config_path` | cross_community | 4 |
| `Generate_sample_outputs → _resolve_config_path` | cross_community | 4 |
| `Reload_prompts → _resolve_config_path` | intra_community | 3 |
| `__init__ → _set_default_config` | intra_community | 3 |
| `__init__ → _resolve_config_path` | intra_community | 3 |

## How to Explore

1. `gitnexus_context({name: "load_configuration"})` — see callers and callees
2. `gitnexus_query({query: "cluster_39"})` — find related execution flows
3. Read key files listed above for implementation details
