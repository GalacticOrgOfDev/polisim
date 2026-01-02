# Security Monitoring & Alerting - PoliSim

**Last Updated:** January 1, 2026  
**Version:** 1.0  
**Status:** Active

---

## Table of Contents

1. [Monitoring Infrastructure](#monitoring-infrastructure)
2. [Key Metrics](#key-metrics)
3. [Alerting Rules](#alerting-rules)
4. [Dashboard Setup](#dashboard-setup)
5. [Log Aggregation](#log-aggregation)
6. [Compliance Monitoring](#compliance-monitoring)

---

## Monitoring Infrastructure

### Architecture

```
Application
├── Instrumentation (Prometheus/StatsD)
├── Metrics Export
└── Log Aggregation
    ├── Datadog / New Relic / ELK Stack
    ├── Metrics Database (Time-series)
    ├── Log Storage (S3/CloudWatch)
    └── Alert Engine
        ├── PagerDuty (On-call)
        ├── Slack (Team notification)
        ├── Email (Archive)
        └── SMS (Critical)
```

### Tools

- **Metrics:** Prometheus, Datadog, New Relic, CloudWatch
- **Logs:** ELK Stack, CloudWatch, Splunk, Datadog
- **Alerting:** PagerDuty, AlertManager, Slack
- **Dashboards:** Grafana, Kibana, Datadog, CloudWatch
- **APM:** Datadog APM, New Relic, Jaeger

---

## Key Metrics

### Infrastructure Metrics

| Metric | Warning | Critical | Check Interval |
|--------|---------|----------|-----------------|
| CPU Usage | > 80% | > 95% | 1 minute |
| Memory Usage | > 85% | > 95% | 1 minute |
| Disk Usage | > 85% | > 95% | 5 minutes |
| Disk I/O | > 80% | > 90% | 1 minute |
| Network I/O | > 80% util | > 95% util | 1 minute |
| System Load | > 4 (4-core) | > 6 (4-core) | 1 minute |
| Connections | > 900/1000 | > 950/1000 | 1 minute |

### Application Metrics

| Metric | Warning | Critical | SLO |
|--------|---------|----------|-----|
| Error Rate | > 1% | > 5% | < 0.1% |
| Response Time P95 | > 2s | > 5s | < 500ms |
| Response Time P99 | > 5s | > 10s | < 1s |
| Throughput | < 500 req/s | < 100 req/s | > 1000 req/s |
| Availability | < 99.5% | < 99% | > 99.9% |

### Security Metrics

| Metric | Warning | Critical | Check Interval |
|--------|---------|----------|-----------------|
| Auth Failures/min | > 10 | > 50 | 1 minute |
| Rate Limit Violations | > 100/min | > 500/min | 1 minute |
| Blocked IPs | > 5 | > 20 | 1 minute |
| Failed TLS Handshakes | > 10/min | > 50/min | 1 minute |
| Port Scans Detected | Any | Any | Real-time |
| Failed Backups | > 1 | > 2 | Daily |
| Certs Expiring | < 30 days | < 7 days | Daily |

### Business Metrics

| Metric | Warning | Critical | Check Interval |
|--------|---------|----------|-----------------|
| Active Users | < 80% baseline | < 50% baseline | 5 minutes |
| Simulation Failures | > 5% | > 10% | 5 minutes |
| API Key Activations | > 100/day | > 500/day | Hourly |
| Failed Logins | > 10/min | > 50/min | 1 minute |

---

## Alerting Rules

### Critical Alerts (PagerDuty immediate page)

```yaml
# Security Incidents
- name: "Unauthorized Access Attempt"
  condition: "failed_auth_attempts > 50 in 5min"
  severity: "critical"
  action: "page_ic"

- name: "Data Access Anomaly"
  condition: "user_data_access > 3_std_dev"
  severity: "critical"
  action: "page_security_lead"

- name: "DDoS Attack Detected"
  condition: "rate_limit_violations > 500/min"
  severity: "critical"
  action: "page_ops_lead + activate_ddos_protection"

- name: "Ransomware Signature Detected"
  condition: "endpoint_protection_alert + file_encryption"
  severity: "critical"
  action: "page_all + isolate_systems"

# Availability
- name: "Service Down"
  condition: "http_status_5xx > 80% for 2min"
  severity: "critical"
  action: "page_ops_lead + activate_failover"

- name: "Database Connection Pool Exhausted"
  condition: "db_connections > 990/1000"
  severity: "critical"
  action: "page_dba"

- name: "Storage Capacity Critical"
  condition: "disk_usage > 95%"
  severity: "critical"
  action: "page_ops_lead"

# Backup/Recovery
- name: "Backup Failed"
  condition: "backup_status == failed"
  severity: "critical"
  action: "page_ops_lead"

- name: "Restore Test Failed"
  condition: "restore_verification == failed"
  severity: "critical"
  action: "page_dba"
```

### High Alerts (PagerDuty page within 4 hours)

```yaml
- name: "High Error Rate"
  condition: "error_rate > 5% for 10min"
  severity: "high"
  action: "slack_ops + email"

- name: "High Latency"
  condition: "p99_latency > 10s for 10min"
  severity: "high"
  action: "slack_ops + email"

- name: "Certificate Expiration Warning"
  condition: "cert_expiry < 7 days"
  severity: "high"
  action: "slack_ops + email"

- name: "Unusual API Activity"
  condition: "api_calls from_ip > 3_std_dev"
  severity: "high"
  action: "slack_security + email"

- name: "Memory Leak Suspected"
  condition: "memory_growth > 1gb/hour for 4hours"
  severity: "high"
  action: "slack_ops + email"

- name: "Database Replication Lag"
  condition: "replication_lag > 60s"
  severity: "high"
  action: "slack_dba + email"
```

### Medium Alerts (Slack notification)

```yaml
- name: "High CPU"
  condition: "cpu_usage > 80% for 15min"
  action: "slack_ops"

- name: "High Disk I/O"
  condition: "disk_io > 80% for 15min"
  action: "slack_ops"

- name: "Slow Queries"
  condition: "query_time > 5s AND frequency > 10/min"
  action: "slack_dba"

- name: "Rate Limiting Active"
  condition: "rate_limit_violations > 100/min for 5min"
  action: "slack_ops"

- name: "Failed Login Attempts"
  condition: "failed_logins > 10/min for 5min"
  action: "slack_security"

- name: "Configuration Change"
  condition: "config_version changed"
  action: "slack_ops"
```

---

## Dashboard Setup

### Executive Dashboard

```
┌─────────────────────────────────────────────────┐
│ PoliSim Health Status Dashboard                 │
├─────────────────────────────────────────────────┤
│                                                 │
│ System Status: 🟢 Healthy                      │
│ Uptime: 99.95%  Incidents (24h): 0             │
│ Active Users: 1,234  API Calls (1h): 45,234    │
│                                                 │
├─────────────────────────────────────────────────┤
│ KEY METRICS (Last 24 hours)                     │
├─────────────────────────────────────────────────┤
│                                                 │
│ Response Time P95  Error Rate  Availability    │
│ ┌──────────────┐  ┌────────┐  ┌──────────┐    │
│ │  342ms       │  │ 0.02%  │  │ 99.95%   │    │
│ │ [▁▂▃▄▅▅▄▃▂▁] │  │ [▁▁▁] │  │ [▆▆▆▆▆▆] │    │
│ └──────────────┘  └────────┘  └──────────┘    │
│                                                 │
├─────────────────────────────────────────────────┤
│ SECURITY METRICS                                │
├─────────────────────────────────────────────────┤
│                                                 │
│ Failed Logins  Blocked IPs  Rate Limit Events  │
│ ┌────────┐     ┌────────┐   ┌────────────┐    │
│ │   2    │     │   0    │   │     45     │    │
│ └────────┘     └────────┘   └────────────┘    │
│                                                 │
├─────────────────────────────────────────────────┤
│ INCIDENTS & ALERTS                              │
├─────────────────────────────────────────────────┤
│                                                 │
│ Recent Incidents: None                          │
│ Active Alerts: None                             │
│ Acknowledged: All                               │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Operations Dashboard

```
Shows:
- Request rate, latency, errors (by endpoint)
- Database queries, latency, connections
- Cache hit/miss rates
- Queue depth
- Resource utilization (CPU, memory, disk)
- Recent deployments
- Infrastructure health
```

### Security Dashboard

```
Shows:
- Authentication metrics (logins, failures, tokens)
- Authorization (permission denials, role changes)
- Rate limiting (violations, blocked IPs)
- Audit events (last 100)
- Threat detections
- Certificate expiration
- Vulnerability status
```

---

## Log Aggregation

### Log Collection

```python
# Structured logging in application
import logging
import json

logger = logging.getLogger(__name__)

# Application logs
logger.info("User login", extra={
    "event": "login_success",
    "user_id": user_id,
    "ip_address": ip,
    "user_agent": user_agent,
    "timestamp": datetime.utcnow().isoformat(),
    "session_id": session_id
})

# Security events
logger.warning("Rate limit violation", extra={
    "event": "rate_limit_violation",
    "ip_address": ip,
    "endpoint": endpoint,
    "limit": limit,
    "count": count,
    "timestamp": datetime.utcnow().isoformat()
})

# Errors
logger.error("API error", extra={
    "event": "api_error",
    "error_code": error_code,
    "error_message": error_message,
    "stack_trace": traceback.format_exc(),
    "timestamp": datetime.utcnow().isoformat()
})
```

### Log Retention

| Log Type | Retention | Storage | Access |
|----------|-----------|---------|--------|
| Application Logs | 30 days | CloudWatch/ELK | Team |
| Audit Logs | 90 days | S3 (immutable) | Admin |
| Security Events | 180 days | S3 + SIEM | Security |
| Error Logs | 30 days | CloudWatch/ELK | Team |
| Access Logs | 30 days | S3 + Analytics | Analytics |
| Backup Logs | 1 year | S3 | Admin |

### Log Analysis Queries

```sql
-- Failed authentication attempts
SELECT timestamp, user_id, ip_address, COUNT(*) as attempts
FROM audit_logs
WHERE event = 'login_failure'
  AND timestamp > NOW() - INTERVAL 1 hour
GROUP BY user_id, ip_address
HAVING COUNT(*) > 5

-- Unusual data access
SELECT timestamp, user_id, resource, action
FROM audit_logs
WHERE event = 'data_access'
  AND timestamp > NOW() - INTERVAL 1 day
  AND (resource_size > 100MB OR access_count > 1000)

-- Configuration changes
SELECT timestamp, user_id, change_type, change_details
FROM audit_logs
WHERE event = 'configuration_change'
  AND timestamp > NOW() - INTERVAL 24 hours
ORDER BY timestamp DESC

-- Rate limit violations
SELECT timestamp, ip_address, endpoint, COUNT(*) as violations
FROM security_logs
WHERE event = 'rate_limit_violation'
  AND timestamp > NOW() - INTERVAL 1 hour
GROUP BY ip_address, endpoint
HAVING COUNT(*) > 50
```

---

## Compliance Monitoring

### GDPR Compliance Monitoring

```yaml
# Data retention checks
rules:
  - name: "Data Retention Policy Violation"
    description: "User data older than retention period"
    query: |
      SELECT user_id, data_type, last_access
      FROM user_data
      WHERE last_access < NOW() - INTERVAL 90 days
    frequency: "daily"
    action: "alert_compliance"

  - name: "Unencrypted PII in Storage"
    description: "Personal data not encrypted at rest"
    query: |
      SELECT storage_location, pii_fields, encryption_status
      FROM data_inventory
      WHERE pii_fields > 0 AND encryption_status = 'none'
    frequency: "hourly"
    action: "alert_critical"

  - name: "Missing Access Logs"
    description: "Data access not logged properly"
    query: |
      SELECT COUNT(*) as missing_logs
      FROM access_events
      WHERE timestamp IS NULL
        OR user_id IS NULL
        OR ip_address IS NULL
    frequency: "hourly"
    action: "alert_compliance"
```

### Audit & Testing

```yaml
# Quarterly security testing
schedule:
  - Q1: "Vulnerability scanning"
  - Q2: "Penetration testing"
  - Q3: "Code review"
  - Q4: "Disaster recovery drill"

# Annual compliance audit
audit:
  - scope: "Security controls"
  - scope: "Data protection"
  - scope: "Access controls"
  - scope: "Incident response"
  - scope: "Audit logging"
  - frequency: "annually"
  - external: "third-party auditor"
```

---

**Monitoring & Alerting Version:** 1.0  
**Last Updated:** January 1, 2026  
**Next Review:** April 1, 2026  
**Status:** ✅ Active
