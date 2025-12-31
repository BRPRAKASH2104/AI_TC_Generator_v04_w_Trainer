"""
Test artifact builder utilities for creating XHTML-formatted test data.

This module provides helper functions to create test artifacts in the XHTML format
that matches the production code output after vision model integration (v2.2.0).

The vision fix changed text extraction from plain text to raw XHTML preservation
to maintain <object> tag references for images. Tests need to match this format.
"""

import random
from typing import Any


def _wrap_in_xhtml(text: str, include_namespace: bool = True) -> str:
    """
    Wrap text content in XHTML structure matching REQIF format.

    Args:
        text: The text content to wrap
        include_namespace: Whether to include XML namespace declarations

    Returns:
        XHTML-formatted string matching production output
    """
    if include_namespace:
        namespace = ' xmlns:ns0="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd" xmlns:html="http://www.w3.org/1999/xhtml"'
    else:
        namespace = ''

    return f'<THE-VALUE{namespace}><html:div><html:p>{text}</html:p></html:div></THE-VALUE>'


def create_test_artifact(
    text: str,
    artifact_type: str = "System Requirement",
    artifact_id: str | None = None,
    include_table: bool = False,
    include_namespace: bool = True,
    **kwargs: Any
) -> dict[str, Any]:
    """
    Create a test artifact with XHTML-formatted text.

    Args:
        text: The text content for the artifact
        artifact_type: Type of artifact (e.g., "System Requirement", "Heading")
        artifact_id: Optional custom ID (auto-generated if not provided)
        include_table: Whether to include an empty table structure
        include_namespace: Whether to include XML namespace declarations
        **kwargs: Additional fields to include in the artifact

    Returns:
        Dictionary representing a test artifact in production format

    Example:
        >>> artifact = create_test_artifact(
        ...     "Door shall lock when speed > 10 km/h",
        ...     artifact_type="System Requirement",
        ...     artifact_id="REQ_001"
        ... )
        >>> assert artifact["type"] == "System Requirement"
        >>> assert "<THE-VALUE>" in artifact["text"]
    """
    if artifact_id is None:
        # Generate random ID based on type
        prefix = artifact_type.replace(" ", "_").upper()[:3]
        artifact_id = f"{prefix}_{random.randint(1000, 9999)}"

    artifact = {
        "id": artifact_id,
        "type": artifact_type,
        "text": _wrap_in_xhtml(text, include_namespace=include_namespace),
    }

    if include_table:
        artifact["table"] = {"data": [], "headers": []}

    # Add any additional fields
    artifact.update(kwargs)

    return artifact


def create_test_requirement(
    requirement_text: str,
    requirement_id: str | None = None,
    include_table: bool = True,
    test_table_data: list[list[str]] | None = None,
    **kwargs: Any
) -> dict[str, Any]:
    """
    Create a test System Requirement artifact with optional test table.

    Args:
        requirement_text: The requirement description
        requirement_id: Optional custom ID (auto-generated if not provided)
        include_table: Whether to include a table structure
        test_table_data: Optional test table data (list of rows)
        **kwargs: Additional fields to include

    Returns:
        Dictionary representing a System Requirement artifact

    Example:
        >>> req = create_test_requirement(
        ...     "ACC shall maintain safe distance",
        ...     requirement_id="REQ_ACC_001",
        ...     test_table_data=[["TC001", "Test safe distance", "Pass"]]
        ... )
    """
    artifact = create_test_artifact(
        text=requirement_text,
        artifact_type="System Requirement",
        artifact_id=requirement_id,
        include_table=include_table,
        **kwargs
    )

    if test_table_data:
        artifact["table"] = {
            "data": test_table_data,
            "headers": ["Test ID", "Description", "Expected Result"]
        }

    return artifact


def create_test_heading(
    heading_text: str,
    heading_id: str | None = None,
    **kwargs: Any
) -> dict[str, Any]:
    """
    Create a test Heading artifact.

    Args:
        heading_text: The heading text
        heading_id: Optional custom ID (auto-generated if not provided)
        **kwargs: Additional fields

    Returns:
        Dictionary representing a Heading artifact

    Example:
        >>> heading = create_test_heading("Door Control System")
        >>> assert heading["type"] == "Heading"
    """
    return create_test_artifact(
        text=heading_text,
        artifact_type="Heading",
        artifact_id=heading_id,
        **kwargs
    )


def create_test_information(
    info_text: str,
    info_id: str | None = None,
    **kwargs: Any
) -> dict[str, Any]:
    """
    Create a test Information artifact.

    Args:
        info_text: The information text
        info_id: Optional custom ID (auto-generated if not provided)
        **kwargs: Additional fields

    Returns:
        Dictionary representing an Information artifact

    Example:
        >>> info = create_test_information("Safety critical component")
        >>> assert info["type"] == "Information"
    """
    return create_test_artifact(
        text=info_text,
        artifact_type="Information",
        artifact_id=info_id,
        **kwargs
    )


def create_test_interface(
    interface_text: str,
    interface_id: str | None = None,
    input_output: str = "Input",
    **kwargs: Any
) -> dict[str, Any]:
    """
    Create a test System Interface artifact.

    Args:
        interface_text: The interface description
        interface_id: Optional custom ID (auto-generated if not provided)
        input_output: "Input" or "Output"
        **kwargs: Additional fields

    Returns:
        Dictionary representing a System Interface artifact

    Example:
        >>> interface = create_test_interface(
        ...     "Vehicle speed signal",
        ...     input_output="Input"
        ... )
    """
    return create_test_artifact(
        text=interface_text,
        artifact_type="System Interface",
        artifact_id=interface_id,
        input_output=input_output,
        **kwargs
    )


def create_test_artifact_with_images(
    text: str,
    image_paths: list[str],
    artifact_type: str = "System Requirement",
    artifact_id: str | None = None,
    image_types: list[str] | None = None,
    **kwargs: Any
) -> dict[str, Any]:
    """
    Create a test artifact with embedded image references.

    This function creates artifacts with <object> tags matching the REQIF format
    that the vision model integration expects.

    Args:
        text: The text content
        image_paths: List of image file paths (e.g., ["1472801/image-001.png"])
        artifact_type: Type of artifact
        artifact_id: Optional custom ID
        image_types: Optional list of image MIME types (defaults to "image/png")
        **kwargs: Additional fields

    Returns:
        Dictionary representing an artifact with image references

    Example:
        >>> artifact = create_test_artifact_with_images(
        ...     "ACC state machine diagram",
        ...     image_paths=["diagrams/acc_states.png"],
        ...     artifact_id="REQ_001"
        ... )
        >>> assert '<html:object' in artifact["text"]
        >>> assert artifact.get("has_images") is True
    """
    if artifact_id is None:
        prefix = artifact_type.replace(" ", "_").upper()[:3]
        artifact_id = f"{prefix}_{random.randint(1000, 9999)}"

    if image_types is None:
        image_types = ["image/png"] * len(image_paths)

    # Build XHTML with embedded image object tags
    namespace = ' xmlns:ns0="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd" xmlns:html="http://www.w3.org/1999/xhtml"'

    # Create object tags for each image
    object_tags = []
    for img_path, img_type in zip(image_paths, image_types):
        object_tags.append(f'<html:object data="{img_path}" type="{img_type}" />')

    # Combine text and images in XHTML structure
    xhtml_content = (
        f'<THE-VALUE{namespace}>'
        f'<html:div>'
        f'<html:p>{text}</html:p>'
        f'{"".join(object_tags)}'
        f'</html:div>'
        f'</THE-VALUE>'
    )

    artifact = {
        "id": artifact_id,
        "type": artifact_type,
        "text": xhtml_content,
        "has_images": True,
        "image_count": len(image_paths),
    }

    # Add any additional fields
    artifact.update(kwargs)

    return artifact


def create_test_table(
    headers: list[str],
    rows: list[list[str]],
) -> dict[str, Any]:
    """
    Create a test table structure.

    Args:
        headers: List of column headers
        rows: List of rows (each row is a list of values)

    Returns:
        Dictionary representing a table structure

    Example:
        >>> table = create_test_table(
        ...     headers=["Test ID", "Description", "Result"],
        ...     rows=[
        ...         ["TC001", "Test door lock", "Pass"],
        ...         ["TC002", "Test window control", "Pass"]
        ...     ]
        ... )
    """
    return {
        "headers": headers,
        "data": rows
    }


def create_augmented_requirement(
    requirement_text: str,
    heading: str = "No Heading",
    info_list: list[dict[str, Any]] | None = None,
    interface_list: list[dict[str, Any]] | None = None,
    requirement_id: str | None = None,
    **kwargs: Any
) -> dict[str, Any]:
    """
    Create an augmented requirement with context (heading, info, interfaces).

    This matches the output of BaseProcessor._build_augmented_requirements()
    which is the core context-aware processing logic.

    Args:
        requirement_text: The requirement description
        heading: Current heading context
        info_list: List of Information artifacts since last heading
        interface_list: List of System Interface artifacts
        requirement_id: Optional custom ID
        **kwargs: Additional fields

    Returns:
        Dictionary representing an augmented requirement with full context

    Example:
        >>> req = create_augmented_requirement(
        ...     "ACC shall maintain safe distance",
        ...     heading="ACC System",
        ...     info_list=[create_test_information("Safety critical")],
        ...     interface_list=[create_test_interface("Speed signal")]
        ... )
        >>> assert req["heading"] == "ACC System"
        >>> assert len(req["info_list"]) == 1
    """
    if info_list is None:
        info_list = []
    if interface_list is None:
        interface_list = []

    requirement = create_test_requirement(
        requirement_text=requirement_text,
        requirement_id=requirement_id,
        **kwargs
    )

    # Add context fields (matching BaseProcessor output)
    requirement["heading"] = heading
    requirement["info_list"] = info_list
    requirement["interface_list"] = interface_list

    return requirement
