---
name: cluster-34
description: "Skill for the Cluster_34 area of AI_TC_Generator_v04_w_Trainer. 13 symbols across 2 files."
---

# Cluster_34

13 symbols | 2 files | Cohesion: 88%

## When to Use

- Working with code in `src/`
- Understanding how test_determine_image_format, test_compute_hash, test_sanitize_filename work
- Modifying cluster_34-related functionality

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
| `_extract_external_images` | Method | `src/core/image_extractor.py` | 165 |
| `_extract_embedded_images` | Method | `src/core/image_extractor.py` | 224 |
| `_extract_base64_images` | Method | `src/core/image_extractor.py` | 252 |
| `_extract_object_images` | Method | `src/core/image_extractor.py` | 324 |
| `_determine_image_format` | Method | `src/core/image_extractor.py` | 365 |
| `_validate_image` | Method | `src/core/image_extractor.py` | 387 |
| `_save_image` | Method | `src/core/image_extractor.py` | 471 |
| `_sanitize_filename` | Method | `src/core/image_extractor.py` | 513 |
| `_compute_hash` | Method | `src/core/image_extractor.py` | 525 |
| `_preprocess_image` | Method | `src/core/image_extractor.py` | 529 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Verify_extraction → _determine_image_format` | cross_community | 6 |
| `Verify_classification → _determine_image_format` | cross_community | 6 |
| `_extract_and_augment_images → _preprocess_image` | cross_community | 6 |
| `Extract_images_from_reqifz → _sanitize_filename` | cross_community | 5 |
| `Verify_extraction → _compute_hash` | cross_community | 5 |
| `Verify_classification → _compute_hash` | cross_community | 5 |
| `_extract_and_augment_images → _sanitize_filename` | cross_community | 5 |
| `_extract_and_augment_images → _compute_hash` | cross_community | 5 |
| `_extract_and_augment_images → _validate_image` | cross_community | 5 |
| `_extract_and_augment_images → _extract_object_images` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_11 | 1 calls |

## How to Explore

1. `context({name: "test_determine_image_format"})` — see callers and callees
2. `query({search_query: "cluster_34"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
