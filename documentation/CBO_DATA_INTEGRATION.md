# CBO Data Integration - Real-Time Updates

**Phase 5.2: Enhanced Data Integration with Reliability & Validation**

This guide covers the real-time data integration system for fetching, validating, and tracking US fiscal data from official government sources.

---

## Overview

The CBO Data Integration system provides:

- **Real-time data fetching** from CBO, Treasury, and OMB
- **Retry logic** with exponential backoff (3 attempts)
- **Data validation** against expected ranges
- **Historical tracking** (365 days of data updates)
- **Change detection** for significant fiscal shifts
- **Cache fallback** for offline reliability
- **Scheduled updates** via automation script
- **Manual refresh API** for on-demand updates (admin only)

---

## Data Sources

### Primary Sources

1. **Congressional Budget Office (CBO)**
   - URL: `https://www.cbo.gov/publications/collections/economic-projections`
   - Data: GDP projections, revenue estimates, spending forecasts

2. **U.S. Treasury Department**
   - URL: `https://fiscal.treasury.gov/reports-statements/financial-report/`
   - Data: National debt figures, interest rates

3. **Office of Management and Budget (OMB)**
   - URL: `https://www.whitehouse.gov/omb/historical-tables/`
   - Data: Historical budget data, multi-year trends

### Fallback Strategy

```
Primary Source → Retry (3x with backoff) → Validation → Cache Fallback
```

---

## Features

### 1. Retry Logic with Exponential Backoff

**Configuration:**
```python
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RETRY_BACKOFF = 2  # multiplier
```

**Behavior:**
- **Attempt 1**: Immediate request
- **Attempt 2**: Wait 2 seconds → retry
- **Attempt 3**: Wait 4 seconds → retry
- **Failure**: Fall back to cache

**No Retry On:**
- 404 Not Found
- 403 Forbidden
- 401 Unauthorized

### 2. Data Validation

**Validation Ranges:**

| Metric | Min | Max | Unit |
|--------|-----|-----|------|
| GDP | 20.0 | 50.0 | Trillions |
| National Debt | 20.0 | 60.0 | Trillions |
| Deficit | -5.0 | 5.0 | Trillions |
| Total Revenue | 3.0 | 8.0 | Trillions |
| Total Spending | 4.0 | 10.0 | Trillions |
| Interest Rate | 0.5 | 10.0 | Percent |

**Validation Process:**
1. Fetch data from sources
2. Check all metrics against ranges
3. Log validation errors
4. Fall back to cache if validation fails

### 3. Historical Data Tracking

**Storage:**
- File: `core/cbo_data_history.json`
- Retention: Last 365 days
- Format:
```json
[
  {
    "timestamp": "2025-12-26T10:30:00",
    "data": {
      "gdp": 30.5,
      "debt": 35.2,
      "deficit": 1.8
    },
    "hash": "a1b2c3d4e5f6"
  }
]
```

### 4. Change Detection

**Thresholds:**
- **GDP Change**: > 5% (e.g., 30.0T → 31.5T)
- **Debt Change**: > $1T (e.g., 35.0T → 36.1T)
- **Deficit Change**: > $500B (e.g., 1.5T → 2.1T)

**Notifications:**
```
⚠️  SIGNIFICANT CHANGES DETECTED:
  • GDP changed +10.0%
  • National debt changed +2.1T
  • Deficit changed -0.7T
```

---

## Usage

### Python API

```python
from core.cbo_scraper import CBODataScraper

# Create scraper
scraper = CBODataScraper(
    use_cache=True,  # Fall back to cache on error
    enable_notifications=True  # Log change notifications
)

# Fetch latest data
data = scraper.get_current_us_budget_data()

# Access data
print(f"GDP: ${data['gdp']:.2f}T")
print(f"National Debt: ${data['debt']:.2f}T")
print(f"Deficit: ${data['deficit']:.2f}T")
print(f"Last Updated: {data['last_updated']}")

# View historical data
history = scraper.history[-10:]  # Last 10 updates
for entry in history:
    print(f"{entry['timestamp']}: GDP=${entry['data']['gdp']:.2f}T")
```

### REST API Endpoints

#### 1. Manual Refresh (Admin Only)

```bash
# Refresh CBO data from live sources
curl -X POST http://localhost:5000/api/data/refresh \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "status": "success",
  "message": "Data refreshed successfully",
  "data": {
    "gdp": 30.5,
    "national_debt": 35.2,
    "deficit": 1.8,
    "total_revenue": 4.5,
    "total_spending": 6.3,
    "interest_rate": 4.2,
    "last_updated": "2025-12-26T10:30:00",
    "data_source": "CBO/Treasury/OMB"
  }
}
```

#### 2. View Historical Data

```bash
# Get last 30 data updates
curl -X GET "http://localhost:5000/api/data/history?limit=30" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "count": 30,
  "history": [
    {
      "timestamp": "2025-12-26T10:30:00",
      "hash": "a1b2c3d4e5f6",
      "gdp": 30.5,
      "debt": 35.2,
      "deficit": 1.8
    }
  ]
}
```

---

## Scheduled Updates

### Automation Script

**File:** `scripts/scheduled_cbo_update.py`

**What it does:**
1. Fetches latest CBO/Treasury/OMB data
2. Validates data against expected ranges
3. Detects significant changes
4. Logs results to `logs/cbo_updates.log`
5. Saves data to cache and history

**Manual Execution:**
```bash
python scripts/scheduled_cbo_update.py
```

**Output:**
```
============================================================
Starting scheduled CBO data update
============================================================
Fetching latest CBO/Treasury/OMB data...
------------------------------------------------------------
Data Update Summary:
  GDP: $30.50T
  National Debt: $35.20T
  Total Revenue: $4.50T
  Total Spending: $6.30T
  Deficit: $1.80T
  Interest Rate: 4.20%
  Last Updated: 2025-12-26T10:30:00
  Data Source: CBO/Treasury/OMB
------------------------------------------------------------
✓ No significant changes detected
============================================================
Scheduled update completed successfully
============================================================
```

### Windows Task Scheduler Setup

1. **Open Task Scheduler** (Windows Key → "Task Scheduler")

2. **Create New Task:**
   - Name: `PoliSim CBO Data Update`
   - Description: `Daily update of CBO fiscal data`

3. **Triggers:**
   - Daily at 6:00 AM
   - Recurrence: Every day
   - Start: Today

4. **Actions:**
   - Action: `Start a program`
   - Program: `python.exe` (full path: `C:\Users\YourUser\AppData\Local\Programs\Python\Python313\python.exe`)
   - Arguments: `"E:\AI Projects\polisim\scripts\scheduled_cbo_update.py"`
   - Start in: `E:\AI Projects\polisim`

5. **Conditions:**
   - Wake computer to run task: ✓
   - Start only if on AC power: (optional)

6. **Settings:**
   - Allow task to run on demand: ✓
   - Run task as soon as possible after missed schedule: ✓
   - Stop task if it runs longer than: 1 hour

### Linux/Mac Cron Setup

Add to crontab (`crontab -e`):

```cron
# Run daily at 6:00 AM
0 6 * * * cd /path/to/polisim && python scripts/scheduled_cbo_update.py >> logs/cron_output.log 2>&1
```

---

## Testing

### Run Tests

```bash
# Run all CBO integration tests
python -m pytest tests/test_cbo_integration.py -v

# Run specific test class
python -m pytest tests/test_cbo_integration.py::TestRetryLogic -v

# Run with coverage
python -m pytest tests/test_cbo_integration.py --cov=core.cbo_scraper --cov-report=html
```

### Test Coverage

- **Retry Logic**: 5 tests (timeouts, connection errors, HTTP errors, success after failures)
- **Data Validation**: 4 tests (valid data, invalid GDP/debt/revenue)
- **Historical Tracking**: 3 tests (save entries, retention, hash generation)
- **Change Detection**: 4 tests (GDP/debt/deficit changes, no changes)
- **Cache Fallback**: 2 tests (network failure, validation failure)

**Total: 18 tests, 100% passing**

---

## Troubleshooting

### Network Errors

**Problem:** `Failed to fetch data after 3 attempts`

**Solution:**
1. Check internet connection
2. Verify CBO/Treasury websites are accessible
3. Check firewall/proxy settings
4. Review logs for specific error messages
5. System will automatically fall back to cache

### Validation Errors

**Problem:** `Data validation failed: GDP 100.0T outside range [20-50]T`

**Solution:**
1. Check if CBO website structure changed
2. Review web scraping logic in `_get_gdp_data()`
3. Update validation ranges if fiscal reality changed
4. System will automatically use cached data

### Cache Corruption

**Problem:** `Could not load cache: JSON decode error`

**Solution:**
```bash
# Delete corrupted cache
rm core/cbo_data_cache.json

# Re-fetch data
python scripts/scheduled_cbo_update.py
```

### Historical Data Too Large

**Problem:** `cbo_data_history.json` growing too large

**Solution:**
- System automatically keeps only last 365 days
- Manual cleanup:
```python
from core.cbo_scraper import CBODataScraper

scraper = CBODataScraper()
# History is auto-pruned on next save
scraper._save_history_entry({'gdp': 30.0, 'debt': 35.0})
```

---

## Architecture

### Class Structure

```
CBODataScraper
├── __init__(use_cache, enable_notifications)
├── Public Methods
│   ├── get_current_us_budget_data() → Dict
│   └── get_current_us_parameters() → Dict (simulation format)
├── Data Fetching (with retry)
│   ├── _get_gdp_data() → float
│   ├── _get_revenue_data() → Dict
│   ├── _get_spending_data() → Dict
│   ├── _get_national_debt() → float
│   └── _get_interest_rate() → float
├── Phase 5.2 Enhancements
│   ├── _request_with_retry(url, description) → Response
│   ├── _validate_data(data) → (bool, List[str])
│   ├── _detect_changes(new_data) → List[str]
│   ├── _hash_data(data) → str
│   └── _save_history_entry(data) → None
└── Cache Management
    ├── _load_cache() → Dict
    ├── _save_cache(data) → None
    └── _load_history() → List[Dict]
```

### Data Flow

```
┌─────────────────┐
│ User/Scheduler  │
└────────┬────────┘
         │
         v
┌─────────────────────┐
│ get_current_us_     │
│  budget_data()      │
└────────┬────────────┘
         │
         ├─────> _get_gdp_data() ───┬──> _request_with_retry()
         ├─────> _get_revenue_data()│          │
         ├─────> _get_spending_data()│         v
         ├─────> _get_national_debt()  CBO/Treasury/OMB
         └─────> _get_interest_rate()         │
                                               │
                       ┌───────────────────────┘
                       v
               ┌───────────────┐
               │ Data Fetched  │
               └───────┬───────┘
                       │
                       v
               ┌─────────────────┐
               │ _validate_data()│
               └───────┬─────────┘
                       │
               ┌───────┴────────┐
               │ Valid?         │
               └───┬────────────┬┘
                   │ Yes        │ No
                   v            v
           ┌──────────┐   ┌──────────┐
           │ Continue │   │ Use Cache│
           └────┬─────┘   └──────────┘
                │
                v
         ┌─────────────────┐
         │ _detect_changes()│
         └────────┬─────────┘
                  │
                  v
         ┌──────────────────┐
         │_save_history_entry│
         └────────┬──────────┘
                  │
                  v
         ┌─────────────┐
         │_save_cache()│
         └─────────────┘
```

---

## Configuration

### Validation Ranges

Edit `CBODataScraper.VALIDATION_RANGES`:

```python
VALIDATION_RANGES = {
    'gdp': (20.0, 50.0),  # Adjust as economy grows
    'debt': (20.0, 60.0),
    'deficit': (-5.0, 5.0),
    'interest_rate': (0.5, 10.0),
    'total_revenue': (3.0, 8.0),
    'total_spending': (4.0, 10.0),
}
```

### Retry Configuration

Edit class constants:

```python
MAX_RETRIES = 3  # Number of retry attempts
RETRY_DELAY = 2  # Initial delay (seconds)
RETRY_BACKOFF = 2  # Exponential multiplier
```

### Change Detection Thresholds

Edit `_detect_changes()` method:

```python
# GDP threshold: 5% change
if abs(new_gdp - old_gdp) / old_gdp > 0.05:
    changes.append(...)

# Debt threshold: $1T change
if abs(new_debt - old_debt) > 1.0:
    changes.append(...)

# Deficit threshold: $500B change
if abs(new_deficit - old_deficit) > 0.5:
    changes.append(...)
```

---

## Files Modified/Created

### Modified
- `core/cbo_scraper.py` (+200 lines)
  - Added retry logic with exponential backoff
  - Added data validation
  - Added historical tracking
  - Added change detection

- `api/rest_server.py` (+95 lines)
  - Added `/api/data/refresh` endpoint (admin only)
  - Added `/api/data/history` endpoint

### Created
- `scripts/scheduled_cbo_update.py` (96 lines)
  - Automated daily data refresh script
  
- `tests/test_cbo_integration.py` (462 lines)
  - 18 comprehensive integration tests
  
- `documentation/CBO_DATA_INTEGRATION.md` (This file)

---

## Next Steps

### Sprint 5.3: Deployment Infrastructure
- Docker containerization
- PostgreSQL database setup
- Redis caching layer
- Nginx reverse proxy
- SSL/TLS certificates
- CI/CD pipeline

### Future Enhancements
- Multi-source data fusion (aggregate CBO + Treasury + OMB)
- Machine learning predictions for missing data
- Real-time WebSocket updates
- Email notifications for significant changes
- Data quality scoring
- API rate limiting per user

---

## Support

**Issues:** Report in GitHub issues
**Documentation:** `documentation/` directory
**Tests:** `tests/test_cbo_integration.py`
**Logs:** `logs/cbo_updates.log`

---

**Last Updated:** December 26, 2025
**Phase:** 5.2 - Real-Time Data Integration
**Status:** ✅ Complete
