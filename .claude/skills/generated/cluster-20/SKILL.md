---
name: cluster-20
description: "Skill for the Cluster_20 area of AI_TC_Generator_v04_w_Trainer. 9 symbols across 5 files."
---

# Cluster_20

9 symbols | 5 files | Cohesion: 67%

## When to Use

- Working with code in `tests/`
- Understanding how register, test_image_extractor_rejects_compression_bomb, test_oversized_image_is_rejected_not_saved work
- Modifying cluster_20-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/core/image_extractor.py` | extract_images_from_reqifz, augment_artifacts_with_images, register |
| `tests/core/test_archive_limits.py` | test_image_extractor_rejects_compression_bomb, test_oversized_image_is_rejected_not_saved |
| `tests/core/test_image_extractor.py` | test_extract_images_without_saving, test_multiple_embedded_images |
| `src/core/extractors.py` | _extract_and_augment_images |
| `tests/core/test_vision_fixes.py` | test_full_extraction_with_preprocessing |

## Entry Points

Start here when exploring this area:

- **`register`** (Function) — `src/core/image_extractor.py:669`
- **`test_image_extractor_rejects_compression_bomb`** (Function) — `tests/core/test_archive_limits.py:121`
- **`test_oversized_image_is_rejected_not_saved`** (Function) — `tests/core/test_archive_limits.py:129`
- **`test_extract_images_without_saving`** (Function) — `tests/core/test_image_extractor.py:166`
- **`test_multiple_embedded_images`** (Function) — `tests/core/test_image_extractor.py:306`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `register` | Function | `src/core/image_extractor.py` | 669 |
| `test_image_extractor_rejects_compression_bomb` | Function | `tests/core/test_archive_limits.py` | 121 |
| `test_oversized_image_is_rejected_not_saved` | Function | `tests/core/test_archive_limits.py` | 129 |
| `test_extract_images_without_saving` | Function | `tests/core/test_image_extractor.py` | 166 |
| `test_multiple_embedded_images` | Function | `tests/core/test_image_extractor.py` | 306 |
| `extract_images_from_reqifz` | Method | `src/core/image_extractor.py` | 101 |
| `augment_artifacts_with_images` | Method | `src/core/image_extractor.py` | 643 |
| `test_full_extraction_with_preprocessing` | Method | `tests/core/test_vision_fixes.py` | 639 |
| `_extract_and_augment_images` | Method | `src/core/extractors.py` | 125 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Verify_extraction → _determine_image_format` | cross_community | 6 |
| `Verify_classification → _determine_image_format` | cross_community | 6 |
| `_extract_and_augment_images → _preprocess_image` | cross_community | 6 |
| `Verify_augmentation → Safe_zip_read` | cross_community | 5 |
| `Extract_images_from_reqifz → _sanitize_filename` | cross_community | 5 |
| `Extract_images_from_reqifz → Add_warning` | cross_community | 5 |
| `Verify_extraction → Safe_zip_read` | cross_community | 5 |
| `Verify_extraction → _compute_hash` | cross_community | 5 |
| `Verify_extraction → Register` | cross_community | 5 |
| `Verify_classification → Safe_zip_read` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_11 | 4 calls |
| Cluster_34 | 3 calls |

## How to Explore

1. `context({name: "register"})` — see callers and callees
2. `query({search_query: "cluster_20"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
