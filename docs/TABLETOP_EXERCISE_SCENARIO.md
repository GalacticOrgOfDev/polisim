# PoliSim Incident Response Tabletop Exercise

## Scenario: Elevated 5xx Errors + Latency Regression

**Exercise Type:** Tabletop Discussion  
**Duration:** 60-90 minutes  
**Date:** [Schedule Date]  
**Facilitator:** [Name]  
**Version:** 1.0

---

## Executive Summary

This tabletop exercise walks through a simulated incident involving elevated 5xx errors combined with latency regression. The goal is to validate our incident response procedures, familiarize the team with monitoring dashboards, and identify any gaps in our runbooks.

---

## Scenario Overview

### The Situation

**Time: Monday 2:15 PM UTC**

The PoliSim API has started experiencing intermittent issues. Users report slow policy simulations, and some requests are failing entirely.

### Initial Alerts Received

```
🚨 ALERT: [CRITICAL] Availability SLO Breach
   - Current availability: 97.2% (target: 99.5%)
   - Error rate: 2.8% (5xx errors)
   - Triggered at: 2:15:32 UTC

🚨 ALERT: [WARNING] P95 Latency Above Threshold
   - Current P95: 4.2s (threshold: 2s)
   - Affected endpoints: /api/v1/simulation/run, /api/v1/policies/{id}
   - Triggered at: 2:14:18 UTC

🚨 ALERT: [WARNING] Simulation Error Rate Elevated
   - Current rate: 8.5% failures (threshold: 5%)
   - Triggered at: 2:16:45 UTC
```

---

## Exercise Phases

### Phase 1: Detection & Acknowledgment (10 minutes)

**Discussion Questions:**

1. **Where do you look first?**
   - Expected: Check Executive Health Dashboard for overall system status
   - URL: `/grafana/d/executive-health`
   - Look at: Availability gauge, Error Rate, P95 Latency panels

2. **How do you confirm this is a real incident vs. a false positive?**
   - Expected: 
     - Check multiple data sources (Prometheus, logs, Sentry)
     - Verify metrics across time range (not a brief spike)
     - Test API manually: `curl -v https://api.polisim.org/health`

3. **What severity level would you declare?**
   - Expected: HIGH (degraded performance, partial service impact)
   - Criteria: API latency >10s, error rate >5%, user-impacting

4. **Who needs to be notified?**
   - Expected: On-call IC, Operations Lead, (Security if suspicious)
   - Method: PagerDuty page + Slack #incident-response

**Action Items for This Phase:**
- [ ] IC acknowledged and joined war room
- [ ] Severity declared: HIGH
- [ ] Status page updated: "Investigating degraded API performance"
- [ ] Initial Slack notification sent

---

### Phase 2: Investigation (20 minutes)

**Scenario Update:**
```
Time: 2:25 PM UTC (10 minutes into incident)

Additional observations:
- Sentry shows 127 new errors in the last 15 minutes
- Most errors: "TimeoutError: Database query exceeded 30s timeout"
- Affected users: ~340 (based on unique user_ids in error logs)
```

**Discussion Questions:**

1. **What dashboards/logs do you check next?**
   - Expected path:
     1. Operations Dashboard → DB Connection panel
     2. Kibana query: `component:database AND level:ERROR AND @timestamp:[now-30m TO now]`
     3. Check DB metrics: connection pool, query times, locks

2. **Run this Kibana query - what would you look for?**
   ```
   level:ERROR AND @timestamp:[now-30m TO now] | top 10 error_message
   ```
   - Expected: Look for patterns - same error type, same endpoint, same query

3. **The error logs show this pattern:**
   ```json
   {
     "timestamp": "2024-01-15T14:18:32Z",
     "level": "ERROR",
     "component": "database",
     "message": "Query timeout: SELECT * FROM policies WHERE ... (took 31.2s)",
     "query_id": "q-789xyz",
     "affected_rows_estimate": 45000
   }
   ```
   **What is your hypothesis?**
   - Expected: Database query performance issue - possibly:
     - Missing index on policies table
     - Lock contention
     - Recent data growth causing full table scans
     - Bad query plan after recent deployment

4. **Check recent changes - what do you look for?**
   ```
   git log --since="2 hours ago" --oneline
   ```
   - Expected: Look for database migrations, query changes, new features

**Scenario Reveal:**
```
Investigation reveals:
- A deployment 2 hours ago added a new filter feature
- The new code path includes: WHERE policy_type IN (...) AND status = 'active'
- The 'policy_type' column is NOT indexed
- Policy table grew from 10K to 50K rows last week
```

**Root Cause Identified:**
- Missing database index on frequently-queried column
- Combined with recent data growth = queries doing full table scans
- Under load, queries timeout, connections pool exhausted, cascade failures

---

### Phase 3: Containment (15 minutes)

**Discussion Questions:**

1. **What are our containment options?**
   - Option A: Rollback the deployment (removes the slow query path)
   - Option B: Add the missing index (fixes root cause but takes time)
   - Option C: Enable read replica / failover (buys time)
   - Option D: Rate limit the affected endpoint (reduces load)

2. **Which option do you choose and why?**
   - Expected discussion:
     - Rollback is fastest but loses feature
     - Index addition is ~5-10 min but requires DB access
     - Rate limiting is quick but degrades user experience
   - Recommended: Rollback first (immediate relief), then add index, then redeploy

3. **What's the rollback procedure?**
   ```bash
   # 1. Identify last good deployment
   git log --oneline | head -5
   
   # 2. Rollback (assuming container deployment)
   kubectl rollout undo deployment/polisim-api
   
   # 3. Verify rollback successful
   curl https://api.polisim.org/health
   kubectl get pods -l app=polisim-api
   ```

4. **What do you communicate?**
   ```
   🔄 INCIDENT UPDATE #1

   Severity: HIGH
   Status: Investigating → Containing

   PROGRESS:
   - Root cause identified: Database query performance issue
   - Containment: Rolling back to previous version
   - ETA to stabilization: 5-10 minutes

   NEXT UPDATE: 2:45 PM UTC
   ```

**Action Items for This Phase:**
- [ ] Rollback initiated
- [ ] Metrics improving (watching dashboards)
- [ ] Status page updated: "Implementing fix"
- [ ] Stakeholder update sent

---

### Phase 4: Eradication & Recovery (15 minutes)

**Scenario Update:**
```
Time: 2:40 PM UTC (25 minutes into incident)

After rollback:
- Error rate dropped to 0.3% (normal)
- P95 latency: 450ms (normal)
- Availability: 99.8% (recovering)
```

**Discussion Questions:**

1. **The rollback worked. What's next?**
   - Expected:
     1. Add the missing index to production DB
     2. Update the code with optimized query
     3. Test in staging
     4. Re-deploy with fix

2. **How do you add the index safely?**
   ```sql
   -- Use CONCURRENTLY to avoid locking table
   CREATE INDEX CONCURRENTLY idx_policies_type ON policies(policy_type);
   
   -- Verify index created
   \d policies
   ```

3. **What monitoring do you set up for the redeploy?**
   - Expected:
     - Watch Operations Dashboard during deploy
     - Kibana alert for query timeouts
     - Sentry: Watch for new errors
     - Compare P95 before/after

4. **When do you declare the incident resolved?**
   - Expected criteria:
     - All metrics within SLO for 15+ minutes
     - No new errors in Sentry
     - Feature working correctly (manual test)
     - Status page updated to "Resolved"

---

### Phase 5: Post-Incident (10 minutes)

**Discussion Questions:**

1. **What goes in the post-incident report?**
   - Timeline with timestamps
   - Root cause: Missing index + data growth
   - Impact: ~340 users affected, 25 min degradation
   - Actions taken: Rollback, index addition, redeploy

2. **What preventive measures do you recommend?**
   - Expected:
     - [ ] Add index verification to deployment checklist
     - [ ] Database query performance testing in CI/CD
     - [ ] Alert on slow queries (>5s) before they become critical
     - [ ] Code review requirement for any query changes

3. **What dashboards/alerts would have caught this sooner?**
   - Expected:
     - Add panel: "Slowest Queries (P95)" to Operations Dashboard
     - Alert: Database query duration P95 > 1s
     - Pre-deployment: Run EXPLAIN on new queries

---

## Validation Checklist

After completing this exercise, verify:

### Runbook Coverage
- [ ] Outage scenario → Covered by Phase 3/4 containment procedures
- [ ] Elevated errors → Covered by this exercise
- [ ] Suspected breach → Security Signals Dashboard + auth logs
- [ ] Bad deploy → Rollback procedure validated
- [ ] Data integrity → Database recovery procedures exist

### Dashboard References
- [ ] Each runbook section references specific dashboard
- [ ] Log queries documented for common scenarios
- [ ] Prometheus queries available for key alerts

### Team Readiness
- [ ] IC knows how to access all dashboards
- [ ] Operations can execute rollback procedure
- [ ] Communication templates are accessible
- [ ] War room setup is documented

---

## Debrief Questions

1. **What went well in this exercise?**
2. **What was confusing or unclear?**
3. **What's missing from our runbooks?**
4. **What additional training would help?**
5. **Should we modify any alert thresholds?**

---

## Action Items from Exercise

| Item | Owner | Deadline | Status |
|------|-------|----------|--------|
| Add slow query alert | [Name] | [Date] | Not Started |
| Update deployment checklist | [Name] | [Date] | Not Started |
| Schedule next exercise | [Name] | [Date] | Not Started |

---

## Related Documentation

- [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md) - Full incident response procedures
- [MONITORING_COMPLIANCE.md](MONITORING_COMPLIANCE.md) - Monitoring standards and telemetry contract
- Executive Health Dashboard: `/grafana/d/executive-health`
- Operations Dashboard: `/grafana/d/operations`
- Security Signals Dashboard: `/grafana/d/security-signals`

---

## Appendix: Quick Reference Card

### First 5 Minutes Checklist
```
1. CHECK: Executive Health Dashboard - overall status
2. CHECK: Operations Dashboard - specific endpoint metrics
3. CHECK: Sentry - error count and types
4. QUERY: Kibana - level:ERROR AND @timestamp:[now-15m TO now]
5. DECIDE: Severity level (CRITICAL/HIGH/MEDIUM/LOW)
6. NOTIFY: Page IC + relevant leads
7. COMMUNICATE: Post in #incident-response
```

### Key Metrics to Watch
| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| Availability | >99.5% | 98-99.5% | <98% |
| P95 Latency | <500ms | 500ms-2s | >2s |
| Error Rate | <0.5% | 0.5-2% | >2% |
| DB Query P95 | <100ms | 100-500ms | >500ms |

---

**Exercise Version:** 1.0  
**Created:** [Date]  
**Last Updated:** [Date]  
**Next Scheduled Exercise:** [Date]

---

© 2026 PoliSim Project. All rights reserved.
