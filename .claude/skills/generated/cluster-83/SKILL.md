---
name: cluster-83
description: "Skill for the Cluster_83 area of AI_TC_Generator_v04_w_Trainer. 7 symbols across 2 files."
---

# Cluster_83

7 symbols | 2 files | Cohesion: 80%

## When to Use

- Working with code in `tests/`
- Understanding how test_augment_requirements_with_relationships, test_calculate_hierarchy_level, test_calculate_hierarchy_level_with_cycle work
- Modifying cluster_83-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_relationship_parser.py` | test_augment_requirements_with_relationships, test_calculate_hierarchy_level, test_calculate_hierarchy_level_with_cycle, test_augment_requirements_without_relationships, test_multiple_levels_hierarchy |
| `src/core/relationship_parser.py` | augment_requirements_with_relationships, _calculate_hierarchy_level |

## Entry Points

Start here when exploring this area:

- **`test_augment_requirements_with_relationships`** (Function) — `tests/core/test_relationship_parser.py:148`
- **`test_calculate_hierarchy_level`** (Function) — `tests/core/test_relationship_parser.py:179`
- **`test_calculate_hierarchy_level_with_cycle`** (Function) — `tests/core/test_relationship_parser.py:193`
- **`test_augment_requirements_without_relationships`** (Function) — `tests/core/test_relationship_parser.py:344`
- **`test_multiple_levels_hierarchy`** (Function) — `tests/core/test_relationship_parser.py:421`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_augment_requirements_with_relationships` | Function | `tests/core/test_relationship_parser.py` | 148 |
| `test_calculate_hierarchy_level` | Function | `tests/core/test_relationship_parser.py` | 179 |
| `test_calculate_hierarchy_level_with_cycle` | Function | `tests/core/test_relationship_parser.py` | 193 |
| `test_augment_requirements_without_relationships` | Function | `tests/core/test_relationship_parser.py` | 344 |
| `test_multiple_levels_hierarchy` | Function | `tests/core/test_relationship_parser.py` | 421 |
| `augment_requirements_with_relationships` | Function | `src/core/relationship_parser.py` | 201 |
| `_calculate_hierarchy_level` | Function | `src/core/relationship_parser.py` | 244 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Parse_and_augment_relationships → _calculate_hierarchy_level` | cross_community | 3 |

## How to Explore

1. `gitnexus_context({name: "test_augment_requirements_with_relationships"})` — see callers and callees
2. `gitnexus_query({query: "cluster_83"})` — find related execution flows
3. Read key files listed above for implementation details
