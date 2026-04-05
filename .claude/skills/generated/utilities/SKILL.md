---
name: utilities
description: "Skill for the Utilities area of AI_TC_Generator_v04_w_Trainer. 58 symbols across 15 files."
---

# Utilities

58 symbols | 15 files | Cohesion: 81%

## When to Use

- Working with code in `utilities/`
- Understanding how verify_all, verify_extraction, verify_classification work
- Modifying utilities-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `utilities/version_check.py` | VersionChecker, check_python_version, _print_upgrade_instructions, check_required_features, run_comprehensive_check (+5) |
| `utilities/verify_v03_compatibility.py` | V03CompatibilityVerifier, verify_all, verify_extraction, verify_classification, verify_augmentation (+3) |
| `utilities/train_vision_model.py` | parse_args, validate_dataset, check_ollama_connection, check_base_model_exists, check_output_model_exists (+2) |
| `tests/integration/test_edge_cases.py` | test_empty_reqifz_file, test_invalid_zip_structure, test_zip_without_reqif_files, test_malformed_xml_in_reqif, test_xml_with_invalid_namespaces (+1) |
| `tests/core/test_relationship_integration.py` | test_extractor_with_relationships, test_extractor_without_relationships, test_extractor_with_dependency_graph, test_extractor_without_augmentation |
| `src/core/extractors.py` | REQIFArtifactExtractor, extract_reqifz_content, parse_and_augment_relationships, HighPerformanceREQIFArtifactExtractor |
| `utilities/build_vision_dataset.py` | parse_args, validate_paths, print_dataset_stats, main |
| `utilities/annotate_raft.py` | annotate_example, batch_annotate, show_stats, main |
| `tests/core/test_relationship_parser.py` | parser, test_build_dependency_graph |
| `src/core/relationship_parser.py` | RequirementRelationshipParser, build_dependency_graph |

## Entry Points

Start here when exploring this area:

- **`verify_all`** (Function) — `utilities/verify_v03_compatibility.py:39`
- **`verify_extraction`** (Function) — `utilities/verify_v03_compatibility.py:55`
- **`verify_classification`** (Function) — `utilities/verify_v03_compatibility.py:93`
- **`verify_augmentation`** (Function) — `utilities/verify_v03_compatibility.py:142`
- **`print_summary`** (Function) — `utilities/verify_v03_compatibility.py:324`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `V03CompatibilityVerifier` | Class | `utilities/verify_v03_compatibility.py` | 26 |
| `RequirementRelationshipParser` | Class | `src/core/relationship_parser.py` | 31 |
| `REQIFArtifactExtractor` | Class | `src/core/extractors.py` | 39 |
| `HighPerformanceREQIFArtifactExtractor` | Class | `src/core/extractors.py` | 662 |
| `VersionChecker` | Class | `utilities/version_check.py` | 18 |
| `TestCaseFormatter` | Class | `src/core/formatters.py` | 24 |
| `StreamingTestCaseFormatter` | Class | `src/core/formatters.py` | 350 |
| `verify_all` | Function | `utilities/verify_v03_compatibility.py` | 39 |
| `verify_extraction` | Function | `utilities/verify_v03_compatibility.py` | 55 |
| `verify_classification` | Function | `utilities/verify_v03_compatibility.py` | 93 |
| `verify_augmentation` | Function | `utilities/verify_v03_compatibility.py` | 142 |
| `print_summary` | Function | `utilities/verify_v03_compatibility.py` | 324 |
| `main` | Function | `utilities/verify_v03_compatibility.py` | 352 |
| `test_empty_reqifz_file` | Function | `tests/integration/test_edge_cases.py` | 38 |
| `test_invalid_zip_structure` | Function | `tests/integration/test_edge_cases.py` | 48 |
| `test_zip_without_reqif_files` | Function | `tests/integration/test_edge_cases.py` | 67 |
| `test_malformed_xml_in_reqif` | Function | `tests/integration/test_edge_cases.py` | 86 |
| `test_xml_with_invalid_namespaces` | Function | `tests/integration/test_edge_cases.py` | 112 |
| `test_extremely_large_reqif_file` | Function | `tests/integration/test_edge_cases.py` | 140 |
| `test_streaming_xml_memory_efficiency` | Function | `tests/performance/test_regression_benchmarks.py` | 251 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _build_spec_type_mapping` | cross_community | 6 |
| `Main → _build_foreign_id_mapping` | cross_community | 6 |
| `Main → _build_attribute_definition_mapping` | cross_community | 6 |
| `Main → RequirementImageExtractor` | cross_community | 6 |
| `Main → _build_mappings_streaming` | cross_community | 5 |
| `Main → _compute_hash` | cross_community | 5 |
| `Main → _map_reqif_type_to_artifact_type` | cross_community | 5 |
| `Main → _extract_foreign_id` | cross_community | 5 |
| `Main → _extract_xhtml_content` | cross_community | 5 |
| `Main → _determine_artifact_type` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 7 calls |
| Training | 5 calls |
| Integration | 2 calls |
| Cluster_88 | 2 calls |
| Cluster_104 | 2 calls |
| Cluster_74 | 1 calls |
| Cluster_81 | 1 calls |
| Cluster_83 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "verify_all"})` — see callers and callees
2. `gitnexus_query({query: "utilities"})` — find related execution flows
3. Read key files listed above for implementation details
