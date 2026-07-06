---
name: httpx
description: "Skill for the Httpx area of AI_TC_Generator_v04_w_Trainer. 138 symbols across 14 files."
---

# Httpx

138 symbols | 14 files | Cohesion: 71%

## When to Use

- Working with code in `evaluate/`
- Understanding how format_response_headers, print_request_headers, print_response_headers work
- Modifying httpx-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/httpx/httpx/_client.py` | _set_timeout, stream, send, _send_handling_auth, _send_handling_redirects (+25) |
| `evaluate/test_repos/httpx/httpx/_models.py` | text, iter_text, aiter_text, read, close (+22) |
| `evaluate/test_repos/httpx/httpx/_urls.py` | copy_set_param, set, __init__, copy_with, copy_remove_param (+11) |
| `evaluate/test_repos/httpx/httpx/_multipart.py` | MultipartStream, _format_form_param, render_headers, render_data, render (+6) |
| `evaluate/test_repos/httpx/httpx/_decoders.py` | decode, flush, decode, flush, decode (+5) |
| `evaluate/test_repos/httpx/httpx/_auth.py` | sync_auth_flow, auth_flow, _parse_challenge, _build_auth_header, _get_header_value (+4) |
| `evaluate/test_repos/httpx/httpx/_content.py` | ByteStream, UnattachedStream, encode_urlencoded_data, encode_content, encode_multipart_data (+3) |
| `evaluate/test_repos/httpx/httpx/_exceptions.py` | HTTPError, RequestError, TransportError, TimeoutException, NetworkError (+2) |
| `evaluate/test_repos/httpx/httpx/_main.py` | format_response_headers, print_request_headers, print_response_headers, trace, print_response (+2) |
| `evaluate/test_repos/httpx/httpx/_utils.py` | get_environment_proxies, primitive_value_to_str, to_bytes, peek_filelike_length, to_str |

## Entry Points

Start here when exploring this area:

- **`format_response_headers`** (Function) — `evaluate/test_repos/httpx/httpx/_main.py:128`
- **`print_request_headers`** (Function) — `evaluate/test_repos/httpx/httpx/_main.py:146`
- **`print_response_headers`** (Function) — `evaluate/test_repos/httpx/httpx/_main.py:155`
- **`trace`** (Function) — `evaluate/test_repos/httpx/httpx/_main.py:211`
- **`get_environment_proxies`** (Function) — `evaluate/test_repos/httpx/httpx/_utils.py:29`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `HTTPError` | Class | `evaluate/test_repos/httpx/httpx/_exceptions.py` | 73 |
| `RequestError` | Class | `evaluate/test_repos/httpx/httpx/_exceptions.py` | 106 |
| `TransportError` | Class | `evaluate/test_repos/httpx/httpx/_exceptions.py` | 122 |
| `TimeoutException` | Class | `evaluate/test_repos/httpx/httpx/_exceptions.py` | 131 |
| `NetworkError` | Class | `evaluate/test_repos/httpx/httpx/_exceptions.py` | 166 |
| `ProtocolError` | Class | `evaluate/test_repos/httpx/httpx/_exceptions.py` | 215 |
| `ByteStream` | Class | `evaluate/test_repos/httpx/httpx/_content.py` | 30 |
| `UnattachedStream` | Class | `evaluate/test_repos/httpx/httpx/_content.py` | 91 |
| `MultipartStream` | Class | `evaluate/test_repos/httpx/httpx/_multipart.py` | 223 |
| `SyncByteStream` | Class | `evaluate/test_repos/httpx/httpx/_types.py` | 91 |
| `AsyncByteStream` | Class | `evaluate/test_repos/httpx/httpx/_types.py` | 105 |
| `format_response_headers` | Function | `evaluate/test_repos/httpx/httpx/_main.py` | 128 |
| `print_request_headers` | Function | `evaluate/test_repos/httpx/httpx/_main.py` | 146 |
| `print_response_headers` | Function | `evaluate/test_repos/httpx/httpx/_main.py` | 155 |
| `trace` | Function | `evaluate/test_repos/httpx/httpx/_main.py` | 211 |
| `get_environment_proxies` | Function | `evaluate/test_repos/httpx/httpx/_utils.py` | 29 |
| `request_context` | Function | `evaluate/test_repos/httpx/httpx/_exceptions.py` | 364 |
| `encode_urlencoded_data` | Function | `evaluate/test_repos/httpx/httpx/_content.py` | 135 |
| `primitive_value_to_str` | Function | `evaluate/test_repos/httpx/httpx/_utils.py` | 14 |
| `print_response` | Function | `evaluate/test_repos/httpx/httpx/_main.py` | 169 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Integration | 2 calls |
| Tests | 1 calls |

## How to Explore

1. `context({name: "format_response_headers"})` — see callers and callees
2. `query({search_query: "httpx"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
