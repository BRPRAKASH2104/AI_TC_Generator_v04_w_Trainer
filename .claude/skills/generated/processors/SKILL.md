---
name: processors
description: "Skill for the Processors area of AI_TC_Generator_v04_w_Trainer. 24 symbols across 8 files."
---

# Processors

24 symbols | 8 files | Cohesion: 57%

## When to Use

- Working with code in `src/`
- Understanding how test_hp_processor_complete_flow, test_hp_processor_no_artifacts, test_hp_processor_with_errors work
- Modifying processors-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/processors/hp_processor.py` | HighPerformanceREQIFZFileProcessor, process_file, _generate_output_path_hp, _create_error_result_hp, _monitor_performance (+2) |
| `src/app_logger.py` | info, error, critical, _log_with_extras, log_file_processing_start (+1) |
| `tests/test_integration_refactored.py` | test_hp_processor_complete_flow, test_hp_processor_no_artifacts, test_hp_processor_with_errors |
| `tests/integration/test_processors.py` | test_process_file_with_failures, test_performance_monitoring |
| `tests/integration/test_end_to_end.py` | test_hp_mode_complete_workflow, test_performance_comparison_workflow |
| `main.py` | _run_standard_mode, _run_hp_mode |
| `tests/test_critical_improvements.py` | test_hp_processor_processes_all_requirements_concurrently |
| `src/config.py` | get_model_for_requirement |

## Entry Points

Start here when exploring this area:

- **`test_hp_processor_complete_flow`** (Function) — `tests/test_integration_refactored.py:133`
- **`test_hp_processor_no_artifacts`** (Function) — `tests/test_integration_refactored.py:175`
- **`test_hp_processor_with_errors`** (Function) — `tests/test_integration_refactored.py:190`
- **`test_hp_processor_processes_all_requirements_concurrently`** (Function) — `tests/test_critical_improvements.py:265`
- **`get_model_for_requirement`** (Function) — `src/config.py:484`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `HighPerformanceREQIFZFileProcessor` | Class | `src/processors/hp_processor.py` | 35 |
| `test_hp_processor_complete_flow` | Function | `tests/test_integration_refactored.py` | 133 |
| `test_hp_processor_no_artifacts` | Function | `tests/test_integration_refactored.py` | 175 |
| `test_hp_processor_with_errors` | Function | `tests/test_integration_refactored.py` | 190 |
| `test_hp_processor_processes_all_requirements_concurrently` | Function | `tests/test_critical_improvements.py` | 265 |
| `get_model_for_requirement` | Function | `src/config.py` | 484 |
| `test_process_file_with_failures` | Function | `tests/integration/test_processors.py` | 192 |
| `test_performance_monitoring` | Function | `tests/integration/test_processors.py` | 223 |
| `test_hp_mode_complete_workflow` | Function | `tests/integration/test_end_to_end.py` | 117 |
| `test_performance_comparison_workflow` | Function | `tests/integration/test_end_to_end.py` | 266 |
| `process_file` | Function | `src/processors/hp_processor.py` | 90 |
| `info` | Function | `src/app_logger.py` | 197 |
| `error` | Function | `src/app_logger.py` | 206 |
| `critical` | Function | `src/app_logger.py` | 211 |
| `log_file_processing_start` | Function | `src/app_logger.py` | 235 |
| `log_file_processing_complete` | Function | `src/app_logger.py` | 245 |
| `process_directory` | Function | `src/processors/hp_processor.py` | 63 |
| `_generate_output_path_hp` | Function | `src/processors/hp_processor.py` | 372 |
| `_create_error_result_hp` | Function | `src/processors/hp_processor.py` | 385 |
| `_monitor_performance` | Function | `src/processors/hp_processor.py` | 399 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Log_info → _log_with_extras` | cross_community | 5 |
| `Log_error → _log_with_extras` | cross_community | 5 |
| `Log_warning → _log_with_extras` | cross_community | 5 |
| `Log_debug → _log_with_extras` | cross_community | 5 |
| `Process_directory → _log_with_extras` | cross_community | 5 |
| `_run_standard_mode → _log_with_extras` | cross_community | 5 |
| `_run_hp_mode → _log_with_extras` | cross_community | 5 |
| `Process_directory → _log_with_extras` | cross_community | 5 |
| `Process_directory → FileProcessingLogger` | cross_community | 4 |
| `_run_standard_mode → FileProcessingLogger` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Integration | 12 calls |
| Tests | 7 calls |
| Cluster_74 | 2 calls |
| Cluster_76 | 2 calls |
| Utilities | 2 calls |
| Cluster_44 | 2 calls |
| Training | 1 calls |
| Cluster_102 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_hp_processor_complete_flow"})` — see callers and callees
2. `gitnexus_query({query: "processors"})` — find related execution flows
3. Read key files listed above for implementation details
