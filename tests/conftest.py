import pytest
from pathlib import Path

@pytest.fixture
def test_file(tmp_path: Path) -> Path:
    """Create a dummy reqifz file for testing."""
    reqifz_content = """<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
  <THE-HEADER>
    <REQ-IF-HEADER IDENTIFIER="_12345">
      <REQ-IF-VERSION>1.0</REQ-IF-VERSION>
      <SOURCE-TOOL-ID>test</SOURCE-TOOL-ID>
      <TITLE>test</TITLE>
    </REQ-IF-HEADER>
  </THE-HEADER>
  <CORE-CONTENT>
    <REQ-IF-CONTENT>
    </REQ-IF-CONTENT>
  </CORE-CONTENT>
</REQ-IF>
"""
    reqif_file = tmp_path / "test.reqif"
    reqif_file.write_text(reqifz_content)

    import zipfile
    reqifz_file = tmp_path / "test.reqifz"
    with zipfile.ZipFile(reqifz_file, "w") as zf:
        zf.write(reqif_file, "test.reqif")

    return reqifz_file
