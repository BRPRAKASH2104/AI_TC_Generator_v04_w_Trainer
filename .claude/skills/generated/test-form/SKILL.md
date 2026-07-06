---
name: test-form
description: "Skill for the Test_form area of AI_TC_Generator_v04_w_Trainer. 18 symbols across 6 files."
---

# Test_form

18 symbols | 6 files | Cohesion: 65%

## When to Use

- Working with code in `evaluate/`
- Understanding how test_required_list_str_schema, test_required_list_str_alias_schema, test_required_list_validation_alias_schema work
- Modifying test_form-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_list.py` | test_required_list_str_schema, test_required_list_str_alias_schema, test_required_list_validation_alias_schema, test_required_list_alias_and_validation_alias_schema |
| `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_optional_list.py` | test_optional_list_str_schema, test_optional_list_str_alias_schema, test_optional_list_validation_alias_schema, test_optional_list_alias_and_validation_alias_schema |
| `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_optional_str.py` | test_optional_str_schema, test_optional_str_alias_schema, test_optional_validation_alias_schema, test_optional_alias_and_validation_alias_schema |
| `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_required_str.py` | test_required_str_schema, test_required_str_alias_schema, test_required_validation_alias_schema, test_required_alias_and_validation_alias_schema |
| `evaluate/test_repos/fastapi/fastapi/applications.py` | openapi |
| `evaluate/test_repos/fastapi/tests/test_request_params/test_form/utils.py` | get_body_model_name |

## Entry Points

Start here when exploring this area:

- **`test_required_list_str_schema`** (Function) — `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_list.py:34`
- **`test_required_list_str_alias_schema`** (Function) — `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_list.py:110`
- **`test_required_list_validation_alias_schema`** (Function) — `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_list.py:213`
- **`test_required_list_alias_and_validation_alias_schema`** (Function) — `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_list.py:328`
- **`test_optional_list_str_schema`** (Function) — `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_optional_list.py:35`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_required_list_str_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_list.py` | 34 |
| `test_required_list_str_alias_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_list.py` | 110 |
| `test_required_list_validation_alias_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_list.py` | 213 |
| `test_required_list_alias_and_validation_alias_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_list.py` | 328 |
| `test_optional_list_str_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_optional_list.py` | 35 |
| `test_optional_list_str_alias_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_optional_list.py` | 105 |
| `test_optional_list_validation_alias_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_optional_list.py` | 188 |
| `test_optional_list_alias_and_validation_alias_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_optional_list.py` | 280 |
| `test_optional_str_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_optional_str.py` | 33 |
| `test_optional_str_alias_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_optional_str.py` | 98 |
| `test_optional_validation_alias_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_optional_str.py` | 175 |
| `test_optional_alias_and_validation_alias_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_optional_str.py` | 267 |
| `test_required_str_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_required_str.py` | 34 |
| `test_required_str_alias_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_required_str.py` | 104 |
| `test_required_validation_alias_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_required_str.py` | 197 |
| `test_required_alias_and_validation_alias_schema` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/test_required_str.py` | 311 |
| `get_body_model_name` | Function | `evaluate/test_repos/fastapi/tests/test_request_params/test_form/utils.py` | 3 |
| `openapi` | Method | `evaluate/test_repos/fastapi/fastapi/applications.py` | 1071 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 4 calls |
| Dependencies | 1 calls |

## How to Explore

1. `context({name: "test_required_list_str_schema"})` — see callers and callees
2. `query({search_query: "test_form"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
