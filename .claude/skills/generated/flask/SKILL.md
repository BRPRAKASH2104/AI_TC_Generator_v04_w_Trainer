---
name: flask
description: "Skill for the Flask area of AI_TC_Generator_v04_w_Trainer. 90 symbols across 18 files."
---

# Flask

90 symbols | 18 files | Cohesion: 86%

## When to Use

- Working with code in `evaluate/`
- Understanding how make_response, view, wrapper work
- Modifying flask-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/flask/src/flask/app.py` | handle_http_exception, handle_user_exception, handle_exception, dispatch_request, full_dispatch_request (+17) |
| `evaluate/test_repos/flask/src/flask/cli.py` | _load_plugin_commands, get_command, prepare_import, load_app, run_command (+7) |
| `evaluate/test_repos/flask/src/flask/templating.py` | _render, render_template, render_template_string, get_source, _get_source_explained (+5) |
| `evaluate/test_repos/flask/src/flask/helpers.py` | make_response, get_debug_flag, get_load_dotenv, _prepare_send_file_kwargs, send_from_directory (+3) |
| `evaluate/test_repos/flask/src/flask/sessions.py` | get_cookie_name, get_signing_serializer, open_session, save_session, SessionMixin (+3) |
| `evaluate/test_repos/flask/src/flask/globals.py` | _get_current_object, ProxyMixin, FlaskProxy, AppContextProxy, _AppCtxGlobalsProxy (+2) |
| `evaluate/test_repos/flask/src/flask/ctx.py` | _get_session, match_request, push, __init__, pop (+1) |
| `evaluate/test_repos/flask/src/flask/views.py` | view, View, MethodView |
| `evaluate/test_repos/flask/src/flask/testing.py` | _copy_environ, _request_from_builder_args, open |
| `evaluate/test_repos/flask/src/flask/sansio/app.py` | _find_error_handler, inject_url_defaults |

## Entry Points

Start here when exploring this area:

- **`make_response`** (Function) — `evaluate/test_repos/flask/src/flask/helpers.py:150`
- **`view`** (Function) — `evaluate/test_repos/flask/src/flask/views.py:105`
- **`wrapper`** (Function) — `evaluate/test_repos/flask/src/flask/app.py:85`
- **`render_template`** (Function) — `evaluate/test_repos/flask/src/flask/templating.py:135`
- **`render_template_string`** (Function) — `evaluate/test_repos/flask/src/flask/templating.py:150`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `Flask` | Class | `evaluate/test_repos/flask/src/flask/app.py` | 108 |
| `ProxyMixin` | Class | `evaluate/test_repos/flask/src/flask/globals.py` | 16 |
| `FlaskProxy` | Class | `evaluate/test_repos/flask/src/flask/globals.py` | 21 |
| `AppContextProxy` | Class | `evaluate/test_repos/flask/src/flask/globals.py` | 23 |
| `RequestProxy` | Class | `evaluate/test_repos/flask/src/flask/globals.py` | 27 |
| `Request` | Class | `evaluate/test_repos/flask/src/flask/wrappers.py` | 17 |
| `SessionMixinProxy` | Class | `evaluate/test_repos/flask/src/flask/globals.py` | 29 |
| `SessionMixin` | Class | `evaluate/test_repos/flask/src/flask/sessions.py` | 23 |
| `SecureCookieSession` | Class | `evaluate/test_repos/flask/src/flask/sessions.py` | 56 |
| `View` | Class | `evaluate/test_repos/flask/src/flask/views.py` | 15 |
| `MethodView` | Class | `evaluate/test_repos/flask/src/flask/views.py` | 137 |
| `BaseView` | Class | `evaluate/test_repos/flask/tests/test_views.py` | 201 |
| `SessionInterface` | Class | `evaluate/test_repos/flask/src/flask/sessions.py` | 99 |
| `SecureCookieSessionInterface` | Class | `evaluate/test_repos/flask/src/flask/sessions.py` | 283 |
| `make_response` | Function | `evaluate/test_repos/flask/src/flask/helpers.py` | 150 |
| `view` | Function | `evaluate/test_repos/flask/src/flask/views.py` | 105 |
| `wrapper` | Function | `evaluate/test_repos/flask/src/flask/app.py` | 85 |
| `render_template` | Function | `evaluate/test_repos/flask/src/flask/templating.py` | 135 |
| `render_template_string` | Function | `evaluate/test_repos/flask/src/flask/templating.py` | 150 |
| `prepare_import` | Function | `evaluate/test_repos/flask/src/flask/cli.py` | 199 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Sansio | 1 calls |

## How to Explore

1. `context({name: "make_response"})` — see callers and callees
2. `query({search_query: "flask"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
