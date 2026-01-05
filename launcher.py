"""
PoliSim Launcher - Enhanced with threading, multiple server options, and dependency checking.
- Non-blocking UI with threading for long-running operations
- Support for multiple servers: Dashboard, REST API, MCP Server
- Integrated dependency checking before launch
- Real-time status feedback
- Color-coded button states for workflow guidance
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

# Color scheme
CYBER_BG = "#0A0E27"
CYBER_PANEL = "#121530"
CYBER_ACCENT = "#FF00FF"
CYBER_TEXT = "#E6E9FF"
CYBER_SUB = "#9AD5FF"
CYBER_SUCCESS = "#00FF00"
CYBER_ERROR = "#FF4444"
CYBER_WARNING = "#FFD700"  # Yellow for pending/next action
CYBER_DISABLED = "#555555"  # Grey for disabled buttons
CYBER_WHITE = "#FFFFFF"  # White for app store buttons


class LauncherApp:
    """Enhanced launcher with threading, multi-server support, and color-coded buttons."""
    
    # Button states
    STATE_NOT_RUN = "not_run"      # Grey/disabled or yellow for next action
    STATE_RUNNING = "running"      # Yellow while in progress
    STATE_SUCCESS = "success"      # Green
    STATE_FAILED = "failed"        # Red
    
    def __init__(self, root):
        self.root = root
        self.root.title("PoliSim Launcher")
        self.root.configure(bg=CYBER_BG)
        self.root.geometry("700x800")
        self.root.resizable(True, True)
        
        self.running_process = None
        
        # Track button states
        self.button_states = {
            'startup': self.STATE_NOT_RUN,
            'dashboard': self.STATE_NOT_RUN,
            'rest_api': self.STATE_NOT_RUN,
            'mcp': self.STATE_NOT_RUN,
        }
        
        self.build_ui()
        self.update_button_colors()
        
    def build_ui(self):
        """Build the launcher UI."""
        # Title
        title = tk.Label(self.root, text="PoliSim", fg=CYBER_ACCENT, bg=CYBER_BG, font=("Segoe UI", 24, "bold"))
        title.pack(pady=(20, 4))
        
        subtitle = tk.Label(self.root, text="Cyberpunk Policy Simulator", fg=CYBER_SUB, bg=CYBER_BG, font=("Segoe UI", 11))
        subtitle.pack(pady=(0, 16))
        
        # Status display
        self.status_text = tk.Label(
            self.root, text="Status: Run Startup Check to begin", fg=CYBER_WARNING, bg=CYBER_BG, font=("Segoe UI", 10)
        )
        self.status_text.pack(pady=(0, 10))
        
        # Main content frame
        self.main_frame = tk.Frame(self.root, bg=CYBER_BG)
        self.main_frame.pack(fill="both", expand=True, padx=16, pady=10)
        
        # Startup check button (starts yellow - first action)
        self.startup_btn = self.add_large_button(
            "1. Run Startup Check",
            self.run_startup_check_threaded,
            bg=CYBER_WARNING
        )
        
        # Separator
        sep1 = tk.Label(self.main_frame, text="━" * 70, fg=CYBER_PANEL, bg=CYBER_BG, font=("Courier", 9))
        sep1.pack(fill="x", pady=12)
        
        # Server options
        tk.Label(self.main_frame, text="Launch Server", fg=CYBER_TEXT, bg=CYBER_BG, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 4))
        
        self.dashboard_btn = self.add_button("📊 Dashboard (Streamlit UI)", self.launch_dashboard_threaded, bg_color=CYBER_DISABLED)
        self.rest_btn = self.add_button("🔌 REST API Server", self.launch_rest_api_threaded, bg_color=CYBER_DISABLED)
        self.mcp_btn = self.add_button("🔗 MCP Server", self.launch_mcp_threaded, bg_color=CYBER_DISABLED)
        
        # Separator
        sep2 = tk.Label(self.main_frame, text="━" * 70, fg=CYBER_PANEL, bg=CYBER_BG, font=("Courier", 9))
        sep2.pack(fill="x", pady=12)
        
        # Resources - always white text
        tk.Label(self.main_frame, text="Resources", fg=CYBER_TEXT, bg=CYBER_BG, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 4))
        
        self.readme_btn = self.add_button("📖 View README / Docs", lambda: webbrowser.open(README_URL), bg_color=CYBER_ACCENT)
        self.android_btn = self.add_button("🤖 Android (Download Link)", lambda: webbrowser.open(ANDROID_URL), bg_color=CYBER_ACCENT, text_color=CYBER_WHITE)
        self.ios_btn = self.add_button("🍎 iOS (Download Link)", lambda: webbrowser.open(IOS_URL), bg_color=CYBER_ACCENT, text_color=CYBER_WHITE)
        
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
        self.log("PoliSim Launcher started.")
        self.log("⚠ Run 'Startup Check' first (yellow button).")
        
    def add_large_button(self, text, command, bg=CYBER_ACCENT, text_color=None):
        """Add a large button."""
        fg_color = text_color if text_color else CYBER_BG
        btn = tk.Button(
            self.main_frame, text=text, command=command, fg=fg_color, bg=bg,
            activebackground=CYBER_SUB, activeforeground=CYBER_BG,
            relief="flat", bd=0, padx=16, pady=14, font=("Segoe UI", 12, "bold"),
            cursor="hand2", wraplength=600, justify="left"
        )
        btn.pack(fill="x", pady=6)
        return btn
        
    def add_button(self, text, command, bg_color=CYBER_ACCENT, text_color=None):
        """Add a standard button."""
        fg_color = text_color if text_color else CYBER_TEXT
        btn = tk.Button(
            self.main_frame, text=text, command=command, fg=fg_color, bg=bg_color,
            activebackground=CYBER_SUB, activeforeground=CYBER_BG,
            relief="flat", bd=0, padx=12, pady=10, font=("Segoe UI", 10, "bold"),
            cursor="hand2", wraplength=600
        )
        btn.pack(fill="x", pady=4)
        return btn
    
    def update_button_colors(self):
        """Update button colors based on current states."""
        # Startup button
        startup_state = self.button_states['startup']
        if startup_state == self.STATE_NOT_RUN:
            self.startup_btn.config(bg=CYBER_WARNING, fg=CYBER_BG)  # Yellow - next action
        elif startup_state == self.STATE_RUNNING:
            self.startup_btn.config(bg=CYBER_WARNING, fg=CYBER_BG)  # Yellow - in progress
        elif startup_state == self.STATE_SUCCESS:
            self.startup_btn.config(bg=CYBER_SUCCESS, fg=CYBER_BG)  # Green - passed
        elif startup_state == self.STATE_FAILED:
            self.startup_btn.config(bg=CYBER_ERROR, fg=CYBER_TEXT)  # Red - failed
        
        # Server buttons - depend on startup success
        startup_passed = self.button_states['startup'] == self.STATE_SUCCESS
        
        # Dashboard button
        dash_state = self.button_states['dashboard']
        if not startup_passed:
            self.dashboard_btn.config(bg=CYBER_DISABLED, fg=CYBER_TEXT, state="disabled")
        elif dash_state == self.STATE_NOT_RUN:
            self.dashboard_btn.config(bg=CYBER_WARNING, fg=CYBER_BG, state="normal")  # Yellow - next action
        elif dash_state == self.STATE_RUNNING:
            self.dashboard_btn.config(bg=CYBER_WARNING, fg=CYBER_BG, state="disabled")
        elif dash_state == self.STATE_SUCCESS:
            self.dashboard_btn.config(bg=CYBER_SUCCESS, fg=CYBER_BG, state="normal")
        elif dash_state == self.STATE_FAILED:
            self.dashboard_btn.config(bg=CYBER_ERROR, fg=CYBER_TEXT, state="normal")
        
        # REST API button
        rest_state = self.button_states['rest_api']
        if not startup_passed:
            self.rest_btn.config(bg=CYBER_DISABLED, fg=CYBER_TEXT, state="disabled")
        elif rest_state == self.STATE_NOT_RUN:
            self.rest_btn.config(bg="#0066CC", fg=CYBER_TEXT, state="normal")  # Original blue
        elif rest_state == self.STATE_RUNNING:
            self.rest_btn.config(bg=CYBER_WARNING, fg=CYBER_BG, state="disabled")
        elif rest_state == self.STATE_SUCCESS:
            self.rest_btn.config(bg=CYBER_SUCCESS, fg=CYBER_BG, state="normal")
        elif rest_state == self.STATE_FAILED:
            self.rest_btn.config(bg=CYBER_ERROR, fg=CYBER_TEXT, state="normal")
        
        # MCP button
        mcp_state = self.button_states['mcp']
        if not startup_passed:
            self.mcp_btn.config(bg=CYBER_DISABLED, fg=CYBER_TEXT, state="disabled")
        elif mcp_state == self.STATE_NOT_RUN:
            self.mcp_btn.config(bg="#FF6600", fg=CYBER_TEXT, state="normal")  # Original orange
        elif mcp_state == self.STATE_RUNNING:
            self.mcp_btn.config(bg=CYBER_WARNING, fg=CYBER_BG, state="disabled")
        elif mcp_state == self.STATE_SUCCESS:
            self.mcp_btn.config(bg=CYBER_SUCCESS, fg=CYBER_BG, state="normal")
        elif mcp_state == self.STATE_FAILED:
            self.mcp_btn.config(bg=CYBER_ERROR, fg=CYBER_TEXT, state="normal")
        
        self.root.update()
    
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
        self.button_states['startup'] = self.STATE_RUNNING
        self.startup_btn.config(state="disabled")
        self.update_button_colors()
        self.update_status("Running startup check...", CYBER_WARNING)
        
        def run_check():
            try:
                self.log("Starting startup check...")
                self.log("  → Checking dependencies, data ingestion, and API prerequisites...")
                
                # Use --auto-install-deps to skip the input() prompt that causes hanging
                result = subprocess.run(
                    [sys.executable, str(ROOT_DIR / "main.py"), "--startup-check-only", "--auto-install-deps"],
                    cwd=str(ROOT_DIR),
                    capture_output=True,
                    text=True,
                    timeout=180  # 3 minutes - allow time for pip installs
                )
                
                # Log the output
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            self.log(f"  {line}")
                
                if result.returncode == 0:
                    self.log("✓ Startup check PASSED - All systems ready")
                    self.button_states['startup'] = self.STATE_SUCCESS
                    self.update_status("Ready to launch servers", CYBER_SUCCESS)
                    self.root.after(0, lambda: messagebox.showinfo("Startup Check", "All dependencies verified! Ready to launch."))
                else:
                    output = (result.stdout + result.stderr).strip()
                    self.log(f"✗ Startup check FAILED")
                    if result.stderr:
                        for line in result.stderr.strip().split('\n'):
                            if line.strip():
                                self.log(f"  ERROR: {line}")
                    self.button_states['startup'] = self.STATE_FAILED
                    self.update_status("Startup check failed - see log", CYBER_ERROR)
                    self.root.after(0, lambda: messagebox.showerror("Startup Check Failed", output[:500] if output else "Unknown error"))
                    
            except subprocess.TimeoutExpired:
                self.log("✗ Startup check timed out (>3 minutes)")
                self.button_states['startup'] = self.STATE_FAILED
                self.update_status("Startup check timed out", CYBER_ERROR)
                self.root.after(0, lambda: messagebox.showerror("Timeout", "Startup check took too long (>3 minutes).\nTry running manually: python main.py --startup-check-only"))
            except Exception as e:
                self.log(f"✗ Startup check error: {str(e)}")
                self.button_states['startup'] = self.STATE_FAILED
                self.update_status("Error running startup check", CYBER_ERROR)
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to run startup check: {str(e)}"))
            finally:
                self.startup_btn.config(state="normal")
                self.update_button_colors()
        
        thread = threading.Thread(target=run_check, daemon=True)
        thread.start()
    
    def launch_dashboard_threaded(self):
        """Launch Streamlit dashboard in background thread."""
        if self.button_states['startup'] != self.STATE_SUCCESS:
            messagebox.showwarning("Startup Check Required", "Please run startup check first (yellow button)!")
            return
        
        self.button_states['dashboard'] = self.STATE_RUNNING
        self.update_button_colors()
        self.log("Launching Dashboard (Streamlit)...")
        self.update_status("Launching Dashboard...", CYBER_WARNING)
        
        def launch():
            try:
                self.log("  → Starting Streamlit dashboard...")
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
                    self.log("✓ Dashboard running at http://localhost:8501")
                    self.button_states['dashboard'] = self.STATE_SUCCESS
                    self.update_status("Dashboard running at http://localhost:8501", CYBER_SUCCESS)
                    self.update_button_colors()
                    webbrowser.open("http://localhost:8501")
                else:
                    output = proc.stdout.read() if proc.stdout else ""
                    self.log(f"✗ Dashboard exited immediately (code {proc.returncode})")
                    if output:
                        self.log(f"  Output: {output[:200]}")
                    self.button_states['dashboard'] = self.STATE_FAILED
                    self.update_status("Dashboard launch failed", CYBER_ERROR)
                    self.update_button_colors()
                    self.root.after(0, lambda: messagebox.showerror("Launch Failed", output[:500] if output else "Streamlit exited before starting"))
            except Exception as e:
                self.log(f"✗ Failed to launch dashboard: {str(e)}")
                self.button_states['dashboard'] = self.STATE_FAILED
                self.update_status("Dashboard launch failed", CYBER_ERROR)
                self.update_button_colors()
                self.root.after(0, lambda: messagebox.showerror("Launch Failed", f"Failed to launch dashboard:\n{str(e)}"))
        
        thread = threading.Thread(target=launch, daemon=True)
        thread.start()
    
    def launch_rest_api_threaded(self):
        """Launch REST API server in background thread."""
        if self.button_states['startup'] != self.STATE_SUCCESS:
            messagebox.showwarning("Startup Check Required", "Please run startup check first!")
            return
        
        self.button_states['rest_api'] = self.STATE_RUNNING
        self.update_button_colors()
        self.log("Launching REST API Server...")
        self.update_status("Launching REST API...", CYBER_WARNING)
        
        def launch():
            try:
                self.log("  → Starting REST API server on localhost:5000...")
                env = dict(os.environ)
                env.setdefault("PYTHONIOENCODING", "utf-8")
                
                log_path = ROOT_DIR / "rest_api_server.log"
                log_file = open(log_path, "w", encoding="utf-8")
                proc = subprocess.Popen(
                    [sys.executable, "-m", "api.rest_server"],
                    cwd=str(ROOT_DIR),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env,
                    close_fds=True,
                )

                # Wait up to 8 seconds for the server to start
                for _ in range(8):
                    if proc.poll() is not None:
                        break
                    time.sleep(1)

                if proc.poll() is None:
                    self.log(f"✓ REST API running at http://localhost:5000 (log: {log_path})")
                    self.button_states['rest_api'] = self.STATE_SUCCESS
                    self.update_status("REST API running at http://localhost:5000", CYBER_SUCCESS)
                    self.update_button_colors()
                    webbrowser.open("http://localhost:5000")
                else:
                    log_file.close()
                    with open(log_path, "r", encoding="utf-8") as f:
                        output = f.read()
                    self.log(f"✗ REST API exited immediately. Output in log file:\n{output}")
                    self.button_states['rest_api'] = self.STATE_FAILED
                    self.update_status("REST API launch failed", CYBER_ERROR)
                    self.update_button_colors()
                    self.root.after(0, lambda: messagebox.showerror("Launch Failed", output[-2000:] if output else "REST API exited"))
            except Exception as e:
                self.log(f"✗ Failed to launch REST API: {str(e)}")
                self.button_states['rest_api'] = self.STATE_FAILED
                self.update_status("REST API launch failed", CYBER_ERROR)
                self.update_button_colors()
                self.root.after(0, lambda: messagebox.showerror("Launch Failed", f"Failed to launch REST API:\n{str(e)}"))
        
        thread = threading.Thread(target=launch, daemon=True)
        thread.start()
    
    def launch_mcp_threaded(self):
        """Launch MCP server in background thread."""
        if self.button_states['startup'] != self.STATE_SUCCESS:
            messagebox.showwarning("Startup Check Required", "Please run startup check first!")
            return
        
        self.button_states['mcp'] = self.STATE_RUNNING
        self.update_button_colors()
        self.log("Launching MCP Server...")
        self.update_status("Launching MCP Server...", CYBER_WARNING)
        
        def launch():
            try:
                self.log("  → Starting MCP server...")
                env = dict(os.environ)
                env.setdefault("PYTHONIOENCODING", "utf-8")
                
                proc = subprocess.Popen(
                    [sys.executable, "mcp_server.py"],
                    cwd=str(ROOT_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env,
                )
                
                # Give the server a moment to start
                time.sleep(2)
                
                if proc.poll() is None:
                    self.log("✓ MCP Server is running")
                    self.button_states['mcp'] = self.STATE_SUCCESS
                    self.update_status("MCP Server running", CYBER_SUCCESS)
                    self.update_button_colors()
                    self.root.after(0, lambda: messagebox.showinfo("MCP Server", "MCP Server is now running and ready for connections."))
                else:
                    output = proc.stdout.read() if proc.stdout else ""
                    self.log(f"✗ MCP Server exited immediately")
                    self.button_states['mcp'] = self.STATE_FAILED
                    self.update_status("MCP server launch failed", CYBER_ERROR)
                    self.update_button_colors()
                    self.root.after(0, lambda: messagebox.showerror("Launch Failed", output[:500] if output else "MCP Server exited"))
            except Exception as e:
                self.log(f"✗ Failed to launch MCP server: {str(e)}")
                self.button_states['mcp'] = self.STATE_FAILED
                self.update_status("MCP server launch failed", CYBER_ERROR)
                self.update_button_colors()
                self.root.after(0, lambda: messagebox.showerror("Launch Failed", f"Failed to launch MCP server:\n{str(e)}"))
        
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