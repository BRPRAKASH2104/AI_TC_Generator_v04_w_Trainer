---
name: cluster-89
description: "Skill for the Cluster_89 area of AI_TC_Generator_v04_w_Trainer. 21 symbols across 2 files."
---

# Cluster_89

21 symbols | 2 files | Cohesion: 93%

## When to Use

- Working with code in `tests/`
- Understanding how test_no_duplicates, test_exact_duplicates, test_similar_duplicates work
- Modifying cluster_89-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_deduplicator.py` | test_no_duplicates, test_exact_duplicates, test_similar_duplicates, test_multiple_duplicate_groups, test_keep_strategy_first (+10) |
| `src/core/deduplicator.py` | TestCaseDeduplicator, deduplicate, _select_duplicates_to_remove, _find_best_test_case, _score_test_case (+1) |

## Entry Points

Start here when exploring this area:

- **`test_no_duplicates`** (Function) — `tests/core/test_deduplicator.py:5`
- **`test_exact_duplicates`** (Function) — `tests/core/test_deduplicator.py:24`
- **`test_similar_duplicates`** (Function) — `tests/core/test_deduplicator.py:43`
- **`test_multiple_duplicate_groups`** (Function) — `tests/core/test_deduplicator.py:59`
- **`test_keep_strategy_first`** (Function) — `tests/core/test_deduplicator.py:78`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `TestCaseDeduplicator` | Class | `src/core/deduplicator.py` | 17 |
| `test_no_duplicates` | Function | `tests/core/test_deduplicator.py` | 5 |
| `test_exact_duplicates` | Function | `tests/core/test_deduplicator.py` | 24 |
| `test_similar_duplicates` | Function | `tests/core/test_deduplicator.py` | 43 |
| `test_multiple_duplicate_groups` | Function | `tests/core/test_deduplicator.py` | 59 |
| `test_keep_strategy_first` | Function | `tests/core/test_deduplicator.py` | 78 |
| `test_keep_strategy_last` | Function | `tests/core/test_deduplicator.py` | 94 |
| `test_keep_strategy_best` | Function | `tests/core/test_deduplicator.py` | 110 |
| `test_keep_strategy_best_by_length` | Function | `tests/core/test_deduplicator.py` | 126 |
| `test_similarity_threshold` | Function | `tests/core/test_deduplicator.py` | 142 |
| `test_custom_fields_to_compare` | Function | `tests/core/test_deduplicator.py` | 160 |
| `test_empty_test_cases_list` | Function | `tests/core/test_deduplicator.py` | 179 |
| `test_deduplication_report_structure` | Function | `tests/core/test_deduplicator.py` | 209 |
| `test_case_insensitive_comparison` | Function | `tests/core/test_deduplicator.py` | 229 |
| `test_whitespace_handling` | Function | `tests/core/test_deduplicator.py` | 244 |
| `test_deduplication_rate_calculation` | Function | `tests/core/test_deduplicator.py` | 259 |
| `deduplicate` | Function | `src/core/deduplicator.py` | 40 |
| `_select_duplicates_to_remove` | Function | `src/core/deduplicator.py` | 147 |
| `_find_best_test_case` | Function | `src/core/deduplicator.py` | 175 |
| `_score_test_case` | Function | `src/core/deduplicator.py` | 202 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Deduplicate → _score_test_case` | intra_community | 4 |
| `Deduplicate → _calculate_similarity` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_90 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_no_duplicates"})` — see callers and callees
2. `gitnexus_query({query: "cluster_89"})` — find related execution flows
3. Read key files listed above for implementation details
