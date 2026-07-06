---
name: cluster-44
description: "Skill for the Cluster_44 area of AI_TC_Generator_v04_w_Trainer. 11 symbols across 2 files."
---

# Cluster_44

11 symbols | 2 files | Cohesion: 91%

## When to Use

- Working with code in `src/`
- Understanding how test_signal_name_extraction, test_batch_validation_report, test_signal_names_extracted_once_per_batch work
- Modifying cluster_44-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/core/validators.py` | _validate_with_signals, _extract_signal_names, _validate_signals, _validate_data_format, validate_batch (+2) |
| `tests/core/test_validators.py` | test_signal_name_extraction, test_batch_validation_report, test_signal_names_extracted_once_per_batch, test_signal_extraction_patterns |

## Entry Points

Start here when exploring this area:

- **`test_signal_name_extraction`** (Function) — `tests/core/test_validators.py:5`
- **`test_batch_validation_report`** (Function) — `tests/core/test_validators.py:87`
- **`test_signal_names_extracted_once_per_batch`** (Function) — `tests/core/test_validators.py:268`
- **`test_signal_extraction_patterns`** (Function) — `tests/core/test_validators.py:290`
- **`validate_batch`** (Method) — `src/core/validators.py:206`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_signal_name_extraction` | Function | `tests/core/test_validators.py` | 5 |
| `test_batch_validation_report` | Function | `tests/core/test_validators.py` | 87 |
| `test_signal_names_extracted_once_per_batch` | Function | `tests/core/test_validators.py` | 268 |
| `test_signal_extraction_patterns` | Function | `tests/core/test_validators.py` | 290 |
| `validate_batch` | Method | `src/core/validators.py` | 206 |
| `_validate_with_signals` | Method | `src/core/validators.py` | 57 |
| `_extract_signal_names` | Method | `src/core/validators.py` | 86 |
| `_validate_signals` | Method | `src/core/validators.py` | 113 |
| `_validate_data_format` | Method | `src/core/validators.py` | 178 |
| `_validate_table_coverage` | Method | `src/core/validators.py` | 255 |
| `_analyze_table_coverage` | Method | `src/core/validators.py` | 329 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Validate_batch → _validate_signals` | intra_community | 3 |
| `Validate_batch → _validate_data_format` | intra_community | 3 |
| `Validate_test_case → _validate_signals` | cross_community | 3 |
| `Validate_test_case → _validate_data_format` | cross_community | 3 |

## How to Explore

1. `context({name: "test_signal_name_extraction"})` — see callers and callees
2. `query({search_query: "cluster_44"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
