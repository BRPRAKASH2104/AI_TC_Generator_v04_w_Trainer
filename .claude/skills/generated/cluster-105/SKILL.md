---
name: cluster-105
description: "Skill for the Cluster_105 area of AI_TC_Generator_v04_w_Trainer. 9 symbols across 1 files."
---

# Cluster_105

9 symbols | 1 files | Cohesion: 76%

## When to Use

- Working with code in `src/`
- Understanding how _extract_foreign_id, _extract_spec_object, _extract_xhtml_content work
- Modifying cluster_105-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/core/extractors.py` | _extract_foreign_id, _extract_spec_object, _extract_xhtml_content, _map_reqif_type_to_artifact_type, _determine_artifact_type (+4) |

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `_extract_foreign_id` | Function | `src/core/extractors.py` | 221 |
| `_extract_spec_object` | Function | `src/core/extractors.py` | 244 |
| `_extract_xhtml_content` | Function | `src/core/extractors.py` | 337 |
| `_map_reqif_type_to_artifact_type` | Function | `src/core/extractors.py` | 352 |
| `_determine_artifact_type` | Function | `src/core/extractors.py` | 373 |
| `_parse_reqif_xml_streaming` | Function | `src/core/extractors.py` | 436 |
| `_build_mappings_streaming` | Function | `src/core/extractors.py` | 475 |
| `_extract_spec_objects_streaming` | Function | `src/core/extractors.py` | 517 |
| `_process_spec_object_batch` | Function | `src/core/extractors.py` | 847 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _build_mappings_streaming` | cross_community | 5 |
| `Main → _map_reqif_type_to_artifact_type` | cross_community | 5 |
| `Main → _extract_foreign_id` | cross_community | 5 |
| `Main → _extract_xhtml_content` | cross_community | 5 |
| `Main → _determine_artifact_type` | cross_community | 5 |
| `Verify_extraction → _build_mappings_streaming` | cross_community | 5 |
| `Verify_extraction → _map_reqif_type_to_artifact_type` | cross_community | 5 |
| `Verify_extraction → _extract_foreign_id` | cross_community | 5 |
| `Verify_extraction → _extract_xhtml_content` | cross_community | 5 |
| `Verify_extraction → _determine_artifact_type` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_86 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "_extract_foreign_id"})` — see callers and callees
2. `gitnexus_query({query: "cluster_105"})` — find related execution flows
3. Read key files listed above for implementation details
