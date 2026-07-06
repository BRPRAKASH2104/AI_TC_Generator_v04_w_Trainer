---
name: compat
description: "Skill for the _compat area of AI_TC_Generator_v04_w_Trainer. 20 symbols across 2 files."
---

# _compat

20 symbols | 2 files | Cohesion: 77%

## When to Use

- Working with code in `evaluate/`
- Understanding how get_definitions, get_model_fields, get_flat_models_from_model work
- Modifying _compat-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | lenient_issubclass, _annotation_is_sequence, _annotation_is_complex, is_uploadfile_or_nonable_uploadfile_annotation, is_uploadfile_sequence_annotation (+8) |
| `evaluate/test_repos/fastapi/fastapi/_compat/v2.py` | _has_computed_fields, get_definitions, get_model_fields, get_flat_models_from_model, get_flat_models_from_annotation (+2) |

## Entry Points

Start here when exploring this area:

- **`get_definitions`** (Function) — `evaluate/test_repos/fastapi/fastapi/_compat/v2.py:271`
- **`get_model_fields`** (Function) — `evaluate/test_repos/fastapi/fastapi/_compat/v2.py:381`
- **`get_flat_models_from_model`** (Function) — `evaluate/test_repos/fastapi/fastapi/_compat/v2.py:423`
- **`get_flat_models_from_annotation`** (Function) — `evaluate/test_repos/fastapi/fastapi/_compat/v2.py:432`
- **`get_flat_models_from_field`** (Function) — `evaluate/test_repos/fastapi/fastapi/_compat/v2.py:448`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `get_definitions` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/v2.py` | 271 |
| `get_model_fields` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/v2.py` | 381 |
| `get_flat_models_from_model` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/v2.py` | 423 |
| `get_flat_models_from_annotation` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/v2.py` | 432 |
| `get_flat_models_from_field` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/v2.py` | 448 |
| `get_flat_models_from_fields` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/v2.py` | 464 |
| `lenient_issubclass` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 46 |
| `is_uploadfile_or_nonable_uploadfile_annotation` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 136 |
| `is_uploadfile_sequence_annotation` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 162 |
| `field_annotation_is_sequence` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 63 |
| `is_bytes_or_nonable_bytes_annotation` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 125 |
| `is_bytes_sequence_annotation` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 147 |
| `is_pydantic_v1_model_class` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 189 |
| `annotation_is_pydantic_v1` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 201 |
| `field_annotation_is_complex` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 87 |
| `field_annotation_is_scalar` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 103 |
| `field_annotation_is_scalar_sequence` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 108 |
| `_has_computed_fields` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/v2.py` | 233 |
| `_annotation_is_sequence` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 57 |
| `_annotation_is_complex` | Function | `evaluate/test_repos/fastapi/fastapi/_compat/shared.py` | 79 |

## How to Explore

1. `context({name: "get_definitions"})` — see callers and callees
2. `query({search_query: "_compat"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
