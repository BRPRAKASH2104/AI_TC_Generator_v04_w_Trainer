---
name: integration
description: "Skill for the Integration area of AI_TC_Generator_v04_w_Trainer. 144 symbols across 23 files."
---

# Integration

144 symbols | 23 files | Cohesion: 84%

## When to Use

- Working with code in `tests/`
- Understanding how run_processing, run_command, check_ollama_service work
- Modifying integration-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/integration/test_edge_cases.py` | test_nested_json_extraction, test_multiple_json_blocks, test_json_with_escaped_characters, test_memory_pressure_simulation, test_invalid_json_response (+13) |
| `tests/integration/e2e_runner_script.py` | add_pass, add_fail, add_skip, summary, run_command (+12) |
| `src/app_logger.py` | __init__, _generate_session_id, _start_performance_monitoring, debug, info (+11) |
| `tests/core/test_parsers.py` | test_extract_direct_json, test_extract_json_from_markdown_block, test_extract_json_from_code_block_without_language, test_extract_json_with_curly_braces_fallback, test_invalid_json_returns_none (+5) |
| `tests/integration/test_end_to_end.py` | test_standard_mode_complete_workflow, test_error_handling_workflow, test_malformed_reqifz_handling, test_ai_service_timeout_handling, test_insufficient_permissions_handling (+5) |
| `tests/core/test_generators.py` | test_generate_test_cases_success, test_generate_test_cases_with_template, test_generate_test_cases_ai_failure, test_generate_test_cases_invalid_json_response, test_prompt_variable_substitution (+4) |
| `tests/integration/test_processors.py` | test_process_file_success, test_process_file_no_system_requirements, test_process_file_success, test_process_file_no_test_cases_generated, test_process_file_with_generator_exception (+3) |
| `tests/test_critical_improvements.py` | test_standard_processor_handles_connection_error, test_standard_processor_handles_model_not_found, test_hp_processor_processes_all_requirements_concurrently, test_no_semaphore_allows_full_concurrency, test_connection_error_raises_ollama_connection_error (+3) |
| `tests/test_integration_refactored.py` | test_standard_processor_complete_flow, test_standard_processor_no_artifacts, test_standard_processor_no_test_cases_generated, test_standard_processor_excel_save_failure, test_context_reset_between_requirements (+3) |
| `src/core/generators.py` | generate_test_cases_for_requirement, extract_image_paths, stamp_validation_results, _postprocess_test_cases, generate_test_cases_batch (+2) |

## Entry Points

Start here when exploring this area:

- **`run_processing`** (Function) — `tests/performance/test_regression_benchmarks.py:80`
- **`run_command`** (Function) — `tests/integration/e2e_runner_script.py:69`
- **`check_ollama_service`** (Function) — `tests/integration/e2e_runner_script.py:82`
- **`check_models_available`** (Function) — `tests/integration/e2e_runner_script.py:88`
- **`get_reqifz_files`** (Function) — `tests/integration/e2e_runner_script.py:99`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `run_processing` | Function | `tests/performance/test_regression_benchmarks.py` | 80 |
| `run_command` | Function | `tests/integration/e2e_runner_script.py` | 69 |
| `check_ollama_service` | Function | `tests/integration/e2e_runner_script.py` | 82 |
| `check_models_available` | Function | `tests/integration/e2e_runner_script.py` | 88 |
| `get_reqifz_files` | Function | `tests/integration/e2e_runner_script.py` | 99 |
| `test_positive_standard_mode` | Function | `tests/integration/e2e_runner_script.py` | 104 |
| `test_positive_hp_mode` | Function | `tests/integration/e2e_runner_script.py` | 125 |
| `test_negative_missing_file` | Function | `tests/integration/e2e_runner_script.py` | 146 |
| `test_negative_invalid_file` | Function | `tests/integration/e2e_runner_script.py` | 160 |
| `test_negative_missing_model` | Function | `tests/integration/e2e_runner_script.py` | 181 |
| `test_output_validation` | Function | `tests/integration/e2e_runner_script.py` | 195 |
| `test_template_validation` | Function | `tests/integration/e2e_runner_script.py` | 219 |
| `test_batch_processing` | Function | `tests/integration/e2e_runner_script.py` | 232 |
| `main` | Function | `tests/integration/e2e_runner_script.py` | 259 |
| `test_generator_confidence_injection` | Function | `tests/core/test_ollama_logprobs.py` | 105 |
| `shutdown_app_logger` | Function | `src/app_logger.py` | 363 |
| `extract_image_paths` | Function | `src/core/generators.py` | 39 |
| `stamp_validation_results` | Function | `src/core/generators.py` | 66 |
| `test_ollama_client_sync_logprobs` | Function | `tests/core/test_ollama_logprobs.py` | 50 |
| `get_app_logger` | Function | `src/app_logger.py` | 332 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _build_spec_type_mapping` | cross_community | 6 |
| `Main → _build_foreign_id_mapping` | cross_community | 6 |
| `Main → _build_attribute_definition_mapping` | cross_community | 6 |
| `_run_hp_mode → _log_with_extras` | cross_community | 6 |
| `Verify_extraction → _determine_image_format` | cross_community | 6 |
| `Verify_extraction → _compute_hash` | cross_community | 6 |
| `Verify_extraction → _validate_image` | cross_community | 6 |
| `Verify_classification → _determine_image_format` | cross_community | 6 |
| `Verify_classification → _compute_hash` | cross_community | 6 |
| `Verify_classification → _validate_image` | cross_community | 6 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Processors | 16 calls |
| Tests | 4 calls |
| Cluster_30 | 2 calls |
| Training | 2 calls |
| Cluster_24 | 2 calls |
| Cluster_28 | 1 calls |
| Cluster_31 | 1 calls |
| Cluster_18 | 1 calls |

## How to Explore

1. `context({name: "run_processing"})` — see callers and callees
2. `query({search_query: "integration"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
