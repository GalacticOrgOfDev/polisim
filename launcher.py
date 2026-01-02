"""
PoliSim Launcher - Enhanced with threading, multiple server options, and dependency checking.
- Non-blocking UI with threading for long-running operations
- Support for multiple servers: Dashboard, REST API, MCP Server
- Integrated dependency checking before launch
- Real-time status feedback
"""
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext
import webbrowser
from pathlib import Path
import platform
import threading
import time
import os
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent
BOOTSTRAP = ROOT_DIR / "scripts" / "bootstrap_windows.ps1"
ANDROID_URL = "https://example.com/polisim-android"
IOS_URL = "https://example.com/polisim-ios"
README_URL = "https://github.com/GalacticOrgOfDev/polisim"

CYBER_BG = "#0A0E27"
CYBER_PANEL = "#121530"
CYBER_ACCENT = "#FF00FF"
CYBER_TEXT = "#E6E9FF"
CYBER_SUB = "#9AD5FF"
CYBER_SUCCESS = "#00FF00"
CYBER_ERROR = "#FF4444"


class LauncherApp:
    """Enhanced launcher with threading and multi-server support."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PoliSim Launcher")
        self.root.configure(bg=CYBER_BG)
        self.root.geometry("700x800")
        self.root.resizable(True, True)
        
        self.running_process = None
        self.is_startup_checked = False
        self.startup_check_passed = False
        
        self.build_ui()
        
    def build_ui(self):
        """Build the launcher UI."""
        # Title
        title = tk.Label(self.root, text="PoliSim", fg=CYBER_ACCENT, bg=CYBER_BG, font=("Segoe UI", 24, "bold"))
        title.pack(pady=(20, 4))
        
        subtitle = tk.Label(self.root, text="Cyberpunk Policy Simulator", fg=CYBER_SUB, bg=CYBER_BG, font=("Segoe UI", 11))
        subtitle.pack(pady=(0, 16))
        
        # Status display
        self.status_text = tk.Label(
            self.root, text="Status: Ready", fg=CYBER_SUB, bg=CYBER_BG, font=("Segoe UI", 10)
        )
        self.status_text.pack(pady=(0, 10))
        
        # Main content frame
        self.main_frame = tk.Frame(self.root, bg=CYBER_BG)
        self.main_frame.pack(fill="both", expand=True, padx=16, pady=10)
        
        # Startup check button
        self.startup_btn = self.add_large_button(
            "1. Run Startup Check",
            self.run_startup_check_threaded,
            bg=CYBER_ACCENT
        )
        
        # Separator
        sep1 = tk.Label(self.main_frame, text="━" * 70, fg=CYBER_PANEL, bg=CYBER_BG, font=("Courier", 9))
        sep1.pack(fill="x", pady=12)
        
        # Server options
        tk.Label(self.main_frame, text="Launch Server", fg=CYBER_TEXT, bg=CYBER_BG, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 4))
        
        self.dashboard_btn = self.add_button("📊 Dashboard (Streamlit UI)", self.launch_dashboard_threaded, bg_color=CYBER_ACCENT)
        self.rest_btn = self.add_button("🔌 REST API Server", self.launch_rest_api_threaded, bg_color="#0066CC")
        self.mcp_btn = self.add_button("🔗 MCP Server", self.launch_mcp_threaded, bg_color="#FF6600")
        
        # Separator
        sep2 = tk.Label(self.main_frame, text="━" * 70, fg=CYBER_PANEL, bg=CYBER_BG, font=("Courier", 9))
        sep2.pack(fill="x", pady=12)
        
        # Resources
        tk.Label(self.main_frame, text="Resources", fg=CYBER_TEXT, bg=CYBER_BG, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 4))
        
        self.add_button("📖 View README / Docs", lambda: webbrowser.open(README_URL))
        self.add_button("🤖 Android (Download Link)", lambda: webbrowser.open(ANDROID_URL))
        self.add_button("🍎 iOS (Download Link)", lambda: webbrowser.open(IOS_URL))
        
        # Log display
        sep3 = tk.Label(self.main_frame, text="━" * 70, fg=CYBER_PANEL, bg=CYBER_BG, font=("Courier", 9))
        sep3.pack(fill="x", pady=12)
        
        tk.Label(self.main_frame, text="Activity Log", fg=CYBER_TEXT, bg=CYBER_BG, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(4, 4))
        
        self.log_display = scrolledtext.ScrolledText(
            self.main_frame, height=10, width=80, bg=CYBER_PANEL, fg=CYBER_SUCCESS, 
            font=("Courier", 9), wrap=tk.WORD
        )
        self.log_display.pack(fill="both", expand=True, pady=(4, 10))
        
        # Bottom button
        self.add_button("❌ Exit Launcher", self.quit_app, bg_color=CYBER_ERROR)
        
        # Initial log message
        self.log("PoliSim Launcher started. Run 'Run Startup Check' first.")
        
    def add_large_button(self, text, command, bg=CYBER_ACCENT):
        """Add a large button."""
        btn = tk.Button(
            self.main_frame, text=text, command=command, fg=CYBER_BG, bg=bg,
            activebackground=CYBER_SUB, activeforeground=CYBER_BG,
            relief="flat", bd=0, padx=16, pady=14, font=("Segoe UI", 12, "bold"),
            cursor="hand2", wraplength=600, justify="left"
        )
        btn.pack(fill="x", pady=6)
        return btn
        
    def add_button(self, text, command, bg_color=CYBER_ACCENT):
        """Add a standard button."""
        btn = tk.Button(
            self.main_frame, text=text, command=command, fg=CYBER_TEXT, bg=bg_color,
            activebackground=CYBER_SUB, activeforeground=CYBER_BG,
            relief="flat", bd=0, padx=12, pady=10, font=("Segoe UI", 10, "bold"),
            cursor="hand2", wraplength=600
        )
        btn.pack(fill="x", pady=4)
        return btn
    
    def log(self, message):
        """Add message to log display."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_display.insert("end", f"[{timestamp}] {message}\n")
        self.log_display.see("end")
        self.root.update()
    
    def update_status(self, message, color=CYBER_SUB):
        """Update status label."""
        self.status_text.config(text=f"Status: {message}", fg=color)
        self.root.update()
        
    def run_startup_check_threaded(self):
        """Run startup check in background thread."""
        self.startup_btn.config(state="disabled")
        self.update_status("Running startup check...", CYBER_ACCENT)
        
        def run_check():
            try:
                self.log("Starting startup check...")
                result = subprocess.run(
                    [sys.executable, str(ROOT_DIR / "main.py"), "--startup-check-only"],
                    cwd=str(ROOT_DIR),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    self.log("✓ Startup check PASSED - All dependencies available")
                    self.is_startup_checked = True
                    self.startup_check_passed = True
                    self.update_status("Ready to launch", CYBER_SUCCESS)
                    messagebox.showinfo("Startup Check", "All dependencies verified! Ready to launch.")
                else:
                    output = result.stdout + result.stderr
                    self.log(f"✗ Startup check FAILED:\n{output}")
                    self.update_status("Startup check failed", CYBER_ERROR)
                    messagebox.showerror("Startup Check Failed", output or "Unknown error")
            except subprocess.TimeoutExpired:
                self.log("✗ Startup check timed out")
                self.update_status("Startup check timed out", CYBER_ERROR)
                messagebox.showerror("Timeout", "Startup check took too long (>2 minutes)")
            except Exception as e:
                self.log(f"✗ Startup check error: {str(e)}")
                self.update_status("Error running startup check", CYBER_ERROR)
                messagebox.showerror("Error", f"Failed to run startup check: {str(e)}")
            finally:
                self.startup_btn.config(state="normal")
        
        thread = threading.Thread(target=run_check, daemon=True)
        thread.start()
    
    def launch_dashboard_threaded(self):
        """Launch Streamlit dashboard in background thread."""
        if not self.startup_check_passed:
            messagebox.showwarning("Startup Check Required", "Please run startup check first!")
            return
        
        self.log("Launching Dashboard (Streamlit)...")
        self.update_status("Launching Dashboard...", CYBER_ACCENT)
        
        def launch():
            try:
                self.log("Starting Streamlit dashboard...")
                env = dict(os.environ)
                env.setdefault("PYTHONIOENCODING", "utf-8")
                env.setdefault("STREAMLIT_SERVER_HEADLESS", "true")

                proc = subprocess.Popen(
                    [sys.executable, "-m", "streamlit", "run", "ui/dashboard.py", 
                     "--server.headless=true", "--logger.level=error"],
                    cwd=str(ROOT_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env,
                )

                # Give Streamlit a moment to boot
                time.sleep(3)

                if proc.poll() is None:
                    self.running_process = proc
                    self.log("✓ Dashboard process started (Streamlit)")
                    self.update_status("Dashboard running at http://localhost:8501", CYBER_SUCCESS)
                    webbrowser.open("http://localhost:8501")
                else:
                    output = proc.stdout.read() if proc.stdout else ""
                    self.log(f"✗ Dashboard exited immediately (code {proc.returncode})\n{output}")
                    self.update_status("Dashboard launch failed", CYBER_ERROR)
                    messagebox.showerror("Launch Failed", output or "Streamlit exited before starting")
            except Exception as e:
                self.log(f"✗ Failed to launch dashboard: {str(e)}")
                self.update_status("Dashboard launch failed", CYBER_ERROR)
                messagebox.showerror("Launch Failed", f"Failed to launch dashboard:\n{str(e)}")
        
        thread = threading.Thread(target=launch, daemon=True)
        thread.start()
    
    def launch_rest_api_threaded(self):
        """Launch REST API server in background thread."""
        if not self.startup_check_passed:
            messagebox.showwarning("Startup Check Required", "Please run startup check first!")
            return
        
        self.log("Launching REST API Server...")
        self.update_status("Launching REST API...", CYBER_ACCENT)
        
        def launch():
            try:
                self.log("Starting REST API server on localhost:5000...")
                result = subprocess.run(
                    [sys.executable, "api/rest_server.py"],
                    cwd=str(ROOT_DIR),
                    timeout=5
                )
            except subprocess.TimeoutExpired:
                self.log("✓ REST API launched on http://localhost:5000")
                self.update_status("REST API running at http://localhost:5000", CYBER_SUCCESS)
                webbrowser.open("http://localhost:5000")
            except Exception as e:
                self.log(f"✗ Failed to launch REST API: {str(e)}")
                self.update_status("REST API launch failed", CYBER_ERROR)
                messagebox.showerror("Launch Failed", f"Failed to launch REST API:\n{str(e)}")
        
        thread = threading.Thread(target=launch, daemon=True)
        thread.start()
    
    def launch_mcp_threaded(self):
        """Launch MCP server in background thread."""
        if not self.startup_check_passed:
            messagebox.showwarning("Startup Check Required", "Please run startup check first!")
            return
        
        self.log("Launching MCP Server...")
        self.update_status("Launching MCP Server...", CYBER_ACCENT)
        
        def launch():
            try:
                self.log("Starting MCP server...")
                result = subprocess.run(
                    [sys.executable, "mcp_server.py"],
                    cwd=str(ROOT_DIR),
                    timeout=5
                )
            except subprocess.TimeoutExpired:
                self.log("✓ MCP Server launched")
                self.update_status("MCP Server running", CYBER_SUCCESS)
                messagebox.showinfo("MCP Server", "MCP Server is now running and ready for connections.")
            except Exception as e:
                self.log(f"✗ Failed to launch MCP server: {str(e)}")
                self.update_status("MCP server launch failed", CYBER_ERROR)
                messagebox.showerror("Launch Failed", f"Failed to launch MCP server:\n{str(e)}")
        
        thread = threading.Thread(target=launch, daemon=True)
        thread.start()
    
    def quit_app(self):
        """Exit launcher."""
        if messagebox.askyesno("Exit", "Close PoliSim Launcher?"):
            self.root.destroy()


def main():
    root = tk.Tk()
    app = LauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()