---
name: processors
description: "Skill for the Processors area of AI_TC_Generator_v04_w_Trainer. 37 symbols across 12 files."
---

# Processors

37 symbols | 12 files | Cohesion: 57%

## When to Use

- Working with code in `src/`
- Understanding how main, get_app_logger, process_file work
- Modifying processors-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/processors/base_processor.py` | _extract_artifacts, _create_metadata, _create_success_result, _create_error_result, _save_raft_example (+5) |
| `src/processors/hp_processor.py` | process_file, _create_error_result_hp, _monitor_performance, _get_performance_summary, process_directory (+2) |
| `tests/integration/test_end_to_end.py` | test_standard_mode_complete_workflow, test_hp_mode_complete_workflow, test_performance_comparison_workflow, test_directory_processing_workflow |
| `main.py` | _run_standard_mode, main, _run_hp_mode |
| `src/app_logger.py` | log_file_processing_start, log_file_processing_complete, get_app_logger |
| `src/processors/standard_processor.py` | process_file, process_directory |
| `src/core/image_extractor.py` | cleanup_extracted_images, auto_cleanup |
| `src/config.py` | apply_cli_overrides, _deep_merge_dict |
| `tests/performance/test_regression_benchmarks.py` | test_processor_consistency |
| `tests/training/test_raft_integration.py` | test_raft_collection_minimal_overhead |

## Entry Points

Start here when exploring this area:

- **`main`** (Function) — `main.py:107`
- **`get_app_logger`** (Function) — `src/app_logger.py:329`
- **`process_file`** (Method) — `src/processors/standard_processor.py:65`
- **`test_standard_mode_complete_workflow`** (Method) — `tests/integration/test_end_to_end.py:76`
- **`test_processor_consistency`** (Method) — `tests/performance/test_regression_benchmarks.py:172`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `main` | Function | `main.py` | 107 |
| `get_app_logger` | Function | `src/app_logger.py` | 329 |
| `process_file` | Method | `src/processors/standard_processor.py` | 65 |
| `test_standard_mode_complete_workflow` | Method | `tests/integration/test_end_to_end.py` | 76 |
| `test_processor_consistency` | Method | `tests/performance/test_regression_benchmarks.py` | 172 |
| `test_raft_collection_minimal_overhead` | Method | `tests/training/test_raft_integration.py` | 208 |
| `process_file` | Method | `src/processors/hp_processor.py` | 102 |
| `test_generate_output_path_includes_timestamp` | Method | `tests/core/test_base_processor.py` | 362 |
| `test_hp_mode_complete_workflow` | Method | `tests/integration/test_end_to_end.py` | 117 |
| `test_performance_comparison_workflow` | Method | `tests/integration/test_end_to_end.py` | 270 |
| `log_file_processing_start` | Method | `src/app_logger.py` | 235 |
| `log_file_processing_complete` | Method | `src/app_logger.py` | 245 |
| `cleanup_extracted_images` | Method | `src/core/image_extractor.py` | 566 |
| `auto_cleanup` | Method | `src/core/image_extractor.py` | 604 |
| `process_directory` | Method | `src/processors/standard_processor.py` | 41 |
| `test_directory_processing_workflow` | Method | `tests/integration/test_end_to_end.py` | 159 |
| `apply_cli_overrides` | Method | `src/config.py` | 611 |
| `process_directory` | Method | `src/processors/hp_processor.py` | 72 |
| `verify_augmentation` | Method | `utilities/verify_v03_compatibility.py` | 142 |
| `_run_standard_mode` | Function | `main.py` | 259 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `_run_hp_mode → _log_with_extras` | cross_community | 6 |
| `Verify_augmentation → _map_reqif_type_to_artifact_type` | cross_community | 5 |
| `Verify_augmentation → _extract_foreign_id` | cross_community | 5 |
| `Verify_augmentation → _extract_xhtml_content` | cross_community | 5 |
| `Verify_augmentation → _determine_artifact_type` | cross_community | 5 |
| `Verify_augmentation → _compute_hash` | cross_community | 5 |
| `Process_directory → _log_with_extras` | cross_community | 5 |
| `Main → _clean_text_for_logging` | cross_community | 5 |
| `_run_hp_mode → _get_performance_summary` | cross_community | 5 |
| `Verify_augmentation → _build_foreign_id_mapping` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Integration | 16 calls |
| Cluster_447 | 4 calls |
| Cluster_453 | 1 calls |
| Cluster_460 | 1 calls |
| Tools | 1 calls |

## How to Explore

1. `context({name: "main"})` — see callers and callees
2. `query({search_query: "processors"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
