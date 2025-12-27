# Startup Check Plan

## Purpose
- Provide a friendly, cross-platform launcher that gets users running polisim without prior Python setup.
- Offer a cyberpunk-themed splash and a clear install plan before any changes are made.
- Make the startup check usable headlessly (CLI) and interactively (GUI), installing all required Python deps when approved.

## User Flow (Launcher)
- Splash screen: PoliSim cyberpunk theme (neon magenta/cyan glow) with a short loading pulse.
- Platform selector: Windows desktop (installs Python + venv + deps), Android (store/TestFlight link), iOS (store/TestFlight link), Linux/macOS (shell instructions or link).
- Install plan panel: shows exact packages/runtime that will be installed and their versions; offers Copy Log.
- User approves (OK) or cancels; on OK, the launcher runs the startup check/installer, then starts the dashboard or API server.

## Windows Desktop Flow (default)
1) Preflight: detect existing Python; if absent, fetch a pinned runtime (embeddable/Miniconda/Mambaforge) into a local runtime folder—no system Python required.
2) Create or refresh a venv inside the project.
3) Install dependencies (from requirements.txt + optional extras) with a clear list and versions.
4) Run the friendly startup check in headless mode to confirm nothing is missing/outdated.
5) Launch target: Streamlit dashboard (ui/dashboard.py) or API server as chosen.

## Dependency Coverage
- Core/data: pandas, numpy, scipy, openpyxl, PyYAML, pypdf.
- Dashboard: streamlit, plotly.
- HTTP/HTML: requests, beautifulsoup4.
- API/auth: flask, flask-cors, PyJWT.
- ORM/migrations/cache: SQLAlchemy, alembic, redis.
- Optional: pdfplumber, reportlab (only if user opts in from the plan panel), gunicorn for Linux/macOS servers.

## Friendly Startup Check Behavior
- Headless (CLI) mode: prints missing/outdated deps, prompts in-console unless auto-install is requested; exits non-zero on failure.
- GUI mode: uses dialogs for consent; shows missing/outdated lists; installs/upgrades approved items; surfaces errors clearly.
- Reusable function so both legacy GUI and launcher share the same dependency logic.

## Android / iOS Handling
- The desktop launcher cannot sideload mobile apps; it shows QR codes/links to the correct store/TestFlight builds and the dependency list for transparency.

## Art Direction (Splash)
- Cyberpunk neon with magenta/cyan, subtle grain, pulsing ring around the PoliSim logotype, minimal motion to keep startup fast.

## Next Implementation Steps
1) Add a headless-friendly `--startup-check-only` flag and extract the dependency checker so it works without Tkinter.
2) Add a Windows bootstrap script to fetch the Python runtime, create venv, install requirements, and invoke the startup check.
3) Build the minimal launcher shell (PyInstaller/Tauri/Electron-lite) that runs the bootstrap + splash + platform selection.
4) Document installer behavior in README and keep the dependency list in sync with requirements.txt.

## Windows Bootstrap Script
- Location: scripts/bootstrap_windows.ps1
- Defaults: Python 3.11.8 embeddable, venv at .venv, installs requirements.txt, runs `python main.py --startup-check-only [--auto-install-deps]`, optional `-LaunchDashboard` to start Streamlit.
- Flow: find existing Python → download embeddable if missing → create/refresh venv → install requirements → run startup check → optional dashboard launch.

## Launcher Shell
- Location: launcher.py in repo root (Tk-based, cyberpunk styling).
- Windows actions: call bootstrap script for install + launch, or startup-check-only.
- Android/iOS actions: open download/TestFlight links (placeholders until real links are available).
- Resources: opens README/docs.
