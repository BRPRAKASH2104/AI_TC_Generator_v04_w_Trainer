---
name: cluster-37
description: "Skill for the Cluster_37 area of AI_TC_Generator_v04_w_Trainer. 9 symbols across 2 files."
---

# Cluster_37

9 symbols | 2 files | Cohesion: 90%

## When to Use

- Working with code in `tests/`
- Understanding how select_relevant_interfaces, test_exact_match_scopes_to_referenced_interface, test_info_text_contributes_to_matching work
- Modifying cluster_37-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_interface_matcher.py` | _index, test_exact_match_scopes_to_referenced_interface, test_info_text_contributes_to_matching, test_no_match_falls_back_to_all_capped, test_fallback_is_capped (+3) |
| `src/core/interface_matcher.py` | select_relevant_interfaces |

## Entry Points

Start here when exploring this area:

- **`select_relevant_interfaces`** (Function) — `src/core/interface_matcher.py:56`
- **`test_exact_match_scopes_to_referenced_interface`** (Function) — `tests/core/test_interface_matcher.py:25`
- **`test_info_text_contributes_to_matching`** (Function) — `tests/core/test_interface_matcher.py:37`
- **`test_no_match_falls_back_to_all_capped`** (Function) — `tests/core/test_interface_matcher.py:47`
- **`test_fallback_is_capped`** (Function) — `tests/core/test_interface_matcher.py:56`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `select_relevant_interfaces` | Function | `src/core/interface_matcher.py` | 56 |
| `test_exact_match_scopes_to_referenced_interface` | Function | `tests/core/test_interface_matcher.py` | 25 |
| `test_info_text_contributes_to_matching` | Function | `tests/core/test_interface_matcher.py` | 37 |
| `test_no_match_falls_back_to_all_capped` | Function | `tests/core/test_interface_matcher.py` | 47 |
| `test_fallback_is_capped` | Function | `tests/core/test_interface_matcher.py` | 56 |
| `test_matched_results_are_capped` | Function | `tests/core/test_interface_matcher.py` | 62 |
| `test_fuzzy_match_tolerates_typo` | Function | `tests/core/test_interface_matcher.py` | 69 |
| `test_short_word_does_not_false_match` | Function | `tests/core/test_interface_matcher.py` | 76 |
| `_index` | Function | `tests/core/test_interface_matcher.py` | 9 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_36 | 2 calls |

## How to Explore

1. `context({name: "select_relevant_interfaces"})` — see callers and callees
2. `query({search_query: "cluster_37"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
