# SOLUTION — Exercise 08: Implement Rate Limiting for Orion API

This document is the answer key for skill-pair-08. Open it after you've completed every task. The reference implementation of `rate_limiter.py` is in `solutions/rate_limiter_solution.py`.

---

## Task 1 — Read and run the rate limiter

The implementation in `starter/rate_limiter.py` is already complete. Students read it and run it without changing it. `solutions/rate_limiter_solution.py` contains the same implementation. The notes below explain how it works.

### Key implementation notes

**`check_rate_limit`:** The method prunes stale timestamps, counts the remainder, and allows or denies based on whether the count is strictly less than `max_requests`. The "strictly less than" comparison (`<`) is correct — when `requests_in_window == max_requests`, the user is AT the limit and must be denied. Only when they are BELOW the limit is the request allowed and recorded.

**`record_request`:** A one-liner: `self._timestamps[user_id].append(time.time())`. It must only be called from within `check_rate_limit` after confirming the request is allowed. Application code should never call `record_request` directly.

**`get_user_stats`:** Same pruning logic as `check_rate_limit` but no `record_request` call. This is a read-only method — it should not modify state beyond pruning expired timestamps (which is a housekeeping operation, not a state change that affects limit decisions).

**Sliding vs. fixed window:** The sliding window correctly measures the most recent `window_seconds` from the moment of each new request. A fixed window would reset at a clock boundary (e.g., top of every hour), which can be gamed: a user who exhausts their limit at 11:59 can immediately submit `max_requests` more at 12:00. The sliding window prevents this — there is no reset moment to exploit.

---

## Task 2 — Usage Log Analysis

The log has 141 requests from 2025-02-24T09:14:22Z to 2025-03-05T15:30:02Z (about 9 days). All timestamps are UTC.

### Suspicious customers

**cust_0042 — Rate abuse (scripted volume attack)**
- 75 requests across the 9-day log period, all in two overnight burst sessions — non-human cadence:
  - 2025-02-25 (Tuesday): 28 requests between 02:07 and 02:42 UTC
  - 2025-03-01 (Saturday): 47 requests between 02:51 and 03:47 UTC
- Timing pattern: 66 of the 73 gaps between requests inside the bursts are exactly 73 or 74 seconds (the rest range from 71 to 151 seconds), strongly suggesting an automated script. Every other customer's requests arrive between 09:00 and 17:00 UTC.
- Query lengths: 282–320 characters, nearly identical from request to request
- Guardrail triggered: 0 times — this customer is not probing for injection bypasses, just generating volume
- **Abuse type:** Financial DoS / cost abuse — systematic high-volume querying outside business hours while maximizing total spend
- **Why this is deliberate and not a retry loop:** Regular, repetitive traffic can also come from a retry or polling loop in a customer's integration. A broken loop tends to run whenever the integration runs. This customer's traffic arrives only in two short bursts, four days apart, both starting after 02:00 UTC, outside the hours when every other customer uses the API, and each burst stops in under an hour. No rate limit was in place during the log period, so the log can't show whether the bursts were sized to stay under a per-hour limit. The busiest rolling hour has 47 requests.

**cust_0099 — Token budget attack**
- Request count (9 requests) is well within normal range, so a simple per-request rate limit won't catch this customer
- Average query length: 5,266 characters (range 5,089–5,441) vs. overall average of 559 characters — nearly 10× the norm
- Very high cost per query — each request submits an oversized context, maximizing token consumption
- **Abuse type:** Token budget exhaustion / context stuffing — targeting cost rather than count

### Total cost and largest contributor

- Total estimated cost across the log period: **$3.35** (141 invocations at avg $0.024)
- **cust_0042:** $1.78 (53.1% of total) — 75 invocations at high volume
- **cust_0099:** $0.81 (24.3%) — 9 invocations at extreme per-query cost due to oversized inputs
- Top 2 customers together account for 77.4% of total spend

### Guardrail trigger rate

- **cust_0088:** 76.9% (10 of 13 requests triggered a guardrail), with query lengths of 178–231 characters. The pattern fits systematic injection probing, and this customer, not cust_0042, is the one to investigate for it. The harmless explanation is an integration that passes raw user content through without client-side filtering. To tell the two apart, check whether the content that triggers the guardrail varies in a systematic way.
- All other customers: 0% (no guardrail triggers in their 128 requests)
- cust_0042 has 0% guardrail trigger rate — scripted volume abuse and injection probing are distinct attack patterns; this customer is abusing cost, not trying to bypass content controls

---

## Task 3 — CloudWatch Alarm Configuration

`EXERCISE.md` asks for one alarm. The model answer is the per-customer query volume alarm below. The other two alarms are optional extras.

### Model answer — Per-customer hourly query volume

**Why this is the highest-priority alarm for Orion AI:** Orion's risk is one of 40 customers using up a $2,000 budget that all customers share, whether through a scripted integration, stolen credentials, or oversized traffic. The provider metric `Invocations` reports only account-wide totals, has no customer dimension, and counts model turns instead of billed queries. An account-wide alarm fires only after total usage is already abnormal, and it can't tell Orion which customer to contact or which credential to revoke. A per-customer alarm counts queries, which is the unit the contract and the bill use, and names the customer.

**Step 1 — What the application must log to CloudWatch Logs:**

The Orion application must write a structured log entry for each request that includes the customer ID in a consistent, parseable format:

```python
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Log this on every request the limiter allows, just before invoke_harness:
logger.info(json.dumps({
    "event": "bedrock_invocation",
    "user_id": user_id,  # the customer ID, e.g. "cust_0042"
    "session_id": session_id,  # the runtimeSessionId passed to invoke_harness; the invocation log doesn't record it
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "input_length_chars": len(user_input),
    "rate_limited": False
}))
```

**Step 2 — CloudWatch Logs Metric Filter to create a per-customer query count:**

In the CloudWatch console:
1. Navigate to **Log groups > /aws/orion-api/app-logs**
2. Click **Metric filters > Create metric filter**
3. **Filter pattern:**
   ```
   { $.event = "bedrock_invocation" }
   ```
4. **Metric name:** `BedrockInvocationsPerUser`
5. **Metric namespace:** `Orion AIAssist/PerUser`
6. **Metric value:** `1` (increment by 1 per matching log event)
7. **Dimensions:** `user_id` = `$.user_id` (this creates a separate time series per customer ID)

**Step 3 — Alarm on the per-customer metric:**

**Threshold and period:** more than 20 queries in 1 hour. The standard contract of 3,000 queries a month averages about 17 queries an hour if a customer uses it only during business hours (see Task 4). 20 is just above that, and below the recommended rate limit of 30 per hour, so the alarm fires before a customer reaches the limit.

```json
{
  "AlarmName": "orion-per-customer-hourly-volume",
  "Namespace": "Orion AIAssist/PerUser",
  "MetricName": "BedrockInvocationsPerUser",
  "Dimensions": [{"Name": "user_id", "Value": "cust_0042"}],
  "Statistic": "Sum",
  "Period": 3600,
  "EvaluationPeriods": 1,
  "Threshold": 20,
  "ComparisonOperator": "GreaterThanThreshold",
  "AlarmActions": ["arn:aws:sns:us-east-1:123456789012:orion-security-alerts"]
}
```

Note: A standard metric alarm watches one dimension value, so this alarm covers one customer. To cover every customer, either (a) create alarms for known high-risk customers identified from the usage log, or (b) build a Lambda that periodically queries the metric for all dimension values and creates or adjusts alarms. CloudWatch Contributor Insights rules and Metrics Insights query alarms may cover every customer with one alarm, but this course hasn't tested them.

---

### Optional: additional alarms

These alarms are worth having, but they don't answer the Task 3 question on their own, because neither one identifies the customer.

#### Daily spend threshold

**Metric:** `EstimatedCharges` (AWS Billing namespace) or, for tighter Bedrock-specific monitoring, create a custom metric by aggregating `InputTokenCount` and `OutputTokenCount` from `AWS/Bedrock` and computing cost.

**Practical approach using AWS Budgets (easier than CloudWatch for cost):**
- Service: AWS Budgets > Create budget > Cost budget
- Threshold: about $67/day (the $2,000 monthly budget ÷ 30 days), so the alert fires on any day that spends faster than the monthly budget allows
- Alert: notify `orion-security-alerts` SNS topic at 100% of daily threshold

**CloudWatch alarm format (using custom cost metric):**
```json
{
  "AlarmName": "orion-daily-bedrock-cost-threshold",
  "AlarmDescription": "Fires when estimated Bedrock spend exceeds $67 in a single day ($2,000 monthly budget / 30 days)",
  "Namespace": "Orion AIAssist/Cost",
  "MetricName": "EstimatedDailyBedrockCostUSD",
  "Statistic": "Sum",
  "Period": 86400,
  "EvaluationPeriods": 1,
  "Threshold": 67.0,
  "ComparisonOperator": "GreaterThanThreshold",
  "AlarmActions": ["arn:aws:sns:us-east-1:123456789012:orion-security-alerts"]
}
```

#### Invocation rate spike

**Metric:** `Invocations` from the `AWS/Bedrock` namespace, dimension `ModelId`. (There's no `InvocationCount` metric.)

**Threshold reasoning:** the budget supports about 83,333 queries a month (Task 4). Spread over a 30-day month (720 hours), that's about 116 queries an hour. Each harness query that uses a tool is at least 2 model turns, so the budget rate is at least about 230 turns an hour. 500 is about twice that.

```json
{
  "AlarmName": "orion-bedrock-invocation-spike",
  "AlarmDescription": "Real-time signal: Bedrock invocations exceeding 500 in any single hour. Budget rate is ~83,333 queries/month / 720 hours = ~116 queries/hour x at least 2 model turns per query = ~230 turns/hour. 500 = about 2x the budget rate.",
  "Namespace": "AWS/Bedrock",
  "MetricName": "Invocations",
  "Dimensions": [{"Name": "ModelId", "Value": "us.anthropic.claude-sonnet-4-5-20250929-v1:0"}],
  "Statistic": "Sum",
  "Period": 3600,
  "EvaluationPeriods": 1,
  "Threshold": 500,
  "ComparisonOperator": "GreaterThanThreshold",
  "AlarmActions": ["arn:aws:sns:us-east-1:123456789012:orion-security-alerts"]
}
```

---

## Task 4 — Rate Limit Calculation

**1. Total queries the budget supports:**
- $2,000/month ÷ $0.024/query = **83,333 queries/month**

**2. Cost of one customer scripting 1 query/second for an hour:**
- 1 query/second × 3,600 seconds = 3,600 queries
- 3,600 queries × $0.024 = **$86.40 for the hour**
- 3,600 queries is 1.2× the customer's entire monthly contract (3,000 queries), in one hour
- $86.40 is 4.3% of the monthly budget. At that rate, the $2,000 budget lasts $2,000 ÷ $86.40 = **about 23 hours**
- **How an hourly limit prevents this:** with a limit of 30 requests/hour, the first 30 requests are allowed (30 × $0.024 = $0.72) and the other 3,570 are denied before `invoke_harness` is called, so they cost nothing

**3. What the contract means per day and per hour:**
- 3,000 queries/month ÷ 30 days = **100 queries/day**
- 100 queries/day ÷ 24 hours = **about 4.2 queries/hour** if the customer's integration runs around the clock
- If the customer uses the API only during business hours: 3,000 ÷ 22 workdays = about 136 queries/workday, and 136 ÷ 8 hours = **about 17 queries/hour**

**Per-hour rate limit recommendation: 30 requests/hour per customer**
- 30/hour is about 1.75× the busiest average use of the contract (17/hour during business hours), and about 7× the around-the-clock average (4.2/hour)
- Leaves headroom for legitimate bursts, such as a batch job or a busy morning, without blocking a customer who is inside their contract. At the cap, a customer can still use the full 3,000-query contract in 100 hours.
- Caps the cost of one customer at 30 × $0.024 = $0.72/hour, or 720 queries × $0.024 = $17.28/day
- Against the log: cust_0042's second burst (47 requests in 56 minutes) would have had 17 requests denied. Its first burst (28 requests in 35 minutes) stays under the limit, which is why the per-customer alarm and a daily limit also matter.

**Per-day limit recommendation (optional): 300 requests/day per customer**
- 300/day = 3× the contract's daily average (100/day)
- A script that stays just under the hourly limit all day would send 720 queries; the daily limit stops it at 300 ($7.20/day)
- Per-hour + per-day together close the gap that either alone would leave open

**Budget check:** 40 customers × 3,000 queries = 120,000 queries/month, which is more than the 83,333 the budget supports. If every customer used their full contract, Orion would spend 120,000 × $0.024 = $2,880. Per-customer limits don't fix that gap. It's a pricing and contract decision to raise with leadership.

---

## Task 5 — Rate Limiting as Blast Radius Reduction

If an enterprise customer's Orion API credentials are stolen and an attacker uses them to flood the API, a per-customer rate limiter constrains the attack in three ways: (1) **Cost impact** is capped — with no limit, a script at 1 query/second costs 3,600 × $0.024 = $86.40/hour and spends the whole $2,000 monthly budget in about 23 hours (faster if the attacker runs several scripts at once), while at 30 requests/hour the same credentials cost at most $0.72/hour, or $17.28/day ($7.20/day with the 300/day limit), and the other 39 customers keep their share of the budget; (2) **Data exposure volume** is bounded — the attacker gets at most 30 responses per hour instead of 3,600, reducing what they can extract from the knowledge base before detection; (3) **Detection window** works in Orion's favor — without a limit, detection depends on the account-wide `Invocations` alarm or a billing alarm that lags by hours, and every hour of lag costs another $86.40; with the limit, the per-customer alarm (more than 20 queries in an hour) fires within the first hour and names the customer, and if the application also logs denied requests, a sudden run of denials for one customer is a second signal, so the security team can revoke the credential while the loss is still a few dollars. Without rate limiting, all three of these bounds disappear.

---

## Console Walkthrough: CloudWatch Metrics and Alarms for Bedrock

### 1. View Bedrock invocation metrics in CloudWatch

1. Navigate to **AWS Console > Services > CloudWatch**
2. In the left sidebar, click **Metrics > All metrics**
3. In the search box, type `Bedrock` and press Enter
4. Click the **AWS/Bedrock** namespace
5. Open the metrics grouped by the `ModelId` dimension
6. Find `Invocations` for `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (the model ID your harness saved; `GetHarness` shows it)
7. Check the box next to the metric and click **Add to graph**
8. Adjust the time range to see your usage pattern

`Invocations` counts model turns, not queries. A harness query that uses a tool produces at least two, and a query the knowledge base can't answer can produce many more. The same dimension also has `InvocationLatency`, `InvocationClientErrors`, `InputTokenCount`, `OutputTokenCount`, and `EstimatedTPMQuotaUsage`. Don't use the harness **Observability** panel for this: its data can be delayed up to 60 minutes.

### 2. Create a CloudWatch alarm on invocations

1. From the metrics view, with `Invocations` selected, click **Create alarm**
   (Alternatively: CloudWatch > Alarms > Create alarm > Select metric)
2. On the **Specify metric and conditions** page:
   - Confirm the metric is `AWS/Bedrock > Invocations` for your model
   - **Statistic:** Sum
   - **Period:** 1 hour
3. Under **Conditions**:
   - **Threshold type:** Static
   - **Whenever Invocations is:** Greater than
   - **Value:** 500
4. Click **Next**
5. Under **Notification**:
   - **In alarm** action: Send notification to SNS topic `orion-security-alerts`
6. Click **Next**, give the alarm a name (e.g., `orion-invocation-spike`), click **Create alarm**

### 3. Create a CloudWatch Logs Metric Filter

1. Navigate to **CloudWatch > Log groups**
2. Click `/aws/orion-api/app-logs`
3. Click the **Metric filters** tab
4. Click **Create metric filter**
5. **Filter pattern:** `{ $.event = "bedrock_invocation" }`
6. Click **Test pattern** (optional) — paste a sample log line to confirm the filter matches
7. Click **Next**
8. **Filter name:** `BedrockInvocationsPerUser`
9. **Metric namespace:** `Orion AIAssist/PerUser`
10. **Metric name:** `BedrockInvocationsPerUser`
11. **Metric value:** `1`
12. **Dimensions:** click **Add dimension**, Key = `user_id`, Value = `$.user_id`
13. Click **Next > Create metric filter**
14. The metric filter is now active — new matching log events will generate the `BedrockInvocationsPerUser` metric with a dimension per customer ID

### 4. Set up AWS Budgets as a secondary cost control

> AWS Budgets access wasn't checked in the Udacity lab. Treat this section as a reference for your own account.

1. Navigate to **AWS Console > Services > AWS Budgets** (search "Budgets")
2. Click **Create budget**
3. Choose **Cost budget** > **Customize**
4. **Budget name:** `orion-api-monthly`
5. **Period:** Monthly
6. **Budget amount:** $2,000
7. Under **Budget scope**, filter by service: **Amazon Bedrock** (to isolate Bedrock costs from other AWS services)
8. Click **Next**
9. Under **Configure alerts**:
   - Add an alert at **80% of budgeted amount** ($1,600) — early warning
   - Add an alert at **100% of budgeted amount** ($2,000) — budget reached
   - Both alerts: notify via email to the finance/security team
10. Click through to **Create budget**
