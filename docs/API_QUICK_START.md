# API Quick Start

Get the latest fiscal projections in 5 minutes using the PoliSim REST API.

## No Setup Required (Try Now)

```bash
# Get list of available scenarios
curl https://polisim.org/api/v1/scenarios?per_page=5
```

*Note: For local development, replace `https://polisim.org` with `http://localhost:5000`*

---

## 1. Get Your API Key (2 minutes)

### Step 1: Register an Account

```bash
curl -X POST https://polisim.org/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@example.com",
    "username": "myusername",
    "password": "securepassword123",
    "organization": "My Research Lab"
  }'
```

**Response:**
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "usr_abc123",
    "email": "you@example.com",
    "username": "myusername",
    "organization": "My Research Lab",
    "created_at": "2026-01-02T10:30:00Z"
  }
}
```

### Step 2: Create API Key

Authenticate with the token from Step 1:

```bash
curl -X POST https://polisim.org/api/auth/api-keys \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My App",
    "rate_limit": 1000
  }'
```

**Response:**
```json
{
  "api_key": {
    "key": "ps_fh9d82ck92hd9k2",
    "name": "My App",
    "rate_limit": 1000,
    "created_at": "2026-01-02T10:35:00Z"
  }
}
```

**⚠️ Important:** Save your API key (`ps_fh9d82ck92hd9k2`)—you won't see it again!

---

## 2. Run Your First Simulation (3 minutes)

### Simple Policy Simulation

```bash
API_KEY="ps_fh9d82ck92hd9k2"

curl -X POST https://polisim.org/api/v1/simulate \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_name": "Medicare for All",
    "years": 10,
    "iterations": 1000,
    "revenue_change_pct": 5.0,
    "spending_change_pct": -2.0
  }'
```

**Response:**
```json
{
  "status": "success",
  "simulation_id": "sim_abc123def456",
  "policy": {
    "name": "Medicare for All",
    "type": "healthcare_reform",
    "parameters": {
      "revenue_change_pct": 5.0,
      "spending_change_pct": -2.0,
      "years": 10
    }
  },
  "results": {
    "baseline_deficit_2030": -1450.5,
    "policy_deficit_2030": -1375.2,
    "deficit_improvement": 75.3,
    "confidence_interval": {
      "p5": 50.1,
      "p50": 75.3,
      "p95": 100.5
    },
    "years_to_surplus": null,
    "coverage_rate": 0.98,
    "cost_per_capita": 8500
  },
  "metadata": {
    "runtime_seconds": 2.34,
    "iterations_completed": 1000,
    "timestamp": "2026-01-02T10:40:00Z"
  }
}
```

### Advanced Policy Simulation

```bash
curl -X POST https://polisim.org/api/v1/simulate \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_name": "Comprehensive Reform",
    "years": 20,
    "iterations": 5000,
    "healthcare": {
      "coverage_target": 0.99,
      "admin_overhead": 0.03,
      "innovation_fund_b": 50
    },
    "tax_policy": {
      "top_marginal_rate": 0.45,
      "corporate_rate": 0.25,
      "capital_gains_rate": 0.28
    },
    "social_security": {
      "payroll_cap": 200000,
      "retirement_age": 67
    }
  }'
```

---

## 3. Use Results in Your Application

### Python Example

```python
import requests
import json

API_KEY = "ps_fh9d82ck92hd9k2"
BASE_URL = "https://polisim.org/api/v1"

def run_simulation(policy_params):
    """Run a policy simulation."""
    response = requests.post(
        f"{BASE_URL}/simulate",
        headers={"X-API-Key": API_KEY},
        json=policy_params
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")

# Example: Carbon tax + healthcare reform
policy = {
    "policy_name": "Carbon Tax + Healthcare Reform",
    "years": 20,
    "iterations": 5000,
    "carbon_tax": 75,
    "healthcare": {
        "coverage_target": 0.95,
        "admin_overhead": 0.05
    }
}

try:
    results = run_simulation(policy)
    
    # Extract key metrics
    deficit_improvement = results['results']['deficit_improvement']
    coverage = results['results']['coverage_rate']
    ci = results['results']['confidence_interval']
    
    print(f"Policy: {results['policy']['name']}")
    print(f"Deficit improvement: ${deficit_improvement:.1f}B")
    print(f"Coverage: {coverage*100:.1f}%")
    print(f"90% CI: ${ci['p5']:.1f}B - ${ci['p95']:.1f}B")
    
except Exception as e:
    print(f"Simulation failed: {e}")
```

### JavaScript Example

```javascript
const API_KEY = 'ps_fh9d82ck92hd9k2';
const BASE_URL = 'https://polisim.org/api/v1';

async function runSimulation(policyParams) {
  const response = await fetch(`${BASE_URL}/simulate`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(policyParams),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }

  return await response.json();
}

// Example usage
const policy = {
  policy_name: 'Progressive Tax Reform',
  years: 15,
  iterations: 3000,
  tax_policy: {
    top_marginal_rate: 0.50,
    capital_gains_rate: 0.30,
  },
};

runSimulation(policy)
  .then(results => {
    console.log(`Deficit change: $${results.results.deficit_improvement}B`);
    console.log(`Confidence: ${results.results.confidence_interval.p5} - ${results.results.confidence_interval.p95}`);
  })
  .catch(err => console.error('Simulation failed:', err));
```

---

## 4. Additional API Endpoints

### List Pre-Built Scenarios

```bash
curl -H "X-API-Key: $API_KEY" \
  "https://polisim.org/api/v1/scenarios?per_page=10"
```

**Response:**
```json
{
  "scenarios": [
    {
      "id": "scenario_001",
      "name": "Progressive Scenario",
      "description": "Higher top tax rates, expanded social programs",
      "category": "comprehensive"
    },
    {
      "id": "scenario_002",
      "name": "Conservative Scenario",
      "description": "Lower taxes, reduced spending growth",
      "category": "comprehensive"
    }
  ],
  "total": 15,
  "page": 1,
  "per_page": 10
}
```

### Get Scenario Details

```bash
curl -H "X-API-Key: $API_KEY" \
  "https://polisim.org/api/v1/scenarios/scenario_001"
```

### Compare Multiple Policies

```bash
curl -X POST https://polisim.org/api/v1/compare \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "policies": [
      {"name": "Baseline", "parameters": {}},
      {"name": "Reform A", "parameters": {"revenue_change_pct": 5}},
      {"name": "Reform B", "parameters": {"spending_change_pct": -3}}
    ],
    "years": 10,
    "iterations": 1000
  }'
```

### Get CBO Baseline Data

```bash
curl -H "X-API-Key: $API_KEY" \
  "https://polisim.org/api/v1/baseline?years=10"
```

**Response:**
```json
{
  "baseline": {
    "years": [2026, 2027, 2028, 2029, 2030, ...],
    "gdp": [28500, 29200, 29950, ...],
    "revenue": [5100, 5350, 5600, ...],
    "spending": [6550, 6800, 7100, ...],
    "deficit": [-1450, -1450, -1500, ...],
    "debt": [28000, 29450, 30950, ...]
  },
  "metadata": {
    "source": "CBO 2024 Budget and Economic Outlook",
    "last_updated": "2025-12-15T00:00:00Z"
  }
}
```

---

## Common Errors & Solutions

| Error | Status | Solution |
|-------|--------|----------|
| `Invalid API key` | 401 | Check key spelling; regenerate if needed |
| `Rate limit exceeded` | 429 | Wait 60 seconds; consider upgrading plan |
| `Invalid parameter` | 400 | Check JSON syntax; see parameter docs |
| `Policy not found` | 404 | Check policy name; list available with `GET /scenarios` |
| `Simulation timeout` | 504 | Reduce iterations or years; try again |
| `Server error` | 500 | Check status page; contact support if persists |

### Example Error Response

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Parameter 'years' must be between 1 and 30",
    "field": "years",
    "value": 50
  },
  "request_id": "req_xyz789"
}
```

---

## Rate Limits

### By Authentication Tier

| Tier | Requests/Minute | Simulations/Minute |
|------|----------------|-------------------|
| Unauthenticated | 100 | N/A |
| Free (Authenticated) | 1,000 | 10 |
| Research/Nonprofit | 10,000 | 100 |
| Enterprise | Custom | Custom |

### Rate Limit Headers

Every response includes:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1704211200
```

### Handling Rate Limits

```python
import time
import requests

def make_request_with_retry(url, headers, data):
    """Make API request with automatic retry on rate limit."""
    max_retries = 3
    
    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 429:
            # Rate limited—wait and retry
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Retrying in {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

---

## Authentication Methods

### Method 1: API Key (Recommended)

```bash
curl -H "X-API-Key: ps_your_key_here" \
  "https://polisim.org/api/v1/simulate"
```

### Method 2: JWT Token

```bash
curl -H "Authorization: Bearer eyJhbGc..." \
  "https://polisim.org/api/v1/simulate"
```

### Method 3: Session Cookie (Dashboard Only)

Used automatically by the Streamlit dashboard. Not recommended for API integration.

---

## Best Practices

### 1. Cache Results
Don't re-run identical simulations—cache results for 24 hours.

```python
import hashlib
import json

def cache_key(params):
    """Generate cache key from parameters."""
    return hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()

# Use Redis, memcached, or simple dict
simulation_cache = {}

def get_or_simulate(params):
    key = cache_key(params)
    if key in simulation_cache:
        return simulation_cache[key]
    
    result = run_simulation(params)
    simulation_cache[key] = result
    return result
```

### 2. Use Batch Requests
Compare multiple policies in one request instead of separate requests.

### 3. Start Small
Test with low iterations (100-1000) before running large simulations (10,000+).

### 4. Monitor Rate Limits
Check `X-RateLimit-Remaining` header and throttle requests accordingly.

### 5. Handle Errors Gracefully
Always wrap API calls in try-catch and implement retry logic.

---

## Next Steps

- **Full API Documentation:** See [API_ENDPOINTS.md](docs/API_ENDPOINTS.md)
- **Authentication Guide:** See [API_AUTHENTICATION.md](documentation/API_AUTHENTICATION.md)
- **Policy Parameters:** See [POLICY_PARAMETERS.md](documentation/POLICY_PARAMETERS.md)
- **Examples:** Browse [examples/](examples/) for more code samples

---

## Need Help?

- **Documentation:** [documentation/](documentation/)
- **GitHub Discussions:** Ask questions and share ideas
- **Email:** galacticorgofdev@gmail.com
- **Issues:** Report bugs on [GitHub Issues](https://github.com/GalacticOrgOfDev/polisim/issues)

---

*Last updated: January 2, 2026*
