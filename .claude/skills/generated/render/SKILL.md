---
name: render
description: "Skill for the Render area of AI_TC_Generator_v04_w_Trainer. 60 symbols across 15 files."
---

# Render

60 symbols | 15 files | Cohesion: 80%

## When to Use

- Working with code in `evaluate/`
- Understanding how TestRenderJSON, TestRenderIndentedJSON, TestRenderSecureJSON work
- Modifying render-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/gin/render/render_test.go` | TestRenderJSON, TestRenderIndentedJSON, TestRenderSecureJSON, TestRenderJsonpJSON, Header (+27) |
| `evaluate/test_repos/gin/render/json.go` | WriteJSON, WriteContentType, Render, WriteContentType, Render (+4) |
| `evaluate/test_repos/gin/render/html.go` | WriteContentType, Instance, loadTemplate, Instance |
| `evaluate/test_repos/gin/render/data.go` | Render, WriteContentType |
| `evaluate/test_repos/gin/render/pdf.go` | Render, WriteContentType |
| `evaluate/test_repos/gin/render/reader.go` | Render, WriteContentType |
| `evaluate/test_repos/gin/render/bson.go` | WriteContentType |
| `evaluate/test_repos/gin/render/msgpack.go` | WriteMsgPack |
| `evaluate/test_repos/gin/render/protobuf.go` | WriteContentType |
| `evaluate/test_repos/gin/render/render.go` | writeContentType |

## Entry Points

Start here when exploring this area:

- **`TestRenderJSON`** (Function) — `evaluate/test_repos/gin/render/render_test.go:25`
- **`TestRenderIndentedJSON`** (Function) — `evaluate/test_repos/gin/render/render_test.go:50`
- **`TestRenderSecureJSON`** (Function) — `evaluate/test_repos/gin/render/render_test.go:73`
- **`TestRenderJsonpJSON`** (Function) — `evaluate/test_repos/gin/render/render_test.go:110`
- **`TestRenderJsonpJSONError2`** (Function) — `evaluate/test_repos/gin/render/render_test.go:218`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `TestRenderJSON` | Function | `evaluate/test_repos/gin/render/render_test.go` | 25 |
| `TestRenderIndentedJSON` | Function | `evaluate/test_repos/gin/render/render_test.go` | 50 |
| `TestRenderSecureJSON` | Function | `evaluate/test_repos/gin/render/render_test.go` | 73 |
| `TestRenderJsonpJSON` | Function | `evaluate/test_repos/gin/render/render_test.go` | 110 |
| `TestRenderJsonpJSONError2` | Function | `evaluate/test_repos/gin/render/render_test.go` | 218 |
| `TestRenderAsciiJSON` | Function | `evaluate/test_repos/gin/render/render_test.go` | 242 |
| `TestRenderPureJSON` | Function | `evaluate/test_repos/gin/render/render_test.go` | 271 |
| `TestRenderYAML` | Function | `evaluate/test_repos/gin/render/render_test.go` | 307 |
| `TestRenderTOML` | Function | `evaluate/test_repos/gin/render/render_test.go` | 344 |
| `TestRenderProtoBuf` | Function | `evaluate/test_repos/gin/render/render_test.go` | 366 |
| `TestRenderBSON` | Function | `evaluate/test_repos/gin/render/render_test.go` | 394 |
| `TestRenderXML` | Function | `evaluate/test_repos/gin/render/render_test.go` | 443 |
| `TestRenderData` | Function | `evaluate/test_repos/gin/render/render_test.go` | 524 |
| `TestRenderString` | Function | `evaluate/test_repos/gin/render/render_test.go` | 584 |
| `TestRenderStringLenZero` | Function | `evaluate/test_repos/gin/render/render_test.go` | 603 |
| `TestRenderReader` | Function | `evaluate/test_repos/gin/render/render_test.go` | 749 |
| `TestRenderReaderNoContentLength` | Function | `evaluate/test_repos/gin/render/render_test.go` | 772 |
| `WriteJSON` | Function | `evaluate/test_repos/gin/render/json.go` | 66 |
| `WriteMsgPack` | Function | `evaluate/test_repos/gin/render/msgpack.go` | 38 |
| `TestRenderHTMLDebugFiles` | Function | `evaluate/test_repos/gin/render/render_test.go` | 648 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Bytesconv | 7 calls |

## How to Explore

1. `context({name: "TestRenderJSON"})` — see callers and callees
2. `query({search_query: "render"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
