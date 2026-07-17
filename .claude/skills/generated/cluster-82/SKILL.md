---
name: cluster-82
description: "Skill for the Cluster_82 area of AI_TC_Generator_v04_w_Trainer. 7 symbols across 2 files."
---

# Cluster_82

7 symbols | 2 files | Cohesion: 80%

## When to Use

- Working with code in `tests/`
- Understanding how create_test_artifact, create_test_heading, test_create_basic_artifact work
- Modifying cluster_82-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/helpers/test_artifact_builder_verification.py` | test_create_basic_artifact, test_create_heading, test_auto_generated_ids, test_xhtml_format_matches_production |
| `tests/helpers/test_artifact_builder.py` | _wrap_in_xhtml, create_test_artifact, create_test_heading |

## Entry Points

Start here when exploring this area:

- **`create_test_artifact`** (Function) — `tests/helpers/test_artifact_builder.py:33`
- **`create_test_heading`** (Function) — `tests/helpers/test_artifact_builder.py:128`
- **`test_create_basic_artifact`** (Method) — `tests/helpers/test_artifact_builder_verification.py:23`
- **`test_create_heading`** (Method) — `tests/helpers/test_artifact_builder_verification.py:56`
- **`test_auto_generated_ids`** (Method) — `tests/helpers/test_artifact_builder_verification.py:133`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `create_test_artifact` | Function | `tests/helpers/test_artifact_builder.py` | 33 |
| `create_test_heading` | Function | `tests/helpers/test_artifact_builder.py` | 128 |
| `test_create_basic_artifact` | Method | `tests/helpers/test_artifact_builder_verification.py` | 23 |
| `test_create_heading` | Method | `tests/helpers/test_artifact_builder_verification.py` | 56 |
| `test_auto_generated_ids` | Method | `tests/helpers/test_artifact_builder_verification.py` | 133 |
| `test_xhtml_format_matches_production` | Method | `tests/helpers/test_artifact_builder_verification.py` | 143 |
| `_wrap_in_xhtml` | Function | `tests/helpers/test_artifact_builder.py` | 14 |

## How to Explore

1. `context({name: "create_test_artifact"})` — see callers and callees
2. `query({search_query: "cluster_82"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
