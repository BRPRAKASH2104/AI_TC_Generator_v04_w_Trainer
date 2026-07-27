---
name: training
description: "Skill for the Training area of AI_TC_Generator_v04_w_Trainer. 261 symbols across 22 files."
---

# Training

261 symbols | 22 files | Cohesion: 87%

## When to Use

- Working with code in `tests/`
- Understanding how trainer, test_result_shape, test_valid_output_scores_one work
- Modifying training-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/training/test_vision_raft_evaluate.py` | _write_jsonl, _text_example, _vision_example, trainer, test_result_shape (+42) |
| `src/training/vision_raft_trainer.py` | evaluate_model, _collect_errors, _load_and_validate_examples, _validate_example_contract, _validate_images (+20) |
| `tests/training/test_judge_calibration.py` | _case, test_all_bands_within_range_passes, test_breached_band_fails_the_report, test_none_metric_with_declared_band_is_a_breach_not_a_crash, test_scorer_returning_none_with_declared_band_is_a_breach (+19) |
| `tests/training/test_raft_dataset_builder.py` | test_build_dataset_success, test_filter_by_quality, test_build_dataset_empty_directory, test_build_dataset_nonexistent_directory, test_skip_unannotated_examples (+13) |
| `tests/training/test_raft_collector.py` | test_collect_example_success, test_collector_disabled_no_op, test_empty_requirement, test_missing_context_fields, test_special_characters_in_requirement_id (+9) |
| `tests/training/test_train_vision_cli.py` | _write_example, test_run_evaluation_forwards_compare_base, test_run_evaluation_threads_base_model_into_config, test_run_evaluation_happy_path_returns_0, _failed_comparison_result (+8) |
| `tests/training/test_progressive_trainer.py` | _rich_example, _simple_example, _poor_example, test_load_validated_examples_skips_corrupt, test_organize_examples_preserves_count_and_buckets_simple (+8) |
| `src/training/progressive_trainer.py` | start_curriculum_training, _load_validated_examples, _organize_examples_by_phase, _train_phase, _simulate_phase_training (+7) |
| `src/training/quality_scorer.py` | assess_example_quality, _calculate_relevance_score, _calculate_domain_relevance, _calculate_context_diversity, _calculate_context_quantity (+6) |
| `tests/training/test_raft_annotator.py` | _example, test_build_context_items_list_reflects_context, test_is_annotated, test_get_unannotated_files_filters_annotated, test_get_unannotated_files_skips_corrupt (+6) |

## Entry Points

Start here when exploring this area:

- **`trainer`** (Function) — `tests/training/test_vision_raft_evaluate.py:120`
- **`test_result_shape`** (Function) — `tests/training/test_vision_raft_evaluate.py:138`
- **`test_valid_output_scores_one`** (Function) — `tests/training/test_vision_raft_evaluate.py:157`
- **`test_invalid_schema_output_scores_zero`** (Function) — `tests/training/test_vision_raft_evaluate.py:177`
- **`test_unparseable_output_scores_zero`** (Function) — `tests/training/test_vision_raft_evaluate.py:190`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `trainer` | Function | `tests/training/test_vision_raft_evaluate.py` | 120 |
| `test_result_shape` | Function | `tests/training/test_vision_raft_evaluate.py` | 138 |
| `test_valid_output_scores_one` | Function | `tests/training/test_vision_raft_evaluate.py` | 157 |
| `test_invalid_schema_output_scores_zero` | Function | `tests/training/test_vision_raft_evaluate.py` | 177 |
| `test_unparseable_output_scores_zero` | Function | `tests/training/test_vision_raft_evaluate.py` | 190 |
| `test_vision_score_is_none_without_vision_examples` | Function | `tests/training/test_vision_raft_evaluate.py` | 202 |
| `test_routes_vision_examples_through_vision_method` | Function | `tests/training/test_vision_raft_evaluate.py` | 214 |
| `test_forwards_canonical_schema_to_model` | Function | `tests/training/test_vision_raft_evaluate.py` | 228 |
| `test_injected_client_never_shells_out` | Function | `tests/training/test_vision_raft_evaluate.py` | 240 |
| `test_no_baseline_or_delta_by_default` | Function | `tests/training/test_vision_raft_evaluate.py` | 258 |
| `test_compare_base_adds_baseline_and_delta` | Function | `tests/training/test_vision_raft_evaluate.py` | 268 |
| `test_compare_base_runs_both_models` | Function | `tests/training/test_vision_raft_evaluate.py` | 282 |
| `test_delta_reflects_customized_minus_base` | Function | `tests/training/test_vision_raft_evaluate.py` | 293 |
| `test_delta_is_none_when_metric_absent_on_a_side` | Function | `tests/training/test_vision_raft_evaluate.py` | 311 |
| `test_total_baseline_failure_withholds_delta` | Function | `tests/training/test_vision_raft_evaluate.py` | 329 |
| `test_partial_baseline_failure_compares_paired_rows_only` | Function | `tests/training/test_vision_raft_evaluate.py` | 351 |
| `test_customized_failures_also_excluded_from_pairing` | Function | `tests/training/test_vision_raft_evaluate.py` | 374 |
| `test_full_success_comparison_is_complete` | Function | `tests/training/test_vision_raft_evaluate.py` | 394 |
| `test_duplicate_heavy_output_does_not_inflate_unique_valid` | Function | `tests/training/test_vision_raft_evaluate.py` | 427 |
| `test_invalid_bulk_output_has_zero_unique_valid` | Function | `tests/training/test_vision_raft_evaluate.py` | 449 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _within` | cross_community | 6 |
| `Run_evaluation → _decoded_image_paths` | cross_community | 6 |
| `Run_evaluation → Extract_json_from_response` | cross_community | 6 |
| `Run_evaluation → Is_canonical_test_case` | cross_community | 6 |
| `Run_evaluation → _reference_answer` | cross_community | 6 |
| `Run_evaluation → Score` | cross_community | 6 |
| `Main → Score` | cross_community | 5 |
| `Main → _format_band` | cross_community | 5 |
| `Run_evaluation → _validate_images` | cross_community | 5 |
| `Run_evaluation → Mean_score` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Integration | 4 calls |
| Cluster_14 | 2 calls |

## How to Explore

1. `context({name: "trainer"})` — see callers and callees
2. `query({search_query: "training"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
