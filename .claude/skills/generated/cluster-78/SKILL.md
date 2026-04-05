---
name: cluster-78
description: "Skill for the Cluster_78 area of AI_TC_Generator_v04_w_Trainer. 7 symbols across 2 files."
---

# Cluster_78

7 symbols | 2 files | Cohesion: 56%

## When to Use

- Working with code in `tests/`
- Understanding how test_signal_name_extraction, test_no_interface_list, test_data_format_validation work
- Modifying cluster_78-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_validators.py` | test_signal_name_extraction, test_no_interface_list, test_data_format_validation, test_similarity_threshold_configuration, test_signal_extraction_patterns |
| `src/core/validators.py` | SemanticValidator, _extract_signal_names |

## Entry Points

Start here when exploring this area:

- **`test_signal_name_extraction`** (Function) — `tests/core/test_validators.py:5`
- **`test_no_interface_list`** (Function) — `tests/core/test_validators.py:114`
- **`test_data_format_validation`** (Function) — `tests/core/test_validators.py:154`
- **`test_similarity_threshold_configuration`** (Function) — `tests/core/test_validators.py:203`
- **`test_signal_extraction_patterns`** (Function) — `tests/core/test_validators.py:225`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `SemanticValidator` | Class | `src/core/validators.py` | 12 |
| `test_signal_name_extraction` | Function | `tests/core/test_validators.py` | 5 |
| `test_no_interface_list` | Function | `tests/core/test_validators.py` | 114 |
| `test_data_format_validation` | Function | `tests/core/test_validators.py` | 154 |
| `test_similarity_threshold_configuration` | Function | `tests/core/test_validators.py` | 203 |
| `test_signal_extraction_patterns` | Function | `tests/core/test_validators.py` | 225 |
| `_extract_signal_names` | Function | `src/core/validators.py` | 71 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Generate_test_cases_for_requirement → _extract_signal_names` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_79 | 3 calls |

## How to Explore

1. `gitnexus_context({name: "test_signal_name_extraction"})` — see callers and callees
2. `gitnexus_query({query: "cluster_78"})` — find related execution flows
3. Read key files listed above for implementation details
