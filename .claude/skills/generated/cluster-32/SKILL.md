---
name: cluster-32
description: "Skill for the Cluster_32 area of AI_TC_Generator_v04_w_Trainer. 13 symbols across 2 files."
---

# Cluster_32

13 symbols | 2 files | Cohesion: 90%

## When to Use

- Working with code in `src/`
- Understanding how test_determine_image_format, test_compute_hash, test_sanitize_filename work
- Modifying cluster_32-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/core/image_extractor.py` | _extract_external_images, _extract_embedded_images, _extract_base64_images, _extract_object_images, _determine_image_format (+5) |
| `tests/core/test_image_extractor.py` | test_determine_image_format, test_compute_hash, test_sanitize_filename |

## Entry Points

Start here when exploring this area:

- **`test_determine_image_format`** (Function) — `tests/core/test_image_extractor.py:182`
- **`test_compute_hash`** (Function) — `tests/core/test_image_extractor.py:205`
- **`test_sanitize_filename`** (Function) — `tests/core/test_image_extractor.py:216`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_determine_image_format` | Function | `tests/core/test_image_extractor.py` | 182 |
| `test_compute_hash` | Function | `tests/core/test_image_extractor.py` | 205 |
| `test_sanitize_filename` | Function | `tests/core/test_image_extractor.py` | 216 |
| `_extract_external_images` | Method | `src/core/image_extractor.py` | 149 |
| `_extract_embedded_images` | Method | `src/core/image_extractor.py` | 207 |
| `_extract_base64_images` | Method | `src/core/image_extractor.py` | 235 |
| `_extract_object_images` | Method | `src/core/image_extractor.py` | 307 |
| `_determine_image_format` | Method | `src/core/image_extractor.py` | 348 |
| `_validate_image` | Method | `src/core/image_extractor.py` | 370 |
| `_save_image` | Method | `src/core/image_extractor.py` | 454 |
| `_sanitize_filename` | Method | `src/core/image_extractor.py` | 496 |
| `_compute_hash` | Method | `src/core/image_extractor.py` | 508 |
| `_preprocess_image` | Method | `src/core/image_extractor.py` | 512 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Verify_extraction → _determine_image_format` | cross_community | 6 |
| `Verify_extraction → _compute_hash` | cross_community | 6 |
| `Verify_classification → _determine_image_format` | cross_community | 6 |
| `Verify_classification → _compute_hash` | cross_community | 6 |
| `_extract_and_augment_images → _preprocess_image` | cross_community | 6 |
| `_extract_and_augment_images → _sanitize_filename` | cross_community | 6 |
| `Verify_augmentation → _compute_hash` | cross_community | 5 |
| `_extract_and_augment_images → _compute_hash` | cross_community | 5 |
| `_extract_and_augment_images → _validate_image` | cross_community | 5 |
| `_extract_and_augment_images → _extract_object_images` | cross_community | 4 |

## How to Explore

1. `context({name: "test_determine_image_format"})` — see callers and callees
2. `query({search_query: "cluster_32"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
