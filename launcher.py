"""
PoliSim launcher shell.
- Presents a simple cyberpunk-styled Tk UI.
- On Windows, can invoke the bootstrap script to fetch Python, create venv, install deps, and launch the dashboard.
- Provides links/QR placeholders for Android/iOS.
"""
import subprocess
import sys
import tkinter as tk
import webbrowser
from tkinter import messagebox
from pathlib import Path
import platform

ROOT_DIR = Path(__file__).resolve().parent
BOOTSTRAP = ROOT_DIR / "scripts" / "bootstrap_windows.ps1"
ANDROID_URL = "https://example.com/polisim-android"  # TODO: replace with real link
IOS_URL = "https://example.com/polisim-ios"          # TODO: replace with real link
README_URL = "https://github.com/GalacticOrgOfDev/polisim"

CYBER_BG = "#0A0E27"  # deep blue
CYBER_PANEL = "#121530"
CYBER_ACCENT = "#FF00FF"  # magenta
CYBER_TEXT = "#E6E9FF"
CYBER_SUB = "#9AD5FF"


def run_bootstrap(launch_dashboard=True, auto_install=True):
    if platform.system().lower() != "windows":
        messagebox.showinfo("Launcher", "Bootstrap is only supported on Windows in this build.")
        return
    if not BOOTSTRAP.exists():
        messagebox.showerror("Launcher", f"Bootstrap script not found: {BOOTSTRAP}")
        return
    cmd = [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", str(BOOTSTRAP),
    ]
    if auto_install:
        cmd.append("-AutoInstallDeps")
    if launch_dashboard:
        cmd.append("-LaunchDashboard")
    try:
        subprocess.check_call(cmd, cwd=str(ROOT_DIR))
    except subprocess.CalledProcessError as exc:
        messagebox.showerror("Launcher", f"Bootstrap failed: {exc}")


def open_link(url):
    webbrowser.open(url)


def build_ui():
    root = tk.Tk()
    root.title("PoliSim Launcher")
    root.configure(bg=CYBER_BG)
    root.geometry("480x520")
    root.resizable(False, False)

    title = tk.Label(root, text="PoliSim", fg=CYBER_ACCENT, bg=CYBER_BG, font=("Segoe UI", 22, "bold"))
    subtitle = tk.Label(root, text="Cyberpunk launchpad", fg=CYBER_SUB, bg=CYBER_BG, font=("Segoe UI", 12))
    title.pack(pady=(28, 4))
    subtitle.pack(pady=(0, 16))

    panel = tk.Frame(root, bg=CYBER_PANEL, bd=0, relief="flat")
    panel.pack(fill="both", expand=True, padx=22, pady=10)

    def add_button(text, command):
        btn = tk.Button(
            panel,
            text=text,
            command=command,
            fg=CYBER_TEXT,
            bg=CYBER_ACCENT,
            activebackground=CYBER_SUB,
            activeforeground=CYBER_BG,
            relief="flat",
            bd=0,
            padx=16,
            pady=12,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2"
        )
        btn.pack(fill="x", pady=10, padx=8)
        return btn

    tk.Label(panel, text="Choose platform", fg=CYBER_TEXT, bg=CYBER_PANEL, font=("Segoe UI", 12, "bold")).pack(pady=(12, 8))

    add_button("Windows desktop (install + launch dashboard)", lambda: run_bootstrap(launch_dashboard=True, auto_install=True))
    add_button("Windows startup check only", lambda: run_bootstrap(launch_dashboard=False, auto_install=True))
    add_button("Android (open download link)", lambda: open_link(ANDROID_URL))
    add_button("iOS (open download link)", lambda: open_link(IOS_URL))

    tk.Label(panel, text="Resources", fg=CYBER_TEXT, bg=CYBER_PANEL, font=("Segoe UI", 12, "bold")).pack(pady=(16, 8))
    add_button("View README / docs", lambda: open_link(README_URL))

    tk.Label(panel, text="Note: Installer flow currently targets Windows; mobile entries open links.",
             fg=CYBER_SUB, bg=CYBER_PANEL, wraplength=400, justify="left", font=("Segoe UI", 9)).pack(pady=(12, 16))

    def quit_app():
        root.destroy()
    add_button("Quit", quit_app)

    return root


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--headless":
        run_bootstrap(launch_dashboard=True, auto_install=True)
        return
    root = build_ui()
    root.mainloop()


if __name__ == "__main__":
    main()