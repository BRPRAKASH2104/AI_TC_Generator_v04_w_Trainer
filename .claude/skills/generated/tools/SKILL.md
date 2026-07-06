---
name: tools
description: "Skill for the Tools area of AI_TC_Generator_v04_w_Trainer. 26 symbols across 11 files."
---

# Tools

26 symbols | 11 files | Cohesion: 68%

## When to Use

- Working with code in `src/`
- Understanding how test_template_rendering, test_auto_selection, generate_sample_outputs work
- Modifying tools-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/yaml_prompt_manager.py` | get_test_prompt, _substitute_variables, list_templates, get_template_info, __init__ (+5) |
| `prompts/tools/validation_and_tools.py` | test_template_rendering, test_auto_selection, generate_sample_outputs, main, validate_all_templates |
| `evaluate/test_repos/nextjs/code_review_graph/tools/community_tools.py` | list_communities_func, get_community_func |
| `evaluate/test_repos/nextjs/code_review_graph/tools/query.py` | query_graph, find_large_functions |
| `main.py` | _validate_templates |
| `evaluate/test_repos/nextjs/code_review_graph/eval/token_benchmark.py` | benchmark_architecture_workflow |
| `evaluate/test_repos/nextjs/code_review_graph/tools/context.py` | get_minimal_context |
| `evaluate/test_repos/nextjs/code_review_graph/tools/flows_tools.py` | list_flows |
| `evaluate/test_repos/nextjs/tests/test_tools.py` | test_output_is_compact |
| `evaluate/test_repos/nextjs/code_review_graph/graph.py` | node_to_dict |

## Entry Points

Start here when exploring this area:

- **`test_template_rendering`** (Function) — `prompts/tools/validation_and_tools.py:60`
- **`test_auto_selection`** (Function) — `prompts/tools/validation_and_tools.py:113`
- **`generate_sample_outputs`** (Function) — `prompts/tools/validation_and_tools.py:167`
- **`main`** (Function) — `prompts/tools/validation_and_tools.py:232`
- **`validate_all_templates`** (Function) — `prompts/tools/validation_and_tools.py:16`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_template_rendering` | Function | `prompts/tools/validation_and_tools.py` | 60 |
| `test_auto_selection` | Function | `prompts/tools/validation_and_tools.py` | 113 |
| `generate_sample_outputs` | Function | `prompts/tools/validation_and_tools.py` | 167 |
| `main` | Function | `prompts/tools/validation_and_tools.py` | 232 |
| `validate_all_templates` | Function | `prompts/tools/validation_and_tools.py` | 16 |
| `benchmark_architecture_workflow` | Function | `evaluate/test_repos/nextjs/code_review_graph/eval/token_benchmark.py` | 47 |
| `list_communities_func` | Function | `evaluate/test_repos/nextjs/code_review_graph/tools/community_tools.py` | 16 |
| `get_minimal_context` | Function | `evaluate/test_repos/nextjs/code_review_graph/tools/context.py` | 35 |
| `list_flows` | Function | `evaluate/test_repos/nextjs/code_review_graph/tools/flows_tools.py` | 16 |
| `node_to_dict` | Function | `evaluate/test_repos/nextjs/code_review_graph/graph.py` | 1006 |
| `get_community_func` | Function | `evaluate/test_repos/nextjs/code_review_graph/tools/community_tools.py` | 70 |
| `query_graph` | Function | `evaluate/test_repos/nextjs/code_review_graph/tools/query.py` | 138 |
| `find_large_functions` | Function | `evaluate/test_repos/nextjs/code_review_graph/tools/query.py` | 485 |
| `get_test_prompt` | Method | `src/yaml_prompt_manager.py` | 154 |
| `list_templates` | Method | `src/yaml_prompt_manager.py` | 288 |
| `get_template_info` | Method | `src/yaml_prompt_manager.py` | 295 |
| `load_configuration` | Method | `src/yaml_prompt_manager.py` | 90 |
| `load_all_prompts` | Method | `src/yaml_prompt_manager.py` | 118 |
| `validate_template_file` | Method | `src/yaml_prompt_manager.py` | 325 |
| `test_output_is_compact` | Method | `evaluate/test_repos/nextjs/tests/test_tools.py` | 798 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _resolve_config_path` | cross_community | 4 |
| `Main → _auto_select_template` | intra_community | 4 |
| `Main → _validate_variables` | intra_community | 4 |
| `Main → _apply_defaults` | intra_community | 4 |
| `Main → _substitute_variables` | intra_community | 4 |
| `Main → List_templates` | intra_community | 3 |
| `Main → Get_selected_template` | intra_community | 3 |
| `Generate_sample_outputs → _validate_variables` | intra_community | 3 |
| `Generate_sample_outputs → _apply_defaults` | intra_community | 3 |
| `Generate_sample_outputs → _substitute_variables` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Code_review_graph | 12 calls |
| Tests | 4 calls |
| Integration | 1 calls |
| Eval | 1 calls |

## How to Explore

1. `context({name: "test_template_rendering"})` — see callers and callees
2. `query({search_query: "tools"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
