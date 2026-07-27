---
name: cluster-1
description: "Skill for the Cluster_1 area of AI_TC_Generator_v04_w_Trainer. 9 symbols across 2 files."
---

# Cluster_1

9 symbols | 2 files | Cohesion: 80%

## When to Use

- Working with code in `src/`
- Understanding how set_nested, update_if_not_overridden, get_preset_config work
- Modifying cluster_1-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/config.py` | get_preset_config, apply_cli_overrides, _apply_env_overrides, _apply_model_specific_defaults, update_if_not_overridden (+2) |
| `main.py` | _apply_preset, set_nested |

## Entry Points

Start here when exploring this area:

- **`set_nested`** (Function) — `main.py:92`
- **`update_if_not_overridden`** (Function) — `src/config.py:788`
- **`get_preset_config`** (Method) — `src/config.py:614`
- **`apply_cli_overrides`** (Method) — `src/config.py:634`
- **`show_effective_config`** (Method) — `src/config.py:812`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `set_nested` | Function | `main.py` | 92 |
| `update_if_not_overridden` | Function | `src/config.py` | 788 |
| `get_preset_config` | Method | `src/config.py` | 614 |
| `apply_cli_overrides` | Method | `src/config.py` | 634 |
| `show_effective_config` | Method | `src/config.py` | 812 |
| `_apply_preset` | Function | `main.py` | 63 |
| `_apply_env_overrides` | Method | `src/config.py` | 711 |
| `_apply_model_specific_defaults` | Method | `src/config.py` | 765 |
| `_deep_merge_dict` | Method | `src/config.py` | 804 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _apply_env_overrides` | cross_community | 3 |
| `Main → _deep_merge_dict` | cross_community | 3 |
| `Show_effective_config → _apply_env_overrides` | intra_community | 3 |
| `Show_effective_config → _deep_merge_dict` | intra_community | 3 |

## How to Explore

1. `context({name: "set_nested"})` — see callers and callees
2. `query({search_query: "cluster_1"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
