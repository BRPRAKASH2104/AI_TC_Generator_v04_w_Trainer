import os
import io
import copy
from pathlib import Path
import xml.etree.ElementTree as ET
from src.core.extractors import REQIFArtifactExtractor

large_xml_parts = ['<?xml version="1.0" encoding="UTF-8"?><reqif:REQ-IF xmlns:reqif="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd" xmlns:html="http://www.w3.org/1999/xhtml"><reqif:CORE-CONTENT><reqif:SPEC-OBJECT-TYPE IDENTIFIER="TYPE_001" LONG-NAME="System Requirement"><reqif:ATTRIBUTE-DEFINITION-STRING LONG-NAME="ReqIF.ForeignID" IDENTIFIER="ATTR_001"/></reqif:SPEC-OBJECT-TYPE><reqif:SPEC-OBJECTS>']

for i in range(2):
    spec_object = f'<reqif:SPEC-OBJECT IDENTIFIER="REQ_{i:03d}"><reqif:TYPE><reqif:SPEC-OBJECT-TYPE-REF>TYPE_001</reqif:SPEC-OBJECT-TYPE-REF></reqif:TYPE><reqif:VALUES><reqif:ATTRIBUTE-VALUE-STRING THE-VALUE="REQ_{i:03d}"><reqif:DEFINITION><reqif:ATTRIBUTE-DEFINITION-STRING-REF>ATTR_001</reqif:ATTRIBUTE-DEFINITION-STRING-REF></reqif:DEFINITION></reqif:ATTRIBUTE-VALUE-STRING><reqif:ATTRIBUTE-VALUE-XHTML><reqif:DEFINITION><reqif:ATTRIBUTE-DEFINITION-XHTML-REF>TEXT_ATTR</reqif:ATTRIBUTE-DEFINITION-XHTML-REF></reqif:DEFINITION><reqif:THE-VALUE><html:div>The system requirement {i} shall work properly.</html:div></reqif:THE-VALUE></reqif:ATTRIBUTE-VALUE-XHTML></reqif:VALUES></reqif:SPEC-OBJECT>'
    large_xml_parts.append(spec_object)

large_xml_parts.append('</reqif:SPEC-OBJECTS></reqif:CORE-CONTENT></reqif:REQ-IF>')
large_xml_content = ''.join(large_xml_parts).encode('utf-8')

namespaces = {
    "reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
    "html": "http://www.w3.org/1999/xhtml",
}

extractor = REQIFArtifactExtractor(use_streaming=True)
spec_type_map, foreign_id_map = extractor._build_mappings_streaming(large_xml_content, namespaces)

artifacts = []
for _, elem in ET.iterparse(io.BytesIO(large_xml_content), events=("end",)):
    if elem.tag.endswith("}SPEC-OBJECT"):
        print(f"Parsing: {elem}")
        artifact = extractor._extract_spec_object(
            elem, namespaces, spec_type_map, foreign_id_map
        )
        print(f"Extracted inside loop: {artifact}")
        if artifact:
            artifacts.append(artifact)

    # Clear large elements to save memory (important for streaming)
    if elem.tag.endswith("}SPEC-OBJECT") or elem.tag.endswith("}SPEC-OBJECT-TYPE") or elem.tag.endswith("}SPEC-RELATION"):
        elem.clear()
        if hasattr(elem, "getparent") and elem.getparent() is not None:
             pass # avoiding lxml specific getparent issue potentially

print(f"Total extracted with clear: {len(artifacts)}")

# What happens if we do ONLY the extraction:
artifacts2 = extractor._extract_spec_objects_streaming(large_xml_content, namespaces, spec_type_map, foreign_id_map)
print(f"Method returned: {len(artifacts2)}")

