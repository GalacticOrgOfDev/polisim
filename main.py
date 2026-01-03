import argparse
import importlib
from pathlib import Path
from importlib import metadata
import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox


DEPENDENCIES = [
    # Core/data
    ("pandas", "pandas", "pandas (dataframes)", "2.2.0", False),
    ("numpy", "numpy", "NumPy (arrays)", "2.1.0", False),
    ("scipy", "scipy", "SciPy (stats)", "1.15.0", False),
    ("openpyxl", "openpyxl", "openpyxl (Excel)", "3.1.0", False),
    ("yaml", "PyYAML", "PyYAML (YAML parser)", "6.0", False),
    ("pypdf", "pypdf", "pypdf (PDF parser)", "3.0", False),

    # Dashboard
    ("streamlit", "streamlit", "Streamlit (dashboard)", "1.28.0", False),
    ("plotly", "plotly", "Plotly (charts)", "5.0.0", False),

    # HTTP/HTML
    ("requests", "requests", "Requests (HTTP)", "2.25.0", False),
    ("bs4", "beautifulsoup4", "BeautifulSoup4 (HTML parser)", "4.12.0", False),

    # API/auth
    ("flask", "flask", "Flask (REST API server)", "2.0", False),
    ("flask_cors", "flask-cors", "Flask-CORS (API cross-origin support)", "3.0", False),
    ("jwt", "PyJWT", "PyJWT (JWT handling)", "2.8.0", False),

    # ORM/migrations/cache
    ("sqlalchemy", "SQLAlchemy", "SQLAlchemy (ORM)", "2.0.0", False),
    ("alembic", "alembic", "Alembic (migrations)", "1.13.0", False),
    ("redis", "redis", "Redis (cache client)", "5.0.0", False),

    # Jupyter Notebooks (Phase 6.6 - Educational content)
    ("jupyter", "jupyter", "Jupyter (notebooks)", "1.0.0", True),
    ("notebook", "notebook", "Notebook (Jupyter server)", "7.0.0", True),
    ("ipykernel", "ipykernel", "IPykernel (Jupyter kernel)", "6.25.0", True),

    # Optional extras
    ("pdfplumber", "pdfplumber", "pdfplumber (Enhanced PDF extraction)", "0.8", True),
    ("reportlab", "reportlab", "ReportLab (PDF generation)", "3.6", True),
]


def run_scenario(scenario_path: str, years: int = 22, start_year: int = 2027):
    """Run the healthcare simulation headless using a scenario JSON.

    Writes `usgha_simulation_22y.csv` to the current working directory.
    """
    # Import here to avoid heavy imports when launching GUI
    from core.scenario_loader import load_scenario
    from core import simulate_healthcare_years

    policy = load_scenario(scenario_path)
    base_gdp = 29e12
    initial_debt = 35e12
    print(f"Running simulation from scenario {scenario_path} (years={years}, start_year={start_year})...")
    df = simulate_healthcare_years(policy, base_gdp=base_gdp, initial_debt=initial_debt, years=years, population=335e6, gdp_growth=0.025, start_year=start_year)
    out = os.path.join(os.getcwd(), 'usgha_simulation_22y.csv')
    df.to_csv(out, index=False)
    print(f'Wrote CSV to {out}')


def parse_ver(v: str) -> tuple[int, ...]:
    parts = []
    for p in v.split('.'):
        num = ''
        for ch in p:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    return tuple(parts)


def is_version_ok(installed: str, minimum: str) -> bool:
    try:
        return parse_ver(str(installed)) >= parse_ver(str(minimum))
    except Exception:
        return False


def _get_installed_version(import_name: str, pip_name: str):
    # Prefer importlib.metadata for version detection (avoids deprecation warnings)
    try:
        return metadata.version(pip_name)
    except Exception:
        pass
    
    # Fallback: try module __version__ attribute
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            mod = importlib.import_module(import_name)
            inst_ver = getattr(mod, '__version__', None)
            if inst_ver:
                return str(inst_ver)
    except Exception:
        pass
    
    return None


def ensure_dependencies(auto_install=False, headless=False, deps=None):
    deps = deps or DEPENDENCIES
    missing = []
    outdated = []

    for import_name, pip_name, friendly, min_ver, optional in deps:
        inst_ver = _get_installed_version(import_name, pip_name)
        if inst_ver is None:
            missing.append((import_name, pip_name, friendly, min_ver, optional))
            continue
        if not is_version_ok(inst_ver, min_ver):
            outdated.append((import_name, pip_name, friendly, min_ver, inst_ver, optional))

    if not missing and not outdated:
        if headless:
            print("All checked dependencies are present.")
        return True

    lines = []
    if missing:
        lines.append("Missing:")
        for _, pip_name, friendly, min_ver, optional in missing:
            opt_tag = " (optional)" if optional else ""
            lines.append(f"- {friendly}{opt_tag} (pip: {pip_name} >= {min_ver})")
    if outdated:
        lines.append("Outdated:")
        for _, pip_name, friendly, min_ver, inst_ver, optional in outdated:
            opt_tag = " (optional)" if optional else ""
            lines.append(f"- {friendly}{opt_tag} (installed: {inst_ver}, required: >= {min_ver})")
    message = "\n".join(lines)

    if headless:
        print("Dependency check detected issues:\n" + message)
        proceed = auto_install
        if not auto_install:
            # Check if we're running in a non-interactive context (subprocess)
            # In that case, don't wait for input - just report and fail
            if not sys.stdin.isatty():
                print("Non-interactive mode detected, cannot prompt for install.")
                print("Run with --auto-install-deps to auto-install, or install manually.")
                return False
            resp = input("Install/upgrade these packages now? [y/N]: ").strip().lower()
            proceed = resp == 'y'
        if not proceed:
            print("Startup check aborted; dependencies remain unresolved.")
            return False
    else:
        root = tk.Tk(); root.withdraw()
        resp = messagebox.askyesno("Dependencies missing or outdated", f"{message}\n\nInstall/upgrade now into {sys.executable}?\n(Requires internet access)")
        root.destroy()
        if not resp:
            tmp = tk.Tk(); tmp.withdraw(); messagebox.showinfo("Startup Aborted", "Required packages are missing or outdated. Run startup check again after installing."); tmp.destroy()
            return False

    to_install = []
    for import_name, pip_name, friendly, min_ver, optional in missing:
        to_install.append(pip_name + (f">={min_ver}" if min_ver else ""))
    for import_name, pip_name, friendly, min_ver, inst_ver, optional in outdated:
        to_install.append(pip_name + (f">={min_ver}" if min_ver else ""))

    for pkg in to_install:
        try:
            print(f"Installing/upgrading {pkg} into: {sys.executable}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])
        except subprocess.CalledProcessError as e:
            if headless:
                print(f"Failed to install {pkg}: {e}")
            else:
                tmp = tk.Tk(); tmp.withdraw(); messagebox.showerror("Install Failed", f"Failed to install/upgrade {pkg}:\n{e}"); tmp.destroy()
            return False

    importlib.invalidate_caches()
    return True


def check_data_ingestion(headless: bool = True) -> bool:
    """Run a lightweight data ingestion check (CBO scraper with cache fallback).
    
    Uses fast cache-only check first to avoid network delays during startup.
    """
    try:
        from core.cbo_scraper import CBODataScraper

        scraper = CBODataScraper(use_cache=True)
        
        # Fast path: try cache-only first (no network)
        data = scraper.get_cached_data_fast()
        if data:
            # Valid cache exists - use it for fast startup
            freshness = float(data.get('freshness_hours', 0.0))
            source = data.get('data_source', 'unknown')
            checksum = data.get('checksum')
            
            line = f"Data ingestion OK (fast cache): source={source}; freshness={freshness:.1f}h; checksum={checksum}"
            if headless:
                print(line)
            else:
                root = tk.Tk(); root.withdraw(); messagebox.showinfo("Startup Check", line); root.destroy()
            return True
        
        # Slow path: need to fetch from network
        if headless:
            print("Cache unavailable or stale, fetching from network...")
        
        data = scraper.get_current_us_budget_data()
        if not data:
            msg = "Data ingestion failed: no live or cached CBO data available."
            if headless:
                print(msg)
            else:
                root = tk.Tk(); root.withdraw(); messagebox.showerror("Startup Check", msg); root.destroy()
            return False

        cache_used = bool(data.get('cache_used', False))
        freshness = float(data.get('freshness_hours', 0.0))
        source = data.get('data_source', 'unknown')
        checksum = data.get('checksum')
        schema_valid = bool(data.get('schema_valid', True))
        validation_errors = data.get('validation_errors', []) or []

        if not checksum:
            msg = "Data ingestion failed: checksum missing from CBO payload."
            if headless:
                print(msg)
            else:
                root = tk.Tk(); root.withdraw(); messagebox.showerror("Startup Check", msg); root.destroy()
            return False

        if not schema_valid:
            msg = f"Data ingestion failed: schema invalid ({'; '.join(validation_errors) or 'no details'})."
            if headless:
                print(msg)
            else:
                root = tk.Tk(); root.withdraw(); messagebox.showerror("Startup Check", msg); root.destroy()
            return False

        if cache_used and freshness > 72:
            msg = f"Data ingestion failed: cache is stale ({freshness:.1f}h > 72h) and live data unavailable."
            if headless:
                print(msg)
            else:
                root = tk.Tk(); root.withdraw(); messagebox.showerror("Startup Check", msg); root.destroy()
            return False

        line = f"Data ingestion OK: source={source}; cache_used={cache_used}; freshness={freshness:.1f}h; checksum={checksum}"
        if headless:
            print(line)
        else:
            root = tk.Tk(); root.withdraw(); messagebox.showinfo("Startup Check", line); root.destroy()
        return True

    except Exception as e:
        msg = f"Data ingestion check failed: {e}"
        if headless:
            print(msg)
        else:
            root = tk.Tk(); root.withdraw(); messagebox.showerror("Startup Check", msg); root.destroy()
        return False


def check_api_prerequisites(headless: bool = True) -> bool:
    """
    Slice 5.7: Check API prerequisites and configuration.
    
    Validates:
    - Pydantic models available (validation_models.py)
    - v1 middleware available (v1_middleware.py)
    - Observability module available (observability.py)
    - Flask and dependencies installed
    - API environment flags set correctly
    """
    try:
        # Check Pydantic
        try:
            import pydantic
        except ImportError:
            msg = "API check failed: pydantic not installed (pip install pydantic)"
            if headless:
                print(msg)
            else:
                root = tk.Tk(); root.withdraw(); messagebox.showerror("Startup Check", msg); root.destroy()
            return False
        
        # Check validation models
        try:
            from api.validation_models import SimulateRequest, SimulateResponse
        except ImportError as e:
            msg = f"API check failed: validation models not available ({e})"
            if headless:
                print(msg)
            else:
                root = tk.Tk(); root.withdraw(); messagebox.showerror("Startup Check", msg); root.destroy()
            return False
        
        # Check v1 middleware
        try:
            from api.v1_middleware import get_api_config, init_rate_limiter
        except ImportError as e:
            msg = f"API check failed: v1 middleware not available ({e})"
            if headless:
                print(msg)
            else:
                root = tk.Tk(); root.withdraw(); messagebox.showerror("Startup Check", msg); root.destroy()
            return False
        
        # Check observability
        try:
            from api.observability import configure_api_logging, MetricsCollector
        except ImportError as e:
            msg = f"API check failed: observability module not available ({e})"
            if headless:
                print(msg)
            else:
                root = tk.Tk(); root.withdraw(); messagebox.showerror("Startup Check", msg); root.destroy()
            return False
        
        # Check Flask
        try:
            import flask
            import flask_cors  # type: ignore[import]
        except ImportError:
            msg = "API check failed: Flask or flask-cors not installed (pip install flask flask-cors)"
            if headless:
                print(msg)
            else:
                root = tk.Tk(); root.withdraw(); messagebox.showerror("Startup Check", msg); root.destroy()
            return False
        
        # Get API config and validate
        config = get_api_config()
        status_lines = [
            f"API Prerequisites OK:",
            f"  PUBLIC_API_ENABLED={config['PUBLIC_API_ENABLED']}",
            f"  API_REQUIRE_AUTH={config['API_REQUIRE_AUTH']}",
            f"  API_AUTH_METHOD={config['API_AUTH_METHOD']}",
            f"  API_RATE_LIMIT_ENABLED={config['API_RATE_LIMIT_ENABLED']}",
            f"  API_MAX_PAYLOAD_MB={config['API_MAX_PAYLOAD_MB']}",
            f"  API_VERSION={config['API_VERSION']}",
        ]
        status = "\n".join(status_lines)
        
        if headless:
            print(status)
        else:
            root = tk.Tk(); root.withdraw(); messagebox.showinfo("Startup Check", status); root.destroy()
        
        return True

    except Exception as e:
        msg = f"API prerequisites check failed: {e}"
        if headless:
            print(msg)
        else:
            root = tk.Tk(); root.withdraw(); messagebox.showerror("Startup Check", msg); root.destroy()
        return False


def main():
    parser = argparse.ArgumentParser(description='Start the Economic Projector GUI or run simulations headless')
    parser.add_argument('--simulate', action='store_true', help='Run headless simulation using scenario file')
    parser.add_argument('--scenario', type=str, default='policies/galactic_health_scenario.json', help='Path to scenario JSON')
    parser.add_argument('--years', type=int, default=22, help='Number of years to simulate')
    parser.add_argument('--start-year', type=int, default=2027, help='Simulation start year')
    parser.add_argument('--startup-check-only', action='store_true', help='Run the friendly startup check without launching any UI')
    parser.add_argument('--auto-install-deps', action='store_true', help='Auto-install missing optional dependencies without prompting')
    parser.add_argument('--dashboard', action='store_true', default=True, help='Launch CBO 2.0 Streamlit dashboard (Phase 2+, default)')
    parser.add_argument('--legacy-gui', action='store_true', help='Launch legacy Tkinter GUI (Phase 1 healthcare only)')
    args = parser.parse_args()

    if args.startup_check_only:
        deps_ok = ensure_dependencies(auto_install=args.auto_install_deps, headless=True)
        data_ok = check_data_ingestion(headless=True)
        api_ok = check_api_prerequisites(headless=True)
        sys.exit(0 if (deps_ok and data_ok and api_ok) else 1)

    if args.simulate:
        # run headless simulation and exit
        run_scenario(args.scenario, years=args.years, start_year=args.start_year)
        return

    # If legacy-gui flag is set, launch Tkinter GUI (Phase 1 healthcare only)
    if args.legacy_gui:
        print("Launching legacy Tkinter GUI...")
        _launch_legacy_gui(args.auto_install_deps)
        return
    
    # Default: Launch CBO 2.0 Streamlit Dashboard
    print("\n" + "="*60)
    print("  CBO 2.0 Streamlit Dashboard")
    print("="*60)
    print("\nFor interactive debugging with F5, use: python debug_dashboard.py")
    print("For command-line launch with custom port, use: python run_dashboard.py --port 8502")
    print("\nLaunching dashboard...\n")

    ok = ensure_dependencies(auto_install=args.auto_install_deps, headless=True)
    if not ok:
        return

    _ = check_data_ingestion(headless=True)
    
    try:
        # Use subprocess to launch streamlit command
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'ui/dashboard.py', '--logger.level=warning'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Could not launch dashboard: {e}")
        print("\nTroubleshooting:")
        print("  1. Try: python debug_dashboard.py")
        print("  2. Try: python run_dashboard.py")
        print("  3. Try: --legacy-gui for Tkinter GUI")
        return
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Try: python debug_dashboard.py")
        print("  2. Try: python run_dashboard.py")
        print("  3. Try: --legacy-gui for Tkinter GUI")
        return


def _launch_legacy_gui(auto_install=False):
    """Launch the legacy Tkinter GUI (Phase 1 healthcare only)."""
    ok = ensure_dependencies(auto_install=auto_install, headless=False)
    if not ok:
        return

    # Import GUI module lazily now that plotting libs are available
    scripts_dir = Path(__file__).resolve().parent / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from Economic_projector import EconomicProjectorApp  # type: ignore[import]
    root = tk.Tk()
    app = EconomicProjectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

