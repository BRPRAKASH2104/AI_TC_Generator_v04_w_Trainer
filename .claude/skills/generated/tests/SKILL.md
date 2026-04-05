---
name: tests
description: "Skill for the Tests area of AI_TC_Generator_v04_w_Trainer. 181 symbols across 28 files."
---

# Tests

181 symbols | 28 files | Cohesion: 70%

## When to Use

- Working with code in `tests/`
- Understanding how test_build_augmented_requirements_with_context, test_build_augmented_requirements_no_requirements, test_build_augmented_requirements_no_heading work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/test_refactoring.py` | test_build_augmented_requirements_with_context, test_build_augmented_requirements_no_requirements, test_build_augmented_requirements_no_heading, test_async_generator_uses_prompt_builder, test_async_generator_no_sync_instantiation (+22) |
| `tests/core/test_base_processor.py` | test_default_initialization, test_initialization_with_dependency_injection, test_build_augmented_requirements_basic_flow, test_build_augmented_requirements_resets_info_after_requirement, test_build_augmented_requirements_new_heading_resets_info (+19) |
| `tests/test_critical_improvements.py` | test_base_processor_context_aware_logic_preserved, test_context_reset_after_each_requirement, test_ollama_connection_error_with_context, test_ollama_timeout_error_with_context, test_ollama_model_not_found_error_with_context (+10) |
| `tests/test_python314_ollama0125.py` | test_ollama_version, test_exception_response_body_field, test_python314_union_type_syntax, test_ollama_larger_context, test_ollama_increased_response_length (+6) |
| `src/core/ollama_client.py` | generate_completion, generate_response_with_vision, _check_version_compatibility, is_feature_available, get_model_info (+5) |
| `src/processors/base_processor.py` | BaseProcessor, _clean_text_for_logging, _build_augmented_requirements, _generate_output_path, _extract_artifacts (+4) |
| `src/core/exceptions.py` | OllamaError, OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaResponseError (+4) |
| `src/core/prompt_builder.py` | _build_from_template, _build_default, format_info_list, format_interfaces, format_image_context (+3) |
| `tests/training/test_raft_integration.py` | test_raft_disabled_no_collector_created, test_raft_enabled_collector_created, test_build_augmented_requirements_unchanged_with_raft, test_context_reset_behavior_intact, test_logger_update_does_not_affect_raft_disabled (+2) |
| `src/config.py` | OllamaConfig, apply_cli_overrides, update_if_not_overridden, _deep_merge_dict, show_effective_config (+2) |

## Entry Points

Start here when exploring this area:

- **`test_build_augmented_requirements_with_context`** (Function) — `tests/test_refactoring.py:41`
- **`test_build_augmented_requirements_no_requirements`** (Function) — `tests/test_refactoring.py:81`
- **`test_build_augmented_requirements_no_heading`** (Function) — `tests/test_refactoring.py:98`
- **`test_base_processor_context_aware_logic_preserved`** (Function) — `tests/test_critical_improvements.py:332`
- **`test_context_reset_after_each_requirement`** (Function) — `tests/test_critical_improvements.py:394`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `BaseProcessor` | Class | `src/processors/base_processor.py` | 22 |
| `OllamaError` | Class | `src/core/exceptions.py` | 13 |
| `OllamaConnectionError` | Class | `src/core/exceptions.py` | 19 |
| `OllamaTimeoutError` | Class | `src/core/exceptions.py` | 30 |
| `OllamaModelNotFoundError` | Class | `src/core/exceptions.py` | 40 |
| `OllamaResponseError` | Class | `src/core/exceptions.py` | 50 |
| `OllamaConfig` | Class | `src/config.py` | 27 |
| `AsyncTestCaseGenerator` | Class | `src/core/generators.py` | 266 |
| `TestCaseGenerator` | Class | `src/core/generators.py` | 109 |
| `MockResponse` | Class | `tests/core/test_ollama_logprobs.py` | 10 |
| `PromptBuilder` | Class | `src/core/prompt_builder.py` | 13 |
| `FileProcessingLogger` | Class | `src/file_processing_logger.py` | 51 |
| `AITestCaseGeneratorError` | Class | `src/core/exceptions.py` | 7 |
| `REQIFParsingError` | Class | `src/core/exceptions.py` | 63 |
| `TestCaseGenerationError` | Class | `src/core/exceptions.py` | 73 |
| `ConfigurationError` | Class | `src/core/exceptions.py` | 83 |
| `AsyncOllamaClient` | Class | `src/core/ollama_client.py` | 494 |
| `test_build_augmented_requirements_with_context` | Function | `tests/test_refactoring.py` | 41 |
| `test_build_augmented_requirements_no_requirements` | Function | `tests/test_refactoring.py` | 81 |
| `test_build_augmented_requirements_no_heading` | Function | `tests/test_refactoring.py` | 98 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _build_mappings_streaming` | cross_community | 5 |
| `Main → _compute_hash` | cross_community | 5 |
| `Main → _map_reqif_type_to_artifact_type` | cross_community | 5 |
| `Main → _extract_foreign_id` | cross_community | 5 |
| `Main → _extract_xhtml_content` | cross_community | 5 |
| `Main → _determine_artifact_type` | cross_community | 5 |
| `Main → FileProcessingLogger` | cross_community | 5 |
| `Generate_test_cases → Format_table` | cross_community | 5 |
| `Generate_test_cases → Format_info_list` | cross_community | 5 |
| `Generate_test_cases → Format_interfaces` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Integration | 30 calls |
| Utilities | 4 calls |
| Cluster_72 | 4 calls |
| Unit | 3 calls |
| Cluster_44 | 2 calls |

## How to Explore

1. `gitnexus_context({name: "test_build_augmented_requirements_with_context"})` — see callers and callees
2. `gitnexus_query({query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
