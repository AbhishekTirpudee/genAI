"""
LLM Evaluation Studio - Root Entry Point
Delegates execution to the modular llm-evaluation-studio application package.
"""

import sys
from pathlib import Path

# Add llm-evaluation-studio to path
PACKAGE_DIR = Path(__file__).resolve().parent / "llm-evaluation-studio"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

# Import and execute main application
from app import main

if __name__ == "__main__":
    main()

