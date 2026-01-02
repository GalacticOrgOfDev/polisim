"""Pytest configuration to ensure project root imports resolve.

Adds the repository root to sys.path so tests can import `core` and other
project packages regardless of how pytest is invoked or which interpreter is used.
"""
import sys
from pathlib import Path

# Resolve repository root: tests/ -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
