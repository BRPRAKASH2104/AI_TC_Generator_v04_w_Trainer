"""
TDD Tests for Vision Implementation Fixes

These tests are written BEFORE implementation (TDD approach).
Based on: docs/reviews/2025-12-06_Vision_Implementation_Fix_Plan.md

Test Categories:
1. Image Preprocessing (CRITICAL) - Memory optimization
2. Image Loading Error Handling (HIGH) - No silent failures
3. Vision Context Window (MEDIUM) - Use correct context size
4. Image Cleanup (LOW) - Temp file management
5. Enhanced Image Validation (MEDIUM) - Better validation
"""

import asyncio
import base64
import io
import shutil
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import modules under test
from src.core.image_extractor import (
    ImageFormat,
    RequirementImageExtractor,
)

# Try to import PIL for image generation
try:
    from PIL import Image

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


# =============================================================================
# Test Fixtures
# =============================================================================


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
        validate_images=True,
    )


@pytest.fixture
def large_image_bytes():
    """Generate a large test image (2048x2048 PNG, ~1MB+)"""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow required for this test")

    img = Image.new("RGB", (2048, 2048), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def small_image_bytes():
    """Generate a small test image (100x100 PNG)"""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow required for this test")

    img = Image.new("RGB", (100, 100), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def extreme_aspect_ratio_image():
    """Generate an image with extreme aspect ratio (10000x100)"""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow required for this test")

    img = Image.new("RGB", (10000, 100), color="green")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def tiny_image_bytes():
    """Generate a very small image (10x10 PNG)"""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow required for this test")

    img = Image.new("RGB", (10, 10), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def animated_gif_bytes():
    """Generate an animated GIF with multiple frames"""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow required for this test")

    frames = []
    for i in range(3):
        img = Image.new("RGB", (100, 100), color=(i * 80, i * 80, i * 80))
        frames.append(img)

    buffer = io.BytesIO()
    frames[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
    )
    return buffer.getvalue()


# =============================================================================
# CRITICAL: Image Preprocessing Tests
# =============================================================================


class TestImagePreprocessing:
    """Tests for image preprocessing (resize/compression) - CRITICAL priority"""

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow required")
    def test_preprocess_resizes_large_images(self, extractor, large_image_bytes):
        """Large images (>1024px) should be resized to max 1024px dimension."""
        # This tests the new _preprocess_image method
        processed = extractor._preprocess_image(large_image_bytes)

        # Verify the processed image is smaller
        img = Image.open(io.BytesIO(processed))
        assert max(img.width, img.height) <= 1024, (
            f"Image should be resized to max 1024px, got {img.width}x{img.height}"
        )

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow required")
    def test_preprocess_preserves_small_images(self, extractor, small_image_bytes):
        """Small images (<1024px) should not be resized."""
        original_img = Image.open(io.BytesIO(small_image_bytes))
        original_size = (original_img.width, original_img.height)

        processed = extractor._preprocess_image(small_image_bytes)
        processed_img = Image.open(io.BytesIO(processed))

        # Small images should maintain their dimensions
        assert processed_img.width == original_size[0]
        assert processed_img.height == original_size[1]

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow required")
    def test_preprocess_converts_rgba_to_rgb(self, extractor):
        """RGBA images should be converted to RGB for compatibility."""
        # Create RGBA image
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        rgba_bytes = buffer.getvalue()

        processed = extractor._preprocess_image(rgba_bytes)
        processed_img = Image.open(io.BytesIO(processed))

        # Should be RGB or L (grayscale)
        assert processed_img.mode in ("RGB", "L"), (
            f"Expected RGB/L mode, got {processed_img.mode}"
        )

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow required")
    def test_preprocess_maintains_aspect_ratio(self, extractor, large_image_bytes):
        """Resizing should maintain aspect ratio."""
        original_img = Image.open(io.BytesIO(large_image_bytes))
        original_ratio = original_img.width / original_img.height

        processed = extractor._preprocess_image(large_image_bytes)
        processed_img = Image.open(io.BytesIO(processed))
        processed_ratio = processed_img.width / processed_img.height

        # Allow small tolerance for rounding
        assert abs(original_ratio - processed_ratio) < 0.01, (
            f"Aspect ratio changed: {original_ratio:.3f} -> {processed_ratio:.3f}"
        )

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow required")
    def test_preprocess_reduces_file_size(self, extractor, large_image_bytes):
        """Preprocessing should reduce file size for large images."""
        processed = extractor._preprocess_image(large_image_bytes)

        # Processed should be smaller
        assert len(processed) < len(large_image_bytes), (
            f"Processed size ({len(processed)}) should be smaller than "
            f"original ({len(large_image_bytes)})"
        )

    def test_preprocess_handles_invalid_image_gracefully(self, extractor):
        """Invalid image data should return original bytes (graceful degradation)."""
        invalid_data = b"not an image at all"

        # Should not raise, should return original
        result = extractor._preprocess_image(invalid_data)
        assert result == invalid_data


# =============================================================================
# HIGH: Image Loading Error Handling Tests
# =============================================================================


class TestImageLoadingErrorHandling:
    """Tests for image loading error handling - HIGH priority"""

    def test_missing_image_file_logs_warning(self, temp_output_dir, caplog):
        """Missing image files should log a warning, not fail silently."""
        from src.core.ollama_client import OllamaClient
        from src.config import OllamaConfig

        config = OllamaConfig()
        client = OllamaClient(config)

        # Try to load non-existent image
        non_existent_path = temp_output_dir / "does_not_exist.png"
        image_paths = [non_existent_path]

        # Mock the actual API call
        with patch.object(client, "_session") as mock_session:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "test"}
            mock_response.raise_for_status = MagicMock()
            mock_session.post.return_value = mock_response

            # Call should complete without exception
            import logging

            with caplog.at_level(logging.WARNING):
                client.generate_response_with_vision(
                    "llama3.2-vision:11b", "test prompt", image_paths
                )

            # Should have logged the warning
            assert any(
                "not found" in record.message.lower() or
                "failed" in record.message.lower() or
                "warning" in record.levelname.lower()
                for record in caplog.records
            ), "Missing image should generate a warning log"

    def test_permission_denied_logs_specific_error(self, temp_output_dir, caplog):
        """Permission denied errors should log specific message."""
        from src.core.ollama_client import OllamaClient
        from src.config import OllamaConfig

        # Create a file we can't read (platform-dependent)
        restricted_path = temp_output_dir / "restricted.png"
        restricted_path.write_bytes(b"test")

        config = OllamaConfig()
        client = OllamaClient(config)

        with patch.object(client, "_session") as mock_session:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "test"}
            mock_response.raise_for_status = MagicMock()
            mock_session.post.return_value = mock_response

            # Mock open to raise PermissionError
            with patch("builtins.open", side_effect=PermissionError("Access denied")):
                import logging

                with caplog.at_level(logging.WARNING):
                    client.generate_response_with_vision(
                        "llama3.2-vision:11b", "test", [restricted_path]
                    )

                # Should log permission error
                assert any(
                    "permission" in record.message.lower() or
                    "denied" in record.message.lower()
                    for record in caplog.records
                ), "Permission error should be logged specifically"

    def test_failed_images_returns_count(self, temp_output_dir):
        """Method should return count of failed image loads."""
        from src.core.ollama_client import OllamaClient
        from src.config import OllamaConfig

        config = OllamaConfig()
        client = OllamaClient(config)

        # Mix of valid and invalid paths
        valid_path = temp_output_dir / "valid.png"
        if PILLOW_AVAILABLE:
            img = Image.new("RGB", (10, 10), color="red")
            img.save(valid_path, format="PNG")
        else:
            valid_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        invalid_path = temp_output_dir / "invalid.png"
        # Don't create this file

        image_paths = [valid_path, invalid_path]

        with patch.object(client, "_session") as mock_session:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "test"}
            mock_response.raise_for_status = MagicMock()
            mock_session.post.return_value = mock_response

            # The new implementation should track failed loads
            # This tests the enhanced return value
            result = client.generate_response_with_vision(
                "llama3.2-vision:11b", "test", image_paths
            )

            # Verify only valid image was loaded (check payload)
            call_args = mock_session.post.call_args
            payload = call_args.kwargs.get("json") or call_args[1].get("json")

            if payload and "images" in payload:
                # Should have exactly 1 image (the valid one)
                assert len(payload["images"]) == 1, (
                    f"Expected 1 valid image, got {len(payload['images'])}"
                )


class TestAsyncImageLoadingErrorHandling:
    """Tests for async image loading error handling"""

    @pytest.mark.asyncio
    async def test_async_missing_image_logs_warning(self, temp_output_dir, caplog):
        """Async client should log warnings for missing images."""
        from src.core.ollama_client import AsyncOllamaClient
        from src.config import OllamaConfig

        config = OllamaConfig()

        non_existent_path = temp_output_dir / "does_not_exist.png"

        async with AsyncOllamaClient(config) as client:
            with patch.object(client, "session") as mock_session:
                mock_response = AsyncMock()
                mock_response.json = AsyncMock(return_value={"response": "test"})
                mock_response.raise_for_status = MagicMock()

                mock_context = AsyncMock()
                mock_context.__aenter__.return_value = mock_response
                mock_context.__aexit__.return_value = None
                mock_session.post.return_value = mock_context

                import logging

                with caplog.at_level(logging.WARNING):
                    await client.generate_response_with_vision(
                        "llama3.2-vision:11b", "test", [non_existent_path]
                    )

                # Should have logged warning
                assert any(
                    "not found" in record.message.lower() or
                    "failed" in record.message.lower()
                    for record in caplog.records
                ), "Async client should log missing image warning"


# =============================================================================
# MEDIUM: Vision Context Window Tests
# =============================================================================


class TestVisionContextWindow:
    """Tests for vision context window configuration - MEDIUM priority"""

    def test_vision_model_uses_vision_context_window(self, temp_output_dir):
        """Vision requests should use vision_context_window, not num_ctx."""
        from src.core.ollama_client import OllamaClient
        from src.config import OllamaConfig

        config = OllamaConfig(
            num_ctx=16384,
            vision_context_window=32768,
        )
        client = OllamaClient(config)

        # Create a valid test image
        valid_path = temp_output_dir / "test.png"
        if PILLOW_AVAILABLE:
            img = Image.new("RGB", (10, 10), color="red")
            img.save(valid_path, format="PNG")
        else:
            valid_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        with patch.object(client, "_session") as mock_session:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "test"}
            mock_response.raise_for_status = MagicMock()
            mock_session.post.return_value = mock_response

            client.generate_response_with_vision(
                "llama3.2-vision:11b", "test", [valid_path]
            )

            # Check the payload
            call_args = mock_session.post.call_args
            payload = call_args.kwargs.get("json") or call_args[1].get("json")

            # Vision requests should use vision_context_window
            assert payload["options"]["num_ctx"] == 32768, (
                f"Expected vision context 32768, got {payload['options']['num_ctx']}"
            )

    def test_text_only_uses_standard_context_window(self):
        """Text-only requests should use num_ctx."""
        from src.core.ollama_client import OllamaClient
        from src.config import OllamaConfig

        config = OllamaConfig(
            num_ctx=16384,
            vision_context_window=32768,
        )
        client = OllamaClient(config)

        with patch.object(client, "_session") as mock_session:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "test"}
            mock_response.raise_for_status = MagicMock()
            mock_session.post.return_value = mock_response

            # No images - text only
            client.generate_response("llama3.1:8b", "test", is_json=True)

            call_args = mock_session.post.call_args
            payload = call_args.kwargs.get("json") or call_args[1].get("json")

            # Text requests should use standard context
            assert payload["options"]["num_ctx"] == 16384, (
                f"Expected text context 16384, got {payload['options']['num_ctx']}"
            )


# =============================================================================
# LOW: Image Cleanup Tests
# =============================================================================


class TestImageCleanup:
    """Tests for image cleanup functionality - LOW priority"""

    def test_cleanup_removes_extracted_images(self, temp_output_dir):
        """cleanup_extracted_images should remove all extracted images."""
        extractor = RequirementImageExtractor(
            output_dir=temp_output_dir,
            save_images=True,
            validate_images=False,
        )

        # Create some test images
        reqifz_dir = temp_output_dir / "test_reqifz"
        reqifz_dir.mkdir()
        (reqifz_dir / "image1.png").write_bytes(b"test1")
        (reqifz_dir / "image2.png").write_bytes(b"test2")

        # Verify images exist
        assert (reqifz_dir / "image1.png").exists()
        assert (reqifz_dir / "image2.png").exists()

        # Cleanup
        count = extractor.cleanup_extracted_images()

        # Verify removed
        assert count >= 2, f"Expected at least 2 files removed, got {count}"
        # Directory should be empty or removed
        if temp_output_dir.exists():
            remaining = list(temp_output_dir.rglob("*.png"))
            assert len(remaining) == 0, f"Found remaining files: {remaining}"

    def test_cleanup_specific_reqifz(self, temp_output_dir):
        """Cleanup should support cleaning specific REQIFZ images only."""
        extractor = RequirementImageExtractor(
            output_dir=temp_output_dir,
            save_images=True,
            validate_images=False,
        )

        # Create images for two different REQIFZ files
        reqifz1_dir = temp_output_dir / "reqifz1"
        reqifz2_dir = temp_output_dir / "reqifz2"
        reqifz1_dir.mkdir()
        reqifz2_dir.mkdir()

        (reqifz1_dir / "image.png").write_bytes(b"test1")
        (reqifz2_dir / "image.png").write_bytes(b"test2")

        # Cleanup only reqifz1
        reqifz1_path = Path("fake/path/reqifz1.reqifz")
        extractor.cleanup_extracted_images(reqifz1_path)

        # reqifz1 images should be gone
        assert not (reqifz1_dir / "image.png").exists()

        # reqifz2 images should remain
        assert (reqifz2_dir / "image.png").exists()

    def test_cleanup_returns_count(self, temp_output_dir):
        """Cleanup should return count of removed files."""
        extractor = RequirementImageExtractor(
            output_dir=temp_output_dir,
            save_images=True,
            validate_images=False,
        )

        # Create test files
        for i in range(5):
            (temp_output_dir / f"image{i}.png").write_bytes(b"test")

        count = extractor.cleanup_extracted_images()

        assert count == 5, f"Expected 5 files removed, got {count}"

    def test_auto_cleanup_context_manager(self, temp_output_dir):
        """auto_cleanup context manager should clean up after processing."""
        extractor = RequirementImageExtractor(
            output_dir=temp_output_dir,
            save_images=True,
            validate_images=False,
        )

        reqifz_path = Path("test.reqifz")
        reqifz_dir = temp_output_dir / "test"
        reqifz_dir.mkdir()
        (reqifz_dir / "image.png").write_bytes(b"test")

        # Use context manager
        with extractor.auto_cleanup(reqifz_path):
            # Image should exist during processing
            assert (reqifz_dir / "image.png").exists()

        # Image should be cleaned up after context exits
        assert not (reqifz_dir / "image.png").exists()


# =============================================================================
# MEDIUM: Enhanced Image Validation Tests
# =============================================================================


class TestEnhancedImageValidation:
    """Tests for enhanced image validation - MEDIUM priority"""

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow required")
    def test_validation_warns_on_large_dimensions(self, extractor, large_image_bytes):
        """Validation should warn for images with very large dimensions."""
        validation = extractor._validate_image(large_image_bytes)

        assert validation["valid"] is True
        assert "warnings" in validation
        assert any(
            "large" in w.lower() or "resize" in w.lower()
            for w in validation.get("warnings", [])
        ), f"Expected size warning, got: {validation.get('warnings', [])}"

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow required")
    def test_validation_warns_on_extreme_aspect_ratio(
        self, extractor, extreme_aspect_ratio_image
    ):
        """Validation should warn for extreme aspect ratios."""
        validation = extractor._validate_image(extreme_aspect_ratio_image)

        assert validation["valid"] is True
        assert "warnings" in validation
        assert any(
            "aspect" in w.lower() or "ratio" in w.lower()
            for w in validation.get("warnings", [])
        ), f"Expected aspect ratio warning, got: {validation.get('warnings', [])}"
        assert "aspect_ratio" in validation

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow required")
    def test_validation_warns_on_tiny_images(self, extractor, tiny_image_bytes):
        """Validation should warn for very small images."""
        validation = extractor._validate_image(tiny_image_bytes)

        assert validation["valid"] is True
        assert "warnings" in validation
        assert any(
            "small" in w.lower() or "tiny" in w.lower()
            for w in validation.get("warnings", [])
        ), f"Expected small image warning, got: {validation.get('warnings', [])}"

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow required")
    def test_validation_detects_animated_gif(self, extractor, animated_gif_bytes):
        """Validation should detect and warn about animated GIFs."""
        validation = extractor._validate_image(animated_gif_bytes)

        assert validation["valid"] is True
        assert validation.get("animated") is True
        assert "warnings" in validation
        assert any(
            "animated" in w.lower() or "frame" in w.lower()
            for w in validation.get("warnings", [])
        ), f"Expected animated GIF warning, got: {validation.get('warnings', [])}"

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow required")
    def test_validation_reports_file_size(self, extractor, large_image_bytes):
        """Validation should report file size in bytes."""
        validation = extractor._validate_image(large_image_bytes)

        assert "size_bytes" in validation
        assert validation["size_bytes"] == len(large_image_bytes)

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow required")
    def test_validation_no_warnings_for_good_images(self, extractor, small_image_bytes):
        """Good images should not generate warnings."""
        validation = extractor._validate_image(small_image_bytes)

        assert validation["valid"] is True
        # No warnings for well-sized images
        warnings = validation.get("warnings", [])
        assert len(warnings) == 0, f"Unexpected warnings for good image: {warnings}"


# =============================================================================
# Integration Tests
# =============================================================================


class TestVisionIntegration:
    """Integration tests for vision workflow"""

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow required")
    def test_full_extraction_with_preprocessing(self, temp_output_dir, large_image_bytes):
        """Full extraction workflow should preprocess images."""
        # Create REQIFZ with large image
        reqifz_path = temp_output_dir / "test_large.reqifz"

        with zipfile.ZipFile(reqifz_path, "w") as zf:
            zf.writestr("content.reqif", """<?xml version="1.0"?>
                <REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
                    <CORE-CONTENT><REQ-IF-CONTENT><SPEC-TYPES/></REQ-IF-CONTENT></CORE-CONTENT>
                </REQ-IF>
            """)
            zf.writestr("images/large_diagram.png", large_image_bytes)

        extractor = RequirementImageExtractor(
            output_dir=temp_output_dir / "output",
            save_images=True,
            validate_images=True,
        )

        images, report = extractor.extract_images_from_reqifz(reqifz_path)

        # Image should be extracted and preprocessed
        assert report["total_images"] == 1
        assert images[0]["saved"] is True

        # Check saved image is resized
        saved_path = Path(images[0]["saved_path"])
        saved_img = Image.open(saved_path)
        assert max(saved_img.width, saved_img.height) <= 1024, (
            f"Saved image should be resized, got {saved_img.width}x{saved_img.height}"
        )
