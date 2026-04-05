---
name: integration
description: "Skill for the Integration area of AI_TC_Generator_v04_w_Trainer. 111 symbols across 22 files."
---

# Integration

111 symbols | 22 files | Cohesion: 59%

## When to Use

- Working with code in `tests/`
- Understanding how test_standard_processor_complete_flow, test_standard_processor_no_artifacts, test_standard_processor_no_test_cases_generated work
- Modifying integration-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/integration/e2e_runner_script.py` | TestResult, summary, get_reqifz_files, test_negative_invalid_file, main (+13) |
| `src/app_logger.py` | AppLogger, debug, warning, log_ai_api_call, log_environment_info (+7) |
| `tests/integration/test_end_to_end.py` | test_standard_mode_complete_workflow, test_directory_processing_workflow, test_error_handling_workflow, test_malformed_reqifz_handling, test_ai_service_timeout_handling (+5) |
| `tests/core/test_parsers.py` | test_extract_direct_json, test_extract_json_from_markdown_block, test_extract_json_from_code_block_without_language, test_extract_json_with_curly_braces_fallback, test_invalid_json_returns_none (+5) |
| `tests/integration/test_edge_cases.py` | mock_config, test_connection_refused_error, test_timeout_error, test_http_error_responses, test_memory_pressure_simulation (+5) |
| `src/config.py` | ConfigManager, get_masked_summary, validate_required_secrets, print_summary, validate_secrets_for_mode (+1) |
| `tests/test_integration_refactored.py` | test_standard_processor_complete_flow, test_standard_processor_no_artifacts, test_standard_processor_no_test_cases_generated, test_standard_processor_excel_save_failure, test_context_reset_between_requirements |
| `tests/performance/test_regression_benchmarks.py` | run_processing, test_processor_consistency, test_memory_efficiency_regression, test_standard_processor_performance_regression, test_context_aware_processing_performance |
| `src/core/parsers.py` | extract_json_from_response, validate_test_cases_structure, extract_json_batch, JSONResponseParser, FastJSONResponseParser |
| `tests/integration/test_processors.py` | test_process_file_success, test_process_file_no_system_requirements, test_process_directory, test_calculate_performance_metrics |

## Entry Points

Start here when exploring this area:

- **`test_standard_processor_complete_flow`** (Function) — `tests/test_integration_refactored.py:30`
- **`test_standard_processor_no_artifacts`** (Function) — `tests/test_integration_refactored.py:69`
- **`test_standard_processor_no_test_cases_generated`** (Function) — `tests/test_integration_refactored.py:82`
- **`test_standard_processor_excel_save_failure`** (Function) — `tests/test_integration_refactored.py:102`
- **`test_context_reset_between_requirements`** (Function) — `tests/test_integration_refactored.py:231`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `REQIFZFileProcessor` | Class | `src/processors/standard_processor.py` | 32 |
| `ConfigManager` | Class | `src/config.py` | 429 |
| `AppLogger` | Class | `src/app_logger.py` | 28 |
| `OllamaClient` | Class | `src/core/ollama_client.py` | 36 |
| `JSONResponseParser` | Class | `src/core/parsers.py` | 24 |
| `FastJSONResponseParser` | Class | `src/core/parsers.py` | 99 |
| `TestResult` | Class | `tests/integration/e2e_runner_script.py` | 33 |
| `test_standard_processor_complete_flow` | Function | `tests/test_integration_refactored.py` | 30 |
| `test_standard_processor_no_artifacts` | Function | `tests/test_integration_refactored.py` | 69 |
| `test_standard_processor_no_test_cases_generated` | Function | `tests/test_integration_refactored.py` | 82 |
| `test_standard_processor_excel_save_failure` | Function | `tests/test_integration_refactored.py` | 102 |
| `test_context_reset_between_requirements` | Function | `tests/test_integration_refactored.py` | 231 |
| `test_standard_processor_handles_connection_error` | Function | `tests/test_critical_improvements.py` | 440 |
| `test_standard_processor_handles_model_not_found` | Function | `tests/test_critical_improvements.py` | 463 |
| `test_process_file_success` | Function | `tests/integration/test_processors.py` | 22 |
| `test_process_file_no_system_requirements` | Function | `tests/integration/test_processors.py` | 73 |
| `test_process_directory` | Function | `tests/integration/test_processors.py` | 120 |
| `test_standard_mode_complete_workflow` | Function | `tests/integration/test_end_to_end.py` | 76 |
| `test_directory_processing_workflow` | Function | `tests/integration/test_end_to_end.py` | 155 |
| `test_error_handling_workflow` | Function | `tests/integration/test_end_to_end.py` | 204 |

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
| `Main → ConfigManager` | cross_community | 4 |
| `_run_standard_mode → FileProcessingLogger` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 37 calls |
| Processors | 12 calls |
| Utilities | 2 calls |
| Training | 2 calls |
| Cluster_89 | 2 calls |
| Cluster_44 | 2 calls |
| Cluster_61 | 1 calls |
| Cluster_102 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_standard_processor_complete_flow"})` — see callers and callees
2. `gitnexus_query({query: "integration"})` — find related execution flows
3. Read key files listed above for implementation details
