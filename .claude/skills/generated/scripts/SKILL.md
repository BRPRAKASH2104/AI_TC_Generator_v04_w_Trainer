---
name: scripts
description: "Skill for the Scripts area of AI_TC_Generator_v04_w_Trainer. 53 symbols across 9 files."
---

# Scripts

53 symbols | 9 files | Cohesion: 83%

## When to Use

- Working with code in `evaluate/`
- Understanding how get_graphql_response, get_graphql_translation_discussions, get_graphql_translation_discussion_comments_edges work
- Modifying scripts-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/fastapi/scripts/translate.py` | get_langs, get_llm_translatable, llm_translatable_json, list_removable, list_all_removable (+9) |
| `evaluate/test_repos/fastapi/scripts/doc_parsing_utils.py` | extract_code_includes, replace_code_includes_with_placeholders, extract_multiline_code_blocks, replace_multiline_code_block, replace_multiline_code_blocks_in_text (+6) |
| `evaluate/test_repos/fastapi/scripts/notify_translations.py` | get_graphql_response, get_graphql_translation_discussions, get_graphql_translation_discussion_comments_edges, get_graphql_translation_discussion_comments, create_comment (+2) |
| `evaluate/test_repos/fastapi/scripts/docs.py` | get_en_config, update_languages, get_updated_config_content, get_lang_paths, build_all (+1) |
| `evaluate/test_repos/fastapi/scripts/contributors.py` | get_graphql_pr_edges, get_pr_nodes, main |
| `evaluate/test_repos/fastapi/scripts/mkdocs_hooks.py` | resolve_file, resolve_files, on_files |
| `evaluate/test_repos/fastapi/scripts/people.py` | get_graphql_question_discussion_edges, get_discussion_nodes, main |
| `evaluate/test_repos/fastapi/scripts/sponsors.py` | get_graphql_sponsor_edges, get_individual_sponsors, main |
| `evaluate/test_repos/fastapi/scripts/translation_fixer.py` | get_all_paths, process_one_page, fix_all |

## Entry Points

Start here when exploring this area:

- **`get_graphql_response`** (Function) — `evaluate/test_repos/fastapi/scripts/notify_translations.py:197`
- **`get_graphql_translation_discussions`** (Function) — `evaluate/test_repos/fastapi/scripts/notify_translations.py:238`
- **`get_graphql_translation_discussion_comments_edges`** (Function) — `evaluate/test_repos/fastapi/scripts/notify_translations.py:250`
- **`get_graphql_translation_discussion_comments`** (Function) — `evaluate/test_repos/fastapi/scripts/notify_translations.py:263`
- **`create_comment`** (Function) — `evaluate/test_repos/fastapi/scripts/notify_translations.py:283`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `get_graphql_response` | Function | `evaluate/test_repos/fastapi/scripts/notify_translations.py` | 197 |
| `get_graphql_translation_discussions` | Function | `evaluate/test_repos/fastapi/scripts/notify_translations.py` | 238 |
| `get_graphql_translation_discussion_comments_edges` | Function | `evaluate/test_repos/fastapi/scripts/notify_translations.py` | 250 |
| `get_graphql_translation_discussion_comments` | Function | `evaluate/test_repos/fastapi/scripts/notify_translations.py` | 263 |
| `create_comment` | Function | `evaluate/test_repos/fastapi/scripts/notify_translations.py` | 283 |
| `update_comment` | Function | `evaluate/test_repos/fastapi/scripts/notify_translations.py` | 294 |
| `main` | Function | `evaluate/test_repos/fastapi/scripts/notify_translations.py` | 305 |
| `extract_code_includes` | Function | `evaluate/test_repos/fastapi/scripts/doc_parsing_utils.py` | 80 |
| `replace_code_includes_with_placeholders` | Function | `evaluate/test_repos/fastapi/scripts/doc_parsing_utils.py` | 96 |
| `extract_multiline_code_blocks` | Function | `evaluate/test_repos/fastapi/scripts/doc_parsing_utils.py` | 481 |
| `replace_multiline_code_block` | Function | `evaluate/test_repos/fastapi/scripts/doc_parsing_utils.py` | 569 |
| `replace_multiline_code_blocks_in_text` | Function | `evaluate/test_repos/fastapi/scripts/doc_parsing_utils.py` | 642 |
| `check_translation` | Function | `evaluate/test_repos/fastapi/scripts/doc_parsing_utils.py` | 675 |
| `replace_markdown_links` | Function | `evaluate/test_repos/fastapi/scripts/doc_parsing_utils.py` | 309 |
| `replace_html_links` | Function | `evaluate/test_repos/fastapi/scripts/doc_parsing_utils.py` | 432 |
| `get_langs` | Function | `evaluate/test_repos/fastapi/scripts/translate.py` | 35 |
| `get_llm_translatable` | Function | `evaluate/test_repos/fastapi/scripts/translate.py` | 210 |
| `llm_translatable_json` | Function | `evaluate/test_repos/fastapi/scripts/translate.py` | 230 |
| `list_removable` | Function | `evaluate/test_repos/fastapi/scripts/translate.py` | 270 |
| `list_all_removable` | Function | `evaluate/test_repos/fastapi/scripts/translate.py` | 282 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Integration | 3 calls |

## How to Explore

1. `context({name: "get_graphql_response"})` — see callers and callees
2. `query({search_query: "scripts"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
