---
name: cluster-44
description: "Skill for the Cluster_44 area of AI_TC_Generator_v04_w_Trainer. 8 symbols across 3 files."
---

# Cluster_44

8 symbols | 3 files | Cohesion: 61%

## When to Use

- Working with code in `src/`
- Understanding how add_requirement_failure, add_ai_response_time, test_calculate_confidence work
- Modifying cluster_44-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/core/generators.py` | extract_image_paths, calculate_confidence, generate_test_cases, _generate_test_cases_for_requirement_async |
| `src/file_processing_logger.py` | RequirementFailure, add_requirement_failure, add_ai_response_time |
| `tests/core/test_ollama_logprobs.py` | test_calculate_confidence |

## Entry Points

Start here when exploring this area:

- **`add_requirement_failure`** (Function) — `src/file_processing_logger.py:145`
- **`add_ai_response_time`** (Function) — `src/file_processing_logger.py:150`
- **`test_calculate_confidence`** (Function) — `tests/core/test_ollama_logprobs.py:31`
- **`extract_image_paths`** (Function) — `src/core/generators.py:28`
- **`calculate_confidence`** (Function) — `src/core/generators.py:55`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `RequirementFailure` | Class | `src/file_processing_logger.py` | 42 |
| `add_requirement_failure` | Function | `src/file_processing_logger.py` | 145 |
| `add_ai_response_time` | Function | `src/file_processing_logger.py` | 150 |
| `test_calculate_confidence` | Function | `tests/core/test_ollama_logprobs.py` | 31 |
| `extract_image_paths` | Function | `src/core/generators.py` | 28 |
| `calculate_confidence` | Function | `src/core/generators.py` | 55 |
| `generate_test_cases` | Function | `src/core/generators.py` | 289 |
| `_generate_test_cases_for_requirement_async` | Function | `src/core/generators.py` | 384 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Generate_test_cases → Format_table` | cross_community | 5 |
| `Generate_test_cases → Format_info_list` | cross_community | 5 |
| `Generate_test_cases → Format_interfaces` | cross_community | 5 |
| `Generate_test_cases → Format_image_context` | cross_community | 5 |
| `Generate_test_cases_batch → Format_table` | cross_community | 5 |
| `Generate_test_cases_batch → Format_info_list` | cross_community | 5 |
| `Generate_test_cases_batch → Format_interfaces` | cross_community | 5 |
| `Generate_test_cases_batch → Format_image_context` | cross_community | 5 |
| `Generate_test_cases → Extract_image_paths` | intra_community | 3 |
| `Generate_test_cases → Calculate_confidence` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 1 calls |
| Cluster_80 | 1 calls |
| Cluster_89 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "add_requirement_failure"})` — see callers and callees
2. `gitnexus_query({query: "cluster_44"})` — find related execution flows
3. Read key files listed above for implementation details
