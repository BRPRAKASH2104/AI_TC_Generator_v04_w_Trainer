#!/bin/bash
# cleanup_cache.sh
# Removes all cache, temporary, and build artifacts from the project
# Safe to run anytime - regenerates automatically during development

set -e

echo "🧹 Cleaning cache and temporary files..."

# Python caches
echo "  Removing Python bytecode..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Type checking cache
echo "  Removing mypy cache..."
rm -rf .mypy_cache

# Linting cache
echo "  Removing ruff cache..."
rm -rf .ruff_cache

# Testing cache
echo "  Removing pytest cache..."
rm -rf .pytest_cache

# Coverage reports
echo "  Removing coverage reports..."
rm -rf htmlcov
rm -f coverage.xml
rm -f .coverage

# Build artifacts
echo "  Removing build artifacts..."
rm -rf build dist *.egg-info

# OS files
echo "  Removing OS metadata files..."
find . -name ".DS_Store" -type f -exec rm -f {} \; 2>/dev/null || true
find . -name "Thumbs.db" -type f -delete 2>/dev/null || true

# Old log files (keep current)
echo "  Removing old rotated log files..."
find output/logs/ -name "*.jsonl.*" -type f -delete 2>/dev/null || true

echo "✅ Cleanup complete!"
echo ""
echo "📊 Current directory sizes:"
du -sh ./* 2>/dev/null | sort -h | tail -10
