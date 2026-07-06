---
name: sansio
description: "Skill for the Sansio area of AI_TC_Generator_v04_w_Trainer. 31 symbols across 5 files."
---

# Sansio

31 symbols | 5 files | Cohesion: 88%

## When to Use

- Working with code in `evaluate/`
- Understanding how find_package, decorator, setupmethod work
- Modifying sansio-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/flask/src/flask/sansio/blueprints.py` | __init__, record, record_once, decorator, add_app_template_filter (+6) |
| `evaluate/test_repos/flask/src/flask/sansio/app.py` | __init__, make_config, make_aborter, auto_find_instance_path, App (+5) |
| `evaluate/test_repos/flask/src/flask/sansio/scaffold.py` | __init__, find_package, setupmethod, Scaffold, _endpoint_from_view_func (+3) |
| `evaluate/test_repos/flask/src/flask/blueprints.py` | Blueprint |
| `evaluate/test_repos/flask/src/flask/app.py` | __init__ |

## Entry Points

Start here when exploring this area:

- **`find_package`** (Function) — `evaluate/test_repos/flask/src/flask/sansio/scaffold.py:753`
- **`decorator`** (Function) — `evaluate/test_repos/flask/src/flask/sansio/blueprints.py:468`
- **`setupmethod`** (Function) — `evaluate/test_repos/flask/src/flask/sansio/scaffold.py:41`
- **`decorator`** (Function) — `evaluate/test_repos/flask/src/flask/sansio/app.py:688`
- **`decorator`** (Function) — `evaluate/test_repos/flask/src/flask/sansio/scaffold.py:359`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `Blueprint` | Class | `evaluate/test_repos/flask/src/flask/blueprints.py` | 17 |
| `App` | Class | `evaluate/test_repos/flask/src/flask/sansio/app.py` | 58 |
| `Blueprint` | Class | `evaluate/test_repos/flask/src/flask/sansio/blueprints.py` | 118 |
| `Scaffold` | Class | `evaluate/test_repos/flask/src/flask/sansio/scaffold.py` | 51 |
| `find_package` | Function | `evaluate/test_repos/flask/src/flask/sansio/scaffold.py` | 753 |
| `decorator` | Function | `evaluate/test_repos/flask/src/flask/sansio/blueprints.py` | 468 |
| `setupmethod` | Function | `evaluate/test_repos/flask/src/flask/sansio/scaffold.py` | 41 |
| `decorator` | Function | `evaluate/test_repos/flask/src/flask/sansio/app.py` | 688 |
| `decorator` | Function | `evaluate/test_repos/flask/src/flask/sansio/scaffold.py` | 359 |
| `make_config` | Method | `evaluate/test_repos/flask/src/flask/sansio/app.py` | 478 |
| `make_aborter` | Method | `evaluate/test_repos/flask/src/flask/sansio/app.py` | 494 |
| `auto_find_instance_path` | Method | `evaluate/test_repos/flask/src/flask/sansio/app.py` | 506 |
| `record` | Method | `evaluate/test_repos/flask/src/flask/sansio/blueprints.py` | 223 |
| `record_once` | Method | `evaluate/test_repos/flask/src/flask/sansio/blueprints.py` | 232 |
| `add_app_template_filter` | Method | `evaluate/test_repos/flask/src/flask/sansio/blueprints.py` | 475 |
| `add_app_template_test` | Method | `evaluate/test_repos/flask/src/flask/sansio/blueprints.py` | 531 |
| `add_app_template_global` | Method | `evaluate/test_repos/flask/src/flask/sansio/blueprints.py` | 589 |
| `add_template_filter` | Method | `evaluate/test_repos/flask/src/flask/sansio/app.py` | 695 |
| `add_template_test` | Method | `evaluate/test_repos/flask/src/flask/sansio/app.py` | 752 |
| `add_template_global` | Method | `evaluate/test_repos/flask/src/flask/sansio/app.py` | 806 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Flask | 2 calls |

## How to Explore

1. `context({name: "find_package"})` — see callers and callees
2. `query({search_query: "sansio"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
