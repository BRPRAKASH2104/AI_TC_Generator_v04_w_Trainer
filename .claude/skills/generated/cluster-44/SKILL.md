---
name: cluster-44
description: "Skill for the Cluster_44 area of AI_TC_Generator_v04_w_Trainer. 13 symbols across 2 files."
---

# Cluster_44

13 symbols | 2 files | Cohesion: 100%

## When to Use

- Working with code in `tests/`
- Understanding how extract_tables_from_html, test_parse_simple_table, test_parse_table_with_multiple_rows work
- Modifying cluster_44-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_parsers.py` | test_parse_simple_table, test_parse_table_with_multiple_rows, test_parse_empty_table, test_parse_malformed_html, test_parse_table_with_nested_elements (+3) |
| `src/core/parsers.py` | extract_tables_from_html, _clean_html_content, _row_cells, _parse_single_table, _fallback_table_parsing |

## Entry Points

Start here when exploring this area:

- **`extract_tables_from_html`** (Method) — `src/core/parsers.py:146`
- **`test_parse_simple_table`** (Method) — `tests/core/test_parsers.py:132`
- **`test_parse_table_with_multiple_rows`** (Method) — `tests/core/test_parsers.py:153`
- **`test_parse_empty_table`** (Method) — `tests/core/test_parsers.py:171`
- **`test_parse_malformed_html`** (Method) — `tests/core/test_parsers.py:179`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `extract_tables_from_html` | Method | `src/core/parsers.py` | 146 |
| `test_parse_simple_table` | Method | `tests/core/test_parsers.py` | 132 |
| `test_parse_table_with_multiple_rows` | Method | `tests/core/test_parsers.py` | 153 |
| `test_parse_empty_table` | Method | `tests/core/test_parsers.py` | 171 |
| `test_parse_malformed_html` | Method | `tests/core/test_parsers.py` | 179 |
| `test_parse_table_with_nested_elements` | Method | `tests/core/test_parsers.py` | 188 |
| `test_parse_table_with_colspan` | Method | `tests/core/test_parsers.py` | 209 |
| `test_parse_table_with_rowspan` | Method | `tests/core/test_parsers.py` | 232 |
| `test_parse_row_with_mixed_th_and_td_cells` | Method | `tests/core/test_parsers.py` | 260 |
| `_clean_html_content` | Method | `src/core/parsers.py` | 177 |
| `_row_cells` | Method | `src/core/parsers.py` | 194 |
| `_parse_single_table` | Method | `src/core/parsers.py` | 203 |
| `_fallback_table_parsing` | Method | `src/core/parsers.py` | 283 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Extract_tables_from_html → _row_cells` | intra_community | 3 |

## How to Explore

1. `context({name: "extract_tables_from_html"})` — see callers and callees
2. `query({search_query: "cluster_44"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
