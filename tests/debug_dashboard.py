"""
Debug launcher for CBO 2.0 Dashboard
Use this when debugging from F5 in VSCode - it avoids subprocess issues with debugpy.

This file launches the Streamlit dashboard using subprocess with -m streamlit.
This works better with debugpy than direct Streamlit CLI imports.
"""

import sys
import os
import subprocess

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 70)
    print("CBO 2.0 DASHBOARD - DEBUG MODE")
    print("=" * 70)
    print()
    print("Initializing dashboard modules...")
    
    try:
        # Check if streamlit is installed
        import streamlit
        print(f"✓ Streamlit {streamlit.__version__} available")
        
        # Run streamlit via subprocess with -m
        print("✓ Launching dashboard on http://localhost:8501")
        print()
        print("=" * 70)
        print()
        
        # Run the dashboard
        result = subprocess.run(
            [sys.executable, '-m', 'streamlit', 'run', 'ui/dashboard.py', '--logger.level=warning'],
            check=False
        )
        
        sys.exit(result.returncode)
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print()
        print("Install missing packages:")
        print("  pip install streamlit plotly")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

