# TEMP Directory

This directory contains temporary files generated during processing.

## Directory Structure

```
TEMP/
├── images/         # Extracted images from REQIFZ files
├── logs/           # Processing log files
└── README.md       # This file
```

## Purpose

**TEMP/images/**: Stores images extracted from REQIFZ files during processing. Each REQIFZ file gets its own subdirectory:
```
TEMP/images/
├── <reqifz_filename>/
│   ├── image1.png
│   ├── image2.jpg
│   └── ...
```

**TEMP/logs/**: Stores processing log files when `log_to_file` is enabled:
```
TEMP/logs/
├── processing_log_2025-11-05_14-30-00.json
└── ...
```

## Configuration

These paths are configured in `src/config.py`:
- **Images:** `ImageExtractionConfig.output_dir` (line 211)
- **Logs:** `LoggingConfig.log_directory` (line 378)

## Environment Variable Override

You can override these paths using environment variables:
```bash
# Change image extraction directory
export AI_TG_IMAGE_EXTRACTION__OUTPUT_DIR="custom/images/path"

# Change log directory
export AI_TG_LOGGING__LOG_DIRECTORY="custom/logs/path"
```

## Cleanup

This directory can be safely cleaned periodically to reclaim disk space:
```bash
# Remove old extracted images (older than 7 days)
find TEMP/images -type f -mtime +7 -delete

# Remove old log files (older than 30 days)
find TEMP/logs -type f -mtime +30 -delete

# Complete cleanup
rm -rf TEMP/images/* TEMP/logs/*
```

## Git Ignore

The TEMP directory is excluded from version control. Only this README is tracked.
