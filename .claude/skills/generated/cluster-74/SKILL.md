---
name: cluster-74
description: "Skill for the Cluster_74 area of AI_TC_Generator_v04_w_Trainer. 17 symbols across 4 files."
---

# Cluster_74

17 symbols | 4 files | Cohesion: 75%

## When to Use

- Working with code in `tests/`
- Understanding how extractor, test_full_extraction_with_preprocessing, extractor work
- Modifying cluster_74-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_image_extractor.py` | extractor, test_extract_external_images, test_extract_embedded_images, test_extract_images_without_saving, test_determine_image_format (+3) |
| `src/core/image_extractor.py` | RequirementImageExtractor, extract_images_from_reqifz, _extract_external_images, _determine_image_format, _save_image (+1) |
| `tests/core/test_vision_fixes.py` | extractor, test_full_extraction_with_preprocessing |
| `src/core/extractors.py` | _extract_and_augment_images |

## Entry Points

Start here when exploring this area:

- **`extractor`** (Function) — `tests/core/test_vision_fixes.py:50`
- **`test_full_extraction_with_preprocessing`** (Function) — `tests/core/test_vision_fixes.py:639`
- **`extractor`** (Function) — `tests/core/test_image_extractor.py:33`
- **`test_extract_external_images`** (Function) — `tests/core/test_image_extractor.py:125`
- **`test_extract_embedded_images`** (Function) — `tests/core/test_image_extractor.py:148`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `RequirementImageExtractor` | Class | `src/core/image_extractor.py` | 65 |
| `extractor` | Function | `tests/core/test_vision_fixes.py` | 50 |
| `test_full_extraction_with_preprocessing` | Function | `tests/core/test_vision_fixes.py` | 639 |
| `extractor` | Function | `tests/core/test_image_extractor.py` | 33 |
| `test_extract_external_images` | Function | `tests/core/test_image_extractor.py` | 125 |
| `test_extract_embedded_images` | Function | `tests/core/test_image_extractor.py` | 148 |
| `test_extract_images_without_saving` | Function | `tests/core/test_image_extractor.py` | 166 |
| `test_determine_image_format` | Function | `tests/core/test_image_extractor.py` | 182 |
| `test_sanitize_filename` | Function | `tests/core/test_image_extractor.py` | 216 |
| `test_extract_images_from_empty_reqifz` | Function | `tests/core/test_image_extractor.py` | 262 |
| `test_multiple_embedded_images` | Function | `tests/core/test_image_extractor.py` | 306 |
| `extract_images_from_reqifz` | Function | `src/core/image_extractor.py` | 89 |
| `_extract_external_images` | Function | `src/core/image_extractor.py` | 144 |
| `_determine_image_format` | Function | `src/core/image_extractor.py` | 343 |
| `_save_image` | Function | `src/core/image_extractor.py` | 448 |
| `_sanitize_filename` | Function | `src/core/image_extractor.py` | 474 |
| `_extract_and_augment_images` | Function | `src/core/extractors.py` | 80 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → RequirementImageExtractor` | cross_community | 6 |
| `_extract_and_augment_images → _sanitize_filename` | cross_community | 6 |
| `Main → _compute_hash` | cross_community | 5 |
| `Verify_extraction → _compute_hash` | cross_community | 5 |
| `Verify_classification → _compute_hash` | cross_community | 5 |
| `_extract_and_augment_images → ImageFormat` | cross_community | 5 |
| `_extract_and_augment_images → _compute_hash` | cross_community | 5 |
| `_extract_and_augment_images → _validate_image` | cross_community | 5 |
| `Main → RequirementImageExtractor` | cross_community | 4 |
| `Main → RequirementImageExtractor` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_100 | 2 calls |
| Cluster_87 | 2 calls |
| Cluster_77 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "extractor"})` — see callers and callees
2. `gitnexus_query({query: "cluster_74"})` — find related execution flows
3. Read key files listed above for implementation details
