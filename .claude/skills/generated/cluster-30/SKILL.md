---
name: cluster-30
description: "Skill for the Cluster_30 area of AI_TC_Generator_v04_w_Trainer. 6 symbols across 2 files."
---

# Cluster_30

6 symbols | 2 files | Cohesion: 83%

## When to Use

- Working with code in `tests/`
- Understanding how cleanup_extracted_images, auto_cleanup, test_cleanup_removes_extracted_images work
- Modifying cluster_30-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_vision_fixes.py` | test_cleanup_removes_extracted_images, test_cleanup_specific_reqifz, test_cleanup_returns_count, test_auto_cleanup_context_manager |
| `src/core/image_extractor.py` | cleanup_extracted_images, auto_cleanup |

## Entry Points

Start here when exploring this area:

- **`cleanup_extracted_images`** (Method) — `src/core/image_extractor.py:571`
- **`auto_cleanup`** (Method) — `src/core/image_extractor.py:609`
- **`test_cleanup_removes_extracted_images`** (Method) — `tests/core/test_vision_fixes.py:458`
- **`test_cleanup_specific_reqifz`** (Method) — `tests/core/test_vision_fixes.py:486`
- **`test_cleanup_returns_count`** (Method) — `tests/core/test_vision_fixes.py:513`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `cleanup_extracted_images` | Method | `src/core/image_extractor.py` | 571 |
| `auto_cleanup` | Method | `src/core/image_extractor.py` | 609 |
| `test_cleanup_removes_extracted_images` | Method | `tests/core/test_vision_fixes.py` | 458 |
| `test_cleanup_specific_reqifz` | Method | `tests/core/test_vision_fixes.py` | 486 |
| `test_cleanup_returns_count` | Method | `tests/core/test_vision_fixes.py` | 513 |
| `test_auto_cleanup_context_manager` | Method | `tests/core/test_vision_fixes.py` | 529 |

## How to Explore

1. `context({name: "cleanup_extracted_images"})` — see callers and callees
2. `query({search_query: "cluster_30"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
