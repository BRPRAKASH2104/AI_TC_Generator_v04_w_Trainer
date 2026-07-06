---
name: cluster-36
description: "Skill for the Cluster_36 area of AI_TC_Generator_v04_w_Trainer. 13 symbols across 2 files."
---

# Cluster_36

13 symbols | 2 files | Cohesion: 100%

## When to Use

- Working with code in `tests/`
- Understanding how extract_tables_from_html, test_parse_simple_table, test_parse_table_with_multiple_rows work
- Modifying cluster_36-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_parsers.py` | test_parse_simple_table, test_parse_table_with_multiple_rows, test_parse_empty_table, test_parse_malformed_html, test_parse_table_with_nested_elements (+3) |
| `src/core/parsers.py` | extract_tables_from_html, _clean_html_content, _row_cells, _parse_single_table, _fallback_table_parsing |

## Entry Points

Start here when exploring this area:

- **`extract_tables_from_html`** (Method) — `src/core/parsers.py:143`
- **`test_parse_simple_table`** (Method) — `tests/core/test_parsers.py:133`
- **`test_parse_table_with_multiple_rows`** (Method) — `tests/core/test_parsers.py:154`
- **`test_parse_empty_table`** (Method) — `tests/core/test_parsers.py:172`
- **`test_parse_malformed_html`** (Method) — `tests/core/test_parsers.py:180`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `extract_tables_from_html` | Method | `src/core/parsers.py` | 143 |
| `test_parse_simple_table` | Method | `tests/core/test_parsers.py` | 133 |
| `test_parse_table_with_multiple_rows` | Method | `tests/core/test_parsers.py` | 154 |
| `test_parse_empty_table` | Method | `tests/core/test_parsers.py` | 172 |
| `test_parse_malformed_html` | Method | `tests/core/test_parsers.py` | 180 |
| `test_parse_table_with_nested_elements` | Method | `tests/core/test_parsers.py` | 189 |
| `test_parse_table_with_colspan` | Method | `tests/core/test_parsers.py` | 210 |
| `test_parse_table_with_rowspan` | Method | `tests/core/test_parsers.py` | 233 |
| `test_parse_row_with_mixed_th_and_td_cells` | Method | `tests/core/test_parsers.py` | 261 |
| `_clean_html_content` | Method | `src/core/parsers.py` | 173 |
| `_row_cells` | Method | `src/core/parsers.py` | 190 |
| `_parse_single_table` | Method | `src/core/parsers.py` | 199 |
| `_fallback_table_parsing` | Method | `src/core/parsers.py` | 279 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Extract_tables_from_html → _row_cells` | intra_community | 3 |

## How to Explore

1. `context({name: "extract_tables_from_html"})` — see callers and callees
2. `query({search_query: "cluster_36"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
