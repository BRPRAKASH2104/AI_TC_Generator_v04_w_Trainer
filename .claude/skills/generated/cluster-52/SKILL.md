---
name: cluster-52
description: "Skill for the Cluster_52 area of AI_TC_Generator_v04_w_Trainer. 11 symbols across 2 files."
---

# Cluster_52

11 symbols | 2 files | Cohesion: 91%

## When to Use

- Working with code in `tests/`
- Understanding how test_valid_test_case, test_invalid_signal_name, test_fuzzy_matching_suggestion work
- Modifying cluster_52-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_validators.py` | test_valid_test_case, test_invalid_signal_name, test_fuzzy_matching_suggestion, test_no_interface_list, test_empty_data_field (+5) |
| `src/core/validators.py` | validate_test_case |

## Entry Points

Start here when exploring this area:

- **`test_valid_test_case`** (Function) — `tests/core/test_validators.py:22`
- **`test_invalid_signal_name`** (Function) — `tests/core/test_validators.py:45`
- **`test_fuzzy_matching_suggestion`** (Function) — `tests/core/test_validators.py:69`
- **`test_no_interface_list`** (Function) — `tests/core/test_validators.py:114`
- **`test_empty_data_field`** (Function) — `tests/core/test_validators.py:132`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_valid_test_case` | Function | `tests/core/test_validators.py` | 22 |
| `test_invalid_signal_name` | Function | `tests/core/test_validators.py` | 45 |
| `test_fuzzy_matching_suggestion` | Function | `tests/core/test_validators.py` | 69 |
| `test_no_interface_list` | Function | `tests/core/test_validators.py` | 114 |
| `test_empty_data_field` | Function | `tests/core/test_validators.py` | 132 |
| `test_data_format_validation` | Function | `tests/core/test_validators.py` | 154 |
| `test_multiple_invalid_signals` | Function | `tests/core/test_validators.py` | 178 |
| `test_similarity_threshold_configuration` | Function | `tests/core/test_validators.py` | 203 |
| `test_unknown_signal_in_test_steps_flagged_without_close_match` | Function | `tests/core/test_validators.py` | 225 |
| `test_generic_words_in_test_steps_not_flagged` | Function | `tests/core/test_validators.py` | 250 |
| `validate_test_case` | Method | `src/core/validators.py` | 141 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Validate_test_case → _validate_signals` | cross_community | 3 |
| `Validate_test_case → _validate_data_format` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_53 | 2 calls |

## How to Explore

1. `context({name: "test_valid_test_case"})` — see callers and callees
2. `query({search_query: "cluster_52"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
