"""
pytest configuration: adds the project root to sys.path so that
'from src.*' imports work when pytest is run from any working directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Insert project root (parent of this file's directory) at the front of sys.path.
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
