"""Main entrypoint for the Multi-Agent Technical Reporting System."""

import sys
from cli import run_cli

if __name__ == "__main__":
    run_cli(sys.argv[1:])
