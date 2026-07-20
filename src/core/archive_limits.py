"""Archive-safety limits for REQIFZ (ZIP) extraction.

REQIFZ files are attacker-influenceable ZIP archives. Reading entries without
bounds allows decompression bombs to exhaust RAM, CPU, and disk. This module
centralises the limits and the two safety primitives used by every extractor:

* :func:`validate_archive_safety` inspects the archive metadata *before* any
  entry is read, rejecting archives with too many entries, oversized declared
  entries, an oversized declared total, or an implausible compression ratio.
* :func:`safe_zip_read` streams a single entry through a byte cap so the actual
  decompressed size is bounded even when the ZIP header lies about it.

Both raise :class:`ArchiveLimitError`, which callers translate into their normal
"could not extract" result (an empty artifact/image list) with a security log.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import zipfile

    from src.file_processing_logger import FileProcessingLogger

# Maximum number of entries permitted in a single REQIFZ archive.
MAX_ARCHIVE_ENTRIES = 10_000

# Maximum declared/decompressed size for any single entry (100 MiB).
MAX_ENTRY_UNCOMPRESSED_SIZE = 100 * 1024 * 1024

# Maximum declared total decompressed size across all entries (500 MiB).
MAX_TOTAL_UNCOMPRESSED_SIZE = 500 * 1024 * 1024

# Maximum per-entry compression ratio (uncompressed / compressed). Classic ZIP
# bombs reach ratios in the thousands; legitimate REQIF XML/images stay well
# under this. Tiny entries are exempt (see ``_RATIO_MIN_SIZE``).
MAX_COMPRESSION_RATIO = 100

# Entries whose uncompressed size is below this are exempt from the ratio check;
# small, highly compressible metadata files would otherwise false-positive.
_RATIO_MIN_SIZE = 4 * 1024


class ArchiveLimitError(Exception):
    """Raised when a ZIP archive exceeds a configured safety limit."""


def validate_archive_safety(
    zip_file: zipfile.ZipFile,
    logger: FileProcessingLogger | None = None,
) -> None:
    """Reject a ZIP archive whose metadata exceeds any safety limit.

    Inspects every ``ZipInfo`` header without reading entry contents, so the
    check is cheap and happens before any decompression.

    Args:
        zip_file: An open ``ZipFile`` to inspect.
        logger: Optional logger for a security-oriented warning on rejection.

    Raises:
        ArchiveLimitError: If the entry count, any per-entry declared size, the
            aggregate declared size, or any per-entry compression ratio exceeds
            its configured maximum.
    """
    infos = zip_file.infolist()

    if len(infos) > MAX_ARCHIVE_ENTRIES:
        _reject(
            logger,
            f"archive has {len(infos)} entries (limit {MAX_ARCHIVE_ENTRIES})",
        )

    total_uncompressed = 0
    for info in infos:
        if info.file_size > MAX_ENTRY_UNCOMPRESSED_SIZE:
            _reject(
                logger,
                f"entry {info.filename!r} declares {info.file_size} bytes "
                f"(limit {MAX_ENTRY_UNCOMPRESSED_SIZE})",
            )

        total_uncompressed += info.file_size
        if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_SIZE:
            _reject(
                logger,
                f"archive declares > {MAX_TOTAL_UNCOMPRESSED_SIZE} bytes uncompressed",
            )

        if info.file_size >= _RATIO_MIN_SIZE and info.compress_size > 0:
            ratio = info.file_size / info.compress_size
            if ratio > MAX_COMPRESSION_RATIO:
                _reject(
                    logger,
                    f"entry {info.filename!r} compression ratio {ratio:.0f}:1 "
                    f"(limit {MAX_COMPRESSION_RATIO}:1)",
                )


def safe_zip_read(
    zip_file: zipfile.ZipFile,
    name: str,
    max_bytes: int,
) -> bytes:
    """Read a single ZIP entry, decompressing at most ``max_bytes`` bytes.

    Streams the entry and stops one byte past the cap, so a header that lies
    about an entry's size cannot force unbounded decompression.

    Args:
        zip_file: An open ``ZipFile``.
        name: Entry name to read.
        max_bytes: Maximum number of decompressed bytes to accept.

    Returns:
        The decompressed entry bytes (at most ``max_bytes``).

    Raises:
        ArchiveLimitError: If the entry decompresses to more than ``max_bytes``.
    """
    with zip_file.open(name) as entry:
        data = entry.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ArchiveLimitError(f"entry {name!r} exceeds {max_bytes} bytes when decompressed")
    return data


def _reject(logger: FileProcessingLogger | None, reason: str) -> None:
    """Log and raise a rejection for an unsafe archive."""
    if logger:
        logger.warning(f"Rejected unsafe REQIFZ archive: {reason}")
    raise ArchiveLimitError(reason)
