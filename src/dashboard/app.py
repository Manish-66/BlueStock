"""Nifty 100 Financial Intelligence Platform — Main Dashboard Entry Point.

Sprint 4: Interactive Dashboard (Module 5).
Mirrors root app.py to satisfy the standard layout specified in Page 33.
"""

import os
import sys

# Ensure root is on sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import app

# Run app main content
if __name__ == "__main__":
    pass
