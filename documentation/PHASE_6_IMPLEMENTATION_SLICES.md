# Phase 6 Implementation Slices - Detailed Breakdown

**Document Purpose:** Concrete implementation tasks with time estimates and acceptance criteria  
**Date Created:** January 1, 2026  
**Total Estimated Effort:** 170-270 hours

---

## SLICE 6.1: INDEPENDENT VALIDATION (Weeks 1-4)

### Overview
Bring in external experts to validate the simulation engine, assumptions, and projections against official government baselines.

---

### 6.1.1: Expert Panel Recruitment (Parallel Activity, Week 1)

**Owner:** Project Lead  
**Duration:** 1-2 weeks (runs in parallel)  
**Effort:** 8-16 hours

#### Tasks

1. **Identify Expert Candidates**
   - [ ] 1-2 CBO economists
   - [ ] 1 SSA actuary
   - [ ] 1-2 healthcare policy researchers (academic or think tank)
   - [ ] 1 fiscal policy expert
   - Research sources: NBER, Brookings, AEI, Urban Institute, Harvard, Stanford

2. **Reach Out & Propose Engagement**
   - [ ] Prepare 1-page project summary
   - [ ] Define scope: 4-6 weeks, ~40 hours per expert
   - [ ] Offer: Acknowledgment in paper, cite their validation, co-authorship opportunity
   - [ ] Target: 3-5 commitments minimum

3. **Create Expert Charter**
   - [ ] Define review scope
   - [ ] Set expectations (timeline, deliverables, confidentiality)
   - [ ] Establish communication cadence (weekly calls)
   - [ ] Provide data access (GitHub repo, API sandbox)

#### Acceptance Criteria
- [ ] 3-5 experts confirmed and onboarded
- [ ] Charter document signed
- [ ] Kickoff call scheduled
- [ ] Experts have access to codebase & API

---

### 6.1.2: Assumption Validation (Weeks 1-3)

**Owner:** Lead Developer + Experts  
**Duration:** 3 weeks  
**Effort:** 60-80 hours (20-25 dev hours + 40-50 expert hours)

#### Task 1: Document All Assumptions

**Dev Time:** 4 hours

- [ ] Create `ASSUMPTIONS.md` (comprehensive list)
  - Healthcare cost elasticity: -0.2 to -0.5
  - Behavioral tax responses: wage elasticity 0.1-0.3
  - Social Security COLA: 2-3% annual
  - Medicare spending growth: 2-3% above GDP
  - Administrative overhead: 5-15% (varies by system)
  - Life expectancy improvement: 0.2 years/year
  - Inflation baseline: 2.5% annual
  - GDP growth baseline: 2.2% annual
  - Interest rate baseline: 4.5%
  - Population growth: 0.7% annual
- [ ] Document source for each assumption
- [ ] List confidence level (high/medium/low)
- [ ] Note parameters that can be adjusted

#### Task 2: Expert Review Meetings

**Dev Time:** 6 hours (attending calls)

- [ ] Week 1, Day 3: Healthcare assumptions (expert panel)
  - Review elasticities, overhead, innovation fund impact
  - Discuss evidence from literature
  - Document expert feedback
  
- [ ] Week 2, Day 1: Revenue & tax assumptions
  - Behavioral responses to tax changes
  - Evidence from NBER, IRS studies
  - Compare to CBO assumptions
  
- [ ] Week 2, Day 4: Mandatory spending assumptions
  - Social Security trust fund depletion
  - Medicare spending growth rates
  - Demographic assumptions
  
- [ ] Week 3, Day 2: Economic assumptions
  - GDP growth, interest rates, inflation
  - Recession scenarios
  - Compare to Fed baseline

#### Task 3: Create Validation Memos

**Dev Time:** 8 hours

For each assumption category, create 2-3 page memo:
- [ ] Healthcare Assumptions Memo
  - Assumption statement
  - Evidence (academic studies, CBO documents)
  - Expert commentary
  - Confidence level
  - Sensitivity impact
  
- [ ] Revenue Assumptions Memo
  - Tax elasticities documented
  - Behavioral responses
  - Historical evidence
  - CBO comparison
  
- [ ] Social Security Assumptions Memo
  - Trust fund depletion dates
  - COLA assumptions
  - Benefit level assumptions
  - SSA reconciliation
  
- [ ] Economic Assumptions Memo
  - GDP growth, inflation, interest rates
  - Recession probability & severity
  - Long-term trends

#### Task 4: Expert Sign-Off

**Dev Time:** 2 hours

- [ ] Collect expert reviews of memos
- [ ] Incorporate feedback
- [ ] Final sign-off on assumptions
- [ ] Document any remaining disagreements

#### Acceptance Criteria
- [ ] `ASSUMPTIONS.md` complete & reviewed
- [ ] 4 validation memos created & signed off
- [ ] Expert feedback incorporated
- [ ] Confidence levels assigned to all assumptions
- [ ] Discrepancies with CBO/SSA documented

---

### 6.1.3: Baseline Reconciliation (Weeks 2-4)

**Owner:** Lead Developer + Experts  
**Duration:** 3 weeks  
**Effort:** 40-50 hours (25 dev + 25 expert)

#### Task 1: Create Reconciliation Notebook

**Dev Time:** 6 hours

Jupyter notebook that:
- [ ] Projects 10-year baseline (current policy)
- [ ] Compares to CBO 2024 Outlook
- [ ] Shows variance by metric:
  - GDP growth: target ±1%
  - Revenue: target ±2%
  - Spending: target ±3%
  - Deficit: target ±2%
  - Debt: target ±3%
- [ ] Identifies sources of variance
- [ ] Documents assumptions differences

#### Task 2: Benchmark Against Official Baselines

**Dev Time:** 8 hours

- [ ] Compare projections to CBO 2024 Budget and Economic Outlook
  - 10-year GDP projections
  - Revenue by category (IIT, payroll, corporate)
  - Spending categories
  - Interest payments
  - Deficit trajectory
  - Debt held by public

- [ ] Compare to SSA 2024 Trustees Report
  - OASI trust fund depletion date
  - Payroll tax revenue
  - Benefit payments
  - DI fund status

- [ ] Compare to CMS Medicare/Medicaid reports
  - Enrollment projections
  - Per-capita spending growth
  - Trust fund status

#### Task 3: Variance Analysis

**Dev Time:** 8 hours

For each variance > 2%:
- [ ] Document the difference
- [ ] Identify assumption differences (our vs. CBO)
- [ ] Determine if difference is explainable
- [ ] Decide: accept difference or adjust model

Example analysis:
```
Metric: Individual Income Tax 2030
PoliSim: $3,120B
CBO:     $3,100B
Variance: +0.6% ✅ ACCEPTABLE

Reason: PoliSim uses slightly higher wage growth assumption (2.3% vs. 2.1%)
Decision: ACCEPT - wage growth within reasonable range
```

#### Task 4: Expert Reconciliation Review

**Dev Time:** 4 hours (calls)

- [ ] Present variance analysis to experts
- [ ] Get consensus on acceptable variance ranges
- [ ] Document expert rationale
- [ ] Final sign-off on reconciliation

#### Acceptance Criteria
- [ ] Reconciliation notebook published
- [ ] All variances > 2% documented & explained
- [ ] Expert consensus on acceptable variance ranges
- [ ] Final reconciliation memo signed
- [ ] Variance analysis added to documentation

---

### 6.1.4: Cross-Model Validation (Week 3)

**Owner:** Developer (with expert input)  
**Duration:** 1 week  
**Effort:** 15-20 hours

#### Task 1: Linkage Verification

**Dev Time:** 8 hours

Validate that model components interact correctly:
- [ ] Healthcare spending linked to economic growth
  - Verify: higher GDP → higher healthcare spending
  - Check elasticity: ~0.8-1.2x GDP growth
  
- [ ] Social Security taxes linked to revenue model
  - Verify: payroll tax revenues appear in both SS & general revenue
  - Check: no double-counting
  
- [ ] Medicare linked to healthcare spending
  - Verify: Medicare growth rates consistent with overall healthcare
  - Check: enrollment projections realistic
  
- [ ] Interest costs linked to debt trajectory
  - Verify: larger debt → larger interest payments
  - Check: interest rate assumptions reasonable

#### Task 2: Consistency Checks

**Dev Time:** 6 hours

Create test suite (10+ tests):
- [ ] Test: Total revenue = IIT + Payroll + Corporate + Other
- [ ] Test: Total spending = Mandatory + Discretionary + Interest
- [ ] Test: Deficit = Spending - Revenue
- [ ] Test: Debt(year) = Debt(year-1) + Deficit(year)
- [ ] Test: Healthcare system solvency (revenues ≥ spending)
- [ ] Test: Social Security solvency (over projection period)
- [ ] Test: No negative values in financial metrics

#### Task 3: Edge Case Validation

**Dev Time:** 4 hours

Test extreme scenarios:
- [ ] Recession scenario: -2% GDP growth for 2 years
- [ ] Inflation scenario: 5% annual inflation
- [ ] Interest rate shock: rates rise to 7%
- [ ] Demographic shock: immigration halts

#### Acceptance Criteria
- [ ] All model linkages verified
- [ ] 10+ consistency tests passing
- [ ] Edge case scenarios documented
- [ ] No circular dependencies detected
- [ ] Expert review completed

---

### 6.1.5: Sensitivity Analysis Review (Week 4)

**Owner:** Developer + Expert (1 expert)  
**Duration:** 1 week  
**Effort:** 15-20 hours

#### Task 1: Update Sensitivity Documentation

**Dev Time:** 6 hours

Create `SENSITIVITY_ANALYSIS.md`:
- [ ] List top 10 model drivers:
  - GDP growth assumption (3-5% impact on debt)
  - Healthcare cost growth (2-4% impact)
  - Wage growth (1-3% impact on revenues)
  - Interest rates (2-4% impact on debt service)
  - Population growth (1-2% impact)
  - Tax elasticities (1-3% impact)
  - COLA assumptions (1-2% impact on SS)
  - Inflation (2-3% impact across economy)
  - Life expectancy (1-2% impact on SS)
  - Employment rate (1-2% impact on revenues)

- [ ] For each driver, document:
  - Base case value
  - Plausible range (low/high scenario)
  - Impact on key metrics (debt, deficit, coverage)
  - Evidence/source for range

#### Task 2: Expert Sensitivity Review

**Dev Time:** 6 hours (calls)

- [ ] Present sensitivity results to expert
- [ ] Get critique on magnitude & ranges
- [ ] Identify missing sensitivities
- [ ] Discuss policy interaction effects
- [ ] Document expert recommendations

#### Task 3: Add New Sensitivities (if expert suggests)

**Dev Time:** 8 hours (optional)

Examples of interactions to explore:
- [ ] Healthcare cost + Life expectancy interaction
- [ ] Tax elasticity + Wage growth interaction
- [ ] Interest rates + Debt accumulation feedback loop
- [ ] Demographic changes + Multiple program impacts

#### Acceptance Criteria
- [ ] Sensitivity analysis documented
- [ ] Top 10 drivers identified & ranked
- [ ] Ranges validated against literature
- [ ] Expert review completed
- [ ] Missing sensitivities identified for Phase 7

---

### 6.1.6: Publication-Ready Write-Up (Week 4)

**Owner:** Developer + Expert (lead expert)  
**Duration:** 1 week  
**Effort:** 20-25 hours

#### Task 1: Draft Technical Methodology Paper

**Dev Time:** 8 hours

Structure:
1. **Abstract** (½ page)
   - What problem we're solving
   - Key innovation
   - Key findings

2. **Introduction** (1 page)
   - Why transparent fiscal modeling matters
   - Limitations of current models
   - Our approach

3. **Methodology** (5-8 pages)
   - Healthcare simulation (2 pages)
   - Revenue modeling (2 pages)
   - Mandatory spending (Social Security, Medicare)
   - Economic linkages
   - Monte Carlo approach

4. **Assumptions** (3-4 pages)
   - Key assumptions summarized
   - Evidence for each
   - Sensitivity to assumptions

5. **Results** (3-4 pages)
   - Baseline projections
   - Policy scenarios
   - Comparison to official baselines

6. **Limitations** (1-2 pages)
   - What we can't model
   - Data quality issues
   - Methodological constraints

7. **Appendix** (5-10 pages)
   - Detailed equations
   - Data sources
   - Full assumption list

#### Task 2: Expert Review & Revision

**Dev Time:** 8 hours

- [ ] Lead expert reviews draft
- [ ] Incorporate major feedback
- [ ] Add expert co-authorship (if agreed)
- [ ] Final review cycle
- [ ] Sign-off

#### Task 3: Prepare PDF + HTML Versions

**Dev Time:** 4 hours

- [ ] Create PDF with proper formatting
- [ ] Create HTML version for web
- [ ] Add citations & references
- [ ] Create executive summary (2 pages)

#### Acceptance Criteria
- [ ] Technical paper complete (15-20 pages)
- [ ] Expert co-signed
- [ ] Published on GitHub & website
- [ ] Executive summary available
- [ ] Press release ready

---

### 6.1 COMPLETION CRITERIA

**Time Estimate:** 4-6 weeks (with 3-5 part-time experts)  
**Developer Effort:** 50-60 hours  
**Expert Effort:** 120-150 hours  
**Success Metrics:**

- [ ] 3-5 experts onboarded & active
- [ ] All assumptions validated & signed off
- [ ] Baseline reconciliation: ±2-5% accuracy confirmed
- [ ] All variances > 2% documented & explained
- [ ] 10+ consistency tests passing
- [ ] Sensitivity analysis complete
- [ ] Technical paper published (15-20 pages)
- [ ] Expert sign-off memo obtained
- [ ] Zero expert concerns on accuracy or methodology

---

## SLICE 6.2: SECURITY HARDENING (Weeks 1-3)

### Overview
Implement production-grade security controls: secrets management, HTTPS, DDoS protection, etc.

---

### 6.2.1: Dependency Audit (Week 1)

**Owner:** Developer  
**Duration:** 2-3 hours  
**Effort:** 2-3 hours

#### Tasks

1. **Run Security Scanners**
   ```bash
   # Install scanners
   pip install pip-audit safety bandit
   
   # Audit dependencies
   pip-audit --desc                    # Show descriptions of vulnerabilities
   safety check --json                 # Check dependencies
   bandit -r . -f json > bandit.json  # Scan code
   ```

2. **Review Results**
   - [ ] Document all high/critical vulnerabilities
   - [ ] Check current version vs. vulnerable version
   - [ ] Assess impact (if vulnerable, exploitable?)

3. **Update Vulnerable Packages**
   - [ ] Update all high-priority vulnerabilities
   - [ ] Run full test suite after each update
   - [ ] Document changes in CHANGELOG

4. **Lock Safe Versions**
   - [ ] Pin all package versions
   - [ ] Document pinning decision
   - [ ] Set up monthly dependency update check

#### Example Output
```
bandit scan results:
✅ No SQL injection risks (using SQLAlchemy)
✅ No XSS risks (Streamlit auto-escapes)
✅ No hardcoded secrets (using environment variables)
⚠️  JWT secret in .env (acceptable, needs rotation)
```

#### Acceptance Criteria
- [ ] pip-audit: Zero high/critical vulnerabilities
- [ ] safety check: Passed
- [ ] bandit: No critical code issues
- [ ] All updates tested
- [ ] Dependency lock file committed

---

### 6.2.2: API Security Hardening (Week 2)

**Owner:** Developer  
**Duration:** 8-10 hours

#### Task 1: CORS Policy Enforcement

**Time:** 1 hour

Current state: `CORS(app)` enables all origins

Change to:
```python
# api/rest_server.py
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:8501",      # Local development
            "https://polisim.org",         # Production
            "https://www.polisim.org",     # Production alt
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["X-RateLimit-Remaining"],
        "max_age": 3600,
    }
})
```

- [ ] Update allowed origins to explicit list
- [ ] Test CORS enforcement
- [ ] Document origin configuration

#### Task 2: Rate Limit Hardening

**Time:** 2-3 hours

Current: Basic rate limiting exists

Add:
- [ ] Bruteforce protection on login (5 attempts/15 min per IP)
- [ ] DDoS detection (>100 requests/sec from single IP)
- [ ] Per-endpoint limits (simulation: 10/min, read: 100/min)
- [ ] Progressive backoff (2x multiplier, max 1 hour)

```python
# Example: Login endpoint rate limiting
@app.route('/api/auth/login', methods=['POST'])
@require_rate_limit(5, 'minute', per_ip=True)  # 5 per minute per IP
def login():
    # On 5th failed attempt, lock out for 15 minutes
    pass
```

#### Task 3: Input Validation & Sanitization

**Time:** 2 hours

- [ ] Verify Pydantic validation on all endpoints
- [ ] Add HTML/script tag filtering (if user input)
- [ ] Add command injection protection (PDF processing)
- [ ] Test with malicious inputs:
  - SQL injection: `'; DROP TABLE users; --`
  - XSS: `<script>alert('xss')</script>`
  - Path traversal: `../../../../etc/passwd`
  - Large inputs: 1GB JSON payload

#### Task 4: Request/Response Security Headers

**Time:** 2 hours

Add headers to all responses:
```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

- [ ] Implement headers
- [ ] Test with security scanner
- [ ] Document headers

#### Task 5: Add Security Tests

**Time:** 1 hour

Add tests in `tests/test_api_security.py`:
- [ ] Test CORS enforcement (✓ allowed origins, ✗ disallowed)
- [ ] Test rate limiting (exceed limit → 429)
- [ ] Test invalid tokens (401)
- [ ] Test SQL injection attempts (400 or 403)
- [ ] Test XSS payloads (escaped or rejected)

#### Acceptance Criteria
- [ ] CORS whitelist implemented & tested
- [ ] Rate limiting: bruteforce protection active
- [ ] Per-endpoint limits: enforced
- [ ] Input validation: all payloads sanitized
- [ ] Security headers: all implemented
- [ ] Security tests: 10+ tests passing
- [ ] No OWASP Top 10 vulnerabilities

---

### 6.2.3: Secrets Management (Week 2)

**Owner:** Developer  
**Duration:** 4-6 hours

#### Task 1: Identify All Secrets

**Time:** 1 hour

Audit codebase for secrets:
```bash
grep -r "secret\|password\|key\|token" . --include="*.py" | grep -v test | grep -v ".pyc"
```

Current secrets to migrate:
- [ ] JWT_SECRET_KEY (currently in .env)
- [ ] POSTGRES_PASSWORD (currently in docker-compose.yml)
- [ ] REDIS_PASSWORD (currently in docker-compose.yml)
- [ ] FLASK_SECRET_KEY (if used)
- [ ] API_KEYS (user-created, stored in database)

#### Task 2: Implement AWS Secrets Manager (Recommended for Production)

**Time:** 2-3 hours

Option A: AWS Secrets Manager (best for production)
```python
# core/secrets.py
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        raise Exception(f"Error retrieving secret: {e}")

# Usage:
jwt_secret = get_secret('polisim/jwt')['secret_key']
```

Setup:
- [ ] Create AWS Secrets Manager secrets
- [ ] Create IAM role for EC2/Lambda
- [ ] Update API to read from Secrets Manager
- [ ] Remove secrets from code/env files

Option B: HashiCorp Vault (if available)
Option C: Environment variables only (development)

#### Task 3: Implement Secret Rotation

**Time:** 1-2 hours

For JWT_SECRET_KEY:
- [ ] Rotate every 90 days
- [ ] Support multiple active keys (old + new)
- [ ] Use new key for token generation
- [ ] Accept both for validation (grace period)

```python
# Rotate JWT secret every 90 days
JWT_SECRETS = {
    'current': get_secret('polisim/jwt/current'),
    'previous': get_secret('polisim/jwt/previous'),  # Still valid for 7 days
}

def create_jwt_token(user_id, email, role):
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.now(UTC) + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRETS['current'], algorithm='HS256')

def decode_jwt_token(token):
    try:
        return jwt.decode(token, JWT_SECRETS['current'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        # Try previous key (grace period)
        return jwt.decode(token, JWT_SECRETS['previous'], algorithms=['HS256'])
```

#### Task 4: Audit Logging for Secrets

**Time:** 1 hour

Log all secret access:
- [ ] Who accessed the secret
- [ ] When it was accessed
- [ ] What was accessed
- [ ] Alert on unusual access patterns

```python
# Log all auth attempts
logger.info(f"Login attempt: user={email}, ip={request.remote_addr}")
logger.warning(f"Failed login: user={email}, attempts=3, ip={request.remote_addr}")
logger.info(f"API key created: key=ps_***, user={user_id}, rate_limit={limit}")
```

#### Acceptance Criteria
- [ ] All secrets migrated to Secrets Manager
- [ ] No hardcoded secrets in code
- [ ] .env files removed from repo
- [ ] Rotation policy implemented
- [ ] Audit logging active
- [ ] Zero secrets visible in logs

---

### 6.2.4: HTTPS/SSL Implementation (Week 2)

**Owner:** DevOps/Developer  
**Duration:** 4-6 hours

#### Task 1: Procure SSL Certificate

**Time:** 1 hour

Option A: Let's Encrypt (free, recommended)
- [ ] Install Certbot
- [ ] Generate certificate for polisim.org
- [ ] Set up auto-renewal (via systemd timer)

Option B: AWS Certificate Manager (if using AWS)
- [ ] Request certificate
- [ ] Validate domain ownership
- [ ] Deploy to Application Load Balancer

Option C: Commercial CA (if required for compliance)

#### Task 2: Configure Nginx Reverse Proxy

**Time:** 2-3 hours

Create `deployment/nginx.conf`:
```nginx
upstream api {
    server localhost:5000;
}

upstream dashboard {
    server localhost:8501;
}

server {
    listen 80;
    server_name polisim.org www.polisim.org;
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name polisim.org www.polisim.org;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/polisim.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/polisim.org/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # API proxy
    location /api {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Dashboard proxy
    location / {
        proxy_pass http://dashboard;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

- [ ] Create nginx.conf
- [ ] Test syntax (`nginx -t`)
- [ ] Deploy in docker-compose.yml
- [ ] Test HTTP→HTTPS redirect
- [ ] Verify SSL certificate validity

#### Task 3: Update Docker Compose

**Time:** 1-2 hours

Add Nginx service:
```yaml
nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - api
      - dashboard
    networks:
      - polisim-network
```

- [ ] Add Nginx service
- [ ] Mount SSL certificates
- [ ] Update API/Dashboard to internal ports
- [ ] Test with `docker-compose up`

#### Task 4: Certificate Auto-Renewal

**Time:** 1 hour

```bash
# Certbot auto-renewal
certbot renew --dry-run  # Test renewal

# Or with systemd timer (Linux)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

- [ ] Configure auto-renewal
- [ ] Test renewal process
- [ ] Verify certificate expiration alerts

#### Acceptance Criteria
- [ ] SSL certificate issued & valid
- [ ] HTTP redirects to HTTPS
- [ ] HTTPS connection secure (A rating from SSL Labs)
- [ ] Certificate auto-renews
- [ ] No security warnings in browser
- [ ] All API calls over HTTPS
- [ ] HSTS headers present

---

### 6.2.5: DDoS & Abuse Prevention (Week 3)

**Owner:** Developer  
**Duration:** 4-6 hours

#### Task 1: CloudFlare Setup (Recommended)

**Time:** 1-2 hours

- [ ] Create CloudFlare account
- [ ] Point DNS to CloudFlare nameservers
- [ ] Enable DDoS protection (automatic)
- [ ] Configure WAF rules:
  - [ ] Block SQL injection patterns
  - [ ] Block XSS patterns
  - [ ] Block rate limit abuse
  - [ ] Allow legitimate traffic

CloudFlare automatically:
- Absorbs DDoS attacks (up to petabyte-scale)
- Caches static assets (faster delivery)
- Provides CDN (global edge locations)

Cost: $20/month (Pro plan) - includes DDoS protection

Alternative: AWS Shield Standard (free, basic) + Shield Advanced ($3,000/month)

#### Task 2: API-Level Rate Limiting (Advanced)

**Time:** 2-3 hours

Detect and block abuse:
```python
# api/rate_limiter.py
from datetime import datetime, timedelta
import redis

class RateLimiter:
    def __init__(self, redis_url):
        self.redis = redis.from_url(redis_url)
    
    def check_limit(self, key, limit, window):
        """Check if request allowed."""
        count = self.redis.incr(key)
        if count == 1:
            self.redis.expire(key, window)
        
        if count > limit:
            remaining_ttl = self.redis.ttl(key)
            raise RateLimitError(
                f"Rate limit exceeded. Retry in {remaining_ttl}s"
            )
        return True
    
    def block_ip(self, ip_address, duration=3600):
        """Temporarily block IP."""
        self.redis.setex(f"blocked:{ip_address}", duration, "1")

# Usage:
@app.route('/api/v1/simulate', methods=['POST'])
def simulate():
    ip = request.remote_addr
    
    # Check if IP is blocked
    if limiter.redis.get(f"blocked:{ip}"):
        return {"error": "IP blocked due to abuse"}, 429
    
    # Check rate limit
    limiter.check_limit(f"api:simulate:{ip}", limit=10, window=60)
    
    # Process request
    ...
```

Implementation:
- [ ] Implement advanced rate limiter class
- [ ] Connect to Redis
- [ ] Add IP blocking capability
- [ ] Add progressive backoff (exponential)
- [ ] Test with stress test tool

#### Task 3: Request Validation & Filtering

**Time:** 1-2 hours

Prevent common attacks:
- [ ] File upload size validation (10MB max for PDFs)
- [ ] Request timeout (30 seconds for long-running sims)
- [ ] Connection limit (1000 concurrent)
- [ ] Request header validation (strip suspicious headers)

```python
# api/v1_middleware.py
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
REQUEST_TIMEOUT = 30  # seconds
MAX_CONNECTIONS = 1000

@app.before_request
def validate_request():
    # Check content length
    if request.content_length > MAX_CONTENT_LENGTH:
        return {"error": "Payload too large"}, 413
    
    # Check for malicious headers
    suspicious_headers = [
        'X-Forwarded-For', 'X-Forwarded-Proto', 'X-Forwarded-Host'
    ]
    for header in suspicious_headers:
        if header in request.headers:
            # These are OK if coming from Nginx, but strip if direct
            pass
```

#### Task 4: Monitoring & Alerting for Abuse

**Time:** 1 hour

- [ ] Alert on >100 requests/sec from single IP
- [ ] Alert on >100 failed login attempts per hour
- [ ] Alert on >50 API errors in 5 minutes
- [ ] Set up Slack/email notifications
- [ ] Create runbook for incident response

#### Acceptance Criteria
- [ ] CloudFlare DDoS protection active
- [ ] Advanced rate limiting implemented
- [ ] IP blocking functional
- [ ] Request validation hardened
- [ ] Monitoring & alerting configured
- [ ] Zero abuse incidents in 2-week test period

---

### 6.2.6: Security Documentation (Week 3)

**Owner:** Developer  
**Duration:** 4-6 hours

#### Task 1: Create SECURITY.md

**Time:** 2 hours

```markdown
# Security & Vulnerability Reporting

## Reporting a Vulnerability

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, email: galacticorgofdev@gmail.com

**Please provide:**
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

## Response Timeline

- **24 hours:** Initial acknowledgment
- **48 hours:** Assessment complete
- **5 days:** Fix deployed to staging
- **7 days:** Fix deployed to production
- **30 days:** Public disclosure

## Security Best Practices

### For Users
- Keep API keys secure (don't commit to version control)
- Use HTTPS only (enforce at network level)
- Enable 2FA if available
- Report suspicious activity

### For Developers
- Don't commit secrets to version control
- Use environment variables for configuration
- Rotate secrets regularly (90-day policy)
- Follow OWASP Top 10 guidelines
- Run security scans (bandit, safety)

## Known Issues & Mitigations

None currently. Report via security@polisim.org.

## Acknowledgments

We appreciate responsible disclosure from security researchers.
```

#### Task 2: Create Security Policy

**Time:** 2-3 hours

Document:
- [ ] Password policy (min 12 chars, complexity)
- [ ] Session timeout (30 min inactivity)
- [ ] API key rotation (90-day policy)
- [ ] Data retention (30-90 days)
- [ ] Incident response process
- [ ] Security audit schedule (quarterly)

#### Task 3: Add Security Tests

**Time:** 1 hour

Add to `tests/test_security.py`:
```python
def test_sql_injection_protection():
    """Verify SQL injection payloads are rejected."""
    payload = "'; DROP TABLE users; --"
    response = client.post('/api/auth/login', json={
        'email': payload,
        'password': 'test'
    })
    assert response.status_code in [400, 401, 404]

def test_xss_protection():
    """Verify XSS payloads are escaped."""
    payload = "<script>alert('xss')</script>"
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'username': payload,
        'password': 'password123'
    })
    assert response.status_code in [400, 422]

def test_rate_limit_enforcement():
    """Verify rate limits block abusive clients."""
    for i in range(11):  # 10 limit + 1
        response = client.post('/api/auth/login', json={
            'email': f'user{i}@test.com',
            'password': 'test'
        })
    
    # 11th request should be rate limited
    assert response.status_code == 429
```

#### Acceptance Criteria
- [ ] SECURITY.md published
- [ ] Security policy documented
- [ ] Incident response plan written
- [ ] Security tests: 10+ passing
- [ ] No OWASP Top 10 vulnerabilities
- [ ] All team members trained

---

### 6.2 COMPLETION CRITERIA

**Time Estimate:** 2-3 weeks (20-30 dev hours)  
**Success Metrics:**

- [ ] Zero high/critical vulnerabilities (pip-audit)
- [ ] CORS whitelist enforced
- [ ] Rate limiting: bruteforce protection active
- [ ] All secrets in Secrets Manager
- [ ] HTTPS enforced (HTTP→HTTPS redirect)
- [ ] SSL certificate valid (A+ from SSL Labs)
- [ ] DDoS protection active (CloudFlare or AWS Shield)
- [ ] WAF rules configured (SQL injection, XSS blocked)
- [ ] Security tests: 20+ passing
- [ ] SECURITY.md published
- [ ] Zero security incidents in 2-week test period

---

## SLICE 6.3: PUBLIC DOCUMENTATION (Weeks 1-2)

### Overview
Create community-facing documentation needed for public launch.

---

### 6.3.1: CONTRIBUTING.md 

**File:** `CONTRIBUTING.md` 

```markdown
# Contributing to PoliSim

We welcome contributions! This guide explains how to report bugs, suggest features, 
and submit code changes.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/polisim.git
   cd polisim
   ```
3. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```
5. **Run tests to verify setup:**
   ```bash
   python -m pytest tests/ -v
   ```

## Reporting Bugs

### Before Reporting
- Check existing issues (might already be reported)
- Check closed issues (might be fixed in main branch)

### How to Report

Create an issue using the **Bug Report** template:
```
Title: [BUG] Brief description of issue

## Description
What's the problem? What did you expect to happen?

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen?

## Actual Behavior
What actually happened?

## Environment
- OS: (Windows/macOS/Linux)
- Python version: (e.g., 3.11)
- PoliSim version: (e.g., main branch)

## Error Messages
(Paste full traceback if applicable)
```

## Suggesting Features

Create an issue using the **Feature Request** template:
```
Title: [FEATURE] Brief description of feature

## Description
What feature would help you?

## Use Case
Why do you need this? What problem does it solve?

## Proposed Solution
How would this feature work?

## Alternatives Considered
Any other ways to solve this?
```

## Code Style Guidelines

We follow PEP 8 with these conventions:

### 1. Type Hints (Required)
```python
# ✅ Good
def simulate(
    policy: HealthcarePolicyModel,
    years: int = 22,
) -> pd.DataFrame:
    pass

# ❌ Bad
def simulate(policy, years=22):
    pass
```

### 2. Docstrings (Required)
```python
def calculate_coverage(
    spending: float,
    population: int,
) -> float:
    """
    Calculate healthcare coverage percentage.
    
    Args:
        spending: Total healthcare spending (billions)
        population: Total population
        
    Returns:
        Coverage percentage (0-1)
    """
```

### 3. Naming Conventions
- Functions & variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### 4. Testing (Required)
- Write test for every new function
- Use descriptive test names: `test_calculate_coverage_valid_inputs()`
- Aim for 80%+ code coverage

```python
def test_calculate_coverage_returns_percentage():
    """Verify coverage is returned as percentage."""
    coverage = calculate_coverage(spending=100, population=1000)
    assert 0 <= coverage <= 1
```

### 5. Linting
```bash
# Format code
black src/

# Check style
pylint src/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

## Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Write code + tests
- Ensure tests pass: `pytest tests/ -v`
- Ensure code style: `black . && pylint .`

### 3. Commit with Descriptive Message
```
Format: [TYPE] Brief summary (max 50 chars)

[TYPE] can be: FEATURE, FIX, DOCS, REFACTOR, TEST, PERF

Examples:
✅ [FEATURE] Add sensitivity analysis endpoint
✅ [FIX] Resolve division by zero in healthcare simulation
✅ [DOCS] Update CBO data integration guide
✅ [TEST] Add validation tests for edge cases
```

### 4. Push & Create Pull Request
```bash
git push origin feature/your-feature-name
```

Then create a PR on GitHub with this template:
```
## Description
What does this PR do?

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
How was this tested?
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guide
- [ ] Type hints added
- [ ] Tests written
- [ ] Documentation updated
- [ ] No breaking changes
```

## Code Review Expectations

- **Response Time:** Within 48 hours
- **Feedback:** Constructive, specific, respectful
- **Approval:** At least 1 maintainer approval required
- **Changes:** Push additional commits to same branch (don't force push)

## Commit Checklist

Before submitting a PR, ensure:
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Code formatted: `black .`
- [ ] Type hints complete: `mypy .`
- [ ] Docstrings present
- [ ] No secrets committed
- [ ] Documentation updated
- [ ] Changelog updated

## Questions?

- Check docs: [documentation/](documentation/)
- Ask on GitHub Discussions
- Email: hello@polisim.org
```

---

### 6.3.2: SECURITY.md (2 hours)

[Already created in Slice 6.2 - Security Hardening]

---

### 6.3.3: FAQ.md (6 hours)

**File:** `FAQ.md` (4-5 KB)

Create 20+ Q&A addressing common questions:

**Accuracy & Validation**
- Q: How accurate are your projections?
  A: Baseline validated to ±2-5% vs CBO, expert-reviewed assumptions, Monte Carlo confidence intervals provided

- Q: How do you compare to CBO/SSA models?
  A: [Reconciliation document], similar methodology, differences documented

- Q: Can I use this to make policy decisions?
  A: Designed for analysis & education; always consult official CBO/SSA for decisions

**Data & Methodology**
- Q: Where does the data come from?
  A: CBO, SSA, Treasury, OMB—all official government sources

- Q: How fresh is the data?
  A: Updated via automated scraper; freshness indicator shown on dashboard

- Q: Can I change the assumptions?
  A: Yes—custom policy builder lets you modify 50+ parameters

- Q: What assumptions are baked in?
  A: See [ASSUMPTIONS.md](documentation/ASSUMPTIONS.md)

**API & Integration**
- Q: How do I access the API?
  A: See [API_QUICK_START.md](documentation/API_QUICK_START.md)

- Q: What are the rate limits?
  A: 1000/min authenticated, 100/min unauthenticated; higher for research/nonprofit use

- Q: Can I use PoliSim in my application?
  A: Yes—MIT license, free for any use; API access available

- Q: Is there an SDK?
  A: Python SDK available; JavaScript/other languages welcome as community contributions

**Privacy & Data**
- Q: Is my data stored? For how long?
  A: Minimal data stored (email, usage patterns); deleted after 30 days

- Q: Can I delete my account?
  A: Yes—request via settings or email; all data deleted within 7 days

- Q: Is this GDPR compliant?
  A: Yes—privacy policy published, data deletion supported

- Q: Can I use PoliSim for commercial purposes?
  A: Yes—MIT license permits commercial use

**License & Contributing**
- Q: What's the license?
  A: MIT—free for any use, including commercial

- Q: Can I contribute?
  A: Yes! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

- Q: Can I fork & modify?
  A: Yes—MIT license allows this; we'd love to hear about your modifications

- Q: How do I report security issues?
  A: See [SECURITY.md](SECURITY.md)—don't create public issues

**Troubleshooting**
- Q: The API is returning an error. What do I do?
  A: Check error message (descriptive), see [API_QUICK_START.md](documentation/API_QUICK_START.md) for common errors

- Q: My simulation is taking too long. How do I speed it up?
  A: Reduce iterations (100 instead of 10K), reduce years (10 instead of 30), or use pre-built scenarios

- Q: I found an inaccuracy. What should I do?
  A: Report via GitHub Issues—include scenario, expected value, actual value

---

### 6.3.4: API_QUICK_START.md (4 hours)

**File:** `API_QUICK_START.md` (3-4 KB)

"Run your first API call in 5 minutes"

```markdown
# API Quick Start

Get the latest fiscal projections in 5 minutes using the PoliSim REST API.

## No Setup Required (Try Now)

```bash
# Get list of available scenarios
curl https://polisim.org/api/v1/scenarios?per_page=5
```

## 1. Get Your API Key (2 minutes)

```bash
# Step 1: Register account
curl -X POST https://polisim.org/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@example.com",
    "username": "myusername",
    "password": "securepassword123",
    "organization": "My Research Lab"
  }'

# Response:
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {...}
}

# Step 2: Create API Key (authenticate with token from above)
curl -X POST https://polisim.org/api/auth/api-keys \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My App",
    "rate_limit": 1000
  }'

# Response:
{
  "api_key": {
    "key": "ps_fh9d82ck92hd9k2",  # ← SAVE THIS
    "rate_limit": 1000
  }
}
```

## 2. Run Your First Simulation (3 minutes)

```bash
# Simple policy simulation
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

# Response:
{
  "status": "success",
  "simulation_id": "sim_abc123...",
  "policy": {
    "name": "Medicare for All",
    "type": "healthcare_reform",
    "parameters": {...}
  },
  "results": {
    "baseline_deficit_2030": -1450.5,
    "policy_deficit_2030": -1375.2,
    "deficit_improvement": 75.3,
    "confidence_interval": {
      "p5": 50.1,
      "p95": 100.5
    },
    "years_to_surplus": null,
    "coverage_rate": 0.98,
    "cost_per_capita": 8500
  },
  "metadata": {
    "runtime_seconds": 2.34,
    "iterations_completed": 1000
  }
}
```

## 3. Use Results in Your Application

```python
import requests
import json

API_KEY = "ps_fh9d82ck92hd9k2"
BASE_URL = "https://polisim.org/api/v1"

# Run simulation
response = requests.post(
    f"{BASE_URL}/simulate",
    headers={"X-API-Key": API_KEY},
    json={
        "policy_name": "Carbon Tax + Healthcare Reform",
        "years": 20,
        "iterations": 5000,
        "carbon_tax": 75,
        "healthcare_coverage": 0.95
    }
)

if response.status_code == 200:
    results = response.json()
    deficit_improvement = results['results']['deficit_improvement']
    coverage = results['results']['coverage_rate']
    confidence = results['results']['confidence_interval']
    
    print(f"Deficit improvement: ${deficit_improvement}B")
    print(f"Coverage: {coverage*100:.1f}%")
    print(f"90% CI: ${confidence['p5']}B - ${confidence['p95']}B")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

## Common Errors & Solutions

| Error | Status | Solution |
|-------|--------|----------|
| `Invalid API key` | 401 | Check key spelling; regenerate if needed |
| `Rate limit exceeded` | 429 | Wait 60 seconds; consider upgrading plan |
| `Invalid parameter` | 400 | Check JSON syntax; see parameter docs |
| `Policy not found` | 404 | Check policy name; list available with `GET /scenarios` |

## Next Steps

- See [API_AUTHENTICATION.md](API_AUTHENTICATION.md) for advanced auth
- See [documentation/](documentation/) for full endpoint reference
- Ask questions on GitHub Discussions
```

---

### 6.3.5: GLOSSARY.md (4 hours)

**File:** `GLOSSARY.md` (4-5 KB)

Define 100+ terms:

```markdown
# PoliSim Glossary

## Economic Terms

**GDP Growth**
Percentage increase in Gross Domestic Product per year. Baseline assumption: 2.2%.
[Learn more: CBO projections](https://www.cbo.gov/)

**Deficit**
Annual federal spending exceeds revenue. Negative value = surplus.
Formula: Deficit = Spending - Revenue

**Debt**
Cumulative government borrowing. Grows when deficit > 0.
Formula: Debt(year) = Debt(year-1) + Deficit(year)

**Interest Rate**
Percentage paid on national debt. Baseline assumption: 4.5%.
Higher debt → higher interest rates (economic feedback).

## Tax Terms

**Tax Elasticity**
How much tax revenue changes when tax rate increases.
Example: Wage elasticity 0.2 means 1% tax increase → 0.2% wage decrease

**Marginal Tax Rate**
Tax rate on the last dollar earned. Progressive system has rates:
- 10% on first $11K
- 12% on $11K-$45K
- 22% on $45K-$95K
- [... and higher brackets]

**Capital Gains Tax**
Tax on investment profits. Long-term (>1 year): 15-20%. Short-term (<1 year): ordinary income rates.

## Healthcare Terms

**Healthcare Spending**
Total medical expenses: hospitals, physicians, drugs, insurance.
Current US: 18% of GDP ($5.2T). PoliSim goal: 9% ($2.6T).

**Coverage Rate**
Percentage of population with health insurance.
Current: 93%. PoliSim target: 99%.

**Administrative Overhead**
Costs for insurance processing, profit, marketing.
Current US: 16%. PoliSim target: 3%.

## Statistical Terms

**Monte Carlo**
Run simulation 1,000+ times with random variations to understand uncertainty.
Returns probability distribution (not just point estimate).

**Confidence Interval**
Range where true value likely falls. 90% CI = 90% probability true value is in range.
Example: Deficit 2030 = $1,400B [90% CI: $1,200B - $1,600B]

**Standard Deviation**
Measure of variability. Higher = more uncertain.

## Policy Terms

**Policy Lever**
Parameter you can adjust to model a policy change.
Example: Healthcare levers = coverage, admin overhead, innovation fund, etc.

**Scenario**
Combination of policy levers + parameters representing a specific policy proposal.
Example: "Progressive Scenario" = higher top tax rate + lower Medicare age + etc.

[... and 80+ more terms]
```

---

### 6.3.6: Updates to README.md (2 hours)

**Update existing README with:**

1. Add "Phase 6 Status" section
2. Add link to CONTRIBUTING.md
3. Add link to SECURITY.md  
4. Add community section
5. Add FAQ link
6. Update test badge: "603/603 tests passing"

---

### 6.3 COMPLETION CRITERIA

**Time Estimate:** 1-2 weeks (20-24 dev hours)  
**Success Metrics:**

- [ ] CONTRIBUTING.md complete & reviewed
- [ ] SECURITY.md published
- [ ] CODE_OF_CONDUCT.md published
- [ ] FAQ.md complete (20+ Q&A)
- [ ] API_QUICK_START.md complete (cURL + Python examples)
- [ ] GLOSSARY.md complete (100+ terms)
- [ ] DATA_DICTIONARY.md complete
- [ ] README.md updated with links
- [ ] All docs spell-checked
- [ ] Community review completed

---

## REMAINING SLICES (Planned)

### 6.4: Community Infrastructure (Weeks 2-3)
- GitHub issue/PR templates
- Discussion board setup
- Code of conduct enforcement
- First 10 community contributions received

### 6.5: Validation Tests (Weeks 1-4)
- 25 baseline reconciliation tests
- 30 expert scenario tests
- 20 regression tests
- 10 load tests
- Total: ~85 new validation tests

### 6.6: Educational Materials (Weeks 3-5)
**📄 Detailed Plan:** [PHASE_6_6_EDUCATIONAL_MATERIALS_PLAN.md](PHASE_6_6_EDUCATIONAL_MATERIALS_PLAN.md)

**6.6.1: Jupyter Notebooks (20-25 hours)**
- **Jupyter Notebooks (10):** Progressive curriculum from basics to advanced
  - 01: Welcome to PoliSim (15 min)
  - 02: Federal Budget Basics (30 min)
  - 03: Healthcare Policy Analysis (45 min)
  - 04: Social Security Deep Dive (45 min)
  - 05: Monte Carlo & Uncertainty (60 min)
  - 06: Tax Policy Modeling (45 min)
  - 07: Policy Extraction from Documents (30 min)
  - 08: API Integration Guide (30 min)
  - 09: Custom Policy Design (60 min)
  - 10: Capstone Full Analysis (2-3 hr)
  
  **6.6.2: Video Tutorials (15-20 hours)**
- **Video Content (7):** Scripts + slides for recorded tutorials
  - Introduction to PoliSim (5 min)
  - Installation & Setup (3 min)
  - First Simulation (5 min)
  - Monte Carlo Results (7 min)
  - Policy Comparison (6 min)
  - API for Developers (5 min)
  - Contributing to PoliSim (4 min)

**6.6.3: Teaching Mode & Guides (8-12 hours)**
- **Teaching Materials:**
  - Teaching mode UI implementation
  - Instructor guide with course integration
  - Student workbook with exercises
  - Workshop kits (1-hour, half-day, full-day)

**6.6.4: Conference Presentations (5-8 hours)**
- **Conference Presentations:**
  - 30-slide main deck
  - Academic poster design
  - Live demo script
  - One-pager fact sheet

**Estimated Effort:** 60-65 hours | **Timeline:** 3-4 weeks

### 6.7: Monitoring & Observability (Weeks 3-4)

**Owner:** Lead Developer  
**Duration:** 1-2 weeks  
**Effort:** 15-20 hours

#### Objective
Make PoliSim production-grade observable: fast detection, clear diagnosis, and reliable incident response. This slice operationalizes the existing monitoring artifacts and code so that failures (security, availability, correctness, performance) are detected quickly and can be triaged with minimal ambiguity.

**Builds on existing work:**
- Logging + basic SLO reporting: [api/observability.py](../api/observability.py)
- Monitoring metrics/alerts reference: [docs/MONITORING_COMPLIANCE.md](../docs/MONITORING_COMPLIANCE.md)
- Incident response process: [docs/INCIDENT_RESPONSE.md](../docs/INCIDENT_RESPONSE.md)

#### Scope (What “done” means)
- A consistent telemetry contract (logs/metrics/traces) for API requests and simulation runs
- Centralized log aggregation and error tracking are wired for the deployment path
- Core SLOs are measurable and dashboarded
- Alerts are actionable and map cleanly to incident runbooks

#### Non-Goals (to prevent scope creep)
- Building new UI dashboards inside the web app (use vendor tools / Grafana / Kibana)
- Full APM re-platforming across every module (instrument the critical paths first)

---

### 6.7.1: Observability Contract & Telemetry Taxonomy (2-3 hours)

1. **Define required telemetry fields** (logs + metrics tags)
  - [ ] Environment: `env` (local/dev/staging/prod)
  - [ ] Request correlation: `request_id` (and propagate from inbound header when present)
  - [ ] Actor context: `user_id` / `api_key_id` (never log secrets)
  - [ ] Request/response context: route, method, status, latency
  - [ ] Domain context: policy_id/scenario_id where applicable

2. **Define event taxonomy** (what gets logged/metric’d)
  - [ ] Auth events (success/failure)
  - [ ] Rate limiting / circuit breaker events
  - [ ] Simulation lifecycle (queued → running → complete/fail)
  - [ ] Extraction lifecycle (ingest → parse → validate → output)

3. **Update monitoring documentation**
  - [ ] Add the above contract/taxonomy to [docs/MONITORING_COMPLIANCE.md](../docs/MONITORING_COMPLIANCE.md) (or reference it clearly if already covered)

**Acceptance Criteria**
- [ ] Telemetry contract fields are explicitly documented
- [ ] A short “event taxonomy” list exists and is referenced by runbooks/alerts

---

### 6.7.2: Structured Logging + Aggregation Pipeline (4-6 hours)

1. **Confirm structured JSON logs are emitted for all requests**
  - [ ] Ensure the request logger is invoked for success + error paths
  - [ ] Ensure request correlation is present consistently (no “unknown” in normal paths)
  - [ ] Ensure no secrets are logged (tokens, passwords, API keys)

2. **Choose and wire one log aggregation target**
  - Option A: **ELK** (local/self-host) via Docker compose + Filebeat/Logstash
  - Option B: **Datadog** (hosted) via agent + log shipping

3. **Add deployment notes**
  - [ ] Document required env vars, ports, and retention expectations
  - [ ] Define minimum retention (e.g., 7-14 days for app logs; longer for audit trails)

**Acceptance Criteria**
- [ ] A single “happy path” deployment can collect and search logs centrally
- [ ] Logs are searchable by `request_id` and endpoint

---

### 6.7.3: Error Tracking (Sentry) (2-3 hours)

1. **Integrate Sentry for unhandled exceptions**
  - [ ] Capture stack traces + request context (no sensitive payloads)
  - [ ] Tag events with `env`, route, method, status_code
  - [ ] Define sampling rules (avoid noisy events overwhelming signal)

2. **Define “release” metadata**
  - [ ] Document how releases are named (git SHA or version)
  - [ ] Ensure Sentry events include release/version where possible

**Acceptance Criteria**
- [ ] Unhandled exceptions reliably appear in Sentry with request correlation fields
- [ ] Noise controls are in place (sampling / ignore lists as needed)

---

### 6.7.4: SLOs + Dashboards (4-6 hours)

1. **Operationalize SLOs already implied by the system**
  - [ ] Availability SLO (API uptime)
  - [ ] Latency SLOs by endpoint category (p95/p99)
  - [ ] Error rate SLO (< 1% overall; tighter for “read-only” endpoints when feasible)
  - [ ] Simulation success rate SLO (define acceptable failure bands)

2. **Make SLO reporting runnable**
  - [ ] Confirm the SLO report generator exists and can be executed on a schedule (see [api/observability.py](../api/observability.py))
  - [ ] Decide where reports are stored (logs/, artifacts, or monitoring backend)

3. **Build dashboards (vendor/Grafana/Kibana)**
  - [ ] “Executive health” dashboard (availability, latency, error rate)
  - [ ] “Operations” dashboard (DB connections, queue depth, saturation)
  - [ ] “Security signals” dashboard (auth failures, rate limits, blocked IPs)

**Acceptance Criteria**
- [ ] Dashboards exist for the 3 views above
- [ ] SLOs are measurable with current telemetry (no “hand-wavy” SLOs)

---

### 6.7.5: Uptime Monitoring + Alert Routing (2-3 hours)

1. **Uptime checks**
  - [ ] Add at least one external HTTP uptime check per environment (staging/prod)
  - [ ] Validate health endpoint semantics (healthy only when dependencies are healthy)

2. **Alert routing to incident process**
  - [ ] Map critical alerts to an escalation route (PagerDuty/Slack/email)
  - [ ] Ensure alerts link to the correct runbook section in [docs/INCIDENT_RESPONSE.md](../docs/INCIDENT_RESPONSE.md)

**Acceptance Criteria**
- [ ] “Service down” pages the correct channel/on-call
- [ ] Alerts include runbook links + minimal repro context

---

### 6.7.6: Runbook Alignment + Dry-Run (1-2 hours)

1. **Runbook validation**
  - [ ] Confirm runbooks cover: outage, elevated errors, suspected breach, bad deploy, data integrity incident
  - [ ] Ensure each runbook lists the dashboards/log queries to check first

2. **Dry-run incident (tabletop)**
  - [ ] Pick one scenario (e.g., elevated 5xx + latency regression)
  - [ ] Walk through detection → triage → containment → rollback → postmortem checklist

**Acceptance Criteria**
- [ ] One tabletop exercise completed with notes
- [ ] Gaps found are logged as actionable follow-ups

---

## EFFORT SUMMARY

| Slice | Hours | Dev | Expert | Timeline |
|-------|-------|-----|--------|----------|
| 6.1: Validation | 50-60 | 50-60 | 120-150 | 4-6 weeks |
| 6.2: Security | 20-30 | 20-30 | — | 2-3 weeks |
| 6.3: Documentation | 20-24 | 20-24 | — | 1-2 weeks |
| 6.4: Community | 8-12 | 8-12 | — | 1-2 weeks |
| 6.5: Tests | 35-50 | 35-50 | 5-10 | 2-3 weeks |
| 6.6: Education | 60-65 | 60-65 | — | 3-4 weeks |
| 6.7: Monitoring | 15-20 | 15-20 | — | 1-2 weeks |
| **TOTAL** | **163-221** | **163-221** | **125-160** | **4-6 weeks (parallel)** |

---

**Ready to implement?** Start with Slices 6.2 & 6.3 (can start immediately), then Slice 6.1 (requires expert panel).
