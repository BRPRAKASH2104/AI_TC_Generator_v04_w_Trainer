---
name: dependencies
description: "Skill for the Dependencies area of AI_TC_Generator_v04_w_Trainer. 26 symbols across 4 files."
---

# Dependencies

26 symbols | 4 files | Cohesion: 77%

## When to Use

- Working with code in `evaluate/`
- Understanding how solve_dependencies, request_params_to_args, request_body_to_args work
- Modifying dependencies-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | _solve_generator, solve_dependencies, _validate_value_with_model_field, _get_multidict_value, request_params_to_args (+12) |
| `evaluate/test_repos/fastapi/fastapi/dependencies/models.py` | _unwrapped_call, _impartial, is_gen_callable, is_async_gen_callable, is_coroutine_callable |
| `evaluate/test_repos/fastapi/fastapi/openapi/utils.py` | _get_openapi_operation_parameters, get_fields_from_routes, get_openapi |
| `evaluate/test_repos/fastapi/fastapi/utils.py` | create_model_field |

## Entry Points

Start here when exploring this area:

- **`solve_dependencies`** (Function) — `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py:597`
- **`request_params_to_args`** (Function) — `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py:783`
- **`request_body_to_args`** (Function) — `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py:950`
- **`get_validation_alias`** (Function) — `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py:1054`
- **`get_flat_dependant`** (Function) — `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py:137`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `solve_dependencies` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 597 |
| `request_params_to_args` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 783 |
| `request_body_to_args` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 950 |
| `get_validation_alias` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 1054 |
| `get_flat_dependant` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 137 |
| `get_flat_params` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 203 |
| `get_fields_from_routes` | Function | `evaluate/test_repos/fastapi/fastapi/openapi/utils.py` | 480 |
| `get_openapi` | Function | `evaluate/test_repos/fastapi/fastapi/openapi/utils.py` | 513 |
| `get_typed_signature` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 227 |
| `get_typed_annotation` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 244 |
| `get_typed_return_annotation` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 253 |
| `analyze_param` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 392 |
| `get_body_field` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 1000 |
| `create_model_field` | Function | `evaluate/test_repos/fastapi/fastapi/utils.py` | 57 |
| `is_gen_callable` | Method | `evaluate/test_repos/fastapi/fastapi/dependencies/models.py` | 105 |
| `is_async_gen_callable` | Method | `evaluate/test_repos/fastapi/fastapi/dependencies/models.py` | 131 |
| `is_coroutine_callable` | Method | `evaluate/test_repos/fastapi/fastapi/dependencies/models.py` | 157 |
| `_solve_generator` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 577 |
| `_validate_value_with_model_field` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 737 |
| `_get_multidict_value` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 752 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Fastapi | 4 calls |
| Openapi | 1 calls |

## How to Explore

1. `context({name: "solve_dependencies"})` — see callers and callees
2. `query({search_query: "dependencies"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
