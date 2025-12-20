# PoliSim REST API Documentation

## Overview

The PoliSim REST API provides HTTP endpoints for:
- Policy simulation and analysis
- Monte Carlo uncertainty quantification
- Fiscal impact calculations
- Scenario comparisons
- Report generation
- Real-time policy recommendations

## Running the Server

```python
from api import run_api_server

# Start API server on localhost:5000
run_api_server(host='127.0.0.1', port=5000, debug=False)
```

Or from command line:
```bash
python -m api.rest_server
```

## Using the Python Client

```python
from api import PoliSimAPIClient

client = PoliSimAPIClient("http://localhost:5000")

# Check API health
health = client.health_check()
print(health['status'])  # 'healthy'

# Simulate a policy
result = client.simulate_policy(
    revenue_change_pct=5,
    spending_change_pct=-3,
    policy_name="Tax Reform",
    iterations=10000
)
print(f"Mean Deficit: ${result['mean_deficit']:,.0f}B")

# Get recommendations
recommendations = client.recommend_policies(fiscal_goal="minimize_deficit")
for rec in recommendations['recommendations']:
    print(f"{rec['policy']}: {rec['overall_score']:.1f}")
```

## API Endpoints

### Health & Status

#### GET `/api/health`
Check API server health.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0",
  "timestamp": "2025-12-20T10:30:00"
}
```

---

### Policy Information

#### GET `/api/policies`
List all available policy templates.

**Response:**
```json
{
  "status": "success",
  "count": 3,
  "policies": [
    {
      "name": "Healthcare Reform",
      "type": "healthcare",
      "parameters": 6
    },
    {
      "name": "Tax Reform",
      "type": "tax",
      "parameters": 6
    }
  ]
}
```

#### GET `/api/policies/{policy_type}`
Get detailed policy template information.

**Parameters:**
- `policy_type` (path): Policy type (e.g., "healthcare", "tax", "spending")

**Response:**
```json
{
  "status": "success",
  "name": "Healthcare Reform",
  "type": "healthcare",
  "description": "Healthcare policy parameters",
  "parameters": [
    {
      "name": "Coverage Expansion",
      "type": "percentage",
      "default": 0,
      "unit": "%"
    }
  ]
}
```

---

### Simulation & Analysis

#### POST `/api/simulate/policy`
Run Monte Carlo policy simulation with confidence bounds.

**Request Body:**
```json
{
  "policy_name": "Tax Reform 2025",
  "revenue_change_pct": 5,
  "spending_change_pct": -3,
  "years": 10,
  "iterations": 10000
}
```

**Response:**
```json
{
  "status": "success",
  "policy_name": "Tax Reform 2025",
  "iterations": 10000,
  "mean_deficit": 845.5,
  "median_deficit": 823.1,
  "std_dev": 125.3,
  "p10_deficit": 625.8,
  "p90_deficit": 1065.2,
  "probability_balanced": 8.5,
  "confidence_bounds": [625.8, 1065.2]
}
```

**Parameters:**
- `policy_name` (string): Name of policy scenario
- `revenue_change_pct` (float): Expected revenue change as percentage
- `spending_change_pct` (float): Expected spending change as percentage
- `years` (int, optional): Projection horizon (default: 10)
- `iterations` (int, optional): Monte Carlo iterations (default: 5000)

---

#### POST `/api/analyze/sensitivity`
Run sensitivity analysis on policy parameters (tornado chart).

**Request Body:**
```json
{
  "base_revenue": 5980,
  "base_spending": 6911,
  "parameter_ranges": {
    "Revenue": [-10, 20],
    "Spending": [-30, 10]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "analysis": "sensitivity",
  "parameters": [
    {
      "Parameter": "Revenue",
      "Total Range": 2980,
      "Elasticity": 0.5
    },
    {
      "Parameter": "Spending",
      "Total Range": 2075,
      "Elasticity": 0.3
    }
  ]
}
```

---

#### POST `/api/analyze/stress`
Run stress test with predefined adverse scenarios.

**Request Body:**
```json
{
  "revenue_change_pct": 5,
  "spending_change_pct": -3
}
```

**Response:**
```json
{
  "status": "success",
  "analysis": "stress_test",
  "scenarios": [
    {
      "Stress Scenario": "Recession",
      "Baseline Deficit": 925.0,
      "Stressed Deficit": 1450.0,
      "Impact": 525.0,
      "% Change": 56.8
    },
    {
      "Stress Scenario": "Inflation",
      "Baseline Deficit": 925.0,
      "Stressed Deficit": 1200.0,
      "Impact": 275.0,
      "% Change": 29.7
    }
  ]
}
```

**Stress Scenarios:**
- Recession: -10% revenue, +5% spending
- Inflation: GDP growth reduction, interest rate increase
- Demographic Shock: Beneficiary surge
- Market Correction: General deficit pressures
- Perfect Storm: Combined worst-case

---

### Recommendations & Impact

#### POST `/api/recommend/policies`
Get policy recommendations based on fiscal goals.

**Request Body:**
```json
{
  "fiscal_goal": "minimize_deficit",
  "limit": 5
}
```

**Response:**
```json
{
  "status": "success",
  "fiscal_goal": "minimize_deficit",
  "recommendations": [
    {
      "policy": "Balanced Budget Package",
      "overall_score": 87.5,
      "fiscal_impact": 92.0,
      "sustainability": 85.0,
      "feasibility": 78.0,
      "equity": 82.0,
      "growth": 75.0
    }
  ]
}
```

**Fiscal Goals:**
- `minimize_deficit`: Reduce annual deficit
- `maximize_revenue`: Increase federal revenue
- `balance_budget`: Achieve balanced budget
- `sustainable_debt`: Control debt-to-GDP ratio
- `growth_focused`: Maximize economic growth
- `equity_focused`: Prioritize distributional equity

---

#### POST `/api/calculate/impact`
Calculate detailed fiscal impact of policy.

**Request Body:**
```json
{
  "policy_name": "Tax Reform",
  "revenue_change_pct": 5,
  "spending_change_pct": -3,
  "years": 10
}
```

**Response:**
```json
{
  "status": "success",
  "policy": "Tax Reform",
  "projections": [
    {
      "Year": 2025,
      "Revenue": 6050.0,
      "Spending": 6881.0,
      "Deficit": 831.0
    },
    {
      "Year": 2026,
      "Revenue": 6100.0,
      "Spending": 6851.0,
      "Deficit": 751.0
    }
  ],
  "total_deficit": 7850.0,
  "avg_deficit": 785.0
}
```

---

### Data Access

#### GET `/api/data/baseline`
Get current baseline fiscal data.

**Response:**
```json
{
  "status": "success",
  "revenue": 5980.0,
  "spending": 6911.0,
  "deficit": 931.0,
  "gdp": 29360.0,
  "deficit_pct_gdp": 3.17
}
```

#### GET `/api/data/historical`
Get historical fiscal data for trend analysis.

**Response:**
```json
{
  "status": "success",
  "historical": [
    {
      "Year": 2015,
      "Revenue": 3300.0,
      "Spending": 3800.0,
      "Deficit": 500.0
    }
  ]
}
```

---

### Report Generation

#### POST `/api/report/generate`
Generate fiscal policy report.

**Request Body:**
```json
{
  "title": "2025 Tax Reform Analysis",
  "author": "Fiscal Analysis Team",
  "description": "Analysis of proposed tax reform package",
  "summary": "This report examines..."
}
```

**Response:**
```json
{
  "status": "success",
  "report": "reports/api_generated/report_20251220_103000.json",
  "format": "json",
  "timestamp": "20251220_103000"
}
```

---

### Scenario Analysis

#### POST `/api/scenarios/compare`
Compare multiple policy scenarios.

**Request Body:**
```json
{
  "scenarios": [
    {
      "name": "Status Quo",
      "revenue_change_pct": 0,
      "spending_change_pct": 0,
      "years": 10
    },
    {
      "name": "Tax Reform",
      "revenue_change_pct": 5,
      "spending_change_pct": 0,
      "years": 10
    },
    {
      "name": "Spending Cut",
      "revenue_change_pct": 0,
      "spending_change_pct": -3,
      "years": 10
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "scenario_count": 3,
  "scenarios": [
    {
      "scenario": "Status Quo",
      "10_year_deficit": 9250.0,
      "avg_deficit": 925.0,
      "final_year_deficit": 950.0
    },
    {
      "scenario": "Tax Reform",
      "10_year_deficit": 8750.0,
      "avg_deficit": 875.0,
      "final_year_deficit": 800.0
    },
    {
      "scenario": "Spending Cut",
      "10_year_deficit": 8500.0,
      "avg_deficit": 850.0,
      "final_year_deficit": 700.0
    }
  ]
}
```

---

## Error Handling

All errors return a standard error response:

```json
{
  "error": "Description of the error",
  "status": "error"
}
```

Common HTTP Status Codes:
- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## CORS

The API server has CORS enabled for all routes, allowing requests from any origin.

---

## Examples

### Python Client Example

```python
from api import PoliSimAPIClient
import pandas as pd

client = PoliSimAPIClient("http://localhost:5000")

# Get baseline data
baseline = client.get_baseline_data()
print(f"Current deficit: ${baseline['deficit']:,.0f}B")

# Simulate multiple policies
policies = [
    ("No Change", 0, 0),
    ("Tax Reform", 5, 0),
    ("Spending Control", 0, -3),
    ("Balanced", 5, -3),
]

results = []
for name, rev, spend in policies:
    result = client.simulate_policy(rev, spend, name, iterations=5000)
    results.append({
        'Policy': name,
        'Mean Deficit': result['mean_deficit'],
        'Best Case (P10)': result['p10_deficit'],
        'Worst Case (P90)': result['p90_deficit'],
        'Prob. Balanced': result['probability_balanced'],
    })

df = pd.DataFrame(results)
print(df.to_string())
```

### cURL Example

```bash
# Health check
curl http://localhost:5000/api/health

# List policies
curl http://localhost:5000/api/policies

# Simulate policy
curl -X POST http://localhost:5000/api/simulate/policy \
  -H "Content-Type: application/json" \
  -d '{
    "policy_name": "Tax Reform",
    "revenue_change_pct": 5,
    "spending_change_pct": -3,
    "iterations": 10000
  }'

# Get recommendations
curl -X POST http://localhost:5000/api/recommend/policies \
  -H "Content-Type: application/json" \
  -d '{
    "fiscal_goal": "minimize_deficit",
    "limit": 5
  }'
```

---

## Rate Limiting

Currently no rate limiting is enforced. Implement rate limiting in production environments.

---

## Authentication

Currently no authentication is required. Add authentication (API keys, JWT) in production.

---

## Version History

- **v1.0** (2025-12-20): Initial release
  - Policy simulation endpoints
  - Monte Carlo analysis
  - Recommendations
  - Report generation
  - Scenario comparison
