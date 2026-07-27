---
name: processors
description: "Skill for the Processors area of AI_TC_Generator_v04_w_Trainer. 42 symbols across 8 files."
---

# Processors

42 symbols | 8 files | Cohesion: 85%

## When to Use

- Working with code in `tests/`
- Understanding how BaseProcessor, HighPerformanceREQIFZFileProcessor, REQIFZFileProcessor work
- Modifying processors-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_base_processor.py` | test_save_raft_example_when_enabled, test_save_raft_example_when_disabled, test_create_error_result, test_create_error_result_default_time, test_initialize_logger_creates_logger (+8) |
| `src/processors/base_processor.py` | _format_raft_test_cases, _save_raft_example, _create_error_result, __init__, _initialize_logger (+4) |
| `tests/training/test_raft_integration.py` | test_save_raft_example_no_op_when_disabled, test_save_raft_example_collects_when_enabled, test_raft_collection_minimal_overhead, test_raft_does_not_change_error_result, test_raft_does_not_change_success_result |
| `tests/test_refactoring.py` | test_create_error_result, test_initialize_logger, test_base_processor_extract_artifacts_failure, test_create_success_result, test_create_metadata |
| `src/processors/hp_processor.py` | _collect_generation_results, __init__, _reset_metrics, HighPerformanceREQIFZFileProcessor |
| `src/processors/standard_processor.py` | _run_generation_loop, _error_result_for_exception, __init__, REQIFZFileProcessor |
| `tests/integration/test_processors.py` | test_metrics_reset_between_files |
| `utilities/verify_v03_compatibility.py` | verify_augmentation |

## Entry Points

Start here when exploring this area:

- **`BaseProcessor`** (Class) — `src/processors/base_processor.py:53`
- **`HighPerformanceREQIFZFileProcessor`** (Class) — `src/processors/hp_processor.py:35`
- **`REQIFZFileProcessor`** (Class) — `src/processors/standard_processor.py:32`
- **`test_save_raft_example_when_enabled`** (Method) — `tests/core/test_base_processor.py:519`
- **`test_save_raft_example_when_disabled`** (Method) — `tests/core/test_base_processor.py:540`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `BaseProcessor` | Class | `src/processors/base_processor.py` | 53 |
| `HighPerformanceREQIFZFileProcessor` | Class | `src/processors/hp_processor.py` | 35 |
| `REQIFZFileProcessor` | Class | `src/processors/standard_processor.py` | 32 |
| `test_save_raft_example_when_enabled` | Method | `tests/core/test_base_processor.py` | 519 |
| `test_save_raft_example_when_disabled` | Method | `tests/core/test_base_processor.py` | 540 |
| `test_save_raft_example_no_op_when_disabled` | Method | `tests/training/test_raft_integration.py` | 50 |
| `test_save_raft_example_collects_when_enabled` | Method | `tests/training/test_raft_integration.py` | 63 |
| `test_raft_collection_minimal_overhead` | Method | `tests/training/test_raft_integration.py` | 220 |
| `test_create_error_result` | Method | `tests/core/test_base_processor.py` | 495 |
| `test_create_error_result_default_time` | Method | `tests/core/test_base_processor.py` | 507 |
| `test_create_error_result` | Method | `tests/test_refactoring.py` | 176 |
| `test_raft_does_not_change_error_result` | Method | `tests/training/test_raft_integration.py` | 204 |
| `test_metrics_reset_between_files` | Method | `tests/integration/test_processors.py` | 241 |
| `test_initialize_logger_creates_logger` | Method | `tests/core/test_base_processor.py` | 78 |
| `test_initialize_logger_updates_raft_collector` | Method | `tests/core/test_base_processor.py` | 91 |
| `test_initialize_logger` | Method | `tests/test_refactoring.py` | 30 |
| `verify_augmentation` | Method | `utilities/verify_v03_compatibility.py` | 142 |
| `test_extract_artifacts_success` | Method | `tests/core/test_base_processor.py` | 115 |
| `test_extract_artifacts_returns_none_when_empty` | Method | `tests/core/test_base_processor.py` | 134 |
| `test_extract_artifacts_returns_none_when_none` | Method | `tests/core/test_base_processor.py` | 147 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Verify_augmentation → _map_reqif_type_to_artifact_type` | cross_community | 5 |
| `Verify_augmentation → _extract_foreign_id` | cross_community | 5 |
| `Verify_augmentation → _extract_xhtml_content` | cross_community | 5 |
| `Verify_augmentation → _determine_artifact_type` | cross_community | 5 |
| `Verify_augmentation → Safe_zip_read` | cross_community | 5 |
| `Main → _clean_text_for_logging` | cross_community | 5 |
| `Verify_augmentation → _build_foreign_id_mapping` | cross_community | 4 |
| `Verify_augmentation → _build_attribute_definition_mapping` | cross_community | 4 |
| `_run_standard_mode → _initialize_logger` | cross_community | 4 |
| `_run_standard_mode → _extract_artifacts` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Integration | 1 calls |
| Tests | 1 calls |

## How to Explore

1. `context({name: "BaseProcessor"})` — see callers and callees
2. `query({search_query: "processors"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
