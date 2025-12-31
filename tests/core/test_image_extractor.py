"""Tests for image extraction from REQIFZ files"""

import base64
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from core.image_extractor import (
    ImageFormat,
    ImageSource,
    RequirementImageExtractor,
)

# Sample 1x1 PNG image (base64-encoded)
SAMPLE_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
SAMPLE_PNG_BYTES = base64.b64decode(SAMPLE_PNG_BASE64)

# Sample 1x1 JPEG image (base64-encoded)
SAMPLE_JPEG_BASE64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k="
SAMPLE_JPEG_BYTES = base64.b64decode(SAMPLE_JPEG_BASE64)


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory"""
    temp_dir = TemporaryDirectory()
    yield Path(temp_dir.name)
    temp_dir.cleanup()


@pytest.fixture
def extractor(temp_output_dir):
    """Create image extractor instance"""
    return RequirementImageExtractor(
        output_dir=temp_output_dir,
        save_images=True,
        validate_images=False,  # Disable validation for tests without Pillow
    )


@pytest.fixture
def sample_reqifz_with_external_images(temp_output_dir):
    """Create a temporary REQIFZ file with external image files"""
    reqif_content = """<?xml version="1.0" encoding="UTF-8"?>
    <REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
        <CORE-CONTENT>
            <REQ-IF-CONTENT>
                <SPEC-TYPES>
                    <SPEC-OBJECT-TYPE IDENTIFIER="OBJ-TYPE-001" LONG-NAME="System Requirement"/>
                </SPEC-TYPES>
            </REQ-IF-CONTENT>
        </CORE-CONTENT>
    </REQ-IF>
    """

    # Create temporary REQIFZ file with images
    temp_dir = TemporaryDirectory()
    reqifz_path = Path(temp_dir.name) / "test_with_images.reqifz"

    with zipfile.ZipFile(reqifz_path, "w") as zip_file:
        zip_file.writestr("content.reqif", reqif_content)
        zip_file.writestr("images/diagram.png", SAMPLE_PNG_BYTES)
        zip_file.writestr("images/screenshot.jpg", SAMPLE_JPEG_BYTES)

    yield reqifz_path

    # Cleanup
    temp_dir.cleanup()


@pytest.fixture
def sample_reqifz_with_embedded_images(temp_output_dir):
    """Create a temporary REQIFZ file with base64-embedded images"""
    reqif_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"
            xmlns:xhtml="http://www.w3.org/1999/xhtml">
        <CORE-CONTENT>
            <REQ-IF-CONTENT>
                <SPEC-TYPES>
                    <SPEC-OBJECT-TYPE IDENTIFIER="OBJ-TYPE-001" LONG-NAME="System Requirement">
                        <SPEC-ATTRIBUTES>
                            <ATTRIBUTE-DEFINITION-XHTML IDENTIFIER="ATTR-TEXT-001" LONG-NAME="ReqIF.Text"/>
                        </SPEC-ATTRIBUTES>
                    </SPEC-OBJECT-TYPE>
                </SPEC-TYPES>
                <SPEC-OBJECTS>
                    <SPEC-OBJECT IDENTIFIER="OBJ-001">
                        <TYPE>
                            <SPEC-OBJECT-TYPE-REF>OBJ-TYPE-001</SPEC-OBJECT-TYPE-REF>
                        </TYPE>
                        <VALUES>
                            <ATTRIBUTE-VALUE-XHTML>
                                <DEFINITION>
                                    <ATTRIBUTE-DEFINITION-XHTML-REF>ATTR-TEXT-001</ATTRIBUTE-DEFINITION-XHTML-REF>
                                </DEFINITION>
                                <THE-VALUE>
                                    <xhtml:div>
                                        <xhtml:p>Requirement with embedded image:</xhtml:p>
                                        <xhtml:img src="data:image/png;base64,{SAMPLE_PNG_BASE64}" alt="Diagram"/>
                                    </xhtml:div>
                                </THE-VALUE>
                            </ATTRIBUTE-VALUE-XHTML>
                        </VALUES>
                    </SPEC-OBJECT>
                </SPEC-OBJECTS>
            </REQ-IF-CONTENT>
        </CORE-CONTENT>
    </REQ-IF>
    """

    # Create temporary REQIFZ file
    temp_dir = TemporaryDirectory()
    reqifz_path = Path(temp_dir.name) / "test_with_embedded.reqifz"

    with zipfile.ZipFile(reqifz_path, "w") as zip_file:
        zip_file.writestr("content.reqif", reqif_content)

    yield reqifz_path

    # Cleanup
    temp_dir.cleanup()


def test_extract_external_images(extractor, sample_reqifz_with_external_images):
    """Test extraction of external image files"""
    images, report = extractor.extract_images_from_reqifz(sample_reqifz_with_external_images)

    assert report["total_images"] == 2
    assert report["external_files"] == 2
    assert report["embedded_images"] == 0

    # Check PNG image
    png_image = next(img for img in images if "png" in img["filename"])
    assert png_image["source"] == ImageSource.EXTERNAL_FILE
    assert png_image["format"] == ImageFormat.PNG
    assert png_image["size_bytes"] == len(SAMPLE_PNG_BYTES)
    assert png_image["saved"] is True
    assert "saved_path" in png_image

    # Check JPEG image
    jpeg_image = next(img for img in images if "jpg" in img["filename"])
    assert jpeg_image["source"] == ImageSource.EXTERNAL_FILE
    assert jpeg_image["format"] in [ImageFormat.JPG, ImageFormat.JPEG]
    assert jpeg_image["saved"] is True


def test_extract_embedded_images(extractor, sample_reqifz_with_embedded_images):
    """Test extraction of base64-embedded images"""
    images, report = extractor.extract_images_from_reqifz(sample_reqifz_with_embedded_images)

    assert report["total_images"] == 1
    assert report["external_files"] == 0
    assert report["embedded_images"] == 1

    # Check embedded image
    image = images[0]
    assert image["source"] == ImageSource.BASE64_EMBEDDED
    assert image["format"] == ImageFormat.PNG
    assert image["size_bytes"] == len(SAMPLE_PNG_BYTES)
    assert image["saved"] is True
    assert "saved_path" in image
    assert "hash" in image


def test_extract_images_without_saving(sample_reqifz_with_external_images, temp_output_dir):
    """Test extraction without saving images"""
    extractor = RequirementImageExtractor(
        output_dir=temp_output_dir, save_images=False, validate_images=False
    )

    images, report = extractor.extract_images_from_reqifz(sample_reqifz_with_external_images)

    assert report["total_images"] == 2
    assert report["saved_images"] == 0

    for image in images:
        assert image["saved"] is False
        assert "saved_path" not in image


def test_determine_image_format():
    """Test image format determination"""
    extractor = RequirementImageExtractor(save_images=False, validate_images=False)

    # Test PNG
    assert extractor._determine_image_format("test.png", SAMPLE_PNG_BYTES) == ImageFormat.PNG
    assert extractor._determine_image_format("test.unknown", SAMPLE_PNG_BYTES) == ImageFormat.PNG

    # Test JPEG
    assert (
        extractor._determine_image_format("test.jpg", SAMPLE_JPEG_BYTES) == ImageFormat.JPG
    )
    assert (
        extractor._determine_image_format("test.unknown", SAMPLE_JPEG_BYTES) == ImageFormat.JPEG
    )

    # Test unknown
    unknown_data = b"not an image"
    assert (
        extractor._determine_image_format("test.unknown", unknown_data) == ImageFormat.UNKNOWN
    )


def test_compute_hash():
    """Test hash computation"""
    extractor = RequirementImageExtractor(save_images=False, validate_images=False)

    hash1 = extractor._compute_hash(SAMPLE_PNG_BYTES)
    hash2 = extractor._compute_hash(SAMPLE_PNG_BYTES)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex digest


def test_sanitize_filename():
    """Test filename sanitization"""
    extractor = RequirementImageExtractor(save_images=False, validate_images=False)

    # Test with unsafe characters
    assert extractor._sanitize_filename("test<file>.png") == "test_file_.png"
    assert extractor._sanitize_filename("path/to/file.png") == "file.png"
    assert extractor._sanitize_filename("safe_file.png") == "safe_file.png"


def test_augment_artifacts_with_images(extractor):
    """Test augmenting artifacts with image references"""
    # Create sample artifacts
    artifacts = [
        {
            "id": "REQ-001",
            "text": f'<div><img src="data:image/png;base64,{SAMPLE_PNG_BASE64}"/></div>',
        },
        {
            "id": "REQ-002",
            "text": "<div>No images here</div>",
        },
    ]

    # Create sample images
    images = [
        {
            "source": ImageSource.BASE64_EMBEDDED,
            "format": ImageFormat.PNG,
            "hash": extractor._compute_hash(SAMPLE_PNG_BYTES),
            "size_bytes": len(SAMPLE_PNG_BYTES),
        }
    ]

    # Augment artifacts
    augmented = extractor.augment_artifacts_with_images(artifacts, images)

    # Check first artifact (has image)
    assert augmented[0]["has_images"] is True
    assert "images" in augmented[0]
    assert len(augmented[0]["images"]) == 1

    # Check second artifact (no images)
    assert augmented[1]["has_images"] is False


def test_extract_images_from_empty_reqifz(extractor, temp_output_dir):
    """Test extraction from REQIFZ without images"""
    # Create empty REQIFZ
    reqif_content = """<?xml version="1.0" encoding="UTF-8"?>
    <REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
        <CORE-CONTENT>
            <REQ-IF-CONTENT>
                <SPEC-TYPES/>
            </REQ-IF-CONTENT>
        </CORE-CONTENT>
    </REQ-IF>
    """

    temp_dir = TemporaryDirectory()
    reqifz_path = Path(temp_dir.name) / "test_empty.reqifz"

    with zipfile.ZipFile(reqifz_path, "w") as zip_file:
        zip_file.writestr("content.reqif", reqif_content)

    images, report = extractor.extract_images_from_reqifz(reqifz_path)

    assert report["total_images"] == 0
    assert report["external_files"] == 0
    assert report["embedded_images"] == 0

    temp_dir.cleanup()


def test_image_source_enum():
    """Test ImageSource enum values"""
    assert ImageSource.EXTERNAL_FILE == "external_file"
    assert ImageSource.BASE64_EMBEDDED == "base64_embedded"
    assert ImageSource.OBJECT_ELEMENT == "object_element"
    assert ImageSource.XHTML_IMG == "xhtml_img"


def test_image_format_enum():
    """Test ImageFormat enum values"""
    assert ImageFormat.PNG == "png"
    assert ImageFormat.JPEG == "jpeg"
    assert ImageFormat.JPG == "jpg"
    assert ImageFormat.SVG == "svg"


def test_multiple_embedded_images(temp_output_dir):
    """Test extraction of multiple embedded images"""
    reqif_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"
            xmlns:xhtml="http://www.w3.org/1999/xhtml">
        <CORE-CONTENT>
            <REQ-IF-CONTENT>
                <SPEC-TYPES>
                    <SPEC-OBJECT-TYPE IDENTIFIER="OBJ-TYPE-001" LONG-NAME="System Requirement">
                        <SPEC-ATTRIBUTES>
                            <ATTRIBUTE-DEFINITION-XHTML IDENTIFIER="ATTR-TEXT-001" LONG-NAME="ReqIF.Text"/>
                        </SPEC-ATTRIBUTES>
                    </SPEC-OBJECT-TYPE>
                </SPEC-TYPES>
                <SPEC-OBJECTS>
                    <SPEC-OBJECT IDENTIFIER="OBJ-001">
                        <TYPE>
                            <SPEC-OBJECT-TYPE-REF>OBJ-TYPE-001</SPEC-OBJECT-TYPE-REF>
                        </TYPE>
                        <VALUES>
                            <ATTRIBUTE-VALUE-XHTML>
                                <DEFINITION>
                                    <ATTRIBUTE-DEFINITION-XHTML-REF>ATTR-TEXT-001</ATTRIBUTE-DEFINITION-XHTML-REF>
                                </DEFINITION>
                                <THE-VALUE>
                                    <xhtml:div>
                                        <xhtml:img src="data:image/png;base64,{SAMPLE_PNG_BASE64}"/>
                                        <xhtml:img src="data:image/jpeg;base64,{SAMPLE_JPEG_BASE64}"/>
                                    </xhtml:div>
                                </THE-VALUE>
                            </ATTRIBUTE-VALUE-XHTML>
                        </VALUES>
                    </SPEC-OBJECT>
                </SPEC-OBJECTS>
            </REQ-IF-CONTENT>
        </CORE-CONTENT>
    </REQ-IF>
    """

    temp_dir = TemporaryDirectory()
    reqifz_path = Path(temp_dir.name) / "test_multiple.reqifz"

    with zipfile.ZipFile(reqifz_path, "w") as zip_file:
        zip_file.writestr("content.reqif", reqif_content)

    extractor = RequirementImageExtractor(
        output_dir=temp_output_dir, save_images=True, validate_images=False
    )

    images, report = extractor.extract_images_from_reqifz(reqifz_path)

    assert report["total_images"] == 2
    assert report["embedded_images"] == 2

    # Check both image formats
    formats = [img["format"] for img in images]
    assert ImageFormat.PNG in formats
    assert ImageFormat.JPEG in formats

    temp_dir.cleanup()


def test_augment_artifacts_without_images(extractor):
    """Test augmenting artifacts when no images present"""
    artifacts = [
        {"id": "REQ-001", "text": "Plain text requirement"},
        {"id": "REQ-002", "text": "Another plain text requirement"},
    ]

    images = []

    augmented = extractor.augment_artifacts_with_images(artifacts, images)

    for artifact in augmented:
        assert artifact["has_images"] is False
        assert "images" not in artifact or len(artifact.get("images", [])) == 0
