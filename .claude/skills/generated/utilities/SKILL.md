---
name: utilities
description: "Skill for the Utilities area of AI_TC_Generator_v04_w_Trainer. 19 symbols across 4 files."
---

# Utilities

19 symbols | 4 files | Cohesion: 72%

## When to Use

- Working with code in `utilities/`
- Understanding how main, annotate_example, batch_annotate work
- Modifying utilities-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `utilities/verify_v03_compatibility.py` | verify_field_mapping, verify_all, verify_extraction, verify_classification, verify_prompt_generation (+1) |
| `utilities/version_check.py` | check_python_version, run_comprehensive_check, main, check_dependencies, _validate_parsed_requirements (+1) |
| `src/core/formatters.py` | format_to_excel, _stringify_list, _prepare_test_cases_for_excel, _write_chunk_to_excel |
| `utilities/annotate_raft.py` | annotate_example, batch_annotate, main |

## Entry Points

Start here when exploring this area:

- **`main`** (Function) — `utilities/verify_v03_compatibility.py:352`
- **`annotate_example`** (Function) — `utilities/annotate_raft.py:15`
- **`batch_annotate`** (Function) — `utilities/annotate_raft.py:179`
- **`main`** (Function) — `utilities/annotate_raft.py:257`
- **`main`** (Function) — `utilities/version_check.py:400`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `main` | Function | `utilities/verify_v03_compatibility.py` | 352 |
| `annotate_example` | Function | `utilities/annotate_raft.py` | 15 |
| `batch_annotate` | Function | `utilities/annotate_raft.py` | 179 |
| `main` | Function | `utilities/annotate_raft.py` | 257 |
| `main` | Function | `utilities/version_check.py` | 400 |
| `format_to_excel` | Method | `src/core/formatters.py` | 34 |
| `verify_field_mapping` | Method | `utilities/verify_v03_compatibility.py` | 257 |
| `verify_all` | Method | `utilities/verify_v03_compatibility.py` | 39 |
| `verify_extraction` | Method | `utilities/verify_v03_compatibility.py` | 55 |
| `verify_classification` | Method | `utilities/verify_v03_compatibility.py` | 93 |
| `verify_prompt_generation` | Method | `utilities/verify_v03_compatibility.py` | 203 |
| `check_python_version` | Method | `utilities/version_check.py` | 25 |
| `run_comprehensive_check` | Method | `utilities/version_check.py` | 335 |
| `check_dependencies` | Method | `utilities/version_check.py` | 200 |
| `_stringify_list` | Method | `src/core/formatters.py` | 73 |
| `_prepare_test_cases_for_excel` | Method | `src/core/formatters.py` | 79 |
| `_write_chunk_to_excel` | Method | `src/core/formatters.py` | 357 |
| `_validate_parsed_requirements` | Method | `utilities/version_check.py` | 245 |
| `_check_core_dependencies` | Method | `utilities/version_check.py` | 309 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _build_spec_type_mapping` | cross_community | 6 |
| `Main → _build_foreign_id_mapping` | cross_community | 6 |
| `Main → _build_attribute_definition_mapping` | cross_community | 6 |
| `Verify_extraction → _determine_image_format` | cross_community | 6 |
| `Verify_extraction → _compute_hash` | cross_community | 6 |
| `Verify_extraction → _validate_image` | cross_community | 6 |
| `Verify_classification → _determine_image_format` | cross_community | 6 |
| `Verify_classification → _compute_hash` | cross_community | 6 |
| `Verify_classification → _validate_image` | cross_community | 6 |
| `Main → Version_tuple` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_453 | 2 calls |
| Training | 2 calls |
| Processors | 1 calls |
| Cluster_466 | 1 calls |
| Cluster_456 | 1 calls |

## How to Explore

1. `context({name: "main"})` — see callers and callees
2. `query({search_query: "utilities"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
