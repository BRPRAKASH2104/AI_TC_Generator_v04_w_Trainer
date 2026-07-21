---
name: cluster-19
description: "Skill for the Cluster_19 area of AI_TC_Generator_v04_w_Trainer. 9 symbols across 3 files."
---

# Cluster_19

9 symbols | 3 files | Cohesion: 73%

## When to Use

- Working with code in `src/`
- Understanding how test_extractor_with_relationships, test_extractor_without_relationships, test_extractor_with_dependency_graph work
- Modifying cluster_19-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_relationship_integration.py` | test_extractor_with_relationships, test_extractor_without_relationships, test_extractor_with_dependency_graph, test_extractor_without_augmentation |
| `src/core/relationship_parser.py` | augment_requirements_with_relationships, _calculate_hierarchy_level, build_dependency_graph |
| `src/core/extractors.py` | _augment_relationships_if_enabled, parse_and_augment_relationships |

## Entry Points

Start here when exploring this area:

- **`test_extractor_with_relationships`** (Function) — `tests/core/test_relationship_integration.py:151`
- **`test_extractor_without_relationships`** (Function) — `tests/core/test_relationship_integration.py:181`
- **`test_extractor_with_dependency_graph`** (Function) — `tests/core/test_relationship_integration.py:246`
- **`test_extractor_without_augmentation`** (Function) — `tests/core/test_relationship_integration.py:268`
- **`parse_and_augment_relationships`** (Method) — `src/core/extractors.py:490`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_extractor_with_relationships` | Function | `tests/core/test_relationship_integration.py` | 151 |
| `test_extractor_without_relationships` | Function | `tests/core/test_relationship_integration.py` | 181 |
| `test_extractor_with_dependency_graph` | Function | `tests/core/test_relationship_integration.py` | 246 |
| `test_extractor_without_augmentation` | Function | `tests/core/test_relationship_integration.py` | 268 |
| `parse_and_augment_relationships` | Method | `src/core/extractors.py` | 490 |
| `augment_requirements_with_relationships` | Method | `src/core/relationship_parser.py` | 203 |
| `build_dependency_graph` | Method | `src/core/relationship_parser.py` | 270 |
| `_augment_relationships_if_enabled` | Method | `src/core/extractors.py` | 96 |
| `_calculate_hierarchy_level` | Method | `src/core/relationship_parser.py` | 246 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Verify_extraction → Build_dependency_graph` | cross_community | 5 |
| `Verify_classification → Build_dependency_graph` | cross_community | 5 |
| `_augment_relationships_if_enabled → _classify_relation_type` | cross_community | 5 |
| `_augment_relationships_if_enabled → _build_relation_type_mapping` | cross_community | 4 |
| `_augment_relationships_if_enabled → _calculate_hierarchy_level` | intra_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Integration | 4 calls |
| Cluster_50 | 1 calls |

## How to Explore

1. `context({name: "test_extractor_with_relationships"})` — see callers and callees
2. `query({search_query: "cluster_19"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
