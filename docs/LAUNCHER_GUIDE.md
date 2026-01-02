# PoliSim Launcher v2 - User Guide

**Version:** 2.0  
**Date:** January 1, 2026  
**Status:** Production Ready

---

## Overview

The overhauled PoliSim Launcher provides a modern, responsive interface for:
- Running dependency checks
- Launching Dashboard (Streamlit)
- Starting REST API Server
- Running MCP Server
- Accessing documentation and resources

---

## Key Features

### ✅ Non-Blocking Interface
- All long-running operations (startup checks, server launches) run in background threads
- UI remains responsive while tasks execute
- No more freezing or "Not Responding" errors

### 🔄 Integrated Startup Check
- Validates all dependencies before launching
- Provides detailed feedback on missing packages
- Auto-installs missing dependencies (with approval)
- Checks CBO data ingestion and API prerequisites

### 🖥️ Multiple Server Options

#### Dashboard (Streamlit)
- Interactive web interface for running simulations
- Access at: `http://localhost:8501`
- Full UI with scenario explorer, report generation, etc.

#### REST API Server
- Headless API for programmatic access
- Base URL: `http://localhost:5000`
- OpenAPI documentation at `/api/docs`

#### MCP Server
- Model Context Protocol server for AI integration
- Enables Claude and other AI assistants to use PoliSim tools
- Configured via `mcp_config.json`

### 📊 Real-Time Activity Log
- See all operations in real-time
- Timestamps for each action
- Clear success/failure messages
- Helpful error details

---

## Getting Started

### 1. Start the Launcher
```bash
python launcher.py
```

### 2. Run Startup Check
Click **"1. Run Startup Check"** button to verify:
- All Python dependencies installed
- Correct versions
- CBO data available (cached or live)
- API configuration valid

**Note:** You must run startup check once before launching any server.

### 3. Launch Your Preferred Server

**Option A: Dashboard (Recommended for Users)**
- Click **"📊 Dashboard (Streamlit UI)"**
- Opens browser at `http://localhost:8501`
- Interactive policy simulator with visualizations

**Option B: REST API Server (For Developers)**
- Click **"🔌 REST API Server"**
- Access at `http://localhost:5000`
- Use for programmatic access or integration

**Option C: MCP Server (For AI Integration)**
- Click **"🔗 MCP Server"**
- Enables AI assistants to use PoliSim
- Check `mcp_config.json` for configuration

### 4. Access Documentation
- **"📖 View README / Docs"** - GitHub repository and documentation
- **"🤖 Android (Download Link)"** - Download mobile app
- **"🍎 iOS (Download Link)"** - Download iOS app

---

## Activity Log Interpretation

### Success Messages
```
[14:23:45] Starting startup check...
[14:23:47] ✓ Startup check PASSED - All dependencies available
[14:23:48] Ready to launch
```

### Error Messages
```
[14:25:12] ✗ Startup check FAILED:
[14:25:12] Missing: openpyxl (Excel support)
[14:25:12] Please install and try again
```

### Server Launch Messages
```
[14:26:01] Launching Dashboard (Streamlit)...
[14:26:02] Starting Streamlit dashboard...
[14:26:05] ✓ Dashboard launched (streamlit is running in background)
[14:26:05] Dashboard running at http://localhost:8501
```

---

## Troubleshooting

### Problem: Startup Check Fails
**Solution:**
1. Check that all required packages are installed: `pip install -r requirements.txt`
2. Run manually: `python main.py --startup-check-only`
3. If specific packages missing, install them: `pip install <package_name>`

### Problem: Dashboard Won't Start
**Solution:**
1. Ensure Streamlit is installed: `pip install streamlit`
2. Check that port 8501 is not in use
3. View the activity log for detailed error messages

### Problem: REST API Won't Start
**Solution:**
1. Verify Flask is installed: `pip install flask flask-cors`
2. Check that port 5000 is not in use
3. Check `config.yaml` for valid API configuration

### Problem: Port Already in Use
**Solution:**
Change the port in `config.yaml`:
```yaml
api:
  port: 5001  # Use different port
```

### Problem: openpyxl Import Fails
**Solution:**
Even if pip shows installed, the import may fail due to environment issues:
```bash
pip uninstall openpyxl -y
pip install openpyxl
```

---

## Advanced Usage

### Running Multiple Servers
You can run multiple servers simultaneously by launching them in sequence:
1. Click "Startup Check" (once per session)
2. Click "Dashboard" → Starts on port 8501
3. Click "REST API Server" → Starts on port 5000
4. Click "MCP Server" → Starts on default MCP port

All run independently in the background.

### Programmatic Access
If using the REST API, you can integrate with external applications:
```python
import requests

# Get health status
response = requests.get('http://localhost:5000/api/health')
print(response.json())

# Run simulation
response = requests.post('http://localhost:5000/api/simulation/run', json={
    "policy": { ... },
    "years": 10
})
```

### Environment Configuration
Set environment variables to customize behavior:
```bash
# Dashboard
set STREAMLIT_SERVER_PORT=8502

# REST API
set API_HOST=0.0.0.0
set API_PORT=5001
set API_DEBUG=false

# Startup check
set AUTO_INSTALL_DEPS=true
```

---

## Architecture

### Threading Model
- Main UI thread handles button clicks and display
- Background threads execute long-running operations
- No blocking operations on main thread
- Graceful error handling and timeouts

### Timeout Protection
- Startup check: 2 minutes max
- Server launches: 5 seconds to start (then runs indefinitely)
- Bootstrap script: 10 minutes max

---

## What's New in v2

✅ **Non-blocking UI** - No more freezing  
✅ **Multiple servers** - Dashboard, REST API, MCP  
✅ **Integrated startup check** - Verify everything before launch  
✅ **Activity log** - Real-time operation feedback  
✅ **Better error messages** - Know what's wrong and how to fix it  
✅ **Threading** - Background execution of long tasks  
✅ **Professional UI** - Cyberpunk theme maintained  

---

## Configuration

All launcher behavior is driven by:
- `config.yaml` - Server ports and settings
- `requirements.txt` - Required packages
- `mcp_config.json` - MCP server configuration
- Environment variables - Runtime overrides

---

## Support

For issues or questions:
1. Check the activity log for error messages
2. Review the docs: `docs/SETUP_AND_STARTUP.md`
3. Check GitHub: https://github.com/GalacticOrgOfDev/polisim

---

**Ready to simulate policy? Start the launcher and hit "Run Startup Check"!**
