# Incident Response Plan - PoliSim

**Last Updated:** January 1, 2026  
**Version:** 1.0  
**Status:** Active

---

## Table of Contents

1. [Overview](#overview)
2. [Incident Response Team](#incident-response-team)
3. [Severity Levels](#severity-levels)
4. [Detection & Alerting](#detection--alerting)
5. [Response Procedures](#response-procedures)
6. [Communication Plan](#communication-plan)
7. [Recovery Procedures](#recovery-procedures)
8. [Post-Incident Review](#post-incident-review)
9. [Checklists](#checklists)

---

## Overview

### Purpose

This document defines the incident response procedures for PoliSim. All personnel should be familiar with their role in the incident response process.

### Scope

- **Covered:** Security breaches, data loss, service outages, attacks, compliance violations
- **Not Covered:** Minor bugs (handled through normal development process)

### Principles

1. **Speed:** Respond quickly to minimize damage
2. **Containment:** Isolate affected systems
3. **Transparency:** Keep stakeholders informed
4. **Recovery:** Restore normal operation
5. **Learning:** Improve processes to prevent recurrence

---

## Incident Response Team

### Organizational Structure

```
Incident Commander (IC)
├── Security Lead
│   └── Incident Response Team
├── Operations Lead
│   └── DevOps/SRE Team
├── Communications Lead
│   └── Communications Team
└── Executive Sponsor
    └── Legal/Compliance
```

### Roles & Responsibilities

#### Incident Commander (IC)
- **Role:** Overall coordination and decision-making
- **Responsibilities:**
  - Declare incident severity
  - Activate response team
  - Make critical decisions
  - Authorize escalations
  - Own timeline/status updates

- **Candidates:** Security Director, VP Engineering
- **Contact:** ic@polisim.org

#### Security Lead
- **Role:** Investigation and forensics
- **Responsibilities:**
  - Investigate root cause
  - Determine scope of compromise
  - Preserve evidence
  - Recommend containment actions

- **Candidates:** Security Engineer, Senior Security Analyst
- **Contact:** security-on-call@polisim.org

#### Operations Lead
- **Role:** System remediation
- **Responsibilities:**
  - Isolate affected systems
  - Deploy patches/updates
  - Coordinate recovery
  - Monitor service restoration

- **Candidates:** SRE Manager, Operations Director
- **Contact:** ops-on-call@polisim.org

#### Communications Lead
- **Role:** Internal/external communication
- **Responsibilities:**
  - Notify affected parties
  - Update status page
  - Prepare public statements
  - Coordinate with legal

- **Candidates:** VP Communications, Director of Communications
- **Contact:** comms-on-call@polisim.org

#### Executive Sponsor
- **Role:** Senior oversight
- **Responsibilities:**
  - Approve major decisions
  - Customer escalation handling
  - Board/regulatory notifications
  - Resource approval

- **Candidates:** CEO, VP Product, General Counsel
- **Contact:** executive-on-call@polisim.org

### Escalation Chain

```
Level 1 Support (15 min response)
↓
Level 2 Ops (5 min response)
↓
Level 3 Security (1 min response) + IC
↓
Executive Leadership + Legal + Communications
```

---

## Severity Levels

### Classification Matrix

| Severity | User Impact | Data Impact | Response Time | Duration | Example |
|----------|-------------|-------------|---------------|----------|---------|
| **CRITICAL** | System down, widespread | Data loss/breach | **1 hour** | Hours | System-wide DDoS, data breach |
| **HIGH** | Degraded service, many users | Potential data loss | **4 hours** | Hours-days | API errors, security vulnerability |
| **MEDIUM** | Minor feature broken | No data loss | **1 day** | Days | Bug in report generation |
| **LOW** | Informational, workaround exists | No impact | **1 week** | Weeks | Documentation error |

### CRITICAL Incident Examples

1. **Data Breach:** Unauthorized access to user/policy data
2. **DDoS Attack:** Service unavailable due to attack
3. **Ransomware:** Systems encrypted, data held hostage
4. **Mass Outage:** Core service down for >15 minutes
5. **Credential Compromise:** Admin credentials leaked

### HIGH Incident Examples

1. **Security Vulnerability:** Exploitable issue found
2. **Degraded Performance:** API latency >10 seconds
3. **Partial Outage:** One region/feature down
4. **Data Integrity:** Corrupted/inconsistent data
5. **Failed Authentication:** Login system broken

---

## Detection & Alerting

### Monitoring & Alerts

#### Grafana Dashboards (Check First)

| Dashboard | URL | Use When |
|-----------|-----|----------|
| **Executive Health** | `/grafana/d/executive-health` | First check - overall system status |
| **Operations** | `/grafana/d/operations` | API issues, latency, endpoint problems |
| **Security Signals** | `/grafana/d/security-signals` | Auth failures, rate limits, suspicious activity |

#### Key Log Queries (Kibana)

```
# OUTAGE - Check for error spikes
level:ERROR AND @timestamp:[now-1h TO now]

# ELEVATED ERRORS - Find 5xx errors
status_code:[500 TO 599] AND @timestamp:[now-30m TO now]

# SUSPECTED BREACH - Auth failures by IP
event_type:AUTH_FAILURE | top 10 client_ip

# BAD DEPLOY - Recent deployment errors
deployment_id:* AND level:ERROR AND @timestamp:[now-2h TO now]

# DATA INTEGRITY - Database errors
component:database AND (corruption OR integrity OR constraint)

# LATENCY REGRESSION - Slow requests
response_time_ms:>5000 AND @timestamp:[now-1h TO now]

# RATE LIMITING - Excessive blocks
event_type:RATE_LIMITED | stats count by client_ip
```

#### Prometheus Alert Queries

```promql
# Availability drop below SLO (99.5%)
(1 - (sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])))) < 0.995

# P95 latency above threshold
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2

# Auth failure spike
rate(auth_failures_total[5m]) > 10

# Simulation failure rate
rate(simulation_errors_total[5m]) / rate(simulation_total[5m]) > 0.1
```

#### Automated Monitoring

```
Prometheus / Grafana / ELK Stack
├── Infrastructure Metrics
│   ├── CPU > 90% (warning), > 95% (critical)
│   ├── Memory > 85% (warning), > 95% (critical)
│   ├── Disk > 90% (warning), > 98% (critical)
│   └── Network > 80% utilized (warning)
├── Application Metrics
│   ├── Error rate > 1% (warning), > 5% (critical)
│   ├── API response time > 5s (warning), > 10s (critical)
│   ├── Failed logins > 10/min (warning), > 50/min (critical)
│   └── Rate limit violations > 100/min (warning)
├── Security Metrics
│   ├── Port scans detected
│   ├── Multiple failed auth attempts
│   ├── Unusual IP access patterns
│   └── Configuration changes
└── Availability
    ├── Health check failures
    ├── Certificate expiration < 30 days
    └── Scheduled maintenance
```

#### Alert Routing

```
Alert
├── Low: Email to ops-team@
├── Medium: Slack #ops-alerts + email
├── High: PagerDuty page (on-call) + Slack + email
└── Critical: PagerDuty critical page + call + SMS
```

### Manual Detection

- **User Reports:** Via support@polisim.org, monitoring dashboard
- **Security Scanning:** Daily vulnerability scans, weekly penetration tests
- **Code Review:** Security review during deployment
- **Log Analysis:** Manual review of audit logs (weekly)

### Initial Report Template

```
From: [Reporter]
Date: [Date/Time UTC]
Subject: INCIDENT: [Brief description]

Severity: [CRITICAL/HIGH/MEDIUM/LOW]
Detection Method: [Automated alert / User report / Security scan]
System Affected: [API / Database / Auth / etc.]
Users Impacted: [Estimated count]
Data Impacted: [What data / scope]

Description:
[Detailed description of what was observed]

Timeline:
- [Time] - Event occurred
- [Time] - Detected
- [Time] - Reported

Evidence:
- Error message: [Copy of error]
- Log excerpt: [Relevant logs]
- Metric graph: [Link to monitoring]
```

---

## Response Procedures

### Phase 1: Acknowledge (0-15 minutes)

#### Actions

1. **Confirm Incident**
   - [ ] Validate alert / report
   - [ ] Confirm issue reproducible
   - [ ] Document initial observations
   - [ ] Take screenshots/logs for evidence

2. **Declare Severity**
   - [ ] Assess user impact
   - [ ] Assess data impact
   - [ ] Determine urgency
   - [ ] Declare severity level

3. **Activate Response Team**
   - [ ] Page on-call IC
   - [ ] Page on-call Security Lead
   - [ ] Page on-call Operations Lead
   - [ ] Create war room (Slack / Zoom)

4. **Initial Containment (if needed)**
   - [ ] Take affected system offline (if safe)
   - [ ] Stop suspicious processes
   - [ ] Block attacking IPs
   - [ ] Enable verbose logging

#### Communication Template

```
🚨 INCIDENT DECLARED: [SEVERITY]

Incident ID: INC-2026-001
Declared: 2026-01-01T12:00:00Z
Severity: CRITICAL

System(s) Affected: [List]
Users Impacted: [Estimated]
Data Impact: [Describe]

Incident Commander: [Name]
War Room: [Zoom link]
Status Page: [Link]

Current Action: [What is being done]
Next Update: [Time in 15 min]
```

### Phase 2: Investigate (15-60 minutes)

#### Actions

1. **Gather Information**
   - [ ] Collect relevant logs (last 24 hours)
   - [ ] Review monitoring graphs
   - [ ] Check for recent deployments/changes
   - [ ] Review audit trail
   - [ ] Identify affected data

2. **Determine Root Cause**
   - [ ] Was this an attack? (check IDS/firewall logs)
   - [ ] Was this a deployment? (check release notes)
   - [ ] Was this a failure? (check error logs)
   - [ ] Was this expected? (check maintenance calendar)

3. **Assess Scope**
   - [ ] How many users affected?
   - [ ] What data was accessed/modified?
   - [ ] What time period is affected?
   - [ ] Is this ongoing or resolved?

4. **Preserve Evidence**
   - [ ] Export logs to S3 (immutable storage)
   - [ ] Screenshot error messages
   - [ ] Save network traffic (pcap files)
   - [ ] Document timeline with timestamps

#### Root Cause Investigation Matrix

```
Investigation Path:
├── Security Incident?
│   ├── Unauthorized access? → Security Signals Dashboard + auth_audit.log
│   ├── Data exfiltration? → Kibana: event_type:DATA_ACCESS | stats by user_id
│   └── System compromise? → Check Sentry errors + endpoint logs
├── Infrastructure Failure?
│   ├── Database down? → Operations Dashboard → DB panel + database.log
│   ├── Disk full? → Executive Health → Infrastructure metrics
│   └── Memory leak? → Operations Dashboard → Memory usage over time
├── Application Failure?
│   ├── API errors? → Operations Dashboard → Error rate by endpoint
│   ├── Simulation failures? → Kibana: component:simulation AND level:ERROR
│   └── Latency spike? → Operations Dashboard → P95 Latency panel
└── Deployment Issue?
    ├── Recent push? → Kibana: deployment_id:* AND @timestamp:[now-2h TO now]
    ├── Configuration change? → Check git log + config version
    └── Third-party service? → Health endpoints → /health/dependencies
```

### Phase 3: Contain (30-120 minutes)

#### Actions

1. **Stop the Bleeding**
   - [ ] Kill compromised processes
   - [ ] Revoke compromised credentials
   - [ ] Block attacking IPs
   - [ ] Disable affected accounts

2. **Isolate Affected Systems**
   - [ ] Disconnect from network (if compromised)
   - [ ] Prevent lateral movement
   - [ ] Isolate database (if breached)
   - [ ] Backup for forensics

3. **Prevent Recurrence**
   - [ ] Apply security patch (if vulnerability)
   - [ ] Update firewall rules (if attack)
   - [ ] Rollback deployment (if recent push)
   - [ ] Implement rate limit increase

#### Containment Strategies by Type

**Security Breach:**
```
1. Revoke all user tokens
2. Force password reset for affected users
3. Block attacker IP ranges
4. Isolate database servers
5. Enable enhanced logging
6. Disable automated backups to prevent spread
```

**DDoS Attack:**
```
1. Activate CloudFlare / WAF
2. Block known attacker IPs/ASNs
3. Enable rate limiting
4. Scale infrastructure (auto-scaling)
5. Divert traffic to backup CDN
6. Contact ISP for upstream filtering
```

**Data Corruption:**
```
1. Stop write operations
2. Revert to last known good backup
3. Identify time of corruption
4. Validate data integrity
5. Freeze all automated processes
6. Manual data review
```

**Service Outage:**
```
1. Failover to backup systems
2. Activate disaster recovery plan
3. Restore from backup (if needed)
4. Validate system state
5. Gradually restore traffic
6. Monitor metrics closely
```

### Phase 4: Eradicate (1-24 hours)

#### Actions

1. **Fix Root Cause**
   - [ ] Apply permanent patch
   - [ ] Update security configuration
   - [ ] Implement preventive control
   - [ ] Test fix thoroughly

2. **Verify Fix**
   - [ ] Reproduction test (verify issue resolved)
   - [ ] Performance testing (ensure no regression)
   - [ ] Security testing (if applicable)
   - [ ] User acceptance testing (if needed)

3. **Deploy Fix**
   - [ ] Create change ticket
   - [ ] Follow deployment checklist
   - [ ] Get approvals
   - [ ] Deploy to staging first
   - [ ] Deploy to production
   - [ ] Verify in production

#### Fix Verification Checklist

- [ ] Issue no longer reproducible
- [ ] Monitoring metrics normal
- [ ] No error logs related to issue
- [ ] User reports resolved
- [ ] Affected data restored/corrected
- [ ] No performance degradation
- [ ] Security controls verified

### Phase 5: Recover (1-48 hours)

#### Actions

1. **Restore Services**
   - [ ] Bring systems back online
   - [ ] Restore from backup (if needed)
   - [ ] Verify data integrity
   - [ ] Test all functionality

2. **Monitor Closely**
   - [ ] Watch error rates
   - [ ] Monitor performance
   - [ ] Check user feedback
   - [ ] Track incident status

3. **Communicate Resolution**
   - [ ] Update status page
   - [ ] Send customer notification
   - [ ] Provide incident summary
   - [ ] Outline follow-up actions

#### Recovery Verification Checklist

- [ ] All systems operational
- [ ] All services responding normally
- [ ] Users able to login
- [ ] Data integrity verified
- [ ] Backups complete
- [ ] Performance metrics normal
- [ ] Error rate < baseline
- [ ] User testing passed

---

## Communication Plan

### Stakeholders & Notification

| Stakeholder | When | Method | Message |
|-------------|------|--------|---------|
| **Employees** | Immediately | Slack channel | "Incident declared, IC activated" |
| **Customers** | 15 min | Status page | "Issue detected, investigating" |
| **Executives** | 15 min | Email + Call | Incident details, ETA |
| **Legal** | 30 min (if breach) | Email + Meeting | Impact assessment |
| **Board** | 1 hour (if critical) | Email + Call | Severity, response plan |
| **Press** | Post-incident | Statement | Incident summary |

### Communication Templates

#### Initial Notification (15 minutes)

```
🚨 INCIDENT ALERT 🚨

Severity: [CRITICAL/HIGH]
Status: Investigating

WHAT HAPPENED:
[1-2 sentence description]

IMPACT:
- Users Affected: [X]
- Services Down: [List]
- Data Affected: [List or "None"]

WHAT WE'RE DOING:
[Current actions being taken]

NEXT UPDATE:
[Time in X minutes]

Incident Tracking: INC-2026-001
Details: [Internal link]
```

#### Progress Update (Every 30 min)

```
🔄 INCIDENT UPDATE #2

Severity: CRITICAL
Status: Investigating → Containing

PROGRESS:
- Root cause identified: [Description]
- Containment actions: [List]
- ETA to resolution: [Time]

IMPACT ASSESSMENT:
- Users affected: [X] → [X] (decreasing)
- Data compromised: [Yes/No]
- Services restored: [List]

NEXT STEPS:
[What happens in next 30 min]

NEXT UPDATE: [Time]
```

#### Resolution Announcement

```
✅ INCIDENT RESOLVED

Severity: CRITICAL
Status: Recovered

RESOLUTION:
- Root cause: [Description]
- Fix applied: [Description]
- Resolution time: [Duration]

IMPACT:
- Users affected: [X]
- Data impact: [Summary]
- Services downtime: [Duration]

NEXT STEPS:
- Post-incident review: [Date/Time]
- Customer communication: [Planned]
- Preventive measures: [Planned]

TIMELINE:
- Started: [Time]
- Detected: [Time]
- Resolved: [Time]

Incident ID: INC-2026-001
```

### Communication Frequency

- **CRITICAL:** Every 15 minutes (minimum)
- **HIGH:** Every 30 minutes
- **MEDIUM:** Every 2 hours
- **LOW:** Daily status
- **Post-Incident:** Final report within 24 hours

---

## Recovery Procedures

### Backup & Restore Process

#### Backup Verification (Daily)

```bash
# Check backup size and timestamp
backup-status --all

# Verify backup integrity
backup-test --latest --database --files

# Ensure off-site replication
s3-sync-status --buckets polisim-*
```

#### Restore Procedure (Testing Weekly)

```bash
# 1. Restore to staging environment
restore-backup --source=latest --target=staging --test

# 2. Verify data integrity
backup-integrity-check --environment=staging

# 3. Run test suite
pytest tests/ --environment=staging

# 4. Manually verify key functions
# - Login works
# - Policies accessible
# - Simulations run
# - Reports generate

# 5. Document findings
# Restore successful on [date] at [time]
```

#### Production Restore (In emergency)

```bash
# 1. Declare disaster
incident-declare --severity=CRITICAL --type=disaster

# 2. Stop all writes
database-set-mode --read-only

# 3. Create backup of current state (for forensics)
backup-create --name=compromised-state --timestamp

# 4. Restore from known-good backup
restore-backup --source=2026-01-01T00:00:00Z --target=production --verify

# 5. Verify restoration
verification-checklist --environment=production

# 6. Gradually bring systems online
load-balancer-activate --gradual --step-up 10%

# 7. Monitor closely for 1 hour
monitoring-focus --duration=3600
```

### Disaster Recovery Plan

**Recovery Time Objectives (RTO):**
- CRITICAL systems: 1 hour
- Standard systems: 4 hours
- Non-critical: 24 hours

**Recovery Point Objectives (RPO):**
- Database: 15 minutes (automated backups)
- Files: 1 hour (backup snapshots)
- Logs: Real-time (streaming to S3)

---

## Post-Incident Review

### Timing

- CRITICAL incidents: 24 hours after resolution
- HIGH incidents: 48 hours after resolution
- Others: 1 week after resolution

### Review Meeting Agenda (90 minutes)

```
1. **Incident Summary** (10 min)
   - What happened?
   - Impact and severity
   - Duration and timeline

2. **Timeline Reconstruction** (15 min)
   - When did it start?
   - When was it detected?
   - When was it fixed?
   - Gap analysis

3. **Root Cause Analysis** (20 min)
   - What was the root cause?
   - Why did it happen?
   - Why wasn't it caught?
   - Contributing factors

4. **Impact Assessment** (10 min)
   - How many users affected?
   - Data compromised?
   - Revenue impact?
   - Reputation impact?

5. **Response Effectiveness** (15 min)
   - Did the incident response work?
   - Were there any gaps?
   - Communication effectiveness?
   - Decision-making speed?

6. **Preventive Actions** (15 min)
   - How can we prevent this?
   - Action items and owners
   - Timeline for implementation
   - Success metrics

7. **Follow-up** (5 min)
   - Next meeting date
   - Assign action item owners
   - Distribute notes
```

### Post-Incident Report Template

```markdown
# Incident Report: INC-2026-001

## Executive Summary
[2-3 sentence summary of what happened]

## Timeline
- 2026-01-01 12:00 UTC - Issue started
- 2026-01-01 12:15 UTC - Detected by alert
- 2026-01-01 12:20 UTC - IC activated
- 2026-01-01 13:30 UTC - Root cause identified
- 2026-01-01 14:00 UTC - Fix deployed
- 2026-01-01 14:15 UTC - Service restored

## Root Cause
[Detailed explanation of root cause]

## Impact
- Users affected: [X]
- Services down: [Y] minutes
- Data compromised: [Yes/No]
- Revenue impact: $[X]

## Response Evaluation
- Detection time: 15 minutes ✅
- MTTR: 1 hour 15 minutes ⚠️
- Communication: Timely ✅
- Decision-making: Effective ✅

## Action Items

| Item | Owner | Deadline | Status |
|------|-------|----------|--------|
| Implement fix | Eng | 2026-01-02 | In Progress |
| Deploy to production | DevOps | 2026-01-02 | In Progress |
| Update monitoring | Ops | 2026-01-05 | Not Started |
| Implement alerting | Ops | 2026-01-05 | Not Started |
| Customer communication | Comms | 2026-01-01 | Complete |

## Lessons Learned

### What Went Well
- Quick detection
- Clear communication
- Effective teamwork

### What Could Improve
- Monitoring gap (X alert missing)
- Documentation (unclear run-book step)
- On-call training (new hire unfamiliar with process)

## Prevention

1. Add monitoring alert for condition X (Due: 2026-01-05)
2. Update run-book with missing steps (Due: 2026-01-05)
3. Additional on-call training (Due: 2026-01-10)
4. Code review process for change X (Due: 2026-01-15)

## Appendices

### A. Detailed Timeline
[Minute-by-minute timeline with quotes]

### B. Technical Analysis
[Technical details of root cause]

### C. Screenshots & Evidence
[Screenshots, logs, monitoring graphs]
```

---

## Checklists

### Incident Activation Checklist

- [ ] Incident confirmed
- [ ] Severity determined ([CRITICAL/HIGH/MEDIUM/LOW])
- [ ] IC paged and acknowledged
- [ ] Security Lead paged and acknowledged
- [ ] Operations Lead paged and acknowledged
- [ ] War room created and link shared
- [ ] Status page updated (incident declared)
- [ ] First customer notification sent
- [ ] Logging increased (verbose mode)
- [ ] Evidence preservation started

**Estimated time: 5-10 minutes**

### Containment Checklist

- [ ] Root cause hypothesis identified
- [ ] Affected systems isolated (if needed)
- [ ] Malicious processes stopped (if applicable)
- [ ] Attacking IPs blocked
- [ ] Compromised credentials revoked
- [ ] Enhanced logging enabled
- [ ] Backup systems activated (if needed)
- [ ] Failover tested
- [ ] Load balanced away from affected systems
- [ ] Incident updates sent every 15 minutes

**Estimated time: 30-120 minutes**

### Recovery Checklist

- [ ] All systems operational
- [ ] Services responding normally
- [ ] Data integrity verified
- [ ] Users able to login
- [ ] Key workflows tested
- [ ] Performance metrics normal
- [ ] Error rate < baseline
- [ ] Incident status updated to "Resolved"
- [ ] Customer notification sent
- [ ] Post-incident review scheduled

**Estimated time: 30 minutes - 24 hours**

### Post-Incident Checklist

- [ ] War room closed
- [ ] Logs exported to S3
- [ ] Evidence preserved
- [ ] Initial report published
- [ ] Post-incident meeting scheduled
- [ ] Action items assigned
- [ ] Timeline confirmed
- [ ] Customer communication sent
- [ ] Preventive measures identified
- [ ] Monitoring improvements documented

**Estimated time: 2-4 hours**

---

## Training & Drills

### Tabletop Exercises

For structured incident response practice, see:
- **[TABLETOP_EXERCISE_SCENARIO.md](TABLETOP_EXERCISE_SCENARIO.md)** - Elevated 5xx + Latency Regression scenario

### Annual Training Requirements

All employees:
- [ ] Incident response overview (30 min)
- [ ] Role-specific training (1 hour)
- [ ] Scenario-based tabletop (2 hours)

Incident response team:
- [ ] Advanced incident management (4 hours)
- [ ] Forensics & evidence preservation (4 hours)
- [ ] Communication & crisis management (2 hours)

### Quarterly Drills

- **Q1:** Simulated security breach
- **Q2:** Simulated data loss/corruption
- **Q3:** Simulated DDoS attack
- **Q4:** Simulated service outage

### Drill Template

```
Scenario: [Brief description]
Date: [Scheduled date]
Participants: [Who]
Duration: [Expected time]
Objectives:
  - [Learning objective 1]
  - [Learning objective 2]

Expected Actions:
  1. [Action 1]
  2. [Action 2]
  3. [Action 3]

Success Criteria:
  - [Criterion 1]
  - [Criterion 2]
  - [Criterion 3]

Debrief: [Scheduled time]
```

---

## Appendix A: Contacts

### On-Call Rotation

See: https://pagerduty.com/polisim-escalation

**Current On-Call:**
- IC: [Name]
- Security: [Name]
- Operations: [Name]
- Communications: [Name]

### Email Addresses

- `security@polisim.org` - General security
- `incident@polisim.org` - Incident reporting
- `ic@polisim.org` - Incident commander
- `ops-on-call@polisim.org` - Operations
- `comms-on-call@polisim.org` - Communications

### Phone Numbers

- Security: +1-XXX-XXX-XXXX
- Operations: +1-XXX-XXX-XXXX
- Emergency: [Emergency number]

---

**Incident Response Plan Version:** 1.0  
**Last Updated:** January 1, 2026  
**Next Review:** April 1, 2026  
**Approved By:** [Title]  
**Status:** ✅ Active

---

© 2026 PoliSim Project. All rights reserved.
