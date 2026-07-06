---
name: training
description: "Skill for the Training area of AI_TC_Generator_v04_w_Trainer. 51 symbols across 12 files."
---

# Training

51 symbols | 12 files | Cohesion: 63%

## When to Use

- Working with code in `src/`
- Understanding how load, dump, save work
- Modifying training-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/training/test_raft_collector.py` | test_collect_example_success, test_empty_requirement, test_missing_context_fields, test_very_long_test_cases, test_unicode_characters_in_context (+5) |
| `src/training/progressive_trainer.py` | __init__, _load_progress, _load_validated_examples, _organize_examples_by_phase, get_training_recommendations (+4) |
| `tests/training/test_raft_dataset_builder.py` | test_save_dataset_jsonl_format, test_validate_dataset_format, test_unicode_in_context, test_get_dataset_stats, test_build_dataset_success (+4) |
| `src/training/raft_annotator.py` | annotate_examples, _get_unannotated_files, _is_annotated, _annotate_single_example, _get_user_oracle_selection (+1) |
| `src/training/raft_collector.py` | collect_example, get_collection_stats, clear_collected_data |
| `src/training/raft_dataset_builder.py` | save_dataset, validate_dataset, build_dataset |
| `src/training/vision_raft_trainer.py` | train, _analyze_dataset, _save_training_progress |
| `src/training/quality_scorer.py` | assess_example_quality, _calculate_relevance_score, batch_assess_quality |
| `evaluate/test_repos/flask/src/flask/json/__init__.py` | load, dump |
| `evaluate/test_repos/nextjs/diagrams/generate_diagrams.py` | save |

## Entry Points

Start here when exploring this area:

- **`load`** (Function) — `evaluate/test_repos/flask/src/flask/json/__init__.py:107`
- **`dump`** (Function) — `evaluate/test_repos/flask/src/flask/json/__init__.py:46`
- **`save`** (Function) — `evaluate/test_repos/nextjs/diagrams/generate_diagrams.py:92`
- **`main`** (Function) — `utilities/build_vision_dataset.py:176`
- **`main`** (Function) — `utilities/train_vision_model.py:249`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `load` | Function | `evaluate/test_repos/flask/src/flask/json/__init__.py` | 107 |
| `dump` | Function | `evaluate/test_repos/flask/src/flask/json/__init__.py` | 46 |
| `save` | Function | `evaluate/test_repos/nextjs/diagrams/generate_diagrams.py` | 92 |
| `main` | Function | `utilities/build_vision_dataset.py` | 176 |
| `main` | Function | `utilities/train_vision_model.py` | 249 |
| `collect_example` | Method | `src/training/raft_collector.py` | 50 |
| `test_collect_example_success` | Method | `tests/training/test_raft_collector.py` | 72 |
| `test_empty_requirement` | Method | `tests/training/test_raft_collector.py` | 173 |
| `test_missing_context_fields` | Method | `tests/training/test_raft_collector.py` | 199 |
| `test_very_long_test_cases` | Method | `tests/training/test_raft_collector.py` | 281 |
| `test_unicode_characters_in_context` | Method | `tests/training/test_raft_collector.py` | 306 |
| `test_empty_info_and_interface_lists` | Method | `tests/training/test_raft_collector.py` | 338 |
| `test_annotated_example_in_stats` | Method | `tests/training/test_raft_collector.py` | 366 |
| `save_dataset` | Method | `src/training/raft_dataset_builder.py` | 184 |
| `validate_dataset` | Method | `src/training/raft_dataset_builder.py` | 297 |
| `test_save_dataset_jsonl_format` | Method | `tests/training/test_raft_dataset_builder.py` | 108 |
| `test_validate_dataset_format` | Method | `tests/training/test_raft_dataset_builder.py` | 277 |
| `test_unicode_in_context` | Method | `tests/training/test_raft_dataset_builder.py` | 297 |
| `test_get_dataset_stats` | Method | `tests/training/test_raft_dataset_builder.py` | 319 |
| `build_dataset` | Method | `src/training/raft_dataset_builder.py` | 44 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Loads` | cross_community | 4 |
| `Main → Dump` | cross_community | 4 |
| `Get_curriculum_status → Load` | cross_community | 4 |
| `Annotate_examples → _show_annotation_help` | cross_community | 4 |
| `Batch_assess_quality → _calculate_domain_relevance` | intra_community | 4 |
| `Main → Load` | cross_community | 4 |
| `Main → Dump` | cross_community | 4 |
| `Main → _prepare_modelfile` | intra_community | 3 |
| `Main → _train_with_ollama` | intra_community | 3 |
| `Start_curriculum_training → Load` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 4 calls |
| Integration | 3 calls |

## How to Explore

1. `context({name: "load"})` — see callers and callees
2. `query({search_query: "training"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
