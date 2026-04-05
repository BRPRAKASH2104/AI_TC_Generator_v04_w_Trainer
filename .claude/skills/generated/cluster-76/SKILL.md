---
name: cluster-76
description: "Skill for the Cluster_76 area of AI_TC_Generator_v04_w_Trainer. 6 symbols across 2 files."
---

# Cluster_76

6 symbols | 2 files | Cohesion: 63%

## When to Use

- Working with code in `tests/`
- Understanding how test_cleanup_removes_extracted_images, test_cleanup_specific_reqifz, test_cleanup_returns_count work
- Modifying cluster_76-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_vision_fixes.py` | test_cleanup_removes_extracted_images, test_cleanup_specific_reqifz, test_cleanup_returns_count, test_auto_cleanup_context_manager |
| `src/core/image_extractor.py` | cleanup_extracted_images, auto_cleanup |

## Entry Points

Start here when exploring this area:

- **`test_cleanup_removes_extracted_images`** (Function) — `tests/core/test_vision_fixes.py:458`
- **`test_cleanup_specific_reqifz`** (Function) — `tests/core/test_vision_fixes.py:486`
- **`test_cleanup_returns_count`** (Function) — `tests/core/test_vision_fixes.py:513`
- **`test_auto_cleanup_context_manager`** (Function) — `tests/core/test_vision_fixes.py:529`
- **`cleanup_extracted_images`** (Function) — `src/core/image_extractor.py:549`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_cleanup_removes_extracted_images` | Function | `tests/core/test_vision_fixes.py` | 458 |
| `test_cleanup_specific_reqifz` | Function | `tests/core/test_vision_fixes.py` | 486 |
| `test_cleanup_returns_count` | Function | `tests/core/test_vision_fixes.py` | 513 |
| `test_auto_cleanup_context_manager` | Function | `tests/core/test_vision_fixes.py` | 529 |
| `cleanup_extracted_images` | Function | `src/core/image_extractor.py` | 549 |
| `auto_cleanup` | Function | `src/core/image_extractor.py` | 587 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_74 | 4 calls |

## How to Explore

1. `gitnexus_context({name: "test_cleanup_removes_extracted_images"})` — see callers and callees
2. `gitnexus_query({query: "cluster_76"})` — find related execution flows
3. Read key files listed above for implementation details
