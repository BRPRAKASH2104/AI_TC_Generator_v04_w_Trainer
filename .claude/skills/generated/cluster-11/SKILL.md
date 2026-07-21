---
name: cluster-11
description: "Skill for the Cluster_11 area of AI_TC_Generator_v04_w_Trainer. 14 symbols across 3 files."
---

# Cluster_11

14 symbols | 3 files | Cohesion: 83%

## When to Use

- Working with code in `tests/`
- Understanding how validate_archive_safety, safe_zip_read, test_valid_archive_passes work
- Modifying cluster_11-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_archive_limits.py` | _make_zip, test_valid_archive_passes, test_rejects_too_many_entries, test_rejects_oversized_entry, test_rejects_oversized_total (+4) |
| `src/core/archive_limits.py` | validate_archive_safety, safe_zip_read, _reject |
| `src/file_processing_logger.py` | add_warning, warning |

## Entry Points

Start here when exploring this area:

- **`validate_archive_safety`** (Function) — `src/core/archive_limits.py:46`
- **`safe_zip_read`** (Function) — `src/core/archive_limits.py:98`
- **`test_valid_archive_passes`** (Function) — `tests/core/test_archive_limits.py:41`
- **`test_rejects_too_many_entries`** (Function) — `tests/core/test_archive_limits.py:47`
- **`test_rejects_oversized_entry`** (Function) — `tests/core/test_archive_limits.py:58`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `validate_archive_safety` | Function | `src/core/archive_limits.py` | 46 |
| `safe_zip_read` | Function | `src/core/archive_limits.py` | 98 |
| `test_valid_archive_passes` | Function | `tests/core/test_archive_limits.py` | 41 |
| `test_rejects_too_many_entries` | Function | `tests/core/test_archive_limits.py` | 47 |
| `test_rejects_oversized_entry` | Function | `tests/core/test_archive_limits.py` | 58 |
| `test_rejects_oversized_total` | Function | `tests/core/test_archive_limits.py` | 66 |
| `test_rejects_high_compression_ratio` | Function | `tests/core/test_archive_limits.py` | 77 |
| `test_tiny_compressible_entry_is_exempt_from_ratio` | Function | `tests/core/test_archive_limits.py` | 85 |
| `test_safe_zip_read_returns_data_within_cap` | Function | `tests/core/test_archive_limits.py` | 97 |
| `test_safe_zip_read_rejects_over_cap` | Function | `tests/core/test_archive_limits.py` | 103 |
| `add_warning` | Method | `src/file_processing_logger.py` | 128 |
| `warning` | Method | `src/file_processing_logger.py` | 228 |
| `_reject` | Function | `src/core/archive_limits.py` | 126 |
| `_make_zip` | Function | `tests/core/test_archive_limits.py` | 26 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Verify_augmentation → Safe_zip_read` | cross_community | 5 |
| `Extract_images_from_reqifz → Add_warning` | cross_community | 5 |
| `Verify_extraction → Safe_zip_read` | cross_community | 5 |
| `Verify_classification → Safe_zip_read` | cross_community | 5 |

## How to Explore

1. `context({name: "validate_archive_safety"})` — see callers and callees
2. `query({search_query: "cluster_11"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
