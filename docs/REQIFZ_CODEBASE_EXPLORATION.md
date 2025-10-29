# REQIFZ File Handling Codebase Exploration

**Project**: AI-powered Test Case Generator for automotive REQIFZ requirements  
**Version**: v2.1.0 (Python 3.14 + Ollama 0.12.5)  
**Architecture**: Modular with Context-Aware Processing  
**Working Directory**: `/Users/ramprakash/Documents/GitHub/AI_TC_Generator_v04_w_Trainer`

---

## 1. REQIFZ File Extraction & Unpacking

### Primary Component
**File**: `src/core/extractors.py` (752 lines)

#### Class: `REQIFArtifactExtractor`
Handles REQIFZ file extraction and XML parsing with support for streaming and parallel processing.

**Key Methods**:

1. **`extract_reqifz_content(reqifz_file_path: Path) -> ArtifactList`**
   - Main entry point for extracting artifacts from REQIFZ files
   - Opens ZIP file using Python's `zipfile.ZipFile`
   - Locates `.reqif` files within the ZIP archive
   - Reads the first REQIF file found and passes to XML parser
   - Returns list of extracted artifacts with metadata
   - Lines 45-71

2. **`_parse_reqif_xml(xml_content: bytes) -> ArtifactList`**
   - Parses REQIF XML content using ElementTree
   - Handles streaming mode (if enabled) or traditional DOM parsing
   - Builds necessary mappings (spec types, foreign IDs, attribute definitions)
   - Finds all `SPEC-OBJECT` elements and extracts them
   - Lines 73-114

3. **`_build_spec_type_mapping(root, namespaces)`**
   - Creates mapping from SPEC-OBJECT-TYPE identifiers to LONG-NAME values
   - Used to determine artifact types (System Requirement, Heading, etc.)
   - Lines 116-135

4. **`_build_foreign_id_mapping(root, namespaces)`**
   - Maps SPEC-OBJECT-TYPE IDs to their ReqIF.ForeignID attribute identifiers
   - Critical for extracting stable requirement IDs instead of internal IDs
   - Lines 137-155

5. **`_build_attribute_definition_mapping(root, namespaces)`**
   - Maps ATTRIBUTE-DEFINITION identifiers to LONG-NAME values
   - **CRITICAL FIX (v2.0)**: Prevents extraction failures by mapping attribute names properly
   - Handles both ATTRIBUTE-DEFINITION-XHTML and ATTRIBUTE-DEFINITION-STRING
   - Lines 157-180

#### XML Namespaces Used
```python
namespaces = {
    "reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
    "html": "http://www.w3.org/1999/xhtml",
}
```

#### Streaming Parsing Support
For large REQIF files, streaming parsing reduces memory usage:
- `_parse_reqif_xml_streaming()` - Lines 409-446
- `_build_mappings_streaming()` - Lines 448-489
- `_extract_spec_objects_streaming()` - Lines 491-520

#### High-Performance Variant
**Class**: `HighPerformanceREQIFArtifactExtractor` (extends REQIFArtifactExtractor)
- Uses concurrent processing with ThreadPoolExecutor
- Processes spec objects in parallel batches
- Lines 536-751

---

## 2. REQIF XML Structure Parsing

### Key XML Elements Extracted

**SPEC-OBJECT Structure** (Lines 205-296):
```
SPEC-OBJECT
├── @IDENTIFIER (internal ID)
├── TYPE
│   └── SPEC-OBJECT-TYPE-REF (references type definition)
└── VALUES
    ├── ATTRIBUTE-VALUE-XHTML (rich text content)
    │   ├── DEFINITION
    │   │   └── ATTRIBUTE-DEFINITION-XHTML-REF
    │   └── THE-VALUE (contains HTML content)
    └── ATTRIBUTE-VALUE-STRING (simple text)
        ├── DEFINITION
        │   └── ATTRIBUTE-DEFINITION-STRING-REF
        └── THE-VALUE
```

**Attribute Extraction** (Lines 247-289):
1. Finds all ATTRIBUTE-VALUE-XHTML elements within SPEC-OBJECT
2. Resolves attribute identifier to LONG-NAME using attribute definition mapping
3. Extracts HTML/XHTML content from THE-VALUE element
4. Handles multiple HTML element types (p, div, span, etc.)
5. Maps attribute content to artifact fields based on attribute name

**XHTML Content Extraction** (Lines 298-323):
- `_extract_xhtml_content()` handles HTML element parsing
- Extracts text from nested HTML elements
- Preserves structure where possible
- Fallback to text-only extraction if HTML parsing fails

**Foreign ID Extraction** (Lines 182-203):
- Looks for ReqIF.ForeignID attribute in ATTRIBUTE-VALUE-STRING
- Uses stable external ID instead of internal IDENTIFIER
- Provides better requirement traceability

---

## 3. Requirements Extraction from SPEC-OBJECTS

### Artifact Types (Enum)
**File**: `src/core/extractors.py`, Lines 23-32

```python
class ArtifactType(StrEnum):
    HEADING = "Heading"
    INFORMATION = "Information"
    DESIGN_INFORMATION = "Design Information"
    APPLICATION_PARAMETER = "Application Parameter"
    SYSTEM_INTERFACE = "System Interface"
    SYSTEM_REQUIREMENT = "System Requirement"
    UNKNOWN = "Unknown"
```

### Artifact Extraction Method
**`_extract_spec_object()` - Lines 205-296**

Returns dictionary with structure:
```python
{
    "id": str,                      # External ID or internal IDENTIFIER
    "text": str,                    # Requirement/specification text
    "type": ArtifactType,           # Artifact classification
    "heading": str,                 # Section heading if available
    "table": dict | None            # Extracted table data if present
}
```

### Type Mapping Logic
**`_map_reqif_type_to_artifact_type()` - Lines 325-344**
- Maps REQIF type names to artifact types using pattern matching
- Looks for keywords: "requirement", "heading", "information", "design", etc.
- Provides structured type classification

### Content-Based Classification
**`_determine_artifact_type()` - Lines 346-407**
- Fallback classification when REQIF type metadata is unavailable
- Analyzes requirement text for keywords
- Priority-based matching (more specific patterns first)
- Classification keywords:
  - **SYSTEM_REQUIREMENT**: "requirement", "shall", "must", "should", "will", "provides", "ensures", "controls", "manages", "performs"
  - **DESIGN_INFORMATION**: "design", "architecture", "diagram", "ecu"
  - **APPLICATION_PARAMETER**: "parameter", "variable", "setting", "threshold", "value", "constant"
  - **SYSTEM_INTERFACE**: "interface", "input", "output", "signal", "boolean", "command"
  - **INFORMATION**: "information", "note", "description"
  - **HEADING**: "heading", "title", "section"

---

## 4. Hierarchies, Images, and Tables

### Table Extraction
**File**: `src/core/parsers.py`, Lines 133-241

**Class**: `HTMLTableParser`

**Methods**:

1. **`extract_tables_from_html(html_content: str) -> HTMLTableData`**
   - Lines 138-166
   - Extracts structured table data from HTML content
   - Uses ElementTree for fast parsing (faster than BeautifulSoup)
   - Handles malformed HTML with regex fallback
   - Returns list of dictionaries representing table rows

2. **`_clean_html_content(html_content: str) -> str`**
   - Lines 168-183
   - Removes script and style tags
   - Fixes common HTML issues (br tags, entity encoding)
   - Prepares HTML for safe parsing

3. **`_parse_single_table(table_element: ET.Element) -> HTMLTableData`**
   - Lines 185-210
   - Extracts headers from first row
   - Converts remaining rows to dictionary format
   - Lines 199-208 validate column count consistency

4. **`_fallback_table_parsing(html_content: str) -> HTMLTableData`**
   - Lines 212-241
   - Regex-based parsing for severely malformed HTML
   - Extracting table/tr/td patterns with regex
   - Useful when XML parsing fails

**Table Integration** (in extractors.py):
- Lines 286-289: Tables detected in artifact text
- HTML table parser automatically invoked if `<table` tag found
- Extracted as: `artifact["table"] = {"rows": len(tables), "data": tables}`

### Hierarchy Handling
**Context-Aware Processing** (BaseProcessor)
- See Section 5 below
- Hierarchical structure maintained through heading tracking
- Information artifacts grouped by section heading
- System interfaces treated as global context

### Image Handling
- Currently NOT explicitly extracted (automotive requirements typically focus on functional specs)
- Images in XHTML content would be referenced via `<img>` tags
- Could be extended with image extraction logic if needed

---

## 5. LLM Processing Preparation

### Context-Aware Augmentation
**File**: `src/processors/base_processor.py`, Lines 89-166

**Method**: `_build_augmented_requirements(artifacts)`

This is the **CRITICAL** method that prepares requirements for LLM processing:

```python
def _build_augmented_requirements(self, artifacts):
    # Track heading context
    current_heading = "No Heading"
    info_since_heading = []
    
    # Classify artifacts to separate interfaces (global context)
    classified_artifacts = self.extractor.classify_artifacts(artifacts)
    system_interfaces = classified_artifacts.get("System Interface", [])
    
    for obj in artifacts:
        # Update heading context when encountered
        if obj.get("type") == "Heading":
            current_heading = obj.get("text", "No Heading")
            info_since_heading = []
            continue
        
        # Collect information artifacts for current section
        elif obj.get("type") == "Information":
            info_since_heading.append(obj)
            continue
        
        # Augment each requirement with FULL context
        elif obj.get("type") == "System Requirement":
            augmented_requirement = obj.copy()
            augmented_requirement.update({
                "heading": current_heading,           # Section context
                "info_list": info_since_heading.copy(),  # Information context
                "interface_list": system_interfaces    # Global interface context
            })
            augmented_requirements.append(augmented_requirement)
            
            # CRITICAL: Reset info context after requirement
            info_since_heading = []
    
    return augmented_requirements, len(system_interfaces)
```

**Key Behaviors**:
1. All artifacts processed in order (no pre-filtering)
2. Heading context resets on new heading
3. Information context resets after each requirement
4. System interfaces available globally
5. All requirements get identical interface context

### Prompt Building
**File**: `src/core/prompt_builder.py`, Lines 14-218

**Class**: `PromptBuilder`

**Method**: `build_prompt(requirement, template_name)`

#### Template Variables Prepared
```python
variables = {
    "requirement_id": requirement.get("id", "UNKNOWN"),
    "heading": requirement.get("heading", ""),
    "requirement_text": requirement.get("text", ""),
    "table_str": self.format_table(requirement.get("table")),
    "row_count": requirement.get("table", {}).get("rows", 0),
    "voltage_precondition": "1. Voltage= 12V\n2. Bat-ON",
    "info_str": self.format_info_list(requirement.get("info_list", [])),
    "interface_str": self.format_interfaces(requirement.get("interface_list", [])),
}
```

#### Context Formatting Methods

1. **`format_info_list(info_list)`** - Lines 183-197
   - Formats information artifacts as bullet list
   - One bullet per information item
   - Used in prompt as contextual information

2. **`format_interfaces(interface_list)`** - Lines 199-218
   - Formats system interfaces as ID: text pairs
   - One bullet per interface
   - Provides signal/parameter dictionary

3. **`format_table(table_data)`** - Lines 144-181
   - Formats table rows as text-based table
   - Extracts headers from first row
   - Limits to first 10 rows with row count indicator

### Default Prompt Format
**Lines 81-142**: Fallback prompt without template
```
You are an expert automotive test engineer. Generate comprehensive test cases for the following requirement with provided context:

--- CONTEXTUAL INFORMATION ---
FEATURE HEADING: {heading}
ADDITIONAL INFORMATION: {info_str}
SYSTEM INTERFACES: {interface_str}

--- PRIMARY REQUIREMENT TO TEST ---
Requirement ID: {requirement_id}
Description: {text}

--- YOUR TASK ---
Generate test cases in JSON format with the following structure:
{
    "test_cases": [
        {
            "summary_suffix": "...",
            "action": "...",
            "data": "...",
            "expected_result": "...",
            "test_type": "positive or negative"
        }
    ]
}
```

### YAML Template System
**File**: `src/yaml_prompt_manager.py`, Lines 1-100+

**Key Features**:
- YAML-based prompt templates
- Variable substitution support
- Auto-selection based on requirement characteristics
- Multiple template support (for different requirement types)

**Available Templates** (in `prompts/templates/`):
1. `test_generation_adaptive.yaml` - Handles both table and text-only requirements
2. `test_generation_v3_structured.yaml` - Legacy v3 format

**Configuration** (in `prompts/config/prompt_config.yaml`):
- Default template selection
- Template file paths
- Template-specific settings

---

## 6. Test Case Generation Using Models

### Synchronous Generation
**File**: `src/core/generators.py`, Lines 23-90

**Class**: `TestCaseGenerator`

**Method**: `generate_test_cases_for_requirement(requirement, model, template_name)`

Steps:
1. Build prompt using PromptBuilder
2. Call Ollama API via OllamaClient
3. Parse JSON response using JSONResponseParser
4. Extract test cases array
5. Add metadata to each test case:
   - requirement_id
   - generation_time
   - test_id (formatted as REQ_ID_TC_001, etc.)
6. Return list of test case dictionaries

**Flow**:
```
Requirement → PromptBuilder.build_prompt() → OllamaClient.generate_response() 
→ JSONResponseParser.extract_json_from_response() → Add metadata → Return test cases
```

### Asynchronous Generation
**File**: `src/core/generators.py`, Lines 93-316

**Class**: `AsyncTestCaseGenerator`

**Method**: `generate_test_cases_batch(requirements, model, template_name)`

**Performance Optimizations**:
1. Creates async tasks for all requirements upfront
2. Uses `asyncio.gather()` with `return_exceptions=True`
3. Processes results with consistent error structure
4. No double semaphore (concurrency controlled by AsyncOllamaClient only)

**Error Handling Pipeline**:
1. Exception from asyncio.gather() → Structured error object
2. Empty response → Error object with "EmptyResponse" type
3. Invalid JSON → Error object with "InvalidJSONStructure" type
4. Empty test cases array → Error object with "EmptyTestCasesList" type
5. Success → List of test cases with metadata

**Concurrency Control** (Lines 141-149):
- AsyncOllamaClient has semaphore (configurable, default=2 for GPU)
- No separate semaphore in generator (removed for throughput)
- Rate-limiting handled transparently by HTTP client

### JSON Response Parsing
**File**: `src/core/parsers.py`, Lines 25-130

**Class**: `JSONResponseParser`

**Method**: `extract_json_from_response(response_text)`

**Multi-Strategy Parsing** (Lines 31-78):
1. Direct JSON parsing attempt
2. Extract from markdown code blocks (```json ... ```)
3. Find JSON-like objects using regex
4. Extract test_cases array pattern
5. Return None if all strategies fail

**Validation** (Lines 80-97):
- Validates presence of "test_cases" field
- Checks for required fields in first test case: summary, action, data, expected_result
- Returns boolean result

### Ollama API Client
**File**: `src/core/ollama_client.py`, Lines 29-135

**Class**: `OllamaClient`

**Method**: `generate_response(model_name, prompt, is_json)`

**Request Structure**:
```python
payload = {
    "model": model_name,
    "prompt": prompt,
    "stream": False,
    "keep_alive": "30m",  # Ollama 0.12.5 optimization
    "options": {
        "temperature": 0.0,
        "num_ctx": 16384,      # 16K context (Ollama 0.12.5)
        "num_predict": 4096,   # 4K max response (Ollama 0.12.5)
        "top_k": 40,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
    },
}
```

**Error Handling** (Lines 79-134):
- OllamaConnectionError: Connection failures
- OllamaTimeoutError: Request timeouts
- OllamaModelNotFoundError: Model not found (404)
- OllamaResponseError: Invalid responses with status codes

### Async Ollama Client
**Class**: `AsyncOllamaClient` (Lines 137-250+)

**Features**:
- aiohttp session management
- Configurable semaphore for concurrency control
- Async context manager support
- Same error handling as sync client

---

## 7. Processor Workflows

### Standard Processor
**File**: `src/processors/standard_processor.py`

**Class**: `REQIFZFileProcessor` (extends BaseProcessor)

**Method**: `process_file(reqifz_path, model, template, output_dir)`

**Workflow**:
1. Initialize logger and components
2. Extract artifacts via REQIFArtifactExtractor
3. Build augmented requirements with context
4. Generate test cases sequentially using TestCaseGenerator
5. Format results to Excel using TestCaseFormatter
6. Save RAFT examples if enabled (non-invasive)
7. Return processing result

**Sequential Processing** (Lines 119-148):
- One requirement at a time
- Suitable for single machines
- Good for debugging and understanding behavior

### High-Performance Processor
**File**: `src/processors/hp_processor.py`

**Class**: `HighPerformanceREQIFZFileProcessor` (extends BaseProcessor)

**Method**: `async process_file(reqifz_path, model, template, output_dir)`

**Enhancements**:
1. Uses HighPerformanceREQIFArtifactExtractor (concurrent extraction)
2. Uses AsyncTestCaseGenerator for concurrent test case generation
3. Uses StreamingTestCaseFormatter for memory efficiency
4. Performance metrics tracking
5. Async context manager for proper resource cleanup

**Concurrent Processing** (Lines 142-187):
- All requirements processed concurrently
- AsyncOllamaClient controls concurrency via semaphore
- Throughput: ~3-5x faster than standard mode
- Lower memory per artifact due to streaming formatter

---

## 8. Output Formatting

### Excel Export
**File**: `src/core/formatters.py`

**Class**: `TestCaseFormatter`

**Method**: `format_to_excel(test_cases, output_path, metadata)`

**Column Structure** (v03-compatible):
```
Issue ID, Summary, Test Type, Issue Type, Project Key, Assignee, 
Description, Action, Data, Expected Result, Planned Execution,
Test Case Type, Feature Group, Components, Labels, LinkTest
```

**Data Preparation** (Lines 77-144):
1. Map v03 and v04 field names (backward compatibility)
2. Format data field with newline separation for steps
3. Generate Issue IDs
4. Apply automotive preconditions
5. Create formatted DataFrame

**Automotive Defaults**:
- Voltage precondition: "1. Voltage= 12V\n2. Bat-ON"
- Test Type: "Functional"
- Issue Type: "Test"
- Project Key: "AUTOMOTIVE"

### Streaming Formatter
**Class**: `StreamingTestCaseFormatter`
- Memory-efficient variant for large datasets
- Streams results to Excel without loading all in memory
- Used by HP processor

---

## 9. Configuration Management

**File**: `src/config.py`

### OllamaConfig (Lines 23-92)
- Host/Port settings (default: localhost:11434)
- Timeout, temperature, context window (16K for Ollama 0.12.5)
- GPU/CPU concurrency limits (default: 2 GPU, 4 CPU)
- Model preferences (default: llama3.1:8b)
- GPU offload support (95% VRAM usage)

### StaticTestConfig (Lines 95+)
- Default test case parameters
- Automotive preconditions
- Test type classifications
- Excel formatting defaults

### ConfigManager
- Loads from YAML or environment
- Applies CLI overrides
- Validates all settings via Pydantic
- Provides effective configuration view

---

## 10. Data Flow Summary

```
REQIFZ File
    ↓
[Extraction]
    zipfile.ZipFile() → Extract .reqif file
    XML parsing with ElementTree
    Build attribute definition mappings (CRITICAL FIX v2.0)
    Extract SPEC-OBJECTS with all context
    ↓
Artifacts List (Heading, Information, System Requirement, System Interface, etc.)
    ↓
[Context-Aware Augmentation] (BaseProcessor._build_augmented_requirements)
    Track heading context
    Collect information artifacts per section
    Augment each requirement with:
        - Current heading
        - Information artifacts since last heading
        - All system interfaces (global)
    ↓
Augmented Requirements (with full context)
    ↓
[Prompt Building] (PromptBuilder)
    Format context information
    Create template variables
    Use YAML template or default prompt
    ↓
LLM Prompt
    ↓
[LLM Processing] (OllamaClient / AsyncOllamaClient)
    Call Ollama API with JSON format request
    Rate-limited concurrency (semaphore)
    ↓
JSON Response
    ↓
[JSON Parsing] (JSONResponseParser)
    Multi-strategy extraction
    Validate test_cases structure
    ↓
Test Cases List
    ↓
[Formatting] (TestCaseFormatter)
    Add metadata and tracking fields
    Format to Excel columns
    Apply automotive defaults
    ↓
Excel File (.xlsx)
    ↓
[RAFT Collection] (RAFTDataCollector - optional, non-invasive)
    Save training example if enabled
    ↓
Output
```

---

## 11. Training Data Collection (RAFT)

**File**: `src/training/raft_collector.py`

**Non-Invasive Design**:
- Disabled by default (`enable_raft: false` in config)
- Collects examples AFTER test case generation
- Zero impact on core logic
- No side effects on output

**RAFT Example Structure**:
```python
{
    "requirement_id": str,
    "requirement_text": str,
    "heading": str,
    "retrieved_context": {
        "heading": {"id": "HEADING", "text": str},
        "info_artifacts": [{"id": str, "text": str}],
        "interfaces": [{"id": str, "text": str}]
    },
    "generated_test_cases": str,
    "model_used": str,
    "generation_timestamp": str,
    "context_annotation": {
        "oracle_context": [],           # To be filled by expert
        "distractor_context": [],       # To be filled by expert
        "annotation_notes": "",
        "quality_rating": None
    },
    "validation_status": "pending"
}
```

---

## 12. Error Handling

**File**: `src/core/exceptions.py`

### Exception Hierarchy
```
AITestCaseGeneratorError (base)
├── OllamaError
│   ├── OllamaConnectionError (host, port)
│   ├── OllamaTimeoutError (timeout)
│   ├── OllamaModelNotFoundError (model)
│   └── OllamaResponseError (status_code, response_body)
├── REQIFParsingError (file_path)
├── TestCaseGenerationError (requirement_id)
└── ConfigurationError
```

### Contextual Error Information
- Connection errors include host/port for diagnostics
- Timeout errors include timeout value for tuning
- Model errors include model name for installation
- Response errors include status code and response body (Ollama 0.12.5)

---

## 13. Key Code Locations

| Task | File | Lines | Class/Function |
|------|------|-------|-----------------|
| REQIFZ unpacking | `extractors.py` | 45-71 | REQIFArtifactExtractor.extract_reqifz_content() |
| REQIF XML parsing | `extractors.py` | 73-114 | REQIFArtifactExtractor._parse_reqif_xml() |
| Attribute mapping | `extractors.py` | 157-180 | _build_attribute_definition_mapping() |
| Foreign ID extraction | `extractors.py` | 182-203 | _extract_foreign_id() |
| Spec object extraction | `extractors.py` | 205-296 | _extract_spec_object() |
| Type mapping | `extractors.py` | 325-344 | _map_reqif_type_to_artifact_type() |
| Table extraction | `parsers.py` | 138-241 | HTMLTableParser.extract_tables_from_html() |
| Context-aware augmentation | `base_processor.py` | 89-166 | BaseProcessor._build_augmented_requirements() |
| Prompt building | `prompt_builder.py` | 28-142 | PromptBuilder.build_prompt() |
| Sync test generation | `generators.py` | 34-90 | TestCaseGenerator.generate_test_cases_for_requirement() |
| Async test generation | `generators.py` | 108-316 | AsyncTestCaseGenerator.generate_test_cases_batch() |
| JSON parsing | `parsers.py` | 31-78 | JSONResponseParser.extract_json_from_response() |
| Ollama API call | `ollama_client.py` | 43-134 | OllamaClient.generate_response() |
| Excel formatting | `formatters.py` | 32-69 | TestCaseFormatter.format_to_excel() |
| Standard workflow | `standard_processor.py` | 63-190 | REQIFZFileProcessor.process_file() |
| HP workflow | `hp_processor.py` | 87-250 | HighPerformanceREQIFZFileProcessor.process_file() |

---

## 14. Critical Features & Optimizations

### v2.1.0 (Python 3.14 + Ollama 0.12.5)
- 16K context window support
- 4K response length support
- GPU offload with 95% VRAM usage
- 2 concurrent GPU requests
- Improved error reporting with response_body field

### v1.5.0 (Critical Improvements)
- Custom exception system with context (10x faster debugging)
- Removed double semaphore (50% throughput improvement)
- Concurrent batch processing (3x faster for large files)

### v2.0 (REQIFZ Extraction Fix)
- Attribute definition mapping (0% → 100% extraction success)
- Foreign ID extraction for stable requirement IDs
- Adaptive prompt templates (handle text-only requirements)

### Architecture Patterns
- Modular component design (extractors, generators, formatters, clients)
- Context-aware processing via BaseProcessor
- Stateless PromptBuilder (decoupled from generators)
- Memory optimization via `__slots__` (20-30% savings)
- Streaming XML parsing for large files
- Concurrent extraction and processing
- RAFT training integration (optional, non-invasive)

---

## 15. Configuration & Logging

### Configuration Management
**File**: `src/config.py`

Multi-source configuration:
1. Base defaults in code
2. YAML configuration file
3. Environment variables
4. CLI argument overrides
5. Applied in priority order

### Logging
**File**: `src/app_logger.py` (centralized)
**File**: `src/file_processing_logger.py` (per-file)

Features:
- Structured logging with JSON format
- Separate loggers for application and file processing
- Metrics tracking (AI response times, requirements processed, etc.)
- File-specific logging with proper cleanup

---

## Summary

This codebase implements a sophisticated, modular system for:

1. **Extraction**: Unpacks REQIFZ files and parses REQIF XML with proper attribute mapping
2. **Analysis**: Classifies artifacts into semantic types and builds context hierarchies
3. **Enrichment**: Augments requirements with section headings, information, and interfaces
4. **Generation**: Uses LLM to generate test cases with full context awareness
5. **Output**: Exports to automotive-standard Excel format
6. **Training**: Optionally collects data for model fine-tuning (non-invasive)

The implementation emphasizes:
- **Correctness**: Proper XML parsing, attribute mapping, context preservation
- **Performance**: Concurrent processing, streaming for memory efficiency
- **Maintainability**: Modular design, clear separation of concerns
- **Reliability**: Structured error handling, comprehensive logging
- **Flexibility**: Multiple processing modes (standard/HP), template system, RAFT optional

