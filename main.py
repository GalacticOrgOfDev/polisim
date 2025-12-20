import argparse
import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox


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


def main():
    parser = argparse.ArgumentParser(description='Start the Economic Projector GUI or run simulations headless')
    parser.add_argument('--simulate', action='store_true', help='Run headless simulation using scenario file')
    parser.add_argument('--scenario', type=str, default='policies/galactic_health_scenario.json', help='Path to scenario JSON')
    parser.add_argument('--years', type=int, default=22, help='Number of years to simulate')
    parser.add_argument('--start-year', type=int, default=2027, help='Simulation start year')
    parser.add_argument('--auto-install-deps', action='store_true', help='Auto-install missing optional dependencies without prompting')
    parser.add_argument('--dashboard', action='store_true', default=True, help='Launch CBO 2.0 Streamlit dashboard (Phase 2+, default)')
    parser.add_argument('--legacy-gui', action='store_true', help='Launch legacy Tkinter GUI (Phase 1 healthcare only)')
    args = parser.parse_args()

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
    # Offer to install any missing packages into the active Python environment.
    # Each entry: (import_name, pip_name, friendly_name, min_version)
    DEPENDENCIES = [
        ("matplotlib", "matplotlib", "Matplotlib (plotting)", "3.0.0"),
        ("yaml", "PyYAML", "PyYAML (YAML parser)", "6.0"),
        ("pypdf", "pypdf", "pypdf (PDF parser)", "6.0"),
    ]

    def parse_ver(v: str):
        # Simple numeric version parser returning tuple of ints for comparison
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
            return parse_ver(installed) >= parse_ver(minimum)
        except Exception:
            return False

    def check_and_offer_install(deps, auto_install=False):
        missing = []
        outdated = []
        for import_name, pip_name, friendly, min_ver in deps:
            try:
                mod = __import__(import_name)
                inst_ver = getattr(mod, '__version__', None)
                if not inst_ver:
                    # Try importlib.metadata
                    try:
                        from importlib import metadata
                        inst_ver = metadata.version(pip_name)
                    except Exception:
                        inst_ver = '0'
                if not is_version_ok(str(inst_ver), min_ver):
                    outdated.append((import_name, pip_name, friendly, min_ver, inst_ver))
            except Exception:
                missing.append((import_name, pip_name, friendly, min_ver))

        if not missing and not outdated:
            return True

        # Build message
        lines = []
        if missing:
            lines.append("Missing:")
            for _, pip_name, friendly, _ in missing:
                lines.append(f"- {friendly} (pip: {pip_name})")
        if outdated:
            lines.append("Outdated:")
            for _, pip_name, friendly, min_ver, inst_ver in outdated:
                lines.append(f"- {friendly} (installed: {inst_ver}, required: >= {min_ver})")

        names = '\n'.join(lines)

        if not auto_install:
            tmp_root = tk.Tk(); tmp_root.withdraw()
            resp = messagebox.askyesno("Missing/Outdated dependencies", f"The following optional packages are missing or outdated:\n\n{names}\n\nWould you like to install/upgrade them now into {sys.executable}?\n(Requires internet access)")
            tmp_root.destroy()
            if not resp:
                tmp = tk.Tk(); tmp.withdraw(); messagebox.showinfo("Startup Aborted", "GUI requires optional packages to function fully. Run with --simulate for headless runs, or install the missing packages into the venv."); tmp.destroy()
                return False

        # Install or upgrade missing/outdated packages
        to_install = []
        for import_name, pip_name, friendly, min_ver in missing:
            to_install.append(pip_name + (f">={min_ver}" if min_ver else ""))
        for import_name, pip_name, friendly, min_ver, inst_ver in outdated:
            to_install.append(pip_name + (f">={min_ver}" if min_ver else ""))

        for pkg in to_install:
            try:
                print(f"Installing/upgrading {pkg} into: {sys.executable}")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])
            except subprocess.CalledProcessError as e:
                tmp = tk.Tk(); tmp.withdraw(); messagebox.showerror("Install Failed", f"Failed to install/upgrade {pkg}:\n{e}"); tmp.destroy()
                return False

        import importlib
        importlib.invalidate_caches()
        return True

    ok = check_and_offer_install(DEPENDENCIES, auto_install=args.auto_install_deps)
    if not ok:
        return

    # Import GUI module lazily now that plotting libs are available
    from Economic_projector import EconomicProjectorApp
    root = tk.Tk()
    app = EconomicProjectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

