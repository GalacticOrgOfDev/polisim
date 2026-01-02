# API Endpoints & Data Ingestion

---

## CBO Data Ingestion Health Endpoint

### Purpose

The `GET /api/data/ingestion-health` endpoint reports the current status of CBO data ingestion, cache usage, and integrity metadata.

- Expose checksum, freshness, and cache age so clients can verify data recency
- Prefer cached data to avoid unnecessary live scrapes
- Fall back to live fetch when no cache exists

### Request

```
GET /api/data/ingestion-health
```

**Authentication:** Not required by default

### Response

```json
{
  "status": "success",
  "data": {
    "data_source": "Cache (cache)",
    "checksum": "abc123def456",
    "cache_used": true,
    "freshness_hours": 5.2,
    "cache_age_hours": 5.2,
    "last_updated": "2025-01-01T00:00:00",
    "fetched_at": "2025-01-01T05:12:00",
    "schema_valid": true,
    "validation_errors": []
  }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `checksum` | string | Hash of the current payload for integrity checking |
| `cache_used` | boolean | `true` when serving cached data; `false` when from live sources |
| `freshness_hours` | number | Age of the data (hours) based on `last_updated` or cache mtime |
| `cache_age_hours` | number | Same as `freshness_hours` when cache used; `0.0` for live responses |
| `data_source` | string | Human-readable provenance (includes `(cache)` suffix when served from cache) |
| `schema_valid` | boolean | `true` when payload contains required keys/types; `false` when issues detected |
| `validation_errors` | array | Schema/range validation issues when `schema_valid` is `false` |

### Operational Behavior

**Cache-First Strategy:**
- If a cache exists, metadata is reported without hitting live endpoints
- If no cache is present, the scraper performs a live fetch and returns live metadata
- Live responses are schema-checked; if validation fails and a cache is available, the API serves the cached payload (marked `cache_used: true`)
- Errors return `status_code` 500 or 503 with an `error` message payload

### Security & Rate Limiting

Authentication and rate limiting can be enabled for this endpoint via environment flags:
- `API_AUTH_REQUIRED` - Enable authentication requirement
- `API_RATE_LIMIT_INGESTION_HEALTH` - Set rate limit (requests/minute)

**Default:** No authentication required; uses global API rate limits

### Example Usage

**Check CBO data freshness:**
```bash
curl -X GET http://localhost:5000/api/data/ingestion-health
```

**Integrated with monitoring:**
```python
import requests

response = requests.get('http://localhost:5000/api/data/ingestion-health')
data = response.json()['data']

if data['schema_valid'] and data['freshness_hours'] < 24:
    print(f"✅ Data is fresh (updated {data['freshness_hours']:.1f} hours ago)")
else:
    print(f"⚠️ Data may be stale or invalid")
```

---

## Related API Endpoints

### Budget Simulation Endpoints

- `POST /api/simulation/run` - Run fiscal impact simulation
- `GET /api/simulation/{id}` - Get simulation results
- `POST /api/scenario` - Create policy scenario
- `GET /api/scenarios` - List available scenarios

### Data Endpoints

- `GET /api/data/fiscal-outlook` - Get CBO fiscal outlook data
- `GET /api/data/validation` - Validate data integrity
- `GET /api/health` - General API health check

### Authentication Endpoints

- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh auth token
- `GET /api/auth/permissions` - Get user permissions

---

## API Configuration

### Environment Variables

```bash
# CBO Data Source
CBO_DATA_CACHE_PATH=./core/cbo_data_cache.json
CBO_DATA_HISTORY_PATH=./core/cbo_data_history.json

# API Server
API_HOST=localhost
API_PORT=5000
API_DEBUG=false

# CORS & Security
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000
API_HTTPS_ONLY=true
API_RATE_LIMIT_GLOBAL=100  # requests/minute per IP

# Authentication
API_AUTH_REQUIRED=false
JWT_SECRET_KEY=change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Response Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful, data returned |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required or invalid |
| 403 | Forbidden | User lacks permission for resource |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error while processing request |
| 503 | Service Unavailable | Service temporarily unavailable (circuit breaker open) |

---

## Data Integrity Verification

### Checksum Validation

The API returns a checksum with each response. Use this to verify data hasn't changed:

```python
import hashlib
import json

def verify_checksum(response_data, reported_checksum):
    """Verify data integrity using checksum."""
    # Hash the actual data payload
    data_bytes = json.dumps(response_data).encode('utf-8')
    computed_checksum = hashlib.sha256(data_bytes).hexdigest()
    
    return computed_checksum == reported_checksum
```

### Schema Validation

If `schema_valid` is `false`, check `validation_errors` for issues:

```python
response = requests.get('/api/data/ingestion-health')
data = response.json()['data']

if not data['schema_valid']:
    for error in data['validation_errors']:
        print(f"Schema error: {error}")
```

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Data Freshness**
   - Alert if `freshness_hours` > 24
   - Alert if `schema_valid` is false

2. **Cache Hit Rate**
   - Track percentage of `cache_used: true` responses
   - Goal: >95% cache hit rate

3. **Request Latency**
   - Monitor endpoint response time
   - Goal: <500ms (cache) or <5s (live fetch)

4. **Error Rate**
   - Track 5xx responses
   - Alert if error rate > 1%

### Example Monitoring Query

```python
# Check data freshness every hour
import schedule

def check_data_freshness():
    response = requests.get('/api/data/ingestion-health')
    if response.status_code == 200:
        data = response.json()['data']
        if data['freshness_hours'] > 24:
            send_alert("CBO data is stale, last updated 24+ hours ago")

schedule.every(1).hours.do(check_data_freshness)
```

