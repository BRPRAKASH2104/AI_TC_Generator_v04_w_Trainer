---
name: utilities
description: "Skill for the Utilities area of AI_TC_Generator_v04_w_Trainer. 46 symbols across 10 files."
---

# Utilities

46 symbols | 10 files | Cohesion: 84%

## When to Use

- Working with code in `utilities/`
- Understanding how create_vision_training_pipeline, parse_args, validate_dataset work
- Modifying utilities-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `utilities/train_vision_model.py` | parse_args, validate_dataset, check_ollama_connection, check_base_model_exists, check_output_model_exists (+6) |
| `utilities/version_check.py` | check_python_version, _print_upgrade_instructions, check_required_features, run_comprehensive_check, main (+4) |
| `utilities/verify_v03_compatibility.py` | verify_field_mapping, verify_all, verify_extraction, verify_classification, verify_prompt_generation (+2) |
| `src/core/formatters.py` | _stringify_list, _prepare_test_cases_for_excel, _get_default_test_values, _generate_issue_id |
| `utilities/build_vision_dataset.py` | parse_args, validate_paths, print_dataset_stats, main |
| `utilities/annotate_raft.py` | annotate_example, batch_annotate, show_stats, main |
| `tests/core/test_formatters_custom.py` | test_excel_description_includes_confidence, test_excel_description_handles_missing_confidence |
| `src/training/raft_dataset_builder.py` | split_dataset, save_split |
| `utilities/compare_v03_v04_output.py` | compare_outputs, main |
| `src/training/vision_raft_trainer.py` | create_vision_training_pipeline |

## Entry Points

Start here when exploring this area:

- **`create_vision_training_pipeline`** (Function) — `src/training/vision_raft_trainer.py:1198`
- **`parse_args`** (Function) — `utilities/train_vision_model.py:71`
- **`validate_dataset`** (Function) — `utilities/train_vision_model.py:172`
- **`check_ollama_connection`** (Function) — `utilities/train_vision_model.py:198`
- **`check_base_model_exists`** (Function) — `utilities/train_vision_model.py:213`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `create_vision_training_pipeline` | Function | `src/training/vision_raft_trainer.py` | 1198 |
| `parse_args` | Function | `utilities/train_vision_model.py` | 71 |
| `validate_dataset` | Function | `utilities/train_vision_model.py` | 172 |
| `check_ollama_connection` | Function | `utilities/train_vision_model.py` | 198 |
| `check_base_model_exists` | Function | `utilities/train_vision_model.py` | 213 |
| `check_output_model_exists` | Function | `utilities/train_vision_model.py` | 234 |
| `print_training_result` | Function | `utilities/train_vision_model.py` | 255 |
| `print_evaluation_result` | Function | `utilities/train_vision_model.py` | 309 |
| `run_evaluation` | Function | `utilities/train_vision_model.py` | 418 |
| `run_judge_calibration` | Function | `utilities/train_vision_model.py` | 471 |
| `main` | Function | `utilities/train_vision_model.py` | 488 |
| `test_excel_description_includes_confidence` | Function | `tests/core/test_formatters_custom.py` | 3 |
| `test_excel_description_handles_missing_confidence` | Function | `tests/core/test_formatters_custom.py` | 24 |
| `parse_args` | Function | `utilities/build_vision_dataset.py` | 62 |
| `validate_paths` | Function | `utilities/build_vision_dataset.py` | 131 |
| `print_dataset_stats` | Function | `utilities/build_vision_dataset.py` | 161 |
| `main` | Function | `utilities/build_vision_dataset.py` | 194 |
| `main` | Function | `utilities/verify_v03_compatibility.py` | 352 |
| `main` | Function | `utilities/version_check.py` | 400 |
| `annotate_example` | Function | `utilities/annotate_raft.py` | 15 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _within` | cross_community | 6 |
| `Run_evaluation → _decoded_image_paths` | cross_community | 6 |
| `Run_evaluation → Extract_json_from_response` | cross_community | 6 |
| `Run_evaluation → Is_canonical_test_case` | cross_community | 6 |
| `Run_evaluation → _reference_answer` | cross_community | 6 |
| `Run_evaluation → Score` | cross_community | 6 |
| `Main → _build_spec_type_mapping` | cross_community | 6 |
| `Main → _build_foreign_id_mapping` | cross_community | 6 |
| `Main → _build_attribute_definition_mapping` | cross_community | 6 |
| `Verify_extraction → _determine_image_format` | cross_community | 6 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Training | 6 calls |
| Integration | 2 calls |
| Processors | 1 calls |
| Tests | 1 calls |

## How to Explore

1. `context({name: "create_vision_training_pipeline"})` — see callers and callees
2. `query({search_query: "utilities"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
