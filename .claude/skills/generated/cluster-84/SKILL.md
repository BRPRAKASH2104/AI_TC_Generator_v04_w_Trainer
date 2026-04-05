---
name: cluster-84
description: "Skill for the Cluster_84 area of AI_TC_Generator_v04_w_Trainer. 6 symbols across 2 files."
---

# Cluster_84

6 symbols | 2 files | Cohesion: 83%

## When to Use

- Working with code in `tests/`
- Understanding how test_find_root_requirements, test_get_requirement_tree, test_get_requirement_tree_with_circular_reference work
- Modifying cluster_84-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_relationship_parser.py` | test_find_root_requirements, test_get_requirement_tree, test_get_requirement_tree_with_circular_reference |
| `src/core/relationship_parser.py` | find_root_requirements, get_requirement_tree, build_subtree |

## Entry Points

Start here when exploring this area:

- **`test_find_root_requirements`** (Function) — `tests/core/test_relationship_parser.py:250`
- **`test_get_requirement_tree`** (Function) — `tests/core/test_relationship_parser.py:280`
- **`test_get_requirement_tree_with_circular_reference`** (Function) — `tests/core/test_relationship_parser.py:322`
- **`find_root_requirements`** (Function) — `src/core/relationship_parser.py:312`
- **`get_requirement_tree`** (Function) — `src/core/relationship_parser.py:346`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_find_root_requirements` | Function | `tests/core/test_relationship_parser.py` | 250 |
| `test_get_requirement_tree` | Function | `tests/core/test_relationship_parser.py` | 280 |
| `test_get_requirement_tree_with_circular_reference` | Function | `tests/core/test_relationship_parser.py` | 322 |
| `find_root_requirements` | Function | `src/core/relationship_parser.py` | 312 |
| `get_requirement_tree` | Function | `src/core/relationship_parser.py` | 346 |
| `build_subtree` | Function | `src/core/relationship_parser.py` | 366 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_83 | 2 calls |

## How to Explore

1. `gitnexus_context({name: "test_find_root_requirements"})` — see callers and callees
2. `gitnexus_query({query: "cluster_84"})` — find related execution flows
3. Read key files listed above for implementation details
