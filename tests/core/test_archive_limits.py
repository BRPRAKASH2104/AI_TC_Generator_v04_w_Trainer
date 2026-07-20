"""Regression tests for REQIFZ archive-safety limits (ZIP-bomb defence).

These cover the primitives in ``src.core.archive_limits`` and their wiring into
``REQIFArtifactExtractor`` and ``RequirementImageExtractor``. Limits are
monkeypatched to small values where a realistic fixture would otherwise need to
be large; the compression-ratio case uses a genuine (tiny) deflate bomb.
"""

import zipfile
from typing import TYPE_CHECKING

import pytest

from src.core import archive_limits
from src.core.archive_limits import (
    ArchiveLimitError,
    safe_zip_read,
    validate_archive_safety,
)
from src.core.extractors import REQIFArtifactExtractor
from src.core.image_extractor import RequirementImageExtractor

if TYPE_CHECKING:
    from pathlib import Path


def _make_zip(
    path: Path, entries: dict[str, bytes], compression: int = zipfile.ZIP_DEFLATED
) -> Path:
    """Write ``entries`` (name -> bytes) into a ZIP file at ``path``."""
    with zipfile.ZipFile(path, "w", compression) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return path


# --------------------------------------------------------------------------- #
# validate_archive_safety
# --------------------------------------------------------------------------- #


def test_valid_archive_passes(tmp_path):
    archive = _make_zip(tmp_path / "ok.reqifz", {"spec.reqif": b"<reqif/>"})
    with zipfile.ZipFile(archive) as zf:
        validate_archive_safety(zf)  # must not raise


def test_rejects_too_many_entries(tmp_path, monkeypatch):
    monkeypatch.setattr(archive_limits, "MAX_ARCHIVE_ENTRIES", 3)
    archive = _make_zip(
        tmp_path / "many.reqifz",
        {f"f{i}.txt": b"x" for i in range(5)},
    )
    with zipfile.ZipFile(archive) as zf:
        with pytest.raises(ArchiveLimitError):
            validate_archive_safety(zf)


def test_rejects_oversized_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(archive_limits, "MAX_ENTRY_UNCOMPRESSED_SIZE", 16)
    archive = _make_zip(tmp_path / "big.reqifz", {"spec.reqif": b"a" * 64})
    with zipfile.ZipFile(archive) as zf:
        with pytest.raises(ArchiveLimitError):
            validate_archive_safety(zf)


def test_rejects_oversized_total(tmp_path, monkeypatch):
    monkeypatch.setattr(archive_limits, "MAX_TOTAL_UNCOMPRESSED_SIZE", 64)
    archive = _make_zip(
        tmp_path / "total.reqifz",
        {f"f{i}.txt": b"a" * 40 for i in range(3)},
    )
    with zipfile.ZipFile(archive) as zf:
        with pytest.raises(ArchiveLimitError):
            validate_archive_safety(zf)


def test_rejects_high_compression_ratio(tmp_path):
    # 1 MiB of zeros compresses to a few dozen bytes -> ratio well over 100:1.
    archive = _make_zip(tmp_path / "bomb.reqifz", {"bomb.reqif": b"\x00" * (1024 * 1024)})
    with zipfile.ZipFile(archive) as zf:
        with pytest.raises(ArchiveLimitError):
            validate_archive_safety(zf)


def test_tiny_compressible_entry_is_exempt_from_ratio(tmp_path):
    # Below _RATIO_MIN_SIZE: highly compressible but too small to be a bomb.
    archive = _make_zip(tmp_path / "small.reqifz", {"spec.reqif": b"\x00" * 512})
    with zipfile.ZipFile(archive) as zf:
        validate_archive_safety(zf)  # must not raise


# --------------------------------------------------------------------------- #
# safe_zip_read
# --------------------------------------------------------------------------- #


def test_safe_zip_read_returns_data_within_cap(tmp_path):
    archive = _make_zip(tmp_path / "r.reqifz", {"spec.reqif": b"hello world"})
    with zipfile.ZipFile(archive) as zf:
        assert safe_zip_read(zf, "spec.reqif", 1024) == b"hello world"


def test_safe_zip_read_rejects_over_cap(tmp_path):
    archive = _make_zip(tmp_path / "r.reqifz", {"spec.reqif": b"a" * 500})
    with zipfile.ZipFile(archive) as zf:
        with pytest.raises(ArchiveLimitError):
            safe_zip_read(zf, "spec.reqif", 100)


# --------------------------------------------------------------------------- #
# End-to-end wiring
# --------------------------------------------------------------------------- #


def test_extractor_rejects_compression_bomb(tmp_path):
    archive = _make_zip(tmp_path / "bomb.reqifz", {"bomb.reqif": b"\x00" * (1024 * 1024)})
    extractor = REQIFArtifactExtractor()
    assert extractor.extract_reqifz_content(archive) == []


def test_image_extractor_rejects_compression_bomb(tmp_path):
    archive = _make_zip(tmp_path / "bomb.reqifz", {"bomb.reqif": b"\x00" * (1024 * 1024)})
    extractor = RequirementImageExtractor(output_dir=tmp_path / "out", save_images=False)
    images, report = extractor.extract_images_from_reqifz(archive)
    assert images == []
    assert "error" in report


def test_oversized_image_is_rejected_not_saved(tmp_path, monkeypatch):
    # A single oversized image entry must be rejected before it is saved.
    monkeypatch.setattr("src.core.image_extractor.MAX_FILE_SIZE", 64)
    archive = _make_zip(
        tmp_path / "img.reqifz",
        {"spec.reqif": b"<reqif/>", "big.png": b"\x89PNG" + b"\x01" * 4096},
        compression=zipfile.ZIP_STORED,  # avoid tripping the ratio guard first
    )
    extractor = RequirementImageExtractor(output_dir=tmp_path / "out", save_images=True)
    images, _ = extractor.extract_images_from_reqifz(archive)
    # The oversized image is recorded as failed, never saved.
    assert all(not img.get("saved") for img in images)
    assert any("error" in img for img in images)
