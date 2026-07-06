---
name: cluster-17
description: "Skill for the Cluster_17 area of AI_TC_Generator_v04_w_Trainer. 6 symbols across 4 files."
---

# Cluster_17

6 symbols | 4 files | Cohesion: 71%

## When to Use

- Working with code in `src/`
- Understanding how test_extract_images_without_saving, test_multiple_embedded_images, extract_images_from_reqifz work
- Modifying cluster_17-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/core/image_extractor.py` | extract_images_from_reqifz, augment_artifacts_with_images |
| `tests/core/test_image_extractor.py` | test_extract_images_without_saving, test_multiple_embedded_images |
| `src/core/extractors.py` | _extract_and_augment_images |
| `tests/core/test_vision_fixes.py` | test_full_extraction_with_preprocessing |

## Entry Points

Start here when exploring this area:

- **`test_extract_images_without_saving`** (Function) — `tests/core/test_image_extractor.py:166`
- **`test_multiple_embedded_images`** (Function) — `tests/core/test_image_extractor.py:306`
- **`extract_images_from_reqifz`** (Method) — `src/core/image_extractor.py:94`
- **`augment_artifacts_with_images`** (Method) — `src/core/image_extractor.py:626`
- **`test_full_extraction_with_preprocessing`** (Method) — `tests/core/test_vision_fixes.py:639`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_extract_images_without_saving` | Function | `tests/core/test_image_extractor.py` | 166 |
| `test_multiple_embedded_images` | Function | `tests/core/test_image_extractor.py` | 306 |
| `extract_images_from_reqifz` | Method | `src/core/image_extractor.py` | 94 |
| `augment_artifacts_with_images` | Method | `src/core/image_extractor.py` | 626 |
| `test_full_extraction_with_preprocessing` | Method | `tests/core/test_vision_fixes.py` | 639 |
| `_extract_and_augment_images` | Method | `src/core/extractors.py` | 112 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Verify_extraction → _determine_image_format` | cross_community | 6 |
| `Verify_extraction → _compute_hash` | cross_community | 6 |
| `Verify_extraction → _validate_image` | cross_community | 6 |
| `Verify_classification → _determine_image_format` | cross_community | 6 |
| `Verify_classification → _compute_hash` | cross_community | 6 |
| `Verify_classification → _validate_image` | cross_community | 6 |
| `_extract_and_augment_images → _preprocess_image` | cross_community | 6 |
| `_extract_and_augment_images → _sanitize_filename` | cross_community | 6 |
| `Verify_augmentation → _compute_hash` | cross_community | 5 |
| `_extract_and_augment_images → _compute_hash` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_29 | 3 calls |

## How to Explore

1. `context({name: "test_extract_images_without_saving"})` — see callers and callees
2. `query({search_query: "cluster_17"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
