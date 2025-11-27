#!/usr/bin/env python
"""Start the backend server."""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.server import main

if __name__ == "__main__":
    main()

