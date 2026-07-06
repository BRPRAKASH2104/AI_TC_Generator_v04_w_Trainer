---
name: processors
description: "Skill for the Processors area of AI_TC_Generator_v04_w_Trainer. 32 symbols across 8 files."
---

# Processors

32 symbols | 8 files | Cohesion: 84%

## When to Use

- Working with code in `tests/`
- Understanding how BaseProcessor, HighPerformanceREQIFZFileProcessor, REQIFZFileProcessor work
- Modifying processors-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_base_processor.py` | test_initialize_logger_creates_logger, test_initialize_logger_updates_raft_collector, test_extract_artifacts_success, test_extract_artifacts_returns_none_when_empty, test_extract_artifacts_returns_none_when_none (+6) |
| `src/processors/base_processor.py` | __init__, _initialize_logger, _extract_artifacts, _create_success_result, _create_error_result (+2) |
| `tests/test_refactoring.py` | test_initialize_logger, test_base_processor_extract_artifacts_failure, test_create_success_result, test_create_error_result, test_create_metadata |
| `src/processors/hp_processor.py` | __init__, _reset_metrics, HighPerformanceREQIFZFileProcessor |
| `src/processors/standard_processor.py` | __init__, REQIFZFileProcessor |
| `tests/training/test_raft_integration.py` | test_raft_does_not_change_success_result, test_raft_does_not_change_error_result |
| `tests/integration/test_processors.py` | test_metrics_reset_between_files |
| `utilities/verify_v03_compatibility.py` | verify_augmentation |

## Entry Points

Start here when exploring this area:

- **`BaseProcessor`** (Class) — `src/processors/base_processor.py:22`
- **`HighPerformanceREQIFZFileProcessor`** (Class) — `src/processors/hp_processor.py:35`
- **`REQIFZFileProcessor`** (Class) — `src/processors/standard_processor.py:32`
- **`test_metrics_reset_between_files`** (Method) — `tests/integration/test_processors.py:219`
- **`test_initialize_logger_creates_logger`** (Method) — `tests/core/test_base_processor.py:76`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `BaseProcessor` | Class | `src/processors/base_processor.py` | 22 |
| `HighPerformanceREQIFZFileProcessor` | Class | `src/processors/hp_processor.py` | 35 |
| `REQIFZFileProcessor` | Class | `src/processors/standard_processor.py` | 32 |
| `test_metrics_reset_between_files` | Method | `tests/integration/test_processors.py` | 219 |
| `test_initialize_logger_creates_logger` | Method | `tests/core/test_base_processor.py` | 76 |
| `test_initialize_logger_updates_raft_collector` | Method | `tests/core/test_base_processor.py` | 89 |
| `test_initialize_logger` | Method | `tests/test_refactoring.py` | 30 |
| `verify_augmentation` | Method | `utilities/verify_v03_compatibility.py` | 142 |
| `test_extract_artifacts_success` | Method | `tests/core/test_base_processor.py` | 113 |
| `test_extract_artifacts_returns_none_when_empty` | Method | `tests/core/test_base_processor.py` | 132 |
| `test_extract_artifacts_returns_none_when_none` | Method | `tests/core/test_base_processor.py` | 145 |
| `test_base_processor_extract_artifacts_failure` | Method | `tests/test_refactoring.py` | 363 |
| `test_create_success_result` | Method | `tests/core/test_base_processor.py` | 420 |
| `test_create_success_result_auto_template` | Method | `tests/core/test_base_processor.py` | 445 |
| `test_create_success_result` | Method | `tests/test_refactoring.py` | 157 |
| `test_raft_does_not_change_success_result` | Method | `tests/training/test_raft_integration.py` | 159 |
| `test_create_error_result` | Method | `tests/core/test_base_processor.py` | 462 |
| `test_create_error_result_default_time` | Method | `tests/core/test_base_processor.py` | 474 |
| `test_create_error_result` | Method | `tests/test_refactoring.py` | 176 |
| `test_raft_does_not_change_error_result` | Method | `tests/training/test_raft_integration.py` | 189 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Verify_augmentation → _map_reqif_type_to_artifact_type` | cross_community | 5 |
| `Verify_augmentation → _extract_foreign_id` | cross_community | 5 |
| `Verify_augmentation → _extract_xhtml_content` | cross_community | 5 |
| `Verify_augmentation → _determine_artifact_type` | cross_community | 5 |
| `Verify_augmentation → _compute_hash` | cross_community | 5 |
| `Main → _clean_text_for_logging` | cross_community | 5 |
| `Verify_augmentation → _build_foreign_id_mapping` | cross_community | 4 |
| `Verify_augmentation → _build_attribute_definition_mapping` | cross_community | 4 |
| `Main → _initialize_logger` | cross_community | 4 |
| `_run_standard_mode → _initialize_logger` | cross_community | 4 |

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
