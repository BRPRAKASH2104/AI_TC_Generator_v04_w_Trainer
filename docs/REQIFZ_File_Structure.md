# REQIFZ File Structure Analysis

## Detailed Analysis Summary of REQIFZ Files

This document provides a comprehensive analysis of the REQIFZ (Requirements Interchange Format Zipped) files used in the AI TC Generator project, based on analysis of 28 real automotive requirements files.

---

## 📊 OVERALL STATISTICS

- **Total Files**: 28 REQIFZ files
- **Total Requirements/Objects**: 3,005 specification objects
- **Total Embedded Images**: 385 images
- **Total Tables**: 658 tables
- **Total Requirement Relations**: 2 active relationships
- **Format**: ReqIF v1.2 (Requirements Interchange Format)
- **Tool**: Json2ReqIF v0.3

---

## 📁 FILE CATEGORIES

The analyzed files cover various automotive system features:

### 1. DIAG (Diagnostics) - 8 files
   - Data Identifiers, DTC, Session and SID, Factory Test Mode, etc.
   - Largest category with most complex requirements
   - Example: `TFDCX32348_DIAG_Data Identifiers_4be054.reqifz` (15MB, 775 objects)

### 2. GAU (Gauges) - 7 files
   - Oil pressure, Boost pressure, Volt gauge, Water temp, etc.
   - Examples: `TFDCX32348_GAU_Oil pressure gauge_b85b72.reqifz`

### 3. VMID (Vehicle Mode Information Display) - 5 files
   - CRAWL, DAC, Drive mode select, Multi-terrain select, Tow Haul Mode
   - Examples: `TFDCX32348_VMID_Drive mode select_6243ef.reqifz`

### 4. MM (Multi-Media/Navigation) - 3 files
   - Navigation Map Drawing, Map ETA, ETC
   - Examples: `TFDCX32348_MM_NAV_Map_Drawing_6453ed.reqifz`

### 5. ADAS (Advanced Driver Assistance) - 1 file
   - ACC (Adaptive Cruise Control)
   - Example: `TFDCX32348_ADAS_ACC (Adaptive Cruise Control)_6ab01f.reqifz`

### 6. Other Features - 3 files
   - CXPI Generic Network, GUI OdoTrip, Voltage Operating Modes

---

## 🏗️ REQIFZ FILE STRUCTURE

### Physical Structure

Each `.reqifz` file is a **ZIP archive** containing:

1. **Requirements.reqif** - Main XML file (512KB to 3.7MB per file)
2. **Numbered directories** (e.g., `1472801/`, `1115144/`, etc.)
   - Each directory contains embedded resources (images, files)
   - Directory names correspond to resource IDs referenced in the XML

Example extracted structure:
```
REQIFZ_Archive/
├── Requirements.reqif (main XML file)
├── 1472801/
│   └── image-20240709-035006.png
├── 1487042/
│   └── image-20240711-230108.png
├── 1115144/
│   └── 384895__df6b9a18-a022-416c-bf35-509f654e2f8e.png
└── ...
```

### REQIF XML Structure

```
REQ-IF (root)
├── THE-HEADER
│   └── REQ-IF-HEADER
│       ├── CREATION-TIME
│       ├── REQ-IF-TOOL-ID
│       ├── REQ-IF-VERSION
│       └── TITLE
│
└── CORE-CONTENT
    └── REQ-IF-CONTENT
        ├── DATATYPES
        ├── SPEC-TYPES
        ├── SPEC-OBJECTS
        ├── SPEC-RELATIONS
        └── SPECIFICATIONS
```

---

## 🔗 COMPONENT LINKING MECHANISM

### 1. Data Type Layer

Defines fundamental data types used throughout the requirements:

- **DATATYPE-DEFINITION-XHTML** - Rich text with HTML formatting
- **DATATYPE-DEFINITION-STRING** - Plain text (max 2000 chars)
- **DATATYPE-DEFINITION-ENUMERATION** - Predefined value lists
- **DATATYPE-DEFINITION-REAL** - Numeric values
- **DATATYPE-DEFINITION-DATE** - DateTime values

### 2. Specification Types Layer

Defines requirement templates with attributes:

#### SPEC-OBJECT-TYPE (4 types found):
1. **Heading** - Section headers for organizing content
2. **Information** - Informational content and descriptions
3. **System Interface** - Interface specifications (signals, data)
4. **System Requirement** - Actual testable requirements

Each type has **11 standard attributes**:
1. ReqIF.Text (XHTML) - Main content
2. ReqIF.ForeignID (String) - Original requirement ID
3. ReqIF.ChapterName (String) - Section name
4. Verification Criteria (XHTML) - Test criteria
5. Verification Method (Enumeration) - How to verify
6. Verification Owner (Enumeration) - Responsible team
7. System Requirement State (Enumeration) - Approval status
8. Secondary Disciplines (Enumeration) - Additional teams
9. Primary Discipline (Enumeration) - Main responsible team
10. Key Requirement (Enumeration) - Criticality flag
11. Additional custom attributes (varies by implementation)

#### SPEC-RELATION-TYPE (3 types):
- **System Element Satisfies** - System element satisfies requirement
- **Satisfies** - General satisfaction relationship
- **Relates** - General relationship between requirements

#### SPECIFICATION-TYPE
- Document hierarchy template

### 3. Specification Objects Layer

Actual requirement instances:
- Each **SPEC-OBJECT** has a unique IDENTIFIER (UUID format)
- References a **SPEC-OBJECT-TYPE** via TYPE/SPEC-OBJECT-TYPE-REF
- Contains **VALUES** with ATTRIBUTE-VALUE-* elements
- Each attribute value references its definition via DEFINITION/*-REF

**Linking Example:**
```xml
<SPEC-OBJECT IDENTIFIER="_json2reqif_d83de6b6-6e5a-d800-3170-a1d4c98b5efe">
  <TYPE>
    <SPEC-OBJECT-TYPE-REF>_json2reqif_abc123...</SPEC-OBJECT-TYPE-REF>
  </TYPE>
  <VALUES>
    <ATTRIBUTE-VALUE-STRING>
      <DEFINITION>
        <ATTRIBUTE-DEFINITION-STRING-REF>_json2reqif_def456...</ATTRIBUTE-DEFINITION-STRING-REF>
      </DEFINITION>
      <THE-VALUE>TFDCX32348-18153</THE-VALUE>
    </ATTRIBUTE-VALUE-STRING>
  </VALUES>
</SPEC-OBJECT>
```

### 4. Hierarchy Structure

Requirements organized in tree structure:

```
SPECIFICATION
└── CHILDREN
    └── SPEC-HIERARCHY (level 1)
        ├── OBJECT → SPEC-OBJECT-REF
        └── CHILDREN
            └── SPEC-HIERARCHY (level 2)
                ├── OBJECT → SPEC-OBJECT-REF
                └── CHILDREN
                    └── ... (nested levels)
```

**Real Example from ADAS_ACC file:**
```
[Heading] TFDCX32348-8484 (Root)
[Heading] History
  └── [Information] Version history table
[Heading] Reference Document
  └── [Heading] Document references
      └── [Information] MET-S_ACC-CSTD-2-05-A-C0.xlsm
[Heading] Overview
  └── [Information] Dynamic radar cruise control description
[Heading] Input Requirements
  └── [Heading] Signal groups
      └── [System Interface] CANSignal - ACCSP
      └── [System Interface] CANSignal - ACCSPST1
      └── [System Interface] CANSignal - ACCSPEXC
      └── ... (more signals)
```

### 5. Relationship Linking

Enables traceability between requirements:
- **SOURCE** → SPEC-OBJECT-REF (originating requirement)
- **TARGET** → SPEC-OBJECT-REF (target requirement)
- **TYPE** → SPEC-RELATION-TYPE-REF (relationship type)

---

## 🖼️ EMBEDDED RESOURCES

### Images

- **Total**: 385 images across all files
- **Format**: Primarily PNG (some without extensions are nested references)
- **Storage**: In numbered directories matching folder IDs
- **Reference Format**: `folder_id/filename.png`
  - Example: `1472801/image-20240709-035006.png`
  - Example: `384895__df6b9a18-a022-416c-bf35-509f654e2f8e.png`

### Image Embedding in XHTML

Images are embedded using HTML object tags:

```xml
<div xmlns="http://www.w3.org/1999/xhtml">
  <object data="1472801/image-20240709-035006.png" type="image/png">
    <param name="attr_height" value="276"/>
    <param name="attr_width" value="468"/>
  </object>
</div>
```

**Image Reference Resolution:**
1. Parser reads the `data` attribute (e.g., `1472801/image-20240709-035006.png`)
2. Looks for folder `1472801/` in the extracted REQIFZ archive
3. Retrieves the PNG file from that folder
4. Displays inline with the requirement text

### Tables

- **Total**: 658 tables across all files
- **Format**: HTML tables within XHTML content
- **Structure**: Standard HTML `<table>`, `<tr>`, `<th>`, `<td>` elements

**Common Table Uses:**
- Version history tracking
- Signal definitions and mappings
- Logic tables and state machines
- Test case matrices
- Reference documentation lists

**Example Table Structure Found:**
```html
<table>
  <tr>
    <th>Version</th>
    <th>Date</th>
    <th>Name</th>
    <th>Description of change</th>
    <th>SRD Baseline</th>
  </tr>
  <tr>
    <td>v0.1</td>
    <td>Jul/19/2024</td>
    <td>Engineer Name</td>
    <td>Initial draft</td>
    <td>Baseline v1.0</td>
  </tr>
</table>
```

---

## 📋 COMMON ENUMERATION VALUES

### Verification Method
- Code/Design Review
- Fault Injection Test
- Functional Verification/Validation
- Software Integration Test
- Software Qualification Test
- System Integration Test
- System Qualification Test
- Unit Test
- TBD

### Verification Owner
- **CS** - Customer Support
- **FV** - Functional Verification
- **MFG** - Manufacturing
- **SW** - Software
- **SY** - System
- **TBD** - To Be Determined

### System Requirement State
- Approved
- Draft
- In Review
- Rejected
- (Other states may exist)

### Primary Discipline
- **SW** - Software
- **SY** - System
- **HW** - Hardware
- (Others as needed)

### Key Requirement Attributes

#### ReqIF.ForeignID
- Original requirement ID from source system
- Example: `TFDCX32348-18153`
- Used for traceability

#### ReqIF.ChapterName
- Section or chapter name
- Example: `Logic Table - InternalSignal - ACC_Set_Speed`

#### ReqIF.Text
- Rich formatted requirement text with images/tables
- XHTML format allowing complex content
- Contains embedded resources

#### Verification Criteria
- Test criteria in XHTML format
- Example: `Verify by executing test cases`
- Detailed acceptance criteria

---

## 🔍 KEY FINDINGS

### 1. Standardized Format
All files follow ReqIF 1.2 standard consistently, ensuring tool interoperability.

### 2. Rich Content
Requirements contain:
- Formatted text (bold, italic, lists)
- Embedded images and diagrams
- Complex tables
- Hyperlinks and cross-references

### 3. Automotive Domain
Files represent complete automotive subsystem specifications for project **TFDCX32348**, including:
- Safety-critical diagnostics
- User interface elements
- Advanced driver assistance systems
- Vehicle network communications

### 4. Traceability Ready
Structure supports full requirement tracing:
- Parent-child relationships via hierarchy
- Cross-cutting relationships via SPEC-RELATIONS
- External tool IDs via ForeignID
- Minimal actual relations found in samples (only 2 total), suggesting:
  - Relations may be managed externally
  - Files represent self-contained modules
  - Tracing happens at integration level

### 5. Self-Contained Archives
Each REQIFZ is a complete, portable archive:
- All resources bundled together
- No external dependencies
- Can be opened independently
- Full rendering capability

### 6. Hierarchical Organization
Clear document structure:
- Logical sectioning with headings
- Nested subsections
- Information grouped by category
- Easy navigation and comprehension

### 7. Comprehensive Metadata
Each requirement tracks:
- Verification method and criteria
- Ownership and responsibility
- Approval status
- Discipline assignment
- Criticality flags

### 8. Tool Compatibility
Format enables interchange between:
- IBM DOORS
- PTC Integrity
- Polarion
- ReqView
- Custom parsers and generators

---

## 📌 PRACTICAL USAGE INSIGHTS

### Project Context

These files represent a complete requirements management system for automotive project **TFDCX32348**, covering:

1. **Diagnostics Subsystems** (Largest portion - 8 files)
   - 775+ objects in Data Identifiers alone
   - DTC (Diagnostic Trouble Codes)
   - Factory test modes
   - Session management
   - Service identifiers (SID)

2. **Gauge/Instrument Cluster Displays** (7 files)
   - Oil temperature and pressure
   - Boost pressure
   - Voltage monitoring
   - Water temperature
   - Power meters

3. **Vehicle Mode Information Systems** (5 files)
   - Crawl control
   - Downhill Assist Control (DAC)
   - Drive mode selection
   - Multi-terrain selection
   - Tow/haul mode

4. **ADAS Features** (1 file)
   - Adaptive Cruise Control (ACC)
   - 170 requirement objects
   - 9 embedded images

5. **Communication Networks** (1 file)
   - CXPI Generic Network specifications

### Independence and Modularity

Each file is:
- **Independently parseable** - No cross-file dependencies
- **Self-documenting** - Contains all type definitions
- **Resource complete** - All images and files included
- **Standalone testable** - Complete verification criteria included

### Integration Patterns

When using REQIFZ files in test case generation:
1. Extract ZIP to temporary directory
2. Parse `Requirements.reqif` XML
3. Build object graph from SPEC-OBJECTS
4. Resolve hierarchy from SPECIFICATION
5. Load embedded resources as needed
6. Generate test cases from System Requirements
7. Link test cases using ForeignID for traceability

### File Size Considerations

- **Small files** (8KB - 100KB): Simple subsystems, few images
- **Medium files** (100KB - 1MB): Typical requirements with moderate images
- **Large files** (1MB - 16MB): Complex subsystems with many diagrams/tables
  - Example: DIAG_DTC_ce1123.reqifz at 16MB
  - Example: DIAG_Data Identifiers at 15MB

---

## 🛠️ TECHNICAL IMPLEMENTATION NOTES

### Parsing Recommendations

1. **Use XML namespaces properly**
   ```python
   ns = {
       'reqif': 'http://www.omg.org/spec/ReqIF/20110401/reqif.xsd',
       'html': 'http://www.w3.org/1999/xhtml'
   }
   ```

2. **Build lookup tables for performance**
   - Index all objects by IDENTIFIER
   - Index type definitions for quick reference
   - Cache attribute definitions

3. **Handle XHTML content carefully**
   - Preserve HTML structure
   - Extract text for analysis
   - Resolve image references
   - Parse tables into structured data

4. **Resource Management**
   - Extract only needed images
   - Use temporary directories
   - Clean up after processing
   - Consider caching for repeated access

### Common Pitfalls to Avoid

1. **Ignoring namespaces** - XML parsing will fail
2. **Missing IDENTIFIER-REF links** - Breaks object relationships
3. **Not handling XHTML** - Loses rich content
4. **Forgetting embedded resources** - Images won't display
5. **Flat reading** - Ignoring hierarchy loses structure

### Performance Optimization

For large files (3MB+ XML):
- Use SAX or iterative parsing instead of DOM
- Stream process when possible
- Index on first pass, query on second
- Limit in-memory object graphs

---

## 📚 REFERENCES

- **ReqIF Specification**: OMG ReqIF 1.2
- **Standard**: Requirements Interchange Format
- **XML Namespace**: http://www.omg.org/spec/ReqIF/20110401/reqif.xsd
- **XHTML Namespace**: http://www.w3.org/1999/xhtml

---

## 📝 DOCUMENT METADATA

- **Analysis Date**: October 26, 2025
- **Files Analyzed**: 28 REQIFZ files from project TFDCX32348
- **Total Data Processed**: ~50MB of requirements data
- **Analysis Tool**: Python 3.x with xml.etree.ElementTree
- **Document Version**: 1.0

---

*This document was automatically generated through comprehensive analysis of real automotive requirements files.*
