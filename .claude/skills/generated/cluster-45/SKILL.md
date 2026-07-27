---
name: cluster-45
description: "Skill for the Cluster_45 area of AI_TC_Generator_v04_w_Trainer. 9 symbols across 3 files."
---

# Cluster_45

9 symbols | 3 files | Cohesion: 92%

## When to Use

- Working with code in `tests/`
- Understanding how displayed_table_rows, test_displayed_rows_helper, test_large_table_coverage_scoped_to_displayed_rows work
- Modifying cluster_45-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_validators.py` | _cases, test_displayed_rows_helper, test_large_table_coverage_scoped_to_displayed_rows, test_large_table_analysis_reports_truncation, test_small_table_still_requires_full_coverage (+1) |
| `src/core/validators.py` | _validate_table_coverage, _analyze_table_coverage |
| `src/core/prompt_builder.py` | displayed_table_rows |

## Entry Points

Start here when exploring this area:

- **`displayed_table_rows`** (Function) — `src/core/prompt_builder.py:25`
- **`test_displayed_rows_helper`** (Method) — `tests/core/test_validators.py:311`
- **`test_large_table_coverage_scoped_to_displayed_rows`** (Method) — `tests/core/test_validators.py:319`
- **`test_large_table_analysis_reports_truncation`** (Method) — `tests/core/test_validators.py:329`
- **`test_small_table_still_requires_full_coverage`** (Method) — `tests/core/test_validators.py:342`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `displayed_table_rows` | Function | `src/core/prompt_builder.py` | 25 |
| `test_displayed_rows_helper` | Method | `tests/core/test_validators.py` | 311 |
| `test_large_table_coverage_scoped_to_displayed_rows` | Method | `tests/core/test_validators.py` | 319 |
| `test_large_table_analysis_reports_truncation` | Method | `tests/core/test_validators.py` | 329 |
| `test_small_table_still_requires_full_coverage` | Method | `tests/core/test_validators.py` | 342 |
| `test_small_table_analysis_not_truncated` | Method | `tests/core/test_validators.py` | 352 |
| `_validate_table_coverage` | Method | `src/core/validators.py` | 361 |
| `_analyze_table_coverage` | Method | `src/core/validators.py` | 446 |
| `_cases` | Method | `tests/core/test_validators.py` | 306 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Validate_batch → Displayed_table_rows` | cross_community | 3 |

## How to Explore

1. `context({name: "displayed_table_rows"})` — see callers and callees
2. `query({search_query: "cluster_45"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
