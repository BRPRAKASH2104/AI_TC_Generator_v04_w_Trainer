---
name: cluster-77
description: "Skill for the Cluster_77 area of AI_TC_Generator_v04_w_Trainer. 7 symbols across 2 files."
---

# Cluster_77

7 symbols | 2 files | Cohesion: 86%

## When to Use

- Working with code in `tests/`
- Understanding how test_validation_warns_on_large_dimensions, test_validation_warns_on_extreme_aspect_ratio, test_validation_warns_on_tiny_images work
- Modifying cluster_77-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_vision_fixes.py` | test_validation_warns_on_large_dimensions, test_validation_warns_on_extreme_aspect_ratio, test_validation_warns_on_tiny_images, test_validation_detects_animated_gif, test_validation_reports_file_size (+1) |
| `src/core/image_extractor.py` | _validate_image |

## Entry Points

Start here when exploring this area:

- **`test_validation_warns_on_large_dimensions`** (Function) — `tests/core/test_vision_fixes.py:560`
- **`test_validation_warns_on_extreme_aspect_ratio`** (Function) — `tests/core/test_vision_fixes.py:572`
- **`test_validation_warns_on_tiny_images`** (Function) — `tests/core/test_vision_fixes.py:587`
- **`test_validation_detects_animated_gif`** (Function) — `tests/core/test_vision_fixes.py:599`
- **`test_validation_reports_file_size`** (Function) — `tests/core/test_vision_fixes.py:612`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_validation_warns_on_large_dimensions` | Function | `tests/core/test_vision_fixes.py` | 560 |
| `test_validation_warns_on_extreme_aspect_ratio` | Function | `tests/core/test_vision_fixes.py` | 572 |
| `test_validation_warns_on_tiny_images` | Function | `tests/core/test_vision_fixes.py` | 587 |
| `test_validation_detects_animated_gif` | Function | `tests/core/test_vision_fixes.py` | 599 |
| `test_validation_reports_file_size` | Function | `tests/core/test_vision_fixes.py` | 612 |
| `test_validation_no_warnings_for_good_images` | Function | `tests/core/test_vision_fixes.py` | 620 |
| `_validate_image` | Function | `src/core/image_extractor.py` | 365 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `_extract_and_augment_images → _validate_image` | cross_community | 5 |

## How to Explore

1. `gitnexus_context({name: "test_validation_warns_on_large_dimensions"})` — see callers and callees
2. `gitnexus_query({query: "cluster_77"})` — find related execution flows
3. Read key files listed above for implementation details
