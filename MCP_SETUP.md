# POLISIM MCP Setup Guide

## Installation & Configuration for Different Environments

### 1. Claude Desktop (Mac/Linux/Windows)

#### Step 1: Install POLISIM

```bash
git clone https://github.com/GalacticOrgOfDev/polisim.git
cd polisim
pip install -r requirements.txt
```

#### Step 2: Configure Claude Desktop

**macOS/Linux:**
```bash
# Edit or create ~/.config/Claude/claude_desktop_config.json
nano ~/.config/Claude/claude_desktop_config.json
```

**Windows:**
```bash
# Edit or create %APPDATA%\Claude\claude_desktop_config.json
# Usually: C:\Users\<Username>\AppData\Roaming\Claude\claude_desktop_config.json
```

**Add this configuration:**
```json
{
  "mcpServers": {
    "polisim": {
      "command": "python",
      "args": ["/absolute/path/to/polisim/mcp_server.py"],
      "cwd": "/absolute/path/to/polisim",
      "env": {
        "PYTHONPATH": "/absolute/path/to/polisim"
      },
      "description": "POLISIM Economic Policy Simulator"
    }
  }
}
```

⚠️ **Important**: Use **absolute paths**, not relative paths or `~`

**Find your absolute path:**
```bash
# macOS/Linux
pwd  # Run this in the polisim directory

# Windows PowerShell
Get-Location
```

#### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop. You should see "POLISIM" in the tools menu.

---

### 2. Cursor IDE

Similar to Claude Desktop. Edit `.cursor/settings.json`:

```json
{
  "mcpServers": {
    "polisim": {
      "command": "python",
      "args": ["/path/to/polisim/mcp_server.py"],
      "cwd": "/path/to/polisim"
    }
  }
}
```

---

### 3. Custom Python Applications

Use the example client:

```python
from mcp_client_example import PolisimMCPClient

# Create client (starts server automatically)
client = PolisimMCPClient()

# Run simulation
result = client.run_simulation(
    policy_name="United_States_Galactic_Health_Act",
    years=30,
    iterations=50000
)

# Print results
if result['result']['status'] == 'success':
    print(f"Mean debt: ${result['result']['results']['mean_debt_2050']:,.0f}B")
```

---

### 4. Programmatic Integration (Direct MCP Protocol)

```python
import json
import subprocess

# Start server
proc = subprocess.Popen(
    ['python', 'mcp_server.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Send request
request = {
    "type": "call_tool",
    "name": "run_simulation",
    "input": {
        "policy_name": "My_Policy",
        "years": 25
    }
}

proc.stdin.write(json.dumps(request) + '\n')
proc.stdin.flush()

# Read response
response = json.loads(proc.stdout.readline())
print(response)
```

---

### 5. Docker Container

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /polisim
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "mcp_server.py"]
```

Build and run:

```bash
docker build -t polisim-mcp .
docker run -i -t polisim-mcp
```

Then reference in MCP config:
```json
{
  "mcpServers": {
    "polisim": {
      "command": "docker",
      "args": ["run", "-i", "polisim-mcp"]
    }
  }
}
```

---

## Verification

### Test the MCP Server

```bash
# Terminal 1: Start server
python mcp_server.py

# Terminal 2: Run example client
python mcp_client_example.py
```

Expected output:
```
======================================================================
POLISIM MCP CLIENT EXAMPLE
======================================================================

1. Listing available tools...
   Found 5 tools:
   - run_simulation: Execute Monte Carlo simulation...
   - compare_scenarios: Compare two policy scenarios...
   - sensitivity_analysis: Analyze parameter sensitivity...
   - get_policy_catalog: Retrieve available policies...
   - get_config_parameters: Access configuration parameters...

2. Retrieving policy catalog...
   Available policies: ['Current_US_Healthcare_System', 'United_States_Galactic_Health_Act']

3. Running simulation...
   Policy: United_States_Galactic_Health_Act
   ...
```

### Check Claude Desktop Connection

In Claude Desktop:
1. Look for 🔌 tool icon in message composer
2. Click to see available tools
3. "POLISIM" should appear with 5 tools listed

---

## Troubleshooting

### "Module not found" errors

Ensure dependencies are installed:
```bash
pip install -r requirements.txt --upgrade
python -c "import pandas; import numpy; import scipy; print('All dependencies OK')"
```

### Server won't start

Check Python path:
```bash
which python  # macOS/Linux
Get-Command python  # Windows
python --version
```

Make sure Python 3.9+ is installed.

### Claude Desktop won't connect

1. Verify absolute path (not `~` or relative)
2. Restart Claude Desktop completely
3. Check config file JSON syntax: `python -m json.tool claude_desktop_config.json`
4. Try running mcp_server.py manually first: `python /path/to/polisim/mcp_server.py`

### Timeout errors

If simulations timeout:
- Reduce `iterations` parameter (default: 10,000)
- Increase timeout in client code
- Run on faster hardware

---

## Environment Variables

The MCP server respects these environment variables:

```bash
# Enable debug logging
export POLISIM_DEBUG=1
python mcp_server.py

# Custom config file
export POLISIM_CONFIG=/path/to/custom_config.yaml
python mcp_server.py

# Log file location
export POLISIM_LOG_FILE=/var/log/polisim_mcp.log
python mcp_server.py
```

---

## Advanced Configuration

### Custom Policy Loading

Place custom policy files in `policies/` directory:

```bash
cp my_policy.json policies/my_policy.json
```

Then reference in MCP calls:
```json
{
  "type": "call_tool",
  "name": "run_simulation",
  "input": {
    "policy_name": "my_policy"
  }
}
```

### Rate Limiting

For production deployments, add rate limiting to `mcp_server.py`:

```python
from functools import wraps
from time import time

def rate_limit(calls_per_second=1):
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time() - last_called[0]
            wait_time = min_interval - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
            result = func(*args, **kwargs)
            last_called[0] = time()
            return result
        return wrapper
    return decorator

# Apply to run_simulation method
@rate_limit(calls_per_second=2)
def run_simulation(self, ...):
    # implementation
```

---

## Performance Optimization

### For AI Agent Integration

Recommended settings for interactive use with LLMs:

```python
# Fast analysis (for exploration)
run_simulation(policy_name="...", iterations=5000)

# Balanced (default)
run_simulation(policy_name="...", iterations=10000)

# Detailed analysis (for publication)
run_simulation(policy_name="...", iterations=100000)
```

### Parallel Simulations

For multiple scenarios, run in parallel:

```python
import concurrent.futures

policies = ["Policy_A", "Policy_B", "Policy_C"]

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(client.run_simulation, policy_name=p)
        for p in policies
    ]
    results = [f.result() for f in futures]
```

---

## Security Best Practices

### For Production

1. **Input Validation**: Add parameter bounds checks
2. **Authentication**: Add API key requirement
3. **Sandboxing**: Run in container with resource limits
4. **Logging**: Monitor all requests
5. **Rate Limiting**: Prevent resource exhaustion

### Example: Add Authentication

```python
import os
import base64

class AuthenticatedPolisimMCPServer(PolisimMCPServer):
    def handle_request(self, request):
        # Check API key
        api_key = request.get("api_key")
        if not api_key or api_key != os.environ.get("POLISIM_API_KEY"):
            return {"type": "error", "message": "Unauthorized"}
        
        return super().handle_request(request)
```

---

## Support & Issues

- **GitHub Issues**: https://github.com/GalacticOrgOfDev/polisim/issues
- **Documentation**: [MCP_INTEGRATION.md](MCP_INTEGRATION.md)
- **Example Client**: [mcp_client_example.py](mcp_client_example.py)

