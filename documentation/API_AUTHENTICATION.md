# API Authentication Documentation

**Version:** 1.0  
**Last Updated:** December 26, 2025  
**Phase:** 5, Sprint 5.1

---

## Overview

The POLISIM REST API now supports JWT-based authentication with API key support for programmatic access. This enables secure user accounts, rate limiting, and usage tracking.

## Authentication Methods

### 1. JWT Tokens (Web/Mobile Apps)
- Bearer token authentication
- 24-hour expiration
- Includes user ID, email, and role
- Suitable for web/mobile applications

### 2. API Keys (Scripts/Automation)
- Long-lived tokens for programmatic access
- Prefix: `ps_` followed by secure random string
- Configurable rate limits per key
- Suitable for scripts, CI/CD, automation

---

## Getting Started

### 1. Register New Account

```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "myusername",
  "password": "securepassword123",
  "full_name": "John Doe",
  "organization": "Research Institute"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "myusername",
    "role": "user",
    ...
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 2. Login

```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "user": {...},
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 3. Using JWT Token

Include token in `Authorization` header:

```bash
GET /api/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## API Keys

### Create API Key

```bash
POST /api/auth/api-keys
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "name": "My Script Key",
  "rate_limit": 1000
}
```

**Response:**
```json
{
  "status": "success",
  "message": "API key created successfully",
  "api_key": {
    "id": 1,
    "name": "My Script Key",
    "key": "ps_Ab3d...xyz",
    "rate_limit": 1000,
    ...
  },
  "warning": "Save this key now. You won't be able to see it again."
}
```

### Using API Key

Include key in `X-API-Key` header:

```bash
GET /api/policies
X-API-Key: ps_Ab3d...xyz
```

### List Your API Keys

```bash
GET /api/auth/api-keys
Authorization: Bearer <your_jwt_token>
```

---

## Protected Endpoints

The following endpoints now require authentication:

- `/api/auth/me` - Get current user profile
- `/api/auth/api-keys` - Manage API keys
- (More endpoints will be protected in future sprints)

---

## Rate Limiting

- **Default rate limit:** 1,000 requests per hour
- **Custom limits:** Configurable per API key
- **Rate limit headers:** Included in responses (coming soon)
- **429 error:** Returned when rate limit exceeded

---

## User Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| `user` | Standard user | Basic API access, create scenarios |
| `researcher` | Academic/research user | Higher rate limits, advanced features |
| `admin` | Administrator | Full access, user management |

---

## Security Best Practices

### For Developers

1. **Never hardcode tokens**
   ```python
   # ❌ BAD
   token = "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
   
   # ✅ GOOD
   token = os.environ.get('POLISIM_API_TOKEN')
   ```

2. **Use environment variables**
   ```bash
   export POLISIM_API_TOKEN="your_token_here"
   ```

3. **Set JWT_SECRET_KEY in production**
   ```bash
   export JWT_SECRET_KEY="your-secure-random-secret-key-here"
   ```

4. **Rotate API keys regularly**
   - Delete old keys after creating new ones
   - Use separate keys for different applications

5. **Handle token expiration**
   ```python
   if response.status_code == 401:
       # Token expired, re-authenticate
       login_response = requests.post('/api/auth/login', ...)
       new_token = login_response.json()['token']
   ```

---

## Code Examples

### Python

```python
import requests
import os

BASE_URL = "http://localhost:5000"

# 1. Register
response = requests.post(f"{BASE_URL}/api/auth/register", json={
    "email": "user@example.com",
    "username": "myuser",
    "password": "securepass123"
})
token = response.json()['token']

# 2. Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
print(response.json())

# 3. Create API key
response = requests.post(
    f"{BASE_URL}/api/auth/api-keys",
    headers=headers,
    json={"name": "My Script Key"}
)
api_key = response.json()['api_key']['key']

# 4. Use API key
headers = {"X-API-Key": api_key}
response = requests.get(f"{BASE_URL}/api/policies", headers=headers)
```

### cURL

```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"myuser","password":"pass123"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}'

# Use token
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Use API key
curl http://localhost:5000/api/policies \
  -H "X-API-Key: ps_Ab3d...xyz"
```

---

## Error Codes

| Code | Error | Description |
|------|-------|-------------|
| 400 | Bad Request | Missing or invalid fields |
| 401 | Unauthorized | Invalid or expired token |
| 403 | Forbidden | Account disabled or insufficient permissions |
| 409 | Conflict | Email or username already exists |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error (check logs) |

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    organization VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    updated_at DATETIME,
    last_login DATETIME
);
```

### API Keys Table
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255),
    prefix VARCHAR(8),
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit INTEGER DEFAULT 1000,
    created_at DATETIME,
    last_used DATETIME,
    expires_at DATETIME
);
```

### Usage Logs Table
```sql
CREATE TABLE usage_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms FLOAT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp DATETIME
);
```

---

## Testing

Run authentication tests:
```bash
pytest tests/test_api_authentication.py -v
```

**Test Coverage:**
- ✅ JWT token creation and validation
- ✅ User registration
- ✅ User login
- ✅ Protected endpoint access
- ✅ API key creation and usage
- ✅ Rate limiting
- ✅ Error handling

**Results:** 23/23 tests passing (100%)

---

## Future Enhancements (Sprint 5.2+)

- [ ] Email verification for new accounts
- [ ] Password reset via email
- [ ] OAuth integration (GitHub, Google)
- [ ] Two-factor authentication (2FA)
- [ ] Session management
- [ ] IP whitelisting for API keys
- [ ] Detailed usage analytics dashboard
- [ ] Webhook notifications for rate limit warnings
- [ ] Admin panel for user management

---

## Support

- **Documentation:** https://github.com/GalacticOrgOfDev/polisim/docs
- **Issues:** https://github.com/GalacticOrgOfDev/polisim/issues
- **Discord:** Coming soon
- **Email:** support@polisim.org (if applicable)

---

**Implementation Complete:** December 26, 2025  
**Phase 5 Sprint 5.1:** ✅ API Authentication COMPLETE
