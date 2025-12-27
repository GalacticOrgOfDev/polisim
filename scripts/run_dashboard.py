#!/usr/bin/env python3
"""
CBO 2.0 Dashboard Launcher
Run this to start the Streamlit web interface with Phase 2-3.1 modules.

Usage:
    python run_dashboard.py              # Start Streamlit dashboard
    python run_dashboard.py --port 8502  # Custom port
    python run_dashboard.py --legacy     # Launch legacy Tkinter GUI instead
"""

import sys
import subprocess
import argparse
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description='Launch CBO 2.0 Dashboard or legacy GUI')
    parser.add_argument('--port', type=int, default=8501, help='Streamlit port (default: 8501)')
    parser.add_argument('--legacy', action='store_true', help='Launch legacy Tkinter GUI instead')
    args = parser.parse_args()
    
    if args.legacy:
        print("Launching legacy Economic Projector GUI...")
        subprocess.run([sys.executable, str(REPO_ROOT / 'main.py'), '--legacy-gui'], cwd=REPO_ROOT)
    else:
        print(f"Launching CBO 2.0 Dashboard on http://localhost:{args.port}")
        print("Press Ctrl+C to stop")
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run',
            str(REPO_ROOT / 'ui' / 'dashboard.py'),
            '--logger.level=warning',
            f'--server.port={args.port}'
        ], cwd=REPO_ROOT)


if __name__ == '__main__':
    main()
