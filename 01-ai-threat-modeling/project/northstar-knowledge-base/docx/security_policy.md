# Northstar Technologies Information Security Policy

**Document ID:** SEC-POL-001 **Version:** 2.3 **Effective Date:** January 15, 2023 **Last Review:** June 1, 2023 **Owner:** Ryan Hall, Security Engineer **Classification:** Internal Use Only

------------------------------------------------------------------------

## 1. Purpose

This Information Security Policy establishes the framework for protecting Northstar Technologies’ information assets, including customer data, intellectual property, and business-critical systems. All employees, contractors, and third parties with access to company systems must comply with this policy.

## 2. Scope

This policy applies to:

- All employees (full-time, part-time, temporary)
- Contractors and consultants
- Third-party vendors with system access
- All information systems, applications, and data owned or managed by Northstar Technologies

## 3. Information Classification

### 3.1 Classification Levels

| Level | Description | Examples |
|----|----|----|
| **Public** | Information approved for public release | Marketing materials, press releases |
| **Internal** | Business information for internal use | Policies, procedures, org charts |
| **Confidential** | Sensitive business information | Financial reports, roadmaps, contracts |
| **Restricted** | Highly sensitive data requiring strict controls | Customer PII, credentials, encryption keys |

### 3.2 Handling Requirements

**Restricted Data:**

- Must be encrypted at rest and in transit
- Access limited to authorized personnel only
- Must not be stored on personal devices
- Requires logging of all access

**Confidential Data:**

- Should be encrypted when transmitted externally
- Access based on business need
- Should not be shared without manager approval

## 4. Access Control

### 4.1 Account Management

- All accounts must be individually assigned (no shared accounts)
- Accounts must be provisioned through the IT ticketing system
- Account access must be reviewed quarterly by managers
- Terminated employee accounts must be disabled within 24 hours

### 4.2 Authentication Requirements

**Password Policy:**

- Minimum 12 characters
- Must include uppercase, lowercase, numbers, and special characters
- Cannot reuse last 12 passwords
- Must be changed every 90 days (or immediately if compromised)

**Multi-Factor Authentication (MFA):**

- Required for all production system access
- Required for VPN access
- Required for administrative accounts
- Recommended for all employee accounts

### 4.3 Privileged Access

- Administrative access granted only when required for job function
- Privileged actions must be logged and reviewed
- Admin accounts must use separate credentials from standard accounts
- Emergency access procedures documented and tested annually

## 5. Network Security

### 5.1 Network Architecture

- Production, staging, and development environments must be logically separated
- Direct internet access to production systems is prohibited
- All external traffic must pass through approved security controls (WAF, firewall)
- Internal network segmented by function and sensitivity

### 5.2 Remote Access

- VPN required for all remote access to internal systems
- Split tunneling is prohibited
- Remote access sessions time out after 30 minutes of inactivity
- Remote access logs retained for 1 year

### 5.3 Wireless Security

- Corporate wireless networks must use WPA3 encryption
- Guest wireless isolated from corporate network
- Wireless access points managed centrally by IT

## 6. Data Protection

### 6.1 Encryption Standards

| Data State | Minimum Standard                     |
|------------|--------------------------------------|
| At Rest    | AES-256                              |
| In Transit | TLS 1.2+ (TLS 1.3 preferred)         |
| Database   | Transparent Data Encryption (TDE)    |
| Backups    | AES-256 with separate key management |

### 6.2 Data Retention

- Customer data retained per contractual obligations
- Log data retained for minimum 1 year
- Backup data retained for 90 days
- Data must be securely destroyed when no longer needed

### 6.3 Data Loss Prevention

- DLP tools monitor for sensitive data exfiltration
- USB storage devices disabled on corporate laptops
- Cloud storage limited to approved services (S3, approved SaaS)
- Email attachments scanned for sensitive content

## 7. Incident Response

### 7.1 Incident Classification

| Severity | Description | Response Time |
|----|----|----|
| **Critical** | Active breach, data exfiltration, service outage | Immediate (\< 15 min) |
| **High** | Attempted breach, vulnerability exploitation | \< 1 hour |
| **Medium** | Policy violation, suspicious activity | \< 4 hours |
| **Low** | Minor policy deviation, informational | \< 24 hours |

### 7.2 Reporting Requirements

All security incidents must be reported immediately to:

- Security Team: security@northstartech.com
- Security Hotline: 206-555-7325
- Slack: \#security-incidents

Do not attempt to investigate or remediate incidents without Security team involvement.

### 7.3 Incident Response Process

1.  **Detection & Reporting** - Identify and report incident
2.  **Triage** - Security team assesses severity and scope
3.  **Containment** - Limit damage and prevent spread
4.  **Eradication** - Remove threat from environment
5.  **Recovery** - Restore normal operations
6.  **Lessons Learned** - Document and improve processes

## 8. Acceptable Use

### 8.1 Permitted Activities

- Business-related use of company systems
- Limited personal use that does not interfere with work
- Accessing approved cloud services and applications
- Using company email for business communications

### 8.2 Prohibited Activities

- Accessing systems without authorization
- Sharing credentials with others
- Installing unauthorized software
- Circumventing security controls
- Storing sensitive data on personal devices
- Using company systems for illegal activities
- Cryptocurrency mining on company resources

## 9. Physical Security

### 9.1 Office Security

- Badge access required for all office locations
- Visitors must sign in and be escorted
- Sensitive areas (server rooms) require additional authorization
- Clean desk policy enforced for sensitive materials

### 9.2 Equipment Security

- Laptops must have full disk encryption enabled
- Mobile devices must have screen lock and remote wipe capability
- Lost or stolen devices must be reported within 4 hours
- Equipment must be securely disposed of through IT

## 10. Third-Party Security

### 10.1 Vendor Requirements

All vendors with access to Northstar systems or data must:

- Sign a Data Processing Agreement (DPA)
- Demonstrate appropriate security controls
- Undergo security assessment for high-risk vendors
- Maintain cyber liability insurance

### 10.2 Ongoing Monitoring

- High-risk vendors reviewed annually
- Security questionnaires required for renewals
- Immediate assessment if vendor experiences breach

## 11. Compliance

### 11.1 Regulatory Requirements

Northstar Technologies maintains compliance with:

- **SOC 2 Type II** - Annual audit
- **GDPR** - For EU customer data
- **CCPA** - For California resident data
- **HIPAA** - For healthcare customers (BAA required)

### 11.2 Policy Violations

Violations of this policy may result in:

- Verbal or written warning
- Mandatory security training
- Suspension of system access
- Termination of employment
- Legal action (for severe violations)

## 12. Training and Awareness

### 12.1 Required Training

| Training            | Frequency | Audience               |
|---------------------|-----------|------------------------|
| Security Awareness  | Annual    | All employees          |
| Phishing Simulation | Quarterly | All employees          |
| Secure Coding       | Annual    | Engineering team       |
| Incident Response   | Annual    | Security & Engineering |
| Data Handling       | Annual    | All employees          |

### 12.2 Security Communications

- Monthly security newsletter
- Alerts for emerging threats
- Lessons learned from incidents (anonymized)

## 13. Policy Review

This policy is reviewed and updated:

- Annually (minimum)
- After significant security incidents
- When regulatory requirements change
- When business operations significantly change

------------------------------------------------------------------------

**Document History**

| Version | Date       | Author    | Changes                      |
|---------|------------|-----------|------------------------------|
| 1.0     | 2020-01-01 | Ryan Hall | Initial policy               |
| 2.0     | 2022-01-15 | Ryan Hall | Added HIPAA requirements     |
| 2.1     | 2022-06-01 | Ryan Hall | Updated encryption standards |
| 2.2     | 2022-12-01 | Ryan Hall | Added remote work guidelines |
| 2.3     | 2023-01-15 | Ryan Hall | Annual review updates        |

------------------------------------------------------------------------

**Approval**

| Role              | Name        | Date             |
|-------------------|-------------|------------------|
| Security Engineer | Ryan Hall   | January 15, 2023 |
| VP of Engineering | Sarah Chen  | January 15, 2023 |
| General Counsel   | Laura Allen | January 15, 2023 |

------------------------------------------------------------------------

*For questions about this policy, contact security@northstartech.com*
