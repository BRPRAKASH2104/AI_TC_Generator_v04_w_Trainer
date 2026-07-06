---
name: fastapi
description: "Skill for the Fastapi area of AI_TC_Generator_v04_w_Trainer. 56 symbols across 14 files."
---

# Fastapi

56 symbols | 14 files | Cohesion: 60%

## When to Use

- Working with code in `evaluate/`
- Understanding how decorator, Default, get_parameterless_sub_dependant work
- Modifying fastapi-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/fastapi/fastapi/routing.py` | __init__, get_request_handler, __init__, __init__, get_route_handler (+21) |
| `evaluate/test_repos/fastapi/fastapi/applications.py` | __init__, add_api_route, api_route, decorator, put (+6) |
| `evaluate/test_repos/fastapi/tests/test_router_events.py` | test_router_nested_lifespan_state, test_merged_mixed_state_lifespans, test_router_events, test_router_async_shutdown_handler |
| `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | get_parameterless_sub_dependant, get_dependant, _should_embed_body_fields |
| `evaluate/test_repos/fastapi/fastapi/datastructures.py` | Default, read |
| `evaluate/test_repos/fastapi/fastapi/exception_handlers.py` | request_validation_exception_handler, websocket_request_validation_exception_handler |
| `evaluate/test_repos/fastapi/docs_src/handling_errors/tutorial005_py310.py` | validation_exception_handler |
| `evaluate/test_repos/fastapi/fastapi/encoders.py` | jsonable_encoder |
| `evaluate/test_repos/fastapi/fastapi/exceptions.py` | errors |
| `evaluate/test_repos/fastapi/tests/test_jsonable_encoder.py` | test_custom_enum_encoders |

## Entry Points

Start here when exploring this area:

- **`decorator`** (Function) — `evaluate/test_repos/fastapi/fastapi/applications.py:1250`
- **`Default`** (Function) — `evaluate/test_repos/fastapi/fastapi/datastructures.py:173`
- **`get_parameterless_sub_dependant`** (Function) — `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py:122`
- **`get_dependant`** (Function) — `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py:285`
- **`get_request_handler`** (Function) — `evaluate/test_repos/fastapi/fastapi/routing.py:350`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `decorator` | Function | `evaluate/test_repos/fastapi/fastapi/applications.py` | 1250 |
| `Default` | Function | `evaluate/test_repos/fastapi/fastapi/datastructures.py` | 173 |
| `get_parameterless_sub_dependant` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 122 |
| `get_dependant` | Function | `evaluate/test_repos/fastapi/fastapi/dependencies/utils.py` | 285 |
| `get_request_handler` | Function | `evaluate/test_repos/fastapi/fastapi/routing.py` | 350 |
| `validation_exception_handler` | Function | `evaluate/test_repos/fastapi/docs_src/handling_errors/tutorial005_py310.py` | 10 |
| `jsonable_encoder` | Function | `evaluate/test_repos/fastapi/fastapi/encoders.py` | 111 |
| `request_validation_exception_handler` | Function | `evaluate/test_repos/fastapi/fastapi/exception_handlers.py` | 19 |
| `websocket_request_validation_exception_handler` | Function | `evaluate/test_repos/fastapi/fastapi/exception_handlers.py` | 28 |
| `test_custom_enum_encoders` | Function | `evaluate/test_repos/fastapi/tests/test_jsonable_encoder.py` | 227 |
| `get_value_or_default` | Function | `evaluate/test_repos/fastapi/fastapi/utils.py` | 120 |
| `test_subrouter_top_level_include_overrides_generate_unique_id` | Function | `evaluate/test_repos/fastapi/tests/test_generate_unique_id_function.py` | 661 |
| `test_router_nested_lifespan_state` | Function | `evaluate/test_repos/fastapi/tests/test_router_events.py` | 113 |
| `test_merged_mixed_state_lifespans` | Function | `evaluate/test_repos/fastapi/tests/test_router_events.py` | 221 |
| `app` | Function | `evaluate/test_repos/fastapi/fastapi/routing.py` | 109 |
| `run_endpoint_function` | Function | `evaluate/test_repos/fastapi/fastapi/routing.py` | 319 |
| `serialize_response` | Function | `evaluate/test_repos/fastapi/fastapi/routing.py` | 276 |
| `test_router_events` | Function | `evaluate/test_repos/fastapi/tests/test_router_events.py` | 26 |
| `test_router_async_shutdown_handler` | Function | `evaluate/test_repos/fastapi/tests/test_router_events.py` | 247 |
| `decorator` | Function | `evaluate/test_repos/fastapi/fastapi/routing.py` | 1323 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 10 calls |
| Dependencies | 8 calls |
| Integration | 2 calls |
| Openapi | 2 calls |

## How to Explore

1. `context({name: "decorator"})` — see callers and callees
2. `query({search_query: "fastapi"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
