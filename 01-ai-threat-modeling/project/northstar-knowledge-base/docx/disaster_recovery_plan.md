# Northstar Technologies Disaster Recovery Plan

**Document ID:** OPS-DR-001 **Version:** 1.5 **Effective Date:** March 1, 2023 **Owner:** David Kim, DevOps Engineer **Classification:** Confidential

------------------------------------------------------------------------

## 1. Executive Summary

This Disaster Recovery Plan (DRP) outlines the procedures for recovering Northstar Technologies’ critical systems and data in the event of a disaster or major outage. The goal is to minimize downtime and data loss while ensuring business continuity for our customers.

### Key Metrics

| Metric                         | Target  | Current Capability |
|--------------------------------|---------|--------------------|
| Recovery Time Objective (RTO)  | 4 hours | 2 hours            |
| Recovery Point Objective (RPO) | 1 hour  | 15 minutes         |
| Maximum Tolerable Downtime     | 8 hours | \-                 |

## 2. Scope

This plan covers disaster recovery for:

- Production application infrastructure (AWS us-east-1)
- Customer data and databases
- Supporting services (authentication, notifications, reporting)
- Critical internal systems

### Out of Scope

- Development and staging environments
- Non-critical internal tools
- Marketing website (covered by separate plan)

## 3. Disaster Scenarios

### 3.1 Scenario Classification

| Category | Examples | Likelihood | Impact |
|----|----|----|----|
| **Infrastructure Failure** | AWS region outage, data center failure | Low | Critical |
| **Data Corruption** | Database corruption, ransomware | Low | Critical |
| **Cyber Attack** | DDoS, breach, malware | Medium | High |
| **Natural Disaster** | Earthquake, severe weather | Low | Medium |
| **Human Error** | Accidental deletion, misconfiguration | Medium | Medium |

### 3.2 Trigger Criteria

Disaster recovery procedures are initiated when:

- Primary AWS region (us-east-1) is unavailable for \> 30 minutes
- Database corruption affects production data integrity
- Security incident requires isolation of primary environment
- Critical infrastructure components fail simultaneously

## 4. Recovery Architecture

### 4.1 AWS Infrastructure Overview

**Primary Region:** us-east-1 (N. Virginia) **DR Region:** us-west-2 (Oregon)

### 4.2 Replication Strategy

| Component          | Replication Method        | Frequency  | DR Location |
|--------------------|---------------------------|------------|-------------|
| RDS PostgreSQL     | Cross-region read replica | Continuous | us-west-2   |
| S3 Buckets         | Cross-region replication  | Real-time  | us-west-2   |
| Application Config | Terraform state in S3     | On change  | us-west-2   |
| Secrets            | AWS Secrets Manager       | Replicated | us-west-2   |
| Container Images   | ECR replication           | On push    | us-west-2   |

### 4.3 DR Environment

The DR environment in us-west-2 maintains:

- Scaled-down replica of application infrastructure (can scale up within 15 min)
- Read replica of production database (promotable to primary)
- Replicated S3 buckets with customer data
- Pre-configured load balancers and DNS failover

## 5. Recovery Procedures

### 5.1 Activation Decision Tree

    Is production unavailable?
        └── YES → Is it a known AWS outage?
                      └── YES → Is estimated recovery > 30 min?
                                  └── YES → ACTIVATE DR
                                  └── NO → Wait and monitor
                      └── NO → Is it a security incident?
                                  └── YES → ACTIVATE DR + Incident Response
                                  └── NO → Troubleshoot primary
        └── NO → Continue normal operations

### 5.2 Activation Authority

| Severity           | Can Activate    | Required Approval |
|--------------------|-----------------|-------------------|
| Full DR Failover   | VP Engineering  | CEO notification  |
| Partial Failover   | DevOps Lead     | VP Engineering    |
| Database Promotion | DevOps Engineer | DevOps Lead       |

### 5.3 Step-by-Step Recovery

#### Phase 1: Assessment (0-15 minutes)

1.  Confirm outage scope and impact
2.  Check AWS Health Dashboard for regional issues
3.  Notify DR team via PagerDuty escalation
4.  Assemble incident response team on Zoom bridge
5.  Make activation decision

#### Phase 2: Failover Initiation (15-45 minutes)

1.  **Database Failover**
    - Promote us-west-2 RDS read replica to primary
    - Update application connection strings in Secrets Manager
    - Verify database accessibility
2.  **Application Deployment**
    - Scale up EC2 instances in us-west-2
    - Deploy latest application version to DR environment
    - Verify application health checks
3.  **DNS Failover**
    - Update Route 53 health checks to point to DR
    - Failover DNS records (5-minute TTL)
    - Verify DNS propagation

#### Phase 3: Validation (45-90 minutes)

1.  Run automated smoke tests against DR environment
2.  Verify critical user workflows
3.  Check data integrity with sample queries
4.  Monitor error rates and latency
5.  Confirm customer-facing functionality

#### Phase 4: Communication (Ongoing)

1.  Update status page (status.northstartech.com)
2.  Send customer notification email
3.  Post updates every 30 minutes until resolved
4.  Notify executive team

## 6. Failback Procedures

### 6.1 Failback Criteria

Failback to primary region should occur when:

- Primary region is fully operational
- Root cause has been identified and resolved
- Maintenance window is available
- Customer communication plan is ready

### 6.2 Failback Steps

1.  **Data Synchronization**
    - Set up replication from DR to primary
    - Allow full sync to complete
    - Verify data consistency
2.  **Application Preparation**
    - Deploy identical application version to primary
    - Verify configuration consistency
    - Run smoke tests on primary
3.  **Cutover**
    - Schedule maintenance window
    - Stop writes to DR database briefly
    - Final data sync
    - Switch DNS back to primary
    - Monitor for issues
4.  **Cleanup**
    - Scale down DR environment
    - Re-establish replication primary → DR
    - Update documentation with lessons learned

## 7. Testing Schedule

### 7.1 Test Types

| Test Type          | Frequency     | Duration | Impact              |
|--------------------|---------------|----------|---------------------|
| Tabletop Exercise  | Quarterly     | 2 hours  | None                |
| Component Failover | Monthly       | 1 hour   | Minimal             |
| Full DR Test       | Semi-annually | 4 hours  | Planned maintenance |

### 7.2 Test Checklist

- [ ] Database failover and promotion
- [ ] Application deployment to DR
- [ ] DNS failover
- [ ] Load balancer health checks
- [ ] Monitoring and alerting in DR
- [ ] Customer notification process
- [ ] Failback procedures

### 7.3 Test Results

| Date       | Test Type | Result | Notes                |
|------------|-----------|--------|----------------------|
| 2023-01-15 | Full DR   | Pass   | RTO: 1h 45m          |
| 2023-03-10 | Tabletop  | Pass   | Updated runbook      |
| 2023-04-20 | Component | Pass   | DB failover \< 5 min |
| 2023-06-01 | Full DR   | Pass   | RTO: 1h 30m          |

## 8. Roles and Responsibilities

### 8.1 DR Team

| Role               | Primary        | Backup         | Contact      |
|--------------------|----------------|----------------|--------------|
| Incident Commander | Sarah Chen     | David Kim      | 206-555-1001 |
| Technical Lead     | David Kim      | Marcus Johnson | 206-555-1004 |
| Database Admin     | Jessica Walker | Priya Sharma   | 206-555-1007 |
| Communications     | Brian Clark    | Nicole Harris  | 212-555-7002 |
| Customer Success   | Lisa Anderson  | Kevin Wilson   | 512-555-4001 |

### 8.2 Escalation Path

1.  **Level 1:** On-call DevOps Engineer (PagerDuty)
2.  **Level 2:** DevOps Lead (David Kim)
3.  **Level 3:** VP Engineering (Sarah Chen)
4.  **Level 4:** Executive Team (CEO)

## 9. Communication Templates

### 9.1 Initial Customer Notification

> Subject: Service Disruption - Northstar Platform
>
> We are currently experiencing a service disruption affecting the Northstar platform. Our team has activated disaster recovery procedures and is working to restore service.
>
> Current Status: \[IN PROGRESS\] Estimated Recovery: \[TIME\]
>
> We will provide updates every 30 minutes. Please monitor status.northstartech.com for real-time updates.

### 9.2 Resolution Notification

> Subject: Service Restored - Northstar Platform
>
> We are pleased to report that the Northstar platform has been fully restored. All services are operating normally.
>
> Duration: \[X hours Y minutes\] Root Cause: \[Brief description\]
>
> A detailed post-mortem will be shared within 5 business days.

## 10. Appendices

### A. Emergency Contact List

- AWS Support: Enterprise support portal or 1-800-xxx-xxxx
- PagerDuty: pagerduty.com/northstar
- Zoom Bridge: https://zoom.us/j/XXXXXXXXX (PIN: 123456)

### B. Runbook Links

- Database Failover: confluence.northstartech.com/dr/db-failover
- Application Deployment: confluence.northstartech.com/dr/app-deploy
- DNS Failover: confluence.northstartech.com/dr/dns-failover

### C. AWS Resource IDs

- Primary RDS: northstar-prod-db
- DR RDS Replica: northstar-dr-db
- Primary ALB: prod-application-lb
- DR ALB: dr-application-lb
- Route 53 Hosted Zone: Z1234567890ABC

------------------------------------------------------------------------

**Document History**

| Version | Date       | Changes                      |
|---------|------------|------------------------------|
| 1.0     | 2021-06-01 | Initial plan                 |
| 1.2     | 2022-01-15 | Added EKS procedures         |
| 1.5     | 2023-03-01 | Updated for new architecture |

------------------------------------------------------------------------

*This document is reviewed quarterly and updated as infrastructure changes. Last review: June 2023*
