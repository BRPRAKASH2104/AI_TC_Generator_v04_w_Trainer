---
name: binding
description: "Skill for the Binding area of AI_TC_Generator_v04_w_Trainer. 90 symbols across 18 files."
---

# Binding

90 symbols | 18 files | Cohesion: 82%

## When to Use

- Working with code in `evaluate/`
- Understanding how TestBindingMsgPack, TestBindingProtoBuf, TestBindingProtoBufFail work
- Modifying binding-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/gin/binding/binding_test.go` | TestBindingProtoBuf, TestBindingProtoBufFail, TestHeaderBinding, testFormBindingEmbeddedStruct, testFormBinding (+33) |
| `evaluate/test_repos/gin/binding/form_mapping.go` | mappingByPtr, trySetCustom, trySetUsingParser, setByForm, setWithProperType (+9) |
| `evaluate/test_repos/gin/binding/form_mapping_test.go` | convertToOidUnmarshalText, TestMappingCustomArrayUnmarshalTextUri, TestMappingCustomArrayUnmarshalTextForm, TestMappingCustomArrayOfArrayUnmarshalTextUri, TestMappingCustomArrayOfArrayUnmarshalTextForm (+8) |
| `evaluate/test_repos/gin/binding/multipart_form_mapping_test.go` | TestFormMultipartBindingBindOneFile, TestFormMultipartBindingBindTwoFiles, createRequestMultipartFiles, assertMultipartFileHeader |
| `evaluate/test_repos/gin/binding/default_validator.go` | ValidateStruct, validateStruct, lazyinit |
| `evaluate/test_repos/gin/binding/multipart_form_mapping.go` | TrySet, setByMultipartFormFile, setArrayOfMultipartFormFiles |
| `evaluate/test_repos/gin/binding/binding_msgpack_test.go` | TestBindingMsgPack, testMsgPackBodyBinding |
| `evaluate/test_repos/gin/binding/header.go` | Bind, mapHeader |
| `evaluate/test_repos/gin/binding/validate_test.go` | createNoValidationValues, TestValidateNoValidationValues |
| `evaluate/test_repos/gin/binding/binding_nomsgpack.go` | validate |

## Entry Points

Start here when exploring this area:

- **`TestBindingMsgPack`** (Function) — `evaluate/test_repos/gin/binding/binding_msgpack_test.go:18`
- **`TestBindingProtoBuf`** (Function) — `evaluate/test_repos/gin/binding/binding_test.go:713`
- **`TestBindingProtoBufFail`** (Function) — `evaluate/test_repos/gin/binding/binding_test.go:725`
- **`TestHeaderBinding`** (Function) — `evaluate/test_repos/gin/binding/binding_test.go:789`
- **`TestPlainBinding`** (Function) — `evaluate/test_repos/gin/binding/binding_test.go:1375`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `TestBindingMsgPack` | Function | `evaluate/test_repos/gin/binding/binding_msgpack_test.go` | 18 |
| `TestBindingProtoBuf` | Function | `evaluate/test_repos/gin/binding/binding_test.go` | 713 |
| `TestBindingProtoBufFail` | Function | `evaluate/test_repos/gin/binding/binding_test.go` | 725 |
| `TestHeaderBinding` | Function | `evaluate/test_repos/gin/binding/binding_test.go` | 789 |
| `TestPlainBinding` | Function | `evaluate/test_repos/gin/binding/binding_test.go` | 1375 |
| `TestBindingFormForTime` | Function | `evaluate/test_repos/gin/binding/binding_test.go` | 270 |
| `TestBindingFormForTime2` | Function | `evaluate/test_repos/gin/binding/binding_test.go` | 288 |
| `TestBindingFormFilesMultipart` | Function | `evaluate/test_repos/gin/binding/binding_test.go` | 657 |
| `TestMappingCustomArrayUnmarshalTextUri` | Function | `evaluate/test_repos/gin/binding/form_mapping_test.go` | 941 |
| `TestMappingCustomArrayUnmarshalTextForm` | Function | `evaluate/test_repos/gin/binding/form_mapping_test.go` | 953 |
| `TestMappingCustomArrayOfArrayUnmarshalTextUri` | Function | `evaluate/test_repos/gin/binding/form_mapping_test.go` | 965 |
| `TestMappingCustomArrayOfArrayUnmarshalTextForm` | Function | `evaluate/test_repos/gin/binding/form_mapping_test.go` | 977 |
| `TestMappingCustomArrayOfArrayUnmarshalTextDefault` | Function | `evaluate/test_repos/gin/binding/form_mapping_test.go` | 989 |
| `TestMappingTimeUnixNano` | Function | `evaluate/test_repos/gin/binding/form_mapping_test.go` | 235 |
| `TestMappingTimeDuration` | Function | `evaluate/test_repos/gin/binding/form_mapping_test.go` | 253 |
| `TestMappingCustomArrayUri` | Function | `evaluate/test_repos/gin/binding/form_mapping_test.go` | 691 |
| `TestMappingCustomArrayForm` | Function | `evaluate/test_repos/gin/binding/form_mapping_test.go` | 703 |
| `TestMappingCustomArrayOfArrayUri` | Function | `evaluate/test_repos/gin/binding/form_mapping_test.go` | 715 |
| `TestMappingCustomArrayOfArrayForm` | Function | `evaluate/test_repos/gin/binding/form_mapping_test.go` | 727 |
| `MapFormWithTag` | Function | `evaluate/test_repos/gin/binding/form_mapping.go` | 39 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Bytesconv | 2 calls |

## How to Explore

1. `context({name: "TestBindingMsgPack"})` — see callers and callees
2. `query({search_query: "binding"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
