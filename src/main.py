#!/usr/bin/env python3
"""
Entry point module for the AI Test Case Generator package.

This module provides the main CLI interface that can be used both
when the package is installed and when running directly.
"""

import sys
from pathlib import Path

# For direct execution, add parent directory to path
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the main function from the root main.py
try:
    from main import main
except ImportError:
    # If running as installed package
    from ..main import main

def cli():
    """Entry point for installed package"""
    main()

if __name__ == "__main__":
    cli()