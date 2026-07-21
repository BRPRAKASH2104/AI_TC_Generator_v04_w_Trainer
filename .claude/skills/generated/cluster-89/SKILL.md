---
name: cluster-89
description: "Skill for the Cluster_89 area of AI_TC_Generator_v04_w_Trainer. 8 symbols across 2 files."
---

# Cluster_89

8 symbols | 2 files | Cohesion: 82%

## When to Use

- Working with code in `tests/`
- Understanding how create_test_requirement, create_test_information, create_test_interface work
- Modifying cluster_89-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/helpers/test_artifact_builder.py` | create_test_requirement, create_test_information, create_test_interface, create_augmented_requirement |
| `tests/helpers/test_artifact_builder_verification.py` | test_create_requirement_with_table, test_create_information, test_create_interface, test_create_augmented_requirement |

## Entry Points

Start here when exploring this area:

- **`create_test_requirement`** (Function) — `tests/helpers/test_artifact_builder.py:84`
- **`create_test_information`** (Function) — `tests/helpers/test_artifact_builder.py:156`
- **`create_test_interface`** (Function) — `tests/helpers/test_artifact_builder.py:184`
- **`create_augmented_requirement`** (Function) — `tests/helpers/test_artifact_builder.py:319`
- **`test_create_requirement_with_table`** (Method) — `tests/helpers/test_artifact_builder_verification.py:39`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `create_test_requirement` | Function | `tests/helpers/test_artifact_builder.py` | 84 |
| `create_test_information` | Function | `tests/helpers/test_artifact_builder.py` | 156 |
| `create_test_interface` | Function | `tests/helpers/test_artifact_builder.py` | 184 |
| `create_augmented_requirement` | Function | `tests/helpers/test_artifact_builder.py` | 319 |
| `test_create_requirement_with_table` | Method | `tests/helpers/test_artifact_builder_verification.py` | 39 |
| `test_create_information` | Method | `tests/helpers/test_artifact_builder_verification.py` | 65 |
| `test_create_interface` | Method | `tests/helpers/test_artifact_builder_verification.py` | 73 |
| `test_create_augmented_requirement` | Method | `tests/helpers/test_artifact_builder_verification.py` | 101 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_88 | 3 calls |

## How to Explore

1. `context({name: "create_test_requirement"})` — see callers and callees
2. `query({search_query: "cluster_89"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
