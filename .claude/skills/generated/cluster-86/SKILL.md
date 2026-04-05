---
name: cluster-86
description: "Skill for the Cluster_86 area of AI_TC_Generator_v04_w_Trainer. 11 symbols across 2 files."
---

# Cluster_86

11 symbols | 2 files | Cohesion: 95%

## When to Use

- Working with code in `tests/`
- Understanding how test_parse_simple_table, test_parse_table_with_multiple_rows, test_parse_empty_table work
- Modifying cluster_86-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_parsers.py` | test_parse_simple_table, test_parse_table_with_multiple_rows, test_parse_empty_table, test_parse_malformed_html, test_parse_table_with_nested_elements (+2) |
| `src/core/parsers.py` | extract_tables_from_html, _clean_html_content, _parse_single_table, _fallback_table_parsing |

## Entry Points

Start here when exploring this area:

- **`test_parse_simple_table`** (Function) — `tests/core/test_parsers.py:133`
- **`test_parse_table_with_multiple_rows`** (Function) — `tests/core/test_parsers.py:154`
- **`test_parse_empty_table`** (Function) — `tests/core/test_parsers.py:172`
- **`test_parse_malformed_html`** (Function) — `tests/core/test_parsers.py:180`
- **`test_parse_table_with_nested_elements`** (Function) — `tests/core/test_parsers.py:189`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_parse_simple_table` | Function | `tests/core/test_parsers.py` | 133 |
| `test_parse_table_with_multiple_rows` | Function | `tests/core/test_parsers.py` | 154 |
| `test_parse_empty_table` | Function | `tests/core/test_parsers.py` | 172 |
| `test_parse_malformed_html` | Function | `tests/core/test_parsers.py` | 180 |
| `test_parse_table_with_nested_elements` | Function | `tests/core/test_parsers.py` | 189 |
| `test_parse_table_with_colspan` | Function | `tests/core/test_parsers.py` | 210 |
| `test_parse_table_with_rowspan` | Function | `tests/core/test_parsers.py` | 233 |
| `extract_tables_from_html` | Function | `src/core/parsers.py` | 138 |
| `_clean_html_content` | Function | `src/core/parsers.py` | 168 |
| `_parse_single_table` | Function | `src/core/parsers.py` | 185 |
| `_fallback_table_parsing` | Function | `src/core/parsers.py` | 266 |

## How to Explore

1. `gitnexus_context({name: "test_parse_simple_table"})` — see callers and callees
2. `gitnexus_query({query: "cluster_86"})` — find related execution flows
3. Read key files listed above for implementation details
