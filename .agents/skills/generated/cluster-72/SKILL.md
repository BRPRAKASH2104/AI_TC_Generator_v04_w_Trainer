---
name: cluster-72
description: "Skill for the Cluster_72 area of AI_TC_Generator_v04_w_Trainer. 6 symbols across 1 files."
---

# Cluster_72

6 symbols | 1 files | Cohesion: 80%

## When to Use

- Working with code in `tests/`
- Understanding how test_thresholds_and_fields_wired_from_config, test_deduplication_disabled_via_config, test_validation_disabled_via_config work
- Modifying cluster_72-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/core/test_generators.py` | _make_config, _client, test_thresholds_and_fields_wired_from_config, test_deduplication_disabled_via_config, test_validation_disabled_via_config (+1) |

## Entry Points

Start here when exploring this area:

- **`test_thresholds_and_fields_wired_from_config`** (Method) — `tests/core/test_generators.py:248`
- **`test_deduplication_disabled_via_config`** (Method) — `tests/core/test_generators.py:260`
- **`test_validation_disabled_via_config`** (Method) — `tests/core/test_generators.py:272`
- **`test_keep_strategy_wired_from_config`** (Method) — `tests/core/test_generators.py:285`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_thresholds_and_fields_wired_from_config` | Method | `tests/core/test_generators.py` | 248 |
| `test_deduplication_disabled_via_config` | Method | `tests/core/test_generators.py` | 260 |
| `test_validation_disabled_via_config` | Method | `tests/core/test_generators.py` | 272 |
| `test_keep_strategy_wired_from_config` | Method | `tests/core/test_generators.py` | 285 |
| `_make_config` | Method | `tests/core/test_generators.py` | 233 |
| `_client` | Method | `tests/core/test_generators.py` | 243 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Integration | 3 calls |

## How to Explore

1. `context({name: "test_thresholds_and_fields_wired_from_config"})` — see callers and callees
2. `query({search_query: "cluster_72"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
