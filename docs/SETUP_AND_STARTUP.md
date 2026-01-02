# Setup, Startup & Deployment

---

## Quick Start Guide

### Minimum Requirements

- **Python:** 3.9+
- **RAM:** 2GB minimum (4GB recommended)
- **Disk:** 500MB for dependencies and cache
- **OS:** Windows, Linux, or macOS

### Installation (Windows Desktop)

#### Option 1: Launcher (Recommended ✅)

```powershell
# Launch the graphical installer/launcher
python launcher.py
```

**Why use the launcher?**
- ✅ Validates all dependencies before starting
- ✅ Checks CBO data ingestion and API prerequisites
- ✅ Auto-installs missing packages (with approval)
- ✅ Non-blocking UI - no freezing during operations
- ✅ Real-time activity log with timestamps
- ✅ One-click access to Dashboard, API, or MCP Server

The launcher will:
1. Detect existing Python or download embeddable Python
2. Create virtual environment
3. Install dependencies
4. Run comprehensive startup check
5. Launch dashboard, API, or MCP server

See [LAUNCHER_GUIDE.md](LAUNCHER_GUIDE.md) for detailed documentation.

#### Option 2: Manual Setup (Advanced Users)

> ⚠️ **Note:** Manual setup skips the comprehensive dependency validation that `launcher.py` provides.

```powershell
# Navigate to project directory
cd e:\AI Projects\polisim

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run startup check
python main.py --startup-check-only

# Start dashboard
streamlit run ui/dashboard.py

# OR start API server
python api/rest_server.py
```

---

## Startup Check

### Purpose

The startup check ensures:
- All dependencies are installed and correct versions
- Python environment is properly configured
- CBO data can be ingested successfully
- API endpoints are functional
- Database connections work (if applicable)

### Run Startup Check

```powershell
# Headless mode (CLI output)
python main.py --startup-check-only

# Auto-install missing dependencies
python main.py --startup-check-only --auto-install-deps

# Verbose output
python main.py --startup-check-only --verbose
```

### Startup Check Output

**Success Example:**
```
✅ Python Environment
   - Version: 3.11.8
   - Virtual env: C:\project\.venv
   - Packages: 47 installed

✅ Core Dependencies
   - pandas: 2.0.1 ✓
   - numpy: 1.24.2 ✓
   - scipy: 1.10.1 ✓
   - PyYAML: 6.0 ✓

✅ API Dependencies
   - flask: 2.3.0 ✓
   - PyJWT: 2.6.0 ✓
   - redis: 4.5.1 ✓

✅ CBO Data Ingestion
   - Cache file: Found (5.2 hours old)
   - Checksum: abc123def456 ✓
   - Schema: Valid ✓

✅ API Health Check
   - Server: Running on localhost:5000 ✓
   - Endpoints: All reachable ✓

✅ All Checks Passed - Ready to run!
```

**Failure Example:**
```
⚠️ Missing Dependencies
   - plotly: NOT INSTALLED (required for dashboards)
   - redis: NOT INSTALLED (optional, for caching)

💡 Install with: pip install plotly redis

🔍 Data Issues
   - CBO Cache: Missing (will fetch on first use)
   - Schema: Validation will run during first request

✓ Continue anyway (data will be fetched at runtime)
✗ Exit and install dependencies
```

---

## Dependency Management

### Core Dependencies (Required)

```
pandas>=2.0.0           # Data manipulation
numpy>=1.24.0           # Numerical computing
scipy>=1.10.0           # Scientific computing
PyYAML>=6.0             # Configuration management
openpyxl>=3.10.0        # Excel file handling
requests>=2.31.0        # HTTP requests
beautifulsoup4>=4.12.0  # HTML parsing
pypdf>=3.13.0           # PDF reading
```

### API Server (Required for REST API)

```
flask>=2.3.0            # Web framework
flask-cors>=4.0.0       # CORS support
PyJWT>=2.6.0            # JWT tokens
SQLAlchemy>=2.0.0       # Database ORM
alembic>=1.11.0         # Database migrations
```

### Dashboard (Required for Streamlit UI)

```
streamlit>=1.28.0       # Web dashboard framework
plotly>=5.14.0          # Interactive charts
```

### Optional Dependencies

```
redis>=4.5.0            # Caching (improves performance)
pdfplumber>=0.10.0      # Advanced PDF extraction
reportlab>=4.0.0        # PDF generation
gunicorn>=21.0.0        # Production WSGI server (Linux/macOS)
pytest>=7.0.0           # Testing (dev only)
pytest-xdist>=3.0.0     # Parallel testing (dev only)
black>=23.0.0           # Code formatting (dev only)
pylint>=2.0.0           # Code linting (dev only)
```

### Check Installed Packages

```powershell
# List all installed packages
pip list

# Check specific package
pip show pandas

# Check if package can be imported
python -c "import pandas; print(pandas.__version__)"
```

### Add New Dependencies

1. **Update requirements.txt:**
```
# requirements.txt
numpy>=1.24.0
pandas>=2.0.0
# ... add new dependency at end
new-package>=1.0.0
```

2. **Install to environment:**
```powershell
pip install new-package>=1.0.0
```

3. **Update startup check:**
   - Edit `main.py` or `conftest.py` to verify new package
   - Test startup check: `python main.py --startup-check-only`

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Python Environment
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# API Configuration
API_HOST=localhost
API_PORT=5000
API_DEBUG=false
API_WORKERS=4

# CBO Data
CBO_DATA_CACHE_PATH=./core/cbo_data_cache.json
CBO_DATA_HISTORY_PATH=./core/cbo_data_history.json

# CORS & Security
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000
API_HTTPS_ONLY=true
API_RATE_LIMIT_GLOBAL=100

# Database (if using)
DATABASE_URL=sqlite:///./polisim.db
DATABASE_POOL_SIZE=5

# Secrets & Auth
JWT_SECRET_KEY=change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379/0
```

### YAML Configuration

Edit `config.yaml` for advanced settings:

```yaml
api:
  host: localhost
  port: 5000
  debug: false
  workers: 4
  rate_limit: 100  # requests/minute per IP

data:
  cache_path: ./core/cbo_data_cache.json
  history_path: ./core/cbo_data_history.json
  cache_ttl: 3600  # seconds

security:
  https_only: true
  cors_origins:
    - http://localhost:3000
    - http://localhost:5000
  jwt_secret: change-in-production
  jwt_expiration: 24  # hours

dashboard:
  theme: light
  port: 8501
  host: 0.0.0.0
```

---

## Running the Application

### Start Dashboard (Streamlit)

```powershell
# Basic start
streamlit run ui/dashboard.py

# Custom port
streamlit run ui/dashboard.py --server.port 8080

# No browser auto-open
streamlit run ui/dashboard.py --logger.level=warning
```

**Access:** http://localhost:8501

### Start API Server (Flask)

```powershell
# Development mode
python api/rest_server.py

# Production mode with gunicorn (Linux/macOS)
gunicorn -w 4 -b 0.0.0.0:5000 api.rest_server:app

# Windows production (use waitress)
pip install waitress
python -m waitress --port=5000 api.rest_server:app
```

**Access:** http://localhost:5000

### Run Simulations

```powershell
# Interactive Python shell
python

# Then in Python:
from core.simulation import PolicySimulator
from core.policies import Policy

# Create a policy
policy = Policy(name="Tax Reform", description="10% corporate tax cut")

# Run simulation
simulator = PolicySimulator()
results = simulator.run(policy, years=10)

# View results
print(f"Revenue impact: ${results.revenue_change:,.0f}")
print(f"GDP impact: {results.gdp_impact:.1%}")
```

---

## Troubleshooting

### Python Not Found

**Error:** `'python' is not recognized`

**Solutions:**
```powershell
# Check Python installation
python --version

# If not found, add Python to PATH or use full path
C:\Python311\python --version

# Use embedded Python from launcher
.\launcher.exe  # Downloads Python if missing
```

### Virtual Environment Issues

**Error:** `Cannot activate virtual environment`

**Solutions:**
```powershell
# Create new virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# If PowerShell won't allow scripts, use:
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
```

### Missing Dependencies

**Error:** `ModuleNotFoundError: No module named 'pandas'`

**Solutions:**
```powershell
# Install missing package
pip install pandas

# Or run startup check and auto-install
python main.py --startup-check-only --auto-install-deps
```

### CBO Data Issues

**Error:** `CBO data cache corrupted or invalid`

**Solutions:**
```powershell
# Clear cache and let it re-fetch
del core\cbo_data_cache.json

# Run startup check (will trigger new fetch)
python main.py --startup-check-only

# Verify schema
python -c "from core.cbo_scraper import scrape_cbo_data; scrape_cbo_data()"
```

### Port Already in Use

**Error:** `Address already in use: ('localhost', 5000)`

**Solutions:**
```powershell
# Find process using port 5000
Get-NetTCPConnection -LocalPort 5000 | Select-Object OwnerProcess

# Kill the process (replace PID with actual process ID)
Stop-Process -Id PID -Force

# Or use different port
streamlit run ui/dashboard.py --server.port 8080
```

---

## Development Workflow

### Setting Up for Development

```powershell
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks (optional)
pre-commit install

# Run tests
pytest

# Run tests in parallel
pytest -n auto

# Run specific test file
pytest tests/test_simulation.py

# Run with coverage
pytest --cov=core --cov=api
```

### Code Style

```powershell
# Format code with black
black .

# Lint with pylint
pylint core api

# Type checking with pyright
pyright .
```

---

## Docker Deployment

### Build Docker Image

```powershell
# Build image
docker build -t polisim:latest .

# Or with dashboard
docker build -f Dockerfile.dashboard -t polisim-dashboard:latest .
```

### Run with Docker Compose

```powershell
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Compose Services

**Default configuration includes:**
- API server (port 5000)
- Streamlit dashboard (port 8501)
- Redis cache (port 6379)
- PostgreSQL database (port 5432)

---

## Platform-Specific Notes

### Windows

- Use `.venv\Scripts\Activate.ps1` to activate virtual environment
- Use backslashes or raw strings for file paths
- PowerShell may require: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned`

### Linux / macOS

- Use `source .venv/bin/activate` to activate virtual environment
- Use forward slashes for file paths
- May need `pip3` instead of `pip`
- Use `gunicorn` for production WSGI server

### Android / iOS

- Download mobile app from app store (when available)
- No local Python setup required
- App connects to remote PoliSim API server

---

## Next Steps

1. **Run startup check:** `python main.py --startup-check-only`
2. **Start dashboard:** `streamlit run ui/dashboard.py`
3. **Access UI:** http://localhost:8501
4. **Create simulation:** Use dashboard UI to create policies and run simulations
5. **Review results:** View charts and export reports

For API development, see [API_ENDPOINTS.md](API_ENDPOINTS.md)  
For testing, see [TEST_SUITE_STATUS.md](TEST_SUITE_STATUS.md)
