---
name: training
description: "Skill for the Training area of AI_TC_Generator_v04_w_Trainer. 94 symbols across 11 files."
---

# Training

94 symbols | 11 files | Cohesion: 92%

## When to Use

- Working with code in `src/`
- Understanding how test_collector_initialization_enabled, test_collect_example_success, test_get_collection_stats_with_data work
- Modifying training-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/training/test_raft_collector.py` | test_collector_initialization_enabled, test_collect_example_success, test_get_collection_stats_with_data, test_clear_collected_data, test_collector_disabled_no_op (+10) |
| `src/training/quality_scorer.py` | QualityMetrics, QualityAssessment, assess_example_quality, _calculate_relevance_score, _calculate_domain_relevance (+9) |
| `src/training/progressive_trainer.py` | start_curriculum_training, _load_validated_examples, _organize_examples_by_phase, _train_phase, _simulate_phase_training (+9) |
| `tests/training/test_raft_dataset_builder.py` | test_builder_initialization, test_build_dataset_success, test_save_dataset_jsonl_format, test_filter_by_quality, test_build_dataset_empty_directory (+8) |
| `src/training/raft_annotator.py` | annotate_examples, _annotate_single_example, _build_context_items_list, _display_context_table, _get_user_oracle_selection (+6) |
| `src/training/vision_raft_trainer.py` | VisionTrainingConfig, TrainingProgress, VisionRAFTTrainer, __init__, create_vision_training_pipeline (+5) |
| `src/training/raft_dataset_builder.py` | RAFTDatasetBuilder, build_dataset, _build_raft_example, save_dataset, get_dataset_stats (+1) |
| `src/training/raft_collector.py` | RAFTDataCollector, collect_example, _extract_images_for_training, get_collection_stats, clear_collected_data |
| `tests/training/test_raft_integration.py` | test_save_raft_example_no_op_when_disabled, test_save_raft_example_collects_when_enabled, test_raft_collection_minimal_overhead |
| `tests/core/test_base_processor.py` | test_save_raft_example_when_enabled, test_save_raft_example_when_disabled |

## Entry Points

Start here when exploring this area:

- **`test_collector_initialization_enabled`** (Function) — `tests/training/test_raft_collector.py:59`
- **`test_collect_example_success`** (Function) — `tests/training/test_raft_collector.py:72`
- **`test_get_collection_stats_with_data`** (Function) — `tests/training/test_raft_collector.py:107`
- **`test_clear_collected_data`** (Function) — `tests/training/test_raft_collector.py:129`
- **`test_collector_disabled_no_op`** (Function) — `tests/training/test_raft_collector.py:155`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `RAFTDataCollector` | Class | `src/training/raft_collector.py` | 22 |
| `RAFTDatasetBuilder` | Class | `src/training/raft_dataset_builder.py` | 19 |
| `QualityMetrics` | Class | `src/training/quality_scorer.py` | 21 |
| `QualityAssessment` | Class | `src/training/quality_scorer.py` | 37 |
| `QualityScorer` | Class | `src/training/quality_scorer.py` | 46 |
| `TrainingProgress` | Class | `src/training/progressive_trainer.py` | 32 |
| `CurriculumStage` | Class | `src/training/progressive_trainer.py` | 46 |
| `VisionTrainingConfig` | Class | `src/training/vision_raft_trainer.py` | 25 |
| `TrainingProgress` | Class | `src/training/vision_raft_trainer.py` | 58 |
| `VisionRAFTTrainer` | Class | `src/training/vision_raft_trainer.py` | 80 |
| `test_collector_initialization_enabled` | Function | `tests/training/test_raft_collector.py` | 59 |
| `test_collect_example_success` | Function | `tests/training/test_raft_collector.py` | 72 |
| `test_get_collection_stats_with_data` | Function | `tests/training/test_raft_collector.py` | 107 |
| `test_clear_collected_data` | Function | `tests/training/test_raft_collector.py` | 129 |
| `test_collector_disabled_no_op` | Function | `tests/training/test_raft_collector.py` | 155 |
| `test_empty_requirement` | Function | `tests/training/test_raft_collector.py` | 173 |
| `test_missing_context_fields` | Function | `tests/training/test_raft_collector.py` | 199 |
| `test_get_stats_no_directory` | Function | `tests/training/test_raft_collector.py` | 226 |
| `test_clear_data_when_disabled` | Function | `tests/training/test_raft_collector.py` | 243 |
| `test_special_characters_in_requirement_id` | Function | `tests/training/test_raft_collector.py` | 256 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Start_curriculum_training → _calculate_domain_relevance` | cross_community | 6 |
| `Get_curriculum_status → _calculate_domain_relevance` | cross_community | 6 |
| `Start_curriculum_training → _calculate_context_diversity` | cross_community | 5 |
| `Start_curriculum_training → _calculate_context_quantity` | cross_community | 5 |
| `Start_curriculum_training → _calculate_requirement_complexity` | cross_community | 5 |
| `Get_curriculum_status → _calculate_context_diversity` | cross_community | 5 |
| `Get_curriculum_status → _calculate_context_quantity` | cross_community | 5 |
| `Get_curriculum_status → _calculate_requirement_complexity` | cross_community | 5 |
| `Get_training_recommendations → _calculate_domain_relevance` | cross_community | 5 |
| `Annotate_examples → _show_annotation_help` | intra_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 5 calls |

## How to Explore

1. `gitnexus_context({name: "test_collector_initialization_enabled"})` — see callers and callees
2. `gitnexus_query({query: "training"})` — find related execution flows
3. Read key files listed above for implementation details
