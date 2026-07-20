---
name: cluster-23
description: "Skill for the Cluster_23 area of AI_TC_Generator_v04_w_Trainer. 6 symbols across 1 files."
---

# Cluster_23

6 symbols | 1 files | Cohesion: 86%

## When to Use

- Working with code in `src/`
- Understanding how format_to_excel, format_to_excel_streaming work
- Modifying cluster_23-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/core/formatters.py` | format_to_excel, _create_formatted_excel, _apply_excel_formatting, _add_metadata_sheet, format_to_excel_streaming (+1) |

## Entry Points

Start here when exploring this area:

- **`format_to_excel`** (Method) — `src/core/formatters.py:42`
- **`format_to_excel_streaming`** (Method) — `src/core/formatters.py:294`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `format_to_excel` | Method | `src/core/formatters.py` | 42 |
| `format_to_excel_streaming` | Method | `src/core/formatters.py` | 294 |
| `_create_formatted_excel` | Method | `src/core/formatters.py` | 204 |
| `_apply_excel_formatting` | Method | `src/core/formatters.py` | 230 |
| `_add_metadata_sheet` | Method | `src/core/formatters.py` | 272 |
| `_write_chunk_to_excel` | Method | `src/core/formatters.py` | 367 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Format_to_excel_streaming → _get_default_test_values` | cross_community | 4 |
| `Format_to_excel_streaming → _generate_issue_id` | cross_community | 4 |
| `Format_to_excel_streaming → _stringify_list` | cross_community | 4 |
| `Format_to_excel → _get_default_test_values` | cross_community | 3 |
| `Format_to_excel → _generate_issue_id` | cross_community | 3 |
| `Format_to_excel → _stringify_list` | cross_community | 3 |
| `Format_to_excel → _apply_excel_formatting` | intra_community | 3 |
| `Format_to_excel → _add_metadata_sheet` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Utilities | 2 calls |

## How to Explore

1. `context({name: "format_to_excel"})` — see callers and callees
2. `query({search_query: "cluster_23"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
