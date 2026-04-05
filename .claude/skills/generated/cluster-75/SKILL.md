---
name: cluster-75
description: "Skill for the Cluster_75 area of AI_TC_Generator_v04_w_Trainer. 7 symbols across 2 files."
---

# Cluster_75

7 symbols | 2 files | Cohesion: 100%

## When to Use

- Working with code in `tests/`
- Understanding how test_preprocess_resizes_large_images, test_preprocess_preserves_small_images, test_preprocess_converts_rgba_to_rgb work
- Modifying cluster_75-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_vision_fixes.py` | test_preprocess_resizes_large_images, test_preprocess_preserves_small_images, test_preprocess_converts_rgba_to_rgb, test_preprocess_maintains_aspect_ratio, test_preprocess_reduces_file_size (+1) |
| `src/core/image_extractor.py` | _preprocess_image |

## Entry Points

Start here when exploring this area:

- **`test_preprocess_resizes_large_images`** (Function) — `tests/core/test_vision_fixes.py:139`
- **`test_preprocess_preserves_small_images`** (Function) — `tests/core/test_vision_fixes.py:151`
- **`test_preprocess_converts_rgba_to_rgb`** (Function) — `tests/core/test_vision_fixes.py:164`
- **`test_preprocess_maintains_aspect_ratio`** (Function) — `tests/core/test_vision_fixes.py:181`
- **`test_preprocess_reduces_file_size`** (Function) — `tests/core/test_vision_fixes.py:196`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_preprocess_resizes_large_images` | Function | `tests/core/test_vision_fixes.py` | 139 |
| `test_preprocess_preserves_small_images` | Function | `tests/core/test_vision_fixes.py` | 151 |
| `test_preprocess_converts_rgba_to_rgb` | Function | `tests/core/test_vision_fixes.py` | 164 |
| `test_preprocess_maintains_aspect_ratio` | Function | `tests/core/test_vision_fixes.py` | 181 |
| `test_preprocess_reduces_file_size` | Function | `tests/core/test_vision_fixes.py` | 196 |
| `test_preprocess_handles_invalid_image_gracefully` | Function | `tests/core/test_vision_fixes.py` | 206 |
| `_preprocess_image` | Function | `src/core/image_extractor.py` | 490 |

## How to Explore

1. `gitnexus_context({name: "test_preprocess_resizes_large_images"})` — see callers and callees
2. `gitnexus_query({query: "cluster_75"})` — find related execution flows
3. Read key files listed above for implementation details
