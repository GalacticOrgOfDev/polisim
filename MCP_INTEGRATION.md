# POLISIM MCP Server - AI Agent Integration Guide

## Overview

POLISIM is now available as an **MCP (Model Context Protocol) Server**, enabling AI agents and LLMs to use it as a callable tool. This allows AI systems to perform economic policy analysis, run simulations, and compare scenarios programmatically.

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/GalacticOrgOfDev/polisim.git
cd polisim

# Install dependencies
pip install -r requirements.txt
```

### 2. Run MCP Server

```bash
# Start the MCP server (listens on stdin/stdout)
python mcp_server.py
```

### 3. Configure Claude Desktop (for Claude users)

Add to `~/.config/Claude/claude_desktop_config.json` (Mac/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "polisim": {
      "command": "python",
      "args": ["/path/to/polisim/mcp_server.py"],
      "cwd": "/path/to/polisim",
      "env": {
        "PYTHONPATH": "/path/to/polisim:$PYTHONPATH"
      }
    }
  }
}
```

Replace `/path/to/polisim` with your actual project path.

## Available Tools

### 1. `run_simulation`

Execute a Monte Carlo economic simulation with specified policy parameters.

**Parameters:**
- `policy_name` (string, required): Name of the policy scenario
- `years` (integer, optional): Number of years to simulate (default: 22)
- `iterations` (integer, optional): Monte Carlo iterations (default: 10,000)
- `parameters` (object, optional): Override economic parameters

**Example:**
```json
{
  "type": "call_tool",
  "name": "run_simulation",
  "input": {
    "policy_name": "United_States_Galactic_Health_Act",
    "years": 30,
    "iterations": 50000
  }
}
```

**Returns:**
```json
{
  "status": "success",
  "results": {
    "policy_name": "United_States_Galactic_Health_Act",
    "years": 30,
    "iterations": 50000,
    "mean_debt_2050": 45230000000000,
    "std_debt_2050": 3210000000000,
    "percentiles": {
      "p10": 42100000000000,
      "p25": 43500000000000,
      "p50": 45200000000000,
      "p75": 46900000000000,
      "p90": 48100000000000
    }
  }
}
```

### 2. `compare_scenarios`

Compare two policy scenarios side-by-side with detailed metrics.

**Parameters:**
- `baseline_policy` (string, required): Name of baseline policy
- `alternative_policy` (string, required): Name of alternative policy
- `years` (integer, optional): Number of years to simulate (default: 22)

**Example:**
```json
{
  "type": "call_tool",
  "name": "compare_scenarios",
  "input": {
    "baseline_policy": "Current_US_Healthcare_System",
    "alternative_policy": "United_States_Galactic_Health_Act",
    "years": 25
  }
}
```

**Returns:**
Detailed comparison with metrics for both scenarios

### 3. `sensitivity_analysis`

Analyze how changes in economic parameters affect simulation outcomes.

**Parameters:**
- `policy_name` (string, required): Policy scenario name
- `parameters` (array, optional): Parameters to vary (e.g., ['inflation_rate', 'population_growth'])
- `variance_percent` (number, optional): Percentage variance (default: 20%)

**Example:**
```json
{
  "type": "call_tool",
  "name": "sensitivity_analysis",
  "input": {
    "policy_name": "United_States_Galactic_Health_Act",
    "parameters": ["inflation_rate", "population_growth"],
    "variance_percent": 25
  }
}
```

### 4. `get_policy_catalog`

Retrieve all available policy scenarios, optionally filtered.

**Parameters:**
- `filter` (string, optional): Filter keyword

**Example:**
```json
{
  "type": "call_tool",
  "name": "get_policy_catalog",
  "input": {
    "filter": "galactic"
  }
}
```

**Returns:**
```json
{
  "status": "success",
  "count": 2,
  "policies": [
    "Current_US_Healthcare_System",
    "United_States_Galactic_Health_Act"
  ]
}
```

### 5. `get_config_parameters`

Retrieve current configuration parameters.

**Parameters:**
- `section` (string, optional): Config section (e.g., 'economic', 'simulation')

**Example:**
```json
{
  "type": "call_tool",
  "name": "get_config_parameters",
  "input": {
    "section": "economic"
  }
}
```

## MCP Request Format

All requests follow the MCP (Model Context Protocol) standard:

```json
{
  "type": "call_tool",
  "name": "tool_name",
  "input": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

## MCP Response Format

Responses include status and results:

```json
{
  "type": "call_tool_response",
  "name": "tool_name",
  "result": {
    "status": "success|error",
    "results": {...} or "message": "error message"
  }
}
```

## Integration with AI Agents

### Claude.ai / Claude Desktop

Once configured, the POLISIM server will be automatically available to Claude. You can ask:

```
"Run a 30-year Monte Carlo simulation of the United States Galactic Health Act 
with 50,000 iterations and show me the percentiles"
```

Claude will automatically:
1. Call the `run_simulation` tool
2. Parse the results
3. Provide analysis and interpretation

### Custom AI Agents

To integrate with your own AI agents:

1. **Start the server:**
   ```bash
   python mcp_server.py
   ```

2. **Send MCP requests via stdin:**
   ```python
   import json
   import subprocess

   proc = subprocess.Popen(
       ['python', 'mcp_server.py'],
       stdin=subprocess.PIPE,
       stdout=subprocess.PIPE,
       stderr=subprocess.PIPE,
       text=True
   )

   # Send request
   request = {
       "type": "call_tool",
       "name": "run_simulation",
       "input": {"policy_name": "My_Policy"}
   }
   proc.stdin.write(json.dumps(request) + '\n')
   proc.stdin.flush()

   # Read response
   response = json.loads(proc.stdout.readline())
   print(response)
   ```

3. **Parse responses and provide to your LLM context**

## Architecture

### MCP Server Components

- **PolisimMCPServer**: Main server class handling MCP protocol
- **Tool Methods**: Each tool is a method on the server class
- **Request Handler**: `handle_request()` routes requests to appropriate tools
- **Error Handling**: All tools return standardized error responses

### Integration with Core Engine

The MCP server wraps the following core modules:

- `core.economic_engine`: MonteCarloEngine, EconomicModel, SensitivityAnalyzer
- `core.config`: Configuration management
- `utils.logging_config`: Structured logging
- `core.policies`: Policy scenario management

## Performance Considerations

### Simulation Parameters

- **Default iterations**: 10,000 (balance between accuracy and speed)
- **Recommended for detailed analysis**: 50,000-100,000 iterations
- **Maximum recommended**: 500,000 iterations (may take several minutes)

### Optimization

For AI agent integration:
- Start with default parameters (10,000 iterations)
- Use fewer iterations for exploratory analysis
- Use sensitivity_analysis instead of multiple simulations when analyzing parameter ranges

## Security

⚠️ **Important**: The MCP server executes code based on AI agent requests. For production deployment:

1. **Validate input parameters** - Don't allow arbitrary parameter overrides
2. **Rate limit requests** - Prevent resource exhaustion
3. **Sandbox execution** - Run in isolated container/environment
4. **Authentication** - Add authentication for external access

## Troubleshooting

### Server won't start

```bash
# Check Python installation
python --version

# Check dependencies
pip list | grep -E "pandas|numpy|scipy"

# Run with verbose output
python mcp_server.py 2>&1 | head -20
```

### Tool execution fails

Check logs:
```bash
# View stderr output
python mcp_server.py 2>/tmp/mcp.log
tail -f /tmp/mcp.log
```

### Configuration issues

Verify config.yaml exists:
```bash
ls -la config.yaml
cat config.yaml | head -20
```

## Examples

### Example 1: Run Simulation and Analyze Results

```python
import json
import subprocess

proc = subprocess.Popen(['python', 'mcp_server.py'], 
                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

request = {
    "type": "call_tool",
    "name": "run_simulation",
    "input": {
        "policy_name": "United_States_Galactic_Health_Act",
        "years": 22,
        "iterations": 50000
    }
}

proc.stdin.write(json.dumps(request) + '\n')
proc.stdin.flush()
response = json.loads(proc.stdout.readline())

if response['result']['status'] == 'success':
    results = response['result']['results']
    print(f"Mean debt in 2050: ${results['mean_debt_2050']:,.0f}B")
    print(f"95% confidence interval: ${results['percentiles']['p2.5']:,.0f}B - ${results['percentiles']['p97.5']:,.0f}B")
```

### Example 2: Compare Two Policies

```python
request = {
    "type": "call_tool",
    "name": "compare_scenarios",
    "input": {
        "baseline_policy": "Current_US_Healthcare_System",
        "alternative_policy": "United_States_Galactic_Health_Act",
        "years": 25
    }
}

proc.stdin.write(json.dumps(request) + '\n')
proc.stdin.flush()
response = json.loads(proc.stdout.readline())
comparison = response['result']['results']
```

## Contributing

To add new tools to the MCP server:

1. Add method to `PolisimMCPServer` class
2. Add tool definition to `list_tools()`
3. Add case to `call_tool()` method
4. Document in this README

## License

MIT License - See LICENSE file

## Support

For issues or questions:
- GitHub Issues: https://github.com/GalacticOrgOfDev/polisim/issues
- Email: galacticorgofdev@gmail.com
