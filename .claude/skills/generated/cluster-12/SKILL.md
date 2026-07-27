---
name: cluster-12
description: "Skill for the Cluster_12 area of AI_TC_Generator_v04_w_Trainer. 21 symbols across 2 files."
---

# Cluster_12

21 symbols | 2 files | Cohesion: 95%

## When to Use

- Working with code in `tests/`
- Understanding how test_no_duplicates, test_exact_duplicates, test_similar_duplicates work
- Modifying cluster_12-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_deduplicator.py` | test_no_duplicates, test_exact_duplicates, test_similar_duplicates, test_multiple_duplicate_groups, test_keep_strategy_first (+14) |
| `src/core/deduplicator.py` | deduplicate, _create_report |

## Entry Points

Start here when exploring this area:

- **`test_no_duplicates`** (Function) — `tests/core/test_deduplicator.py:5`
- **`test_exact_duplicates`** (Function) — `tests/core/test_deduplicator.py:24`
- **`test_similar_duplicates`** (Function) — `tests/core/test_deduplicator.py:47`
- **`test_multiple_duplicate_groups`** (Function) — `tests/core/test_deduplicator.py:71`
- **`test_keep_strategy_first`** (Function) — `tests/core/test_deduplicator.py:90`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_no_duplicates` | Function | `tests/core/test_deduplicator.py` | 5 |
| `test_exact_duplicates` | Function | `tests/core/test_deduplicator.py` | 24 |
| `test_similar_duplicates` | Function | `tests/core/test_deduplicator.py` | 47 |
| `test_multiple_duplicate_groups` | Function | `tests/core/test_deduplicator.py` | 71 |
| `test_keep_strategy_first` | Function | `tests/core/test_deduplicator.py` | 90 |
| `test_keep_strategy_last` | Function | `tests/core/test_deduplicator.py` | 106 |
| `test_keep_strategy_best` | Function | `tests/core/test_deduplicator.py` | 122 |
| `test_keep_strategy_best_by_length` | Function | `tests/core/test_deduplicator.py` | 143 |
| `test_similarity_threshold` | Function | `tests/core/test_deduplicator.py` | 163 |
| `test_custom_fields_to_compare` | Function | `tests/core/test_deduplicator.py` | 181 |
| `test_empty_test_cases_list` | Function | `tests/core/test_deduplicator.py` | 204 |
| `test_deduplication_report_structure` | Function | `tests/core/test_deduplicator.py` | 254 |
| `test_case_insensitive_comparison` | Function | `tests/core/test_deduplicator.py` | 274 |
| `test_whitespace_handling` | Function | `tests/core/test_deduplicator.py` | 293 |
| `test_deduplication_rate_calculation` | Function | `tests/core/test_deduplicator.py` | 312 |
| `test_adaptive_schema_distinct_cases_are_kept` | Function | `tests/core/test_deduplicator.py` | 342 |
| `test_adaptive_schema_exact_duplicates_removed` | Function | `tests/core/test_deduplicator.py` | 374 |
| `test_cross_schema_aliases_detected_as_duplicates` | Function | `tests/core/test_deduplicator.py` | 392 |
| `test_list_valued_test_steps_supported` | Function | `tests/core/test_deduplicator.py` | 415 |
| `deduplicate` | Method | `src/core/deduplicator.py` | 57 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Deduplicate → _field_value` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Training | 1 calls |
| Cluster_14 | 1 calls |

## How to Explore

1. `context({name: "test_no_duplicates"})` — see callers and callees
2. `query({search_query: "cluster_12"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
