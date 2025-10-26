# REQIFZ Codebase Architecture Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLI ENTRY POINT                              │
│                      (main.py - 390 lines)                          │
│                                                                      │
│  - Click-based command parsing                                      │
│  - Standard vs High-Performance mode selection                      │
│  - Configuration loading and CLI override application               │
│  - Template validation and listing utilities                        │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            v                     v
  ┌──────────────────┐  ┌──────────────────────┐
  │ Standard Mode    │  │ High-Performance    │
  │                  │  │ Mode (Async)        │
  └────────┬─────────┘  └─────────┬───────────┘
           │                      │
           v                      v
 ┌─────────────────────────────────────────────────────────────────┐
 │                    PROCESSOR LAYER                              │
 │              (extends BaseProcessor)                            │
 ├──────────────────────┬──────────────────────────────────────────┤
 │ REQIFZFileProcessor  │  HighPerformanceREQIFZFileProcessor      │
 │                      │  (Async/Concurrent)                      │
 │ - Sync processing    │  - Async processing                      │
 │ - Sequential TC gen  │  - Concurrent TC gen                    │
 │ - TestCaseFormatter  │  - StreamingTestCaseFormatter            │
 └──────────┬───────────┴──────────────────┬──────────────────────┘
            │                              │
            └──────────────┬───────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
         v                                   v
    ┌─────────────────────────────────────────────────────────┐
    │          SHARED BASE PROCESSOR LOGIC                     │
    │      (BaseProcessor - 256 lines)                         │
    ├─────────────────────────────────────────────────────────┤
    │ CRITICAL: _build_augmented_requirements()               │
    │ - Context-aware artifact processing                    │
    │ - Heading tracking                                     │
    │ - Information aggregation                              │
    │ - System interface global context                      │
    │ - Full requirement augmentation with context            │
    │                                                         │
    │ PLUS:                                                   │
    │ - Logger initialization                                │
    │ - Artifact extraction coordination                      │
    │ - Output path generation                               │
    │ - Metadata creation                                    │
    │ - RAFT example collection (optional)                    │
    └──────────────────────┬──────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       v                   v                   v
    ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
    │  EXTRACTION      │ │   GENERATION     │ │   FORMATTING     │
    │                  │ │                  │ │                  │
    │ extractors.py    │ │ generators.py    │ │ formatters.py    │
    │ (752 lines)      │ │ (316 lines)      │ │ (400+ lines)     │
    └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
             │                    │                    │
             │                    │                    │
             v                    v                    v
    ┌──────────────────────────────────────────────────────────┐
    │                   CORE COMPONENTS                        │
    ├──────────────────────────────────────────────────────────┤
    │                                                          │
    │  EXTRACTORS:                                            │
    │  - REQIFArtifactExtractor (standard)                    │
    │  - HighPerformanceREQIFArtifactExtractor (concurrent)   │
    │                                                          │
    │  GENERATORS:                                            │
    │  - TestCaseGenerator (sync)                            │
    │  - AsyncTestCaseGenerator (async)                      │
    │                                                          │
    │  FORMATTERS:                                            │
    │  - TestCaseFormatter (standard)                        │
    │  - StreamingTestCaseFormatter (memory-efficient)       │
    │                                                          │
    │  SUPPORTING:                                            │
    │  - PromptBuilder (stateless prompt construction)       │
    │  - JSONResponseParser / FastJSONResponseParser         │
    │  - HTMLTableParser                                     │
    │  - OllamaClient / AsyncOllamaClient                    │
    │  - YAMLPromptManager                                   │
    │  - Custom Exception Hierarchy                          │
    │  - ConfigManager                                       │
    │                                                          │
    └──────────────────────────────────────────────────────────┘
```

---

## Detailed Component Interactions

### 1. REQIFZ Extraction Pipeline

```
REQIFZ File (.zip)
    │
    v
zipfile.ZipFile(path, 'r')
    │
    ├─ List all files in archive
    │
    v
Find .reqif files
    │
    ├─ Read first .reqif file content (bytes)
    │
    v
ElementTree.fromstring(xml_content)
    │
    ├─ Namespace: http://www.omg.org/spec/ReqIF/20110401/reqif.xsd
    │
    v
Build Three Mappings (CRITICAL):
    │
    ├─ _build_spec_type_mapping()
    │   └─ SPEC-OBJECT-TYPE @IDENTIFIER → LONG-NAME
    │      (e.g., "_10001" → "System Requirement")
    │
    ├─ _build_foreign_id_mapping()
    │   └─ SPEC-OBJECT-TYPE ID → ReqIF.ForeignID attribute ID
    │      (enables stable external IDs)
    │
    └─ _build_attribute_definition_mapping()
       └─ ATTRIBUTE-DEFINITION @IDENTIFIER → LONG-NAME
          (FIX v2.0: maps "_json2reqif_123" to "ReqIF.Text")
    │
    v
Find all SPEC-OBJECT elements
    │
    ├─ For each SPEC-OBJECT:
    │   │
    │   ├─ Extract @IDENTIFIER
    │   │
    │   ├─ Resolve TYPE/SPEC-OBJECT-TYPE-REF using mapping
    │   │   └─ Map REQIF type to ArtifactType enum
    │   │
    │   ├─ For each ATTRIBUTE-VALUE-XHTML:
    │   │   ├─ Get DEFINITION/ATTRIBUTE-DEFINITION-XHTML-REF
    │   │   ├─ Resolve to LONG-NAME using mapping
    │   │   ├─ Extract THE-VALUE (HTML content)
    │   │   └─ Parse XHTML to text
    │   │       ├─ Handle <p>, <div>, <span>, etc.
    │   │       └─ Extract all text content
    │   │
    │   ├─ Check for tables in text
    │   │   └─ HTMLTableParser.extract_tables_from_html()
    │   │       ├─ ElementTree parsing (fast)
    │   │       ├─ Header extraction from first row
    │   │       └─ Regex fallback for malformed HTML
    │   │
    │   ├─ Extract ReqIF.ForeignID if available
    │   │   └─ Use external ID instead of IDENTIFIER
    │   │
    │   └─ Create artifact dictionary:
    │       {
    │           "id": str (external or internal),
    │           "text": str (requirement text),
    │           "type": ArtifactType (enum),
    │           "heading": str (if present),
    │           "table": dict (if tables found)
    │       }
    │
    v
Return Artifacts List
(Heading, Information, System Requirement, System Interface, etc.)
```

### 2. Context-Aware Augmentation

```
Raw Artifacts List (in document order)
    │
    v
Classify artifacts by type
    │
    ├─ Extract all System Interfaces (global context)
    │
    v
Initialize context:
    current_heading = "No Heading"
    info_since_heading = []
    system_interfaces = [all interfaces]
    │
    v
Iterate through artifacts IN ORDER:
    │
    ├─ Artifact type = "Heading"
    │   ├─ Update current_heading = artifact.text
    │   ├─ Reset info_since_heading = []
    │   └─ Continue (skip to next)
    │
    ├─ Artifact type = "Information"
    │   ├─ Append to info_since_heading
    │   └─ Continue (skip to next)
    │
    ├─ Artifact type = "System Requirement"
    │   ├─ Skip if no text content (empty requirement)
    │   │
    │   ├─ Augment with context:
    │   │   artifact.update({
    │   │       "heading": current_heading,
    │   │       "info_list": info_since_heading.copy(),
    │   │       "interface_list": system_interfaces
    │   │   })
    │   │
    │   ├─ Add to augmented_requirements list
    │   │
    │   └─ CRITICAL: Reset info_since_heading = []
    │      (information context resets after EACH requirement)
    │
    └─ Other types (Design Info, Parameter, Interface)
       └─ Continue (skip, used for context only)
    │
    v
Return: (augmented_requirements, interface_count)
```

### 3. Prompt Building & LLM Processing

```
Augmented Requirement
{
    "id": "REQ_001",
    "text": "System shall detect door opening...",
    "type": "System Requirement",
    "heading": "Door Module Requirements",
    "info_list": [
        {"text": "Door sensor resolution: 100ms"},
        {"text": "Error codes in appendix A"}
    ],
    "interface_list": [
        {"id": "DoorSensor", "text": "GPIO signal HIGH when open"},
        {"id": "BusError", "text": "CAN message ID 0x123"}
    ],
    "table": None
}
    │
    v
PromptBuilder.build_prompt(requirement, template_name)
    │
    ├─ Prepare template variables:
    │   {
    │       "requirement_id": "REQ_001",
    │       "heading": "Door Module Requirements",
    │       "requirement_text": "System shall detect door opening...",
    │       "table_str": "No table data available",
    │       "row_count": 0,
    │       "voltage_precondition": "1. Voltage= 12V\n2. Bat-ON",
    │       "info_str": "- Door sensor resolution: 100ms\n- Error codes in appendix A",
    │       "interface_str": "- DoorSensor: GPIO signal HIGH when open\n- BusError: CAN message ID 0x123"
    │   }
    │
    ├─ Load YAML template from prompts/templates/
    │   └─ test_generation_adaptive.yaml (handles tables + text)
    │
    ├─ Substitute variables in template
    │   └─ Creates final prompt text
    │
    v
LLM Prompt
"You are an expert automotive test engineer...
[Full context: heading, info, interfaces]
[Requirement text]
Generate test cases in JSON..."
    │
    v
OllamaClient.generate_response(model, prompt, is_json=True)
│  (or AsyncOllamaClient for concurrent mode)
│
├─ Build API payload:
│   {
│       "model": "llama3.1:8b",
│       "prompt": "...",
│       "stream": false,
│       "format": "json",
│       "options": {
│           "temperature": 0.0,
│           "num_ctx": 16384,      # 16K context (Ollama 0.12.5)
│           "num_predict": 4096,   # 4K response (Ollama 0.12.5)
│       }
│   }
│
├─ POST to http://localhost:11434/api/generate
│
├─ Handle errors:
│   ├─ Connection → OllamaConnectionError (host, port)
│   ├─ Timeout → OllamaTimeoutError (timeout)
│   ├─ 404 → OllamaModelNotFoundError (model)
│   └─ Other → OllamaResponseError (status, response_body)
│
│  (For async: AsyncOllamaClient adds semaphore for rate-limiting)
│
v
JSON Response String
"{\"test_cases\": [{...}, {...}]}"
    │
    v
JSONResponseParser.extract_json_from_response(response)
    │
    ├─ Strategy 1: Direct JSON parse
    │   └─ json.loads(response)
    │
    ├─ Strategy 2: Extract from markdown blocks
    │   └─ Regex: ```json ... ```
    │
    ├─ Strategy 3: Find JSON-like objects
    │   └─ Regex pattern matching
    │
    ├─ Strategy 4: Extract test_cases array
    │   └─ Pattern: "test_cases": [...]
    │
    └─ Return: dict or None
    │
    v
Validate Structure
    ├─ Check for "test_cases" key
    ├─ Verify first test case has required fields
    │   (summary, action, data, expected_result)
    └─ Return boolean
    │
    v
Test Cases List
[
    {
        "summary": "Test door detection with valid input",
        "action": "1. Voltage= 12V\n2. Bat-ON\n3. Press door sensor",
        "data": "1) Apply voltage\n2) Wait 100ms\n3) Read sensor status",
        "expected_result": "GPIO reads HIGH, no error codes",
        "test_type": "positive",
        "requirement_id": "REQ_001",
        "generation_time": 2.34,
        "test_id": "REQ_001_TC_001"
    },
    {...}
]
    │
    v
Add Metadata (handled by generator):
    ├─ requirement_id
    ├─ generation_time (how long LLM took)
    └─ test_id (formatted as REQ_ID_TC_XXX)
    │
    v
TestCaseFormatter.format_to_excel(test_cases, output_path)
    │
    ├─ Prepare Excel columns (v03-compatible):
    │   Issue ID | Summary | Test Type | Issue Type | ...
    │
    ├─ For each test case:
    │   ├─ Generate Issue ID (sequenced)
    │   ├─ Format action/data with newlines
    │   ├─ Apply automotive defaults
    │   └─ Create DataFrame row
    │
    ├─ Create workbook with formatting
    │   ├─ Header styling
    │   ├─ Column widths
    │   └─ Alignment
    │
    └─ Save to .xlsx file
    │
    v
Excel Output File (.xlsx)
```

### 4. Processing Mode Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    STANDARD MODE                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Flow:                                                          │
│  1. Extract artifacts (sequential)                             │
│  2. Augment requirements (sequential)                          │
│  3. For each requirement:                                      │
│     ├─ Build prompt                                            │
│     ├─ Call LLM (blocks until response)                       │
│     ├─ Parse response                                          │
│     └─ Add to results                                          │
│  4. Format to Excel (all in memory)                           │
│                                                                 │
│  Components:                                                   │
│  - REQIFArtifactExtractor                                     │
│  - TestCaseGenerator                                           │
│  - OllamaClient (sync, blocks on I/O)                         │
│  - TestCaseFormatter                                           │
│                                                                 │
│  Performance:                                                  │
│  - Sequential: process one requirement at a time              │
│  - Good for: debugging, small files (< 100 requirements)     │
│  - Throughput: ~7 test cases/second                           │
│  - Memory: All artifacts in memory during processing          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              HIGH-PERFORMANCE (ASYNC) MODE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Flow:                                                          │
│  1. Extract artifacts (parallel with ThreadPoolExecutor)      │
│  2. Augment requirements (sequential)                          │
│  3. Create async tasks for ALL requirements                   │
│  4. Execute concurrently with:                                │
│     ├─ AsyncOllamaClient (aiohttp, semaphore-limited)        │
│     ├─ asyncio.gather() with exception handling              │
│     └─ Rate-limiting: 2 concurrent GPU requests              │
│  5. Stream to Excel (memory-efficient)                       │
│                                                                 │
│  Components:                                                   │
│  - HighPerformanceREQIFArtifactExtractor (parallel)           │
│  - AsyncTestCaseGenerator                                     │
│  - AsyncOllamaClient (async, semaphore=2 for GPU)            │
│  - StreamingTestCaseFormatter                                 │
│                                                                 │
│  Performance:                                                  │
│  - Concurrent: all requirements in flight simultaneously      │
│  - Optimized for: large files (> 100 requirements)           │
│  - Throughput: ~24 test cases/second (3x improvement)        │
│  - Memory: Streaming to avoid accumulation                   │
│  - Concurrency: 2 GPU requests + queue                       │
│                                                                 │
│  Example Timeline (4 requirements):                            │
│  Standard:  T=0 ┌─T1───────┐ ┌─T2───────┐ ┌─T3───────┐ ┌─T4───────┐
│             Total: 8s
│                                                                 │
│  Async:     T=0 ┌─T1────┐       (semaphore allows 2 concurrent)
│                 ┌─T2────┐                                     │
│                    ┌─T3────┐                                  │
│                    ┌─T4────┐                                  │
│             Total: 2.5s (3x faster)                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
src/
├── core/
│   ├── extractors.py          # REQIF parsing (752 lines)
│   │   ├── REQIFArtifactExtractor
│   │   ├── HighPerformanceREQIFArtifactExtractor
│   │   └── ArtifactType enum
│   │
│   ├── generators.py          # Test case generation (316 lines)
│   │   ├── TestCaseGenerator
│   │   └── AsyncTestCaseGenerator
│   │
│   ├── prompt_builder.py      # Prompt construction (218 lines)
│   │   └── PromptBuilder (stateless)
│   │
│   ├── parsers.py             # Response parsing (242 lines)
│   │   ├── JSONResponseParser
│   │   ├── FastJSONResponseParser
│   │   └── HTMLTableParser
│   │
│   ├── ollama_client.py       # LLM API clients (250+ lines)
│   │   ├── OllamaClient (sync)
│   │   └── AsyncOllamaClient (async)
│   │
│   ├── formatters.py          # Output formatting (400+ lines)
│   │   ├── TestCaseFormatter
│   │   └── StreamingTestCaseFormatter
│   │
│   ├── exceptions.py          # Error hierarchy (88 lines)
│   │   ├── AITestCaseGeneratorError
│   │   ├── OllamaError
│   │   ├── OllamaConnectionError
│   │   ├── OllamaTimeoutError
│   │   ├── OllamaModelNotFoundError
│   │   ├── OllamaResponseError
│   │   └── REQIFParsingError
│   │
│   └── __init__.py
│
├── processors/
│   ├── base_processor.py       # Shared logic (256 lines)
│   │   └── BaseProcessor
│   │       └── _build_augmented_requirements() [CRITICAL]
│   │
│   ├── standard_processor.py   # Sequential workflow (190+ lines)
│   │   └── REQIFZFileProcessor
│   │
│   ├── hp_processor.py         # Async workflow (250+ lines)
│   │   └── HighPerformanceREQIFZFileProcessor
│   │
│   └── __init__.py
│
├── training/
│   ├── raft_collector.py       # Training data (100+ lines)
│   │   └── RAFTDataCollector
│   │
│   ├── raft_dataset_builder.py
│   ├── quality_scorer.py
│   ├── progressive_trainer.py
│   └── __init__.py
│
├── config.py                   # Configuration (400+ lines)
│   ├── OllamaConfig
│   ├── StaticTestConfig
│   └── ConfigManager
│
├── yaml_prompt_manager.py     # Template management (300+ lines)
│   └── YAMLPromptManager
│
├── app_logger.py              # Central logging (400+ lines)
│   └── Centralized metrics & logging
│
├── file_processing_logger.py  # Per-file logging (350+ lines)
│   └── FileProcessingLogger
│
└── main.py                    # CLI entry (250+ lines)
    └── main() with Click decorators

prompts/
├── config/
│   └── prompt_config.yaml     # Template configuration
│
└── templates/
    ├── test_generation_adaptive.yaml
    └── test_generation_v3_structured.yaml

input/
└── REQIFZ_Files/
    └── *.reqifz               # Input requirement files
```

---

## Key Data Structures

### Artifact
```python
type ArtifactData = {
    "id": str,
    "text": str,
    "type": ArtifactType,  # Enum: Heading, Information, System Requirement, etc.
    "heading": str,
    "table": {
        "rows": int,
        "data": list[dict[str, str]]
    } | None
}
```

### Augmented Requirement
```python
type AugmentedRequirement = {
    "id": str,
    "text": str,
    "type": ArtifactType,
    "heading": str,                    # From context
    "info_list": list[ArtifactData],  # From context
    "interface_list": list[ArtifactData],  # From context
    "table": dict | None
}
```

### Test Case
```python
type TestCaseData = {
    "summary": str,
    "action": str,              # Preconditions
    "data": str,                # Test steps
    "expected_result": str,
    "test_type": str,           # "positive" or "negative"
    "requirement_id": str,
    "generation_time": float,
    "test_id": str             # "REQ_001_TC_001"
}
```

---

## Processing Statistics

### Extraction Performance
- Zipfile unpacking: < 100ms
- XML parsing: proportional to file size
- Attribute mapping: ~1ms per mapping
- Spec object extraction: ~2ms per object
- Overall throughput: ~7,254 artifacts/second (DOM parsing)

### Generation Performance
- Standard mode: ~7 test cases/second
- HP mode: ~24 test cases/second (3-5x faster)
- LLM latency: 2-5 seconds per requirement (dominant factor)
- Concurrency impact: 2 concurrent GPU requests

### Memory Efficiency
- Standard formatter: all test cases in memory
- Streaming formatter: constant memory per batch
- Memory per artifact: ~0.010 MB with __slots__
- 20-30% reduction with __slots__ vs standard Python

---

## Error Handling Flow

```
API Call
    │
    ├─ Connection Error?
    │   └─ OllamaConnectionError(host, port)
    │
    ├─ Timeout?
    │   └─ OllamaTimeoutError(timeout)
    │
    ├─ 404 Not Found?
    │   └─ OllamaModelNotFoundError(model)
    │
    ├─ Invalid Response?
    │   └─ OllamaResponseError(status_code, response_body)
    │
    ├─ JSON Parse Error?
    │   └─ Handle gracefully, return empty test cases
    │
    └─ Success → Process response

    For async calls:
    ├─ Exceptions caught by asyncio.gather()
    ├─ Wrapped in structured error object
    └─ Result processed with consistent format
```

