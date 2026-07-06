---
name: security
description: "Skill for the Security area of AI_TC_Generator_v04_w_Trainer. 34 symbols across 11 files."
---

# Security

34 symbols | 11 files | Cohesion: 95%

## When to Use

- Working with code in `evaluate/`
- Understanding how get_user, authenticate_user, get_current_user work
- Modifying security-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/fastapi/fastapi/security/http.py` | HTTPBase, HTTPBearer, make_not_authenticated_error, __call__, __call__ (+1) |
| `evaluate/test_repos/fastapi/fastapi/security/oauth2.py` | OAuth2, __init__, __init__, make_not_authenticated_error, __call__ (+1) |
| `evaluate/test_repos/fastapi/docs_src/security/tutorial004_py310.py` | get_user, authenticate_user, get_current_user, get_current_active_user, login_for_access_token |
| `evaluate/test_repos/fastapi/docs_src/security/tutorial005_py310.py` | get_user, authenticate_user, get_current_user, login_for_access_token |
| `evaluate/test_repos/fastapi/docs_src/security/tutorial003_py310.py` | fake_decode_token, get_current_user, get_current_active_user |
| `evaluate/test_repos/fastapi/docs_src/security/tutorial004_an_py310.py` | get_user, authenticate_user, login_for_access_token |
| `evaluate/test_repos/fastapi/docs_src/security/tutorial005_an_py310.py` | get_user, authenticate_user, login_for_access_token |
| `evaluate/test_repos/fastapi/fastapi/security/api_key.py` | APIKeyBase |
| `evaluate/test_repos/fastapi/fastapi/security/base.py` | SecurityBase |
| `evaluate/test_repos/fastapi/fastapi/security/utils.py` | get_authorization_scheme_param |

## Entry Points

Start here when exploring this area:

- **`get_user`** (Function) — `evaluate/test_repos/fastapi/docs_src/security/tutorial004_py310.py:64`
- **`authenticate_user`** (Function) — `evaluate/test_repos/fastapi/docs_src/security/tutorial004_py310.py:70`
- **`get_current_user`** (Function) — `evaluate/test_repos/fastapi/docs_src/security/tutorial004_py310.py:91`
- **`get_current_active_user`** (Function) — `evaluate/test_repos/fastapi/docs_src/security/tutorial004_py310.py:111`
- **`login_for_access_token`** (Function) — `evaluate/test_repos/fastapi/docs_src/security/tutorial004_py310.py:118`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `APIKeyBase` | Class | `evaluate/test_repos/fastapi/fastapi/security/api_key.py` | 10 |
| `SecurityBase` | Class | `evaluate/test_repos/fastapi/fastapi/security/base.py` | 3 |
| `HTTPBase` | Class | `evaluate/test_repos/fastapi/fastapi/security/http.py` | 68 |
| `HTTPBearer` | Class | `evaluate/test_repos/fastapi/fastapi/security/http.py` | 221 |
| `OAuth2` | Class | `evaluate/test_repos/fastapi/fastapi/security/oauth2.py` | 329 |
| `get_user` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial004_py310.py` | 64 |
| `authenticate_user` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial004_py310.py` | 70 |
| `get_current_user` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial004_py310.py` | 91 |
| `get_current_active_user` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial004_py310.py` | 111 |
| `login_for_access_token` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial004_py310.py` | 118 |
| `get_authorization_scheme_param` | Function | `evaluate/test_repos/fastapi/fastapi/security/utils.py` | 0 |
| `get_user` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial005_py310.py` | 79 |
| `authenticate_user` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial005_py310.py` | 85 |
| `get_current_user` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial005_py310.py` | 106 |
| `login_for_access_token` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial005_py310.py` | 150 |
| `fake_decode_token` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial003_py310.py` | 48 |
| `get_current_user` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial003_py310.py` | 55 |
| `get_current_active_user` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial003_py310.py` | 66 |
| `get_user` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial004_an_py310.py` | 65 |
| `authenticate_user` | Function | `evaluate/test_repos/fastapi/docs_src/security/tutorial004_an_py310.py` | 71 |

## How to Explore

1. `context({name: "get_user"})` — see callers and callees
2. `query({search_query: "security"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
