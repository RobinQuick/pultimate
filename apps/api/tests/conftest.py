"""Pytest configuration for apps/api tests.

This file ensures the apps/api directory is in the Python path
so that imports like 'from services.xxx import yyy' work correctly.
"""

import sys
from pathlib import Path

# Add the apps/api directory to Python path
api_dir = Path(__file__).parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))
