---
name: training
description: "Skill for the Training area of AI_TC_Generator_v04_w_Trainer. 85 symbols across 12 files."
---

# Training

85 symbols | 12 files | Cohesion: 89%

## When to Use

- Working with code in `src/`
- Understanding how test_nonzero_returncode_is_failed_with_error, test_timeout_is_failed_with_error, test_command_not_found_is_failed_with_error work
- Modifying training-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/training/test_raft_collector.py` | test_collect_example_success, test_collector_disabled_no_op, test_empty_requirement, test_missing_context_fields, test_special_characters_in_requirement_id (+9) |
| `src/training/progressive_trainer.py` | start_curriculum_training, _load_validated_examples, _organize_examples_by_phase, _train_phase, _simulate_phase_training (+7) |
| `tests/training/test_raft_dataset_builder.py` | test_build_dataset_success, test_filter_by_quality, test_build_dataset_empty_directory, test_build_dataset_nonexistent_directory, test_skip_unannotated_examples (+7) |
| `src/training/quality_scorer.py` | assess_example_quality, _calculate_relevance_score, _calculate_domain_relevance, _calculate_context_diversity, _calculate_context_quantity (+6) |
| `src/training/raft_annotator.py` | annotate_examples, _annotate_single_example, _build_context_items_list, _display_context_table, _get_user_oracle_selection (+6) |
| `src/training/raft_dataset_builder.py` | build_dataset, _build_raft_example, save_dataset, get_dataset_stats, validate_dataset |
| `src/training/vision_raft_trainer.py` | train, _analyze_dataset, _prepare_modelfile, _train_with_ollama, _save_training_progress |
| `tests/training/test_vision_raft_trainer.py` | _trainer, test_nonzero_returncode_is_failed_with_error, test_timeout_is_failed_with_error, test_command_not_found_is_failed_with_error, test_success_is_completed_without_errors |
| `src/training/raft_collector.py` | collect_example, _extract_images_for_training, get_collection_stats, clear_collected_data |
| `tests/training/test_raft_integration.py` | test_save_raft_example_no_op_when_disabled, test_save_raft_example_collects_when_enabled, test_raft_collection_minimal_overhead |

## Entry Points

Start here when exploring this area:

- **`test_nonzero_returncode_is_failed_with_error`** (Function) — `tests/training/test_vision_raft_trainer.py:40`
- **`test_timeout_is_failed_with_error`** (Function) — `tests/training/test_vision_raft_trainer.py:53`
- **`test_command_not_found_is_failed_with_error`** (Function) — `tests/training/test_vision_raft_trainer.py:66`
- **`test_success_is_completed_without_errors`** (Function) — `tests/training/test_vision_raft_trainer.py:79`
- **`assess_example_quality`** (Method) — `src/training/quality_scorer.py:122`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_nonzero_returncode_is_failed_with_error` | Function | `tests/training/test_vision_raft_trainer.py` | 40 |
| `test_timeout_is_failed_with_error` | Function | `tests/training/test_vision_raft_trainer.py` | 53 |
| `test_command_not_found_is_failed_with_error` | Function | `tests/training/test_vision_raft_trainer.py` | 66 |
| `test_success_is_completed_without_errors` | Function | `tests/training/test_vision_raft_trainer.py` | 79 |
| `assess_example_quality` | Method | `src/training/quality_scorer.py` | 122 |
| `batch_assess_quality` | Method | `src/training/quality_scorer.py` | 563 |
| `annotate_examples` | Method | `src/training/raft_annotator.py` | 53 |
| `collect_example` | Method | `src/training/raft_collector.py` | 50 |
| `test_collect_example_success` | Method | `tests/training/test_raft_collector.py` | 72 |
| `test_collector_disabled_no_op` | Method | `tests/training/test_raft_collector.py` | 155 |
| `test_empty_requirement` | Method | `tests/training/test_raft_collector.py` | 173 |
| `test_missing_context_fields` | Method | `tests/training/test_raft_collector.py` | 199 |
| `test_special_characters_in_requirement_id` | Method | `tests/training/test_raft_collector.py` | 256 |
| `test_very_long_test_cases` | Method | `tests/training/test_raft_collector.py` | 281 |
| `test_unicode_characters_in_context` | Method | `tests/training/test_raft_collector.py` | 306 |
| `test_empty_info_and_interface_lists` | Method | `tests/training/test_raft_collector.py` | 338 |
| `start_curriculum_training` | Method | `src/training/progressive_trainer.py` | 148 |
| `get_training_recommendations` | Method | `src/training/progressive_trainer.py` | 403 |
| `get_curriculum_status` | Method | `src/training/progressive_trainer.py` | 474 |
| `build_dataset` | Method | `src/training/raft_dataset_builder.py` | 44 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Annotate_examples → _show_annotation_help` | intra_community | 4 |
| `Batch_assess_quality → _calculate_domain_relevance` | intra_community | 4 |
| `Main → _analyze_dataset` | cross_community | 3 |
| `Main → _prepare_modelfile` | cross_community | 3 |
| `Main → _train_with_ollama` | cross_community | 3 |
| `Main → _save_training_progress` | cross_community | 3 |
| `Start_curriculum_training → _simulate_phase_training` | intra_community | 3 |
| `Get_curriculum_status → _load_validated_examples` | intra_community | 3 |
| `Get_curriculum_status → _organize_examples_by_phase` | intra_community | 3 |
| `Main → _build_raft_example` | cross_community | 3 |

## How to Explore

1. `context({name: "test_nonzero_returncode_is_failed_with_error"})` — see callers and callees
2. `query({search_query: "training"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
