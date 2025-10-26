"""
Image extraction module for REQIFZ files.

This module provides functionality to extract and process images from REQIFZ files,
including external image files, base64-encoded images, and embedded objects.
"""

import base64
import hashlib
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from enum import StrEnum
from pathlib import Path
from typing import Any

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Type aliases for better readability (PEP 695 style)
type ImageData = dict[str, Any]
type ImageList = list[ImageData]


class ImageFormat(StrEnum):
    """Enumeration of supported image formats"""

    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"
    GIF = "gif"
    BMP = "bmp"
    SVG = "svg"
    TIFF = "tiff"
    WEBP = "webp"
    UNKNOWN = "unknown"


class ImageSource(StrEnum):
    """Enumeration of image source types"""

    EXTERNAL_FILE = "external_file"
    BASE64_EMBEDDED = "base64_embedded"
    OBJECT_ELEMENT = "object_element"
    XHTML_IMG = "xhtml_img"
    UNKNOWN = "unknown"


class RequirementImageExtractor:
    """Extracts and processes images from REQIFZ files"""

    __slots__ = ("logger", "output_dir", "save_images", "validate_images")

    # Supported image extensions
    IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".tiff", ".webp"]

    def __init__(
        self,
        logger=None,
        output_dir: Path | None = None,
        save_images: bool = True,
        validate_images: bool = True,
    ):
        self.logger = logger
        self.output_dir = output_dir or Path("extracted_images")
        self.save_images = save_images
        self.validate_images = validate_images

        # Create output directory if saving images
        if self.save_images:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_images_from_reqifz(
        self, reqifz_file_path: Path
    ) -> tuple[ImageList, dict[str, Any]]:
        """
        Extract all images from a REQIFZ file.

        Args:
            reqifz_file_path: Path to the REQIFZ file

        Returns:
            Tuple of (images_list, extraction_report)
            - images_list: List of extracted image data
            - extraction_report: Summary of extraction process
        """
        try:
            with zipfile.ZipFile(reqifz_file_path, "r") as zip_file:
                images = []
                report = {
                    "total_images": 0,
                    "external_files": 0,
                    "embedded_images": 0,
                    "saved_images": 0,
                    "failed_images": 0,
                }

                # Phase 1: Extract external image files
                external_images = self._extract_external_images(zip_file, reqifz_file_path)
                images.extend(external_images)
                report["external_files"] = len(external_images)

                # Phase 2: Extract embedded images from REQIF XML
                reqif_files = [f for f in zip_file.namelist() if f.endswith(".reqif")]
                if reqif_files:
                    reqif_content = zip_file.read(reqif_files[0])
                    embedded_images = self._extract_embedded_images(
                        reqif_content, reqifz_file_path
                    )
                    images.extend(embedded_images)
                    report["embedded_images"] = len(embedded_images)

                report["total_images"] = len(images)
                report["saved_images"] = sum(1 for img in images if img.get("saved"))
                report["failed_images"] = sum(1 for img in images if img.get("error"))

                if self.logger:
                    self.logger.info(
                        f"Extracted {report['total_images']} images from {reqifz_file_path.name}: "
                        f"{report['external_files']} external, {report['embedded_images']} embedded"
                    )

                return images, report

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error extracting images from {reqifz_file_path}: {e}")
            return [], {"total_images": 0, "error": str(e)}

    def _extract_external_images(
        self, zip_file: zipfile.ZipFile, reqifz_path: Path
    ) -> ImageList:
        """Extract external image files from REQIFZ archive"""
        images = []

        for file_info in zip_file.filelist:
            file_name = file_info.filename

            # Check if this is an image file
            if any(file_name.lower().endswith(ext) for ext in self.IMAGE_EXTENSIONS):
                try:
                    # Read image data
                    image_data = zip_file.read(file_name)

                    # Determine format
                    image_format = self._determine_image_format(file_name, image_data)

                    # Create image info
                    image_info = {
                        "source": ImageSource.EXTERNAL_FILE,
                        "format": image_format,
                        "filename": file_name,
                        "size_bytes": len(image_data),
                        "hash": self._compute_hash(image_data),
                        "reqifz_source": reqifz_path.name,
                    }

                    # Validate image if requested
                    if self.validate_images and PILLOW_AVAILABLE:
                        validation = self._validate_image(image_data)
                        image_info.update(validation)

                    # Save image if requested
                    if self.save_images:
                        saved_path = self._save_image(image_data, file_name, reqifz_path)
                        if saved_path:
                            image_info["saved_path"] = str(saved_path)
                            image_info["saved"] = True
                        else:
                            image_info["saved"] = False
                    else:
                        image_info["saved"] = False

                    images.append(image_info)

                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Error extracting image {file_name}: {e}")
                    images.append(
                        {
                            "source": ImageSource.EXTERNAL_FILE,
                            "filename": file_name,
                            "error": str(e),
                            "saved": False,
                        }
                    )

        return images

    def _extract_embedded_images(self, reqif_content: bytes, reqifz_path: Path) -> ImageList:
        """Extract embedded images from REQIF XML content"""
        images = []

        try:
            # Parse XML content
            root = ET.fromstring(reqif_content)

            # REQIF namespaces
            namespaces = {
                "reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
                "xhtml": "http://www.w3.org/1999/xhtml",
            }

            # Phase 1: Extract base64-encoded images from XHTML content
            base64_images = self._extract_base64_images(root, namespaces, reqifz_path)
            images.extend(base64_images)

            # Phase 2: Extract images from OBJECT elements
            object_images = self._extract_object_images(root, namespaces, reqifz_path)
            images.extend(object_images)

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error parsing REQIF for embedded images: {e}")

        return images

    def _extract_base64_images(
        self, root: ET.Element, namespaces: dict[str, str], reqifz_path: Path
    ) -> ImageList:
        """Extract base64-encoded images from XHTML content"""
        images = []

        # Find all XHTML content
        xhtml_elements = root.findall(".//reqif:ATTRIBUTE-VALUE-XHTML", namespaces)

        for xhtml_elem in xhtml_elements:
            the_value = xhtml_elem.find(".//reqif:THE-VALUE", namespaces)
            if the_value is not None:
                # Convert to string for regex matching
                xhtml_str = ET.tostring(the_value, encoding="unicode")

                # Pattern: <img src="data:image/png;base64,..." (with or without namespace prefix)
                # Match both <img and <xhtml:img or <ns0:img etc
                pattern = r'<(?:\w+:)?img[^>]*src=["\']data:image/([^;]+);base64,([^"\']+)["\']'
                matches = re.finditer(pattern, xhtml_str, re.IGNORECASE | re.DOTALL)

                for match in matches:
                    image_format = match.group(1)
                    base64_data = match.group(2)

                    try:
                        # Decode base64 data
                        image_data = base64.b64decode(base64_data)

                        # Create image info
                        image_info = {
                            "source": ImageSource.BASE64_EMBEDDED,
                            "format": ImageFormat(image_format.lower())
                            if image_format.lower() in ImageFormat
                            else ImageFormat.UNKNOWN,
                            "size_bytes": len(image_data),
                            "hash": self._compute_hash(image_data),
                            "reqifz_source": reqifz_path.name,
                        }

                        # Validate image if requested
                        if self.validate_images and PILLOW_AVAILABLE:
                            validation = self._validate_image(image_data)
                            image_info.update(validation)

                        # Save image if requested
                        if self.save_images:
                            filename = f"embedded_{image_info['hash'][:8]}.{image_format}"
                            saved_path = self._save_image(image_data, filename, reqifz_path)
                            if saved_path:
                                image_info["saved_path"] = str(saved_path)
                                image_info["saved"] = True
                            else:
                                image_info["saved"] = False
                        else:
                            image_info["saved"] = False

                        images.append(image_info)

                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"Error decoding base64 image: {e}")
                        images.append(
                            {
                                "source": ImageSource.BASE64_EMBEDDED,
                                "format": image_format,
                                "error": str(e),
                                "saved": False,
                            }
                        )

        return images

    def _extract_object_images(
        self, root: ET.Element, namespaces: dict[str, str], reqifz_path: Path
    ) -> ImageList:
        """Extract images from OBJECT elements"""
        images = []

        # Find all OBJECT elements in XHTML content
        xhtml_elements = root.findall(".//reqif:ATTRIBUTE-VALUE-XHTML", namespaces)

        for xhtml_elem in xhtml_elements:
            the_value = xhtml_elem.find(".//reqif:THE-VALUE", namespaces)
            if the_value is not None:
                # Look for xhtml:object elements
                objects = the_value.findall(".//xhtml:object", namespaces)

                for obj in objects:
                    obj_type = obj.get("type", "")
                    obj_data = obj.get("data", "")

                    # Check if this is an image object
                    if "image" in obj_type.lower() or any(
                        ext in obj_data.lower() for ext in self.IMAGE_EXTENSIONS
                    ):
                        image_info = {
                            "source": ImageSource.OBJECT_ELEMENT,
                            "object_type": obj_type,
                            "object_data": obj_data,
                            "reqifz_source": reqifz_path.name,
                            "saved": False,
                        }

                        # Try to determine format from data attribute
                        for ext in self.IMAGE_EXTENSIONS:
                            if ext in obj_data.lower():
                                image_info["format"] = ImageFormat(ext[1:])
                                break

                        images.append(image_info)

        return images

    def _determine_image_format(self, filename: str, image_data: bytes) -> ImageFormat:
        """Determine image format from filename and/or image data"""
        # Try from filename extension
        filename_lower = filename.lower()
        for ext in self.IMAGE_EXTENSIONS:
            if filename_lower.endswith(ext):
                return ImageFormat(ext[1:])

        # Try from image data magic bytes
        if image_data.startswith(b"\x89PNG"):
            return ImageFormat.PNG
        elif image_data.startswith(b"\xff\xd8\xff"):
            return ImageFormat.JPEG
        elif image_data.startswith(b"GIF87a") or image_data.startswith(b"GIF89a"):
            return ImageFormat.GIF
        elif image_data.startswith(b"BM"):
            return ImageFormat.BMP
        elif b"<svg" in image_data[:100]:
            return ImageFormat.SVG

        return ImageFormat.UNKNOWN

    def _validate_image(self, image_data: bytes) -> dict[str, Any]:
        """Validate image data using PIL/Pillow"""
        validation = {"valid": False}

        if not PILLOW_AVAILABLE:
            validation["error"] = "Pillow not available"
            return validation

        try:
            img = Image.open(io.BytesIO(image_data))
            validation.update(
                {
                    "valid": True,
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "pil_format": img.format,
                }
            )
        except Exception as e:
            validation["error"] = str(e)

        return validation

    def _save_image(
        self, image_data: bytes, filename: str, reqifz_path: Path
    ) -> Path | None:
        """Save image to output directory"""
        try:
            # Create subdirectory for this REQIFZ file
            reqifz_dir = self.output_dir / reqifz_path.stem
            reqifz_dir.mkdir(parents=True, exist_ok=True)

            # Sanitize filename
            safe_filename = self._sanitize_filename(filename)

            # Full output path
            output_path = reqifz_dir / safe_filename

            # Write image data
            output_path.write_bytes(image_data)

            if self.logger:
                self.logger.debug(f"Saved image: {output_path}")

            return output_path

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error saving image {filename}: {e}")
            return None

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe filesystem operations"""
        # Get just the filename without path
        filename = Path(filename).name

        # Replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, "_")

        return filename

    def _compute_hash(self, data: bytes) -> str:
        """Compute SHA256 hash of data"""
        return hashlib.sha256(data).hexdigest()

    def augment_artifacts_with_images(
        self, artifacts: list[dict[str, Any]], images: ImageList
    ) -> list[dict[str, Any]]:
        """
        Augment artifacts with image references.

        This method adds image metadata to artifacts that reference images.

        Args:
            artifacts: List of artifact dictionaries
            images: List of extracted images

        Returns:
            List of artifacts augmented with image references
        """
        # Create image lookup by hash and filename
        image_lookup = {}
        for img in images:
            if "hash" in img:
                image_lookup[img["hash"]] = img
            if "filename" in img:
                image_lookup[img["filename"]] = img

        # Augment each artifact
        for artifact in artifacts:
            artifact_images = []
            text = artifact.get("text", "")

            # Look for image references in text
            # Pattern 1: img src references (with or without namespace prefix)
            img_pattern = r'<(?:\w+:)?img[^>]*src=["\']([^"\']+)["\']'
            img_matches = re.finditer(img_pattern, text, re.IGNORECASE | re.DOTALL)

            for match in img_matches:
                src = match.group(1)

                # Check if this is a base64 image
                if src.startswith("data:image"):
                    # Extract hash from base64 data
                    base64_pattern = r"base64,([^\"']+)"
                    base64_match = re.search(base64_pattern, src)
                    if base64_match:
                        try:
                            image_data = base64.b64decode(base64_match.group(1))
                            img_hash = self._compute_hash(image_data)
                            if img_hash in image_lookup:
                                artifact_images.append(image_lookup[img_hash])
                        except Exception:
                            pass
                else:
                    # External image reference
                    if src in image_lookup:
                        artifact_images.append(image_lookup[src])

            # Add image references to artifact
            if artifact_images:
                artifact["images"] = artifact_images
                artifact["has_images"] = True
            else:
                artifact["has_images"] = False

        return artifacts
