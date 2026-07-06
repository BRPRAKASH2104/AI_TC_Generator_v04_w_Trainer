---
name: integration
description: "Skill for the Integration area of AI_TC_Generator_v04_w_Trainer. 40 symbols across 12 files."
---

# Integration

40 symbols | 12 files | Cohesion: 77%

## When to Use

- Working with code in `tests/`
- Understanding how run_command, check_ollama_service, check_models_available work
- Modifying integration-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/integration/e2e_runner_script.py` | add_pass, add_fail, run_command, check_ollama_service, check_models_available (+9) |
| `src/app_logger.py` | __init__, _start_performance_monitoring, info, warning, log_application_metrics (+3) |
| `tests/integration/test_edge_cases.py` | test_memory_pressure_simulation, test_json_missing_test_cases_key, test_malformed_test_case_structure, test_extremely_large_response, test_json_with_escaped_characters |
| `src/config.py` | get_masked_summary, print_summary, validate_secrets_for_mode |
| `tests/integration/test_end_to_end.py` | test_logging_integration_workflow, test_secrets_management_workflow |
| `src/core/parsers.py` | extract_json_from_response, extract_json_from_response |
| `evaluate/test_repos/fastapi/scripts/translate.py` | commands_json |
| `evaluate/test_repos/fastapi/tests/test_dependency_yield_scope.py` | iter_data |
| `evaluate/test_repos/flask/src/flask/json/__init__.py` | dumps |
| `src/core/generators.py` | generate_test_cases_for_requirement |

## Entry Points

Start here when exploring this area:

- **`run_command`** (Function) — `tests/integration/e2e_runner_script.py:69`
- **`check_ollama_service`** (Function) — `tests/integration/e2e_runner_script.py:82`
- **`check_models_available`** (Function) — `tests/integration/e2e_runner_script.py:88`
- **`test_positive_standard_mode`** (Function) — `tests/integration/e2e_runner_script.py:104`
- **`test_positive_hp_mode`** (Function) — `tests/integration/e2e_runner_script.py:125`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `run_command` | Function | `tests/integration/e2e_runner_script.py` | 69 |
| `check_ollama_service` | Function | `tests/integration/e2e_runner_script.py` | 82 |
| `check_models_available` | Function | `tests/integration/e2e_runner_script.py` | 88 |
| `test_positive_standard_mode` | Function | `tests/integration/e2e_runner_script.py` | 104 |
| `test_positive_hp_mode` | Function | `tests/integration/e2e_runner_script.py` | 125 |
| `test_negative_missing_file` | Function | `tests/integration/e2e_runner_script.py` | 146 |
| `test_negative_invalid_file` | Function | `tests/integration/e2e_runner_script.py` | 160 |
| `test_negative_missing_model` | Function | `tests/integration/e2e_runner_script.py` | 181 |
| `test_output_validation` | Function | `tests/integration/e2e_runner_script.py` | 195 |
| `test_template_validation` | Function | `tests/integration/e2e_runner_script.py` | 219 |
| `test_batch_processing` | Function | `tests/integration/e2e_runner_script.py` | 232 |
| `main` | Function | `tests/integration/e2e_runner_script.py` | 259 |
| `shutdown_app_logger` | Function | `src/app_logger.py` | 360 |
| `commands_json` | Function | `evaluate/test_repos/fastapi/scripts/translate.py` | 244 |
| `iter_data` | Function | `evaluate/test_repos/fastapi/tests/test_dependency_yield_scope.py` | 80 |
| `dumps` | Function | `evaluate/test_repos/flask/src/flask/json/__init__.py` | 12 |
| `add_pass` | Method | `tests/integration/e2e_runner_script.py` | 43 |
| `add_fail` | Method | `tests/integration/e2e_runner_script.py` | 47 |
| `info` | Method | `src/app_logger.py` | 197 |
| `warning` | Method | `src/app_logger.py` | 201 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `_run_hp_mode → _log_with_extras` | cross_community | 6 |
| `Process_directory → _log_with_extras` | cross_community | 5 |
| `_run_standard_mode → _log_with_extras` | cross_community | 4 |
| `Shutdown_app_logger → _log_with_extras` | cross_community | 4 |
| `Main → _log_with_extras` | cross_community | 3 |
| `Main → Run_command` | intra_community | 3 |
| `Main → Dumps` | cross_community | 3 |
| `__init__ → _log_with_extras` | cross_community | 3 |
| `Log_application_metrics → _log_with_extras` | cross_community | 3 |
| `Generate_test_cases_for_requirement → Calculate_confidence` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_447 | 3 calls |
| Cluster_457 | 3 calls |
| Training | 1 calls |
| Processors | 1 calls |

## How to Explore

1. `context({name: "run_command"})` — see callers and callees
2. `query({search_query: "integration"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
