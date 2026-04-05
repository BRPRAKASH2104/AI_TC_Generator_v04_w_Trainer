---
name: cluster-79
description: "Skill for the Cluster_79 area of AI_TC_Generator_v04_w_Trainer. 8 symbols across 2 files."
---

# Cluster_79

8 symbols | 2 files | Cohesion: 58%

## When to Use

- Working with code in `tests/`
- Understanding how test_valid_test_case, test_invalid_signal_name, test_fuzzy_matching_suggestion work
- Modifying cluster_79-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_validators.py` | test_valid_test_case, test_invalid_signal_name, test_fuzzy_matching_suggestion, test_empty_data_field, test_multiple_invalid_signals |
| `src/core/validators.py` | validate_test_case, _validate_signals, _validate_data_format |

## Entry Points

Start here when exploring this area:

- **`test_valid_test_case`** (Function) — `tests/core/test_validators.py:22`
- **`test_invalid_signal_name`** (Function) — `tests/core/test_validators.py:45`
- **`test_fuzzy_matching_suggestion`** (Function) — `tests/core/test_validators.py:69`
- **`test_empty_data_field`** (Function) — `tests/core/test_validators.py:132`
- **`test_multiple_invalid_signals`** (Function) — `tests/core/test_validators.py:178`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_valid_test_case` | Function | `tests/core/test_validators.py` | 22 |
| `test_invalid_signal_name` | Function | `tests/core/test_validators.py` | 45 |
| `test_fuzzy_matching_suggestion` | Function | `tests/core/test_validators.py` | 69 |
| `test_empty_data_field` | Function | `tests/core/test_validators.py` | 132 |
| `test_multiple_invalid_signals` | Function | `tests/core/test_validators.py` | 178 |
| `validate_test_case` | Function | `src/core/validators.py` | 28 |
| `_validate_signals` | Function | `src/core/validators.py` | 98 |
| `_validate_data_format` | Function | `src/core/validators.py` | 149 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Generate_test_cases_for_requirement → _extract_signal_names` | cross_community | 4 |
| `Generate_test_cases_for_requirement → _validate_signals` | cross_community | 4 |
| `Generate_test_cases_for_requirement → _validate_data_format` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_78 | 6 calls |

## How to Explore

1. `gitnexus_context({name: "test_valid_test_case"})` — see callers and callees
2. `gitnexus_query({query: "cluster_79"})` — find related execution flows
3. Read key files listed above for implementation details
