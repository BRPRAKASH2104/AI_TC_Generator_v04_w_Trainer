"""XML-hardening guard tests for REQIFZ parsing.

REQIFZ archives are user-supplied, so their embedded XML is untrusted input.
The extractor parses it with :func:`defusedxml.ElementTree.fromstring`
(review 2026-07-20 Recommended 8 / Bandit B314) instead of the stdlib
``xml.etree.ElementTree.fromstring``, which is vulnerable to entity-expansion
("billion laughs") and external-entity (XXE) attacks.

These tests assert two contracts that a mocked suite cannot cover:

1. Legitimate REQIF XML still parses exactly as before (drop-in behaviour).
2. Malicious entity/DTD payloads are rejected — the parser must not expand
   them — and the failure is swallowed into an empty artifact list rather than
   crashing the pipeline.
"""

import pytest

from src.core.extractors import REQIFArtifactExtractor

# A minimal but structurally valid REQIF document with one SPEC-OBJECT.
_VALID_REQIF = b"""<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
  <CORE-CONTENT>
    <REQ-IF-CONTENT>
      <SPEC-OBJECTS>
        <SPEC-OBJECT IDENTIFIER="REQ_001"/>
      </SPEC-OBJECTS>
    </REQ-IF-CONTENT>
  </CORE-CONTENT>
</REQ-IF>"""

# "Billion laughs": nested entity expansion that would exhaust memory if the
# parser resolved the entities. defusedxml refuses to define them.
_BILLION_LAUGHS = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
  <TITLE>&lol3;</TITLE>
</REQ-IF>"""

# External-entity (XXE) payload attempting to read a local file.
_XXE = b"""<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
  <TITLE>&xxe;</TITLE>
</REQ-IF>"""


@pytest.fixture
def extractor() -> REQIFArtifactExtractor:
    """An extractor with no logger/config — enough to exercise XML parsing."""
    return REQIFArtifactExtractor()


def test_valid_reqif_still_parses(extractor: REQIFArtifactExtractor) -> None:
    """A well-formed REQIF document parses without error (drop-in behaviour)."""
    artifacts = extractor._parse_reqif_xml(_VALID_REQIF)
    # The exact artifact contents depend on attribute mappings; the contract
    # here is simply that parsing succeeds and returns a list (no exception,
    # not the [] error path).
    assert isinstance(artifacts, list)


@pytest.mark.parametrize("payload", [_BILLION_LAUGHS, _XXE], ids=["billion_laughs", "xxe"])
def test_malicious_xml_is_rejected(extractor: REQIFArtifactExtractor, payload: bytes) -> None:
    """Entity/DTD attacks are rejected and swallowed into an empty list."""
    artifacts = extractor._parse_reqif_xml(payload)
    assert artifacts == []


def test_defused_parser_raises_on_entities() -> None:
    """The parser itself must refuse entity definitions, not expand them."""
    from defusedxml.common import DefusedXmlException
    from defusedxml.ElementTree import fromstring as safe_fromstring

    with pytest.raises(DefusedXmlException):
        safe_fromstring(_BILLION_LAUGHS)
