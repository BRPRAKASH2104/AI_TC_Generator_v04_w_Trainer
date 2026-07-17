---
name: utilities
description: "Skill for the Utilities area of AI_TC_Generator_v04_w_Trainer. 40 symbols across 9 files."
---

# Utilities

40 symbols | 9 files | Cohesion: 85%

## When to Use

- Working with code in `utilities/`
- Understanding how create_vision_training_pipeline, parse_args, validate_dataset work
- Modifying utilities-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `utilities/version_check.py` | check_python_version, _print_upgrade_instructions, check_required_features, run_comprehensive_check, main (+4) |
| `utilities/train_vision_model.py` | parse_args, validate_dataset, check_ollama_connection, check_base_model_exists, check_output_model_exists (+2) |
| `utilities/verify_v03_compatibility.py` | verify_field_mapping, verify_all, verify_extraction, verify_classification, verify_prompt_generation (+2) |
| `src/core/formatters.py` | _stringify_list, _prepare_test_cases_for_excel, _get_default_test_values, _generate_issue_id |
| `utilities/annotate_raft.py` | annotate_example, batch_annotate, show_stats, main |
| `utilities/build_vision_dataset.py` | parse_args, validate_paths, print_dataset_stats, main |
| `tests/core/test_formatters_custom.py` | test_excel_description_includes_confidence, test_excel_description_handles_missing_confidence |
| `utilities/compare_v03_v04_output.py` | compare_outputs, main |
| `src/training/vision_raft_trainer.py` | create_vision_training_pipeline |

## Entry Points

Start here when exploring this area:

- **`create_vision_training_pipeline`** (Function) — `src/training/vision_raft_trainer.py:443`
- **`parse_args`** (Function) — `utilities/train_vision_model.py:64`
- **`validate_dataset`** (Function) — `utilities/train_vision_model.py:117`
- **`check_ollama_connection`** (Function) — `utilities/train_vision_model.py:143`
- **`check_base_model_exists`** (Function) — `utilities/train_vision_model.py:158`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `create_vision_training_pipeline` | Function | `src/training/vision_raft_trainer.py` | 443 |
| `parse_args` | Function | `utilities/train_vision_model.py` | 64 |
| `validate_dataset` | Function | `utilities/train_vision_model.py` | 117 |
| `check_ollama_connection` | Function | `utilities/train_vision_model.py` | 143 |
| `check_base_model_exists` | Function | `utilities/train_vision_model.py` | 158 |
| `check_output_model_exists` | Function | `utilities/train_vision_model.py` | 179 |
| `print_training_result` | Function | `utilities/train_vision_model.py` | 200 |
| `main` | Function | `utilities/train_vision_model.py` | 249 |
| `test_excel_description_includes_confidence` | Function | `tests/core/test_formatters_custom.py` | 4 |
| `test_excel_description_handles_missing_confidence` | Function | `tests/core/test_formatters_custom.py` | 22 |
| `main` | Function | `utilities/verify_v03_compatibility.py` | 352 |
| `main` | Function | `utilities/version_check.py` | 400 |
| `annotate_example` | Function | `utilities/annotate_raft.py` | 15 |
| `batch_annotate` | Function | `utilities/annotate_raft.py` | 179 |
| `show_stats` | Function | `utilities/annotate_raft.py` | 224 |
| `main` | Function | `utilities/annotate_raft.py` | 257 |
| `parse_args` | Function | `utilities/build_vision_dataset.py` | 62 |
| `validate_paths` | Function | `utilities/build_vision_dataset.py` | 113 |
| `print_dataset_stats` | Function | `utilities/build_vision_dataset.py` | 143 |
| `main` | Function | `utilities/build_vision_dataset.py` | 176 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _build_spec_type_mapping` | cross_community | 6 |
| `Main → _build_foreign_id_mapping` | cross_community | 6 |
| `Main → _build_attribute_definition_mapping` | cross_community | 6 |
| `Verify_extraction → _determine_image_format` | cross_community | 6 |
| `Verify_extraction → _compute_hash` | cross_community | 6 |
| `Verify_classification → _determine_image_format` | cross_community | 6 |
| `Verify_classification → _compute_hash` | cross_community | 6 |
| `Main → Version_tuple` | cross_community | 5 |
| `Main → _clean_text_for_logging` | cross_community | 5 |
| `Verify_extraction → _map_reqif_type_to_artifact_type` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Training | 3 calls |
| Integration | 2 calls |
| Processors | 1 calls |
| Tests | 1 calls |

## How to Explore

1. `context({name: "create_vision_training_pipeline"})` — see callers and callees
2. `query({search_query: "utilities"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
