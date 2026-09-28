# Demo: Preventing API Abuse on a Bedrock-Powered Application

**Estimated Time:** 10 minutes

---

> **Note:** This demo uses **Aria**, the internal assistant of **Vantage Technologies**, running on an Amazon Bedrock AgentCore harness (harness → AgentCore Gateway → Managed Knowledge Base, Claude Sonnet 4.5), built on the **Build Aria: Set Up the Demo Environment** page in Lesson 1 (the same steps as `skill-pair-00-bedrock-setup/WALKTHROUGH.md`), with model invocation logging on. Employees reach Aria through a Streamlit app. The goal is to show the concept working in a live environment before you apply it to the scenario in `EXERCISE.md`. Your capstone project, Northstar Assist, uses the same setup.

## Scenario

Aria has no rate limiting. Every signed-in employee can send unlimited questions through the Streamlit app, as fast as they like.

A disgruntled employee notices and writes a Python script that loops 1,000 questions in about 20 minutes, in the middle of a busy workday. Other employees wait 30 seconds for answers, the on-call engineer is paged because the Streamlit app keeps timing out, and at month end the AWS bill shows a $400 Bedrock line item that was budgeted at $60.

The system stayed up the whole time. That's a financial denial of service: it still runs, but Vantage can no longer afford to run it.

---

## Tools Used

- AWS Console (Service Quotas, CloudWatch, Amazon Bedrock AgentCore)
- Python with boto3 (`boto3>=1.43.52`)

---

## Key Insights to Surface During the Demo

**Service quotas aren't application rate limiting.**
Amazon Bedrock applies requests-per-minute and tokens quotas per account, per model. They protect AWS infrastructure. They don't stop one employee from spending most of the budget in an afternoon. Per-user limits are yours to build.

**One question is several model calls.**
A harness question that uses the knowledge base produces at least two model invocations: a turn that calls the tool and a turn that writes the answer. When the answer isn't in the knowledge base, the model can keep searching. Each call costs cents depending on context length, so cost per question, not throughput, is the main denial of service risk.

**The app is where the user lives.**
The model invocation log records the harness role plus a session ID, with no user. The model invocation log doesn't record the `runtimeSessionId` or `runtimeUserId` your app sends. The session ID in `identity.arn` is a different value that the harness generates. To name the user behind a request, your app must log the user and `runtimeSessionId` itself. The Streamlit app knows who signed in, so the limiter runs there, keyed on the user ID, before `invoke_harness`.

**Alarms are the safety net.**
An alarm on the model's `Invocations` metric fires within the hour. A billing alarm catches runaway spend, but billing data lags by hours. Neither needs application changes, and neither tells you who did it.

**Rate limiting belongs in the threat model under Denial of Service.**
Blocking availability is one threat. Generating unbounded cost is another. Both need mitigations.

---

## Demo Steps

### Step 1: Show the Amazon Bedrock service quotas

Open **Service Quotas > AWS services > Amazon Bedrock** and search for `Sonnet 4.5`. You'll see rows such as:

- "Cross-region model inference requests per minute for Anthropic Claude Sonnet 4.5 V1"
- "Global cross-region model inference tokens per day…"

Point out: these quotas apply to the whole account for that model and inference type, not to individual users. A script that uses up the per-minute quota throttles every other Aria user at the AWS level, before any application limit fires. A simple loop won't get there: in the lab account, the cross-region requests-per-minute quota for Sonnet 4.5 was 10,000. The point is that the quota is shared by the whole account.

Ask students: "What would you need to know about your users to set a sane per-user limit?"
(Expected answer: number of users, expected questions per user per day, peak concurrency.)

---

### Step 2: Show what makes one question expensive

Open the harness details page in the Amazon Bedrock AgentCore console, or run `GetHarness`. Point out the defaults:

- `maxIterations`: **75**
- `timeoutSeconds`: **3600**

These caps bound how long one request can run and how many tool rounds it can take. In the lab, a question whose answer had been removed from the knowledge base ("What discount can a sales engineer approve without escalation?") drove **9 Retrieve calls** before Aria answered. Another question drove 6. Every tool round is another model invocation. Review the harness's invocation limits and set them to what a real question needs.

Two client-side cost multipliers came up in the lab too:

- A call with no explicit read timeout hung for about **2.7 hours**.
- A retried call can replay into the **same session**, adding model calls (and it changed the answer, because the model replied from history).

Set explicit timeouts, turn off silent SDK retries, and use a fresh session ID if you retry.

---

### Step 3: Show the safety-net alarms

**Operational alarm (build this one).** First create the SNS topic `vantage-aria-security-alerts` (SNS > Topics > Create topic > Standard) and subscribe your email address. If you created it in Lesson 9, reuse it. Aria's alarm is `VantageAria-HighInvocationVolume`:

| Setting | Value |
|---|---|
| Namespace / metric | `AWS/Bedrock` / `Invocations` |
| Dimension | `ModelId` = `us.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| Statistic / period | Sum / 1 hour |
| Condition | > 50 |
| Action | SNS topic `vantage-aria-security-alerts` |

```python
import boto3

sns = boto3.client("sns", region_name="us-east-1")
# Returns the topic's ARN, including when the topic already exists
topic_arn = sns.create_topic(Name="vantage-aria-security-alerts")["TopicArn"]

cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")

cloudwatch.put_metric_alarm(
    AlarmName="VantageAria-HighInvocationVolume",
    AlarmDescription="Model invocations for Aria's model above normal hourly volume",
    Namespace="AWS/Bedrock",
    MetricName="Invocations",
    Dimensions=[{"Name": "ModelId", "Value": "us.anthropic.claude-sonnet-4-5-20250929-v1:0"}],
    Statistic="Sum",
    Period=3600,
    EvaluationPeriods=1,
    Threshold=50,
    ComparisonOperator="GreaterThanThreshold",
    AlarmActions=[topic_arn],
)
```

The metric is `Invocations`. There's no `InvocationCount`. It counts model turns, not questions, so size the threshold from turns per question. Right after you create the alarm it shows `INSUFFICIENT_DATA` until traffic arrives. Use the model ID your harness saved (`GetHarness` shows it). `AWS/Bedrock` also has `Invocations` series for the global inference profile, such as `global.anthropic.claude-sonnet-4-5…`. An alarm on one profile's `ModelId` never gets data from traffic that uses the other.

Other `AWS/Bedrock` metrics with the `ModelId` dimension: `InvocationLatency`, `InvocationClientErrors`, `InputTokenCount`, `OutputTokenCount`, and `EstimatedTPMQuotaUsage`.

**Billing alarm (describe only).** A billing alarm on `EstimatedCharges` in `AWS/Billing` catches runaway spend before month end. Its weakness is lag: billing data arrives hours late, so it can't stop a fast event. The rate limiter is the real-time control. Alarms are the safety net.

---

### Step 4: Show the sliding window rate limiter

Open `starter/rate_limiter.py` and walk through `RateLimiter`.

The sliding window algorithm:
1. Each time a user makes a request, record the current timestamp for that user.
2. Before allowing a request, discard timestamps older than the window.
3. Count what's left. If the count is at or above the limit, deny the request.
4. Otherwise, allow it and append the new timestamp.

The window slides forward in time, so bursts are measured over a rolling period. A fixed clock window can be gamed: 20 requests at 11:59 and 20 more at 12:01.

Run `python starter/rate_limiter.py`. With `max_requests=3`, a user's first five calls come back ALLOWED, ALLOWED, ALLOWED, DENIED, DENIED. A second user is unaffected, and the first user is allowed again once the window passes.

---

### Step 5: Put the check before `invoke_harness`

In the Streamlit app, the limiter runs first. A rejected request never reaches the model, so it costs nothing.

```python
import json
import logging
import os
import uuid

import boto3
import streamlit as st
from botocore.config import Config

from rate_limiter import RateLimiter

HARNESS_ARN = os.environ["AGENTCORE_HARNESS_ARN"]
REGION = os.environ.get("AWS_REGION", "us-east-1")
logger = logging.getLogger("aria")


@st.cache_resource
def get_limiter():
    # Shared by every browser session in this app process, so a new tab doesn't reset the count
    return RateLimiter(window_seconds=3600, max_requests=20)


@st.cache_resource
def get_client():
    # Explicit timeouts, and no silent SDK retries into the same session
    return boto3.client(
        "bedrock-agentcore",
        region_name=REGION,
        config=Config(connect_timeout=10, read_timeout=120, retries={"total_max_attempts": 1}),
    )


limiter = get_limiter()
client = get_client()
user_id = st.session_state.get("user_id", "anonymous")  # set by your login step

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if prompt := st.chat_input("Ask Aria a question..."):
    # 1. Rate limit first: a rejected request never reaches the model
    if not limiter.check_rate_limit(user_id):
        st.error("You've reached the hourly request limit. Please wait before submitting another query.")
        st.stop()

    # 2. Log who asked. The invocation log won't record this user or session ID
    logger.info(json.dumps({"event": "harness_invocation", "user_id": user_id,
                            "session_id": st.session_state.session_id}))

    # 3. Only now call the harness
    response = client.invoke_harness(
        harnessArn=HARNESS_ARN,
        runtimeSessionId=st.session_state.session_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )
    answer = ""
    for event in response["stream"]:
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"]["delta"]
            if "text" in delta:
                answer += delta["text"]
    st.markdown(answer)
```

Point out three things:
- The user ID comes from the app. The model invocation log doesn't record the `runtimeSessionId` or `runtimeUserId` your app sends, so the app log is the only record of who asked.
- The limiter lives in `st.cache_resource`, not `st.session_state`. Per-session state resets when the user opens a new tab.
- The limiter only guards the app. Anyone with `bedrock-agentcore:InvokeHarness` and `bedrock-agentcore:InvokeAgentRuntime` on the harness can call it directly, so only the app's role should hold them (lesson 7).

---

### Step 6: Watch a capped loop hit the limit

Run a small loop from the `starter/` folder. The loop reads `AGENTCORE_HARNESS_ARN` and `AWS_REGION`, which `setup_aws.py` sets (`WALKTHROUGH.md` Step 8). Keep it capped: every allowed call is billed.

```python
import os
import time
import uuid

import boto3
from botocore.config import Config

from rate_limiter import RateLimiter

client = boto3.client(
    "bedrock-agentcore",
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
    config=Config(connect_timeout=10, read_timeout=120, retries={"total_max_attempts": 1}),
)
limiter = RateLimiter(window_seconds=3600, max_requests=3)

QUESTION = "What is Vantage's remote work policy?"
ATTEMPTS = 5  # keep this small: every allowed call is billed

for i in range(1, ATTEMPTS + 1):
    if not limiter.check_rate_limit("demo-user"):
        print(f"Request {i}: DENIED by the rate limiter, harness not called")
        continue

    start = time.time()
    response = client.invoke_harness(
        harnessArn=os.environ["AGENTCORE_HARNESS_ARN"],
        runtimeSessionId=str(uuid.uuid4()),  # fresh session per call
        messages=[{"role": "user", "content": [{"text": QUESTION}]}],
    )
    answer = ""
    for event in response["stream"]:
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"]["delta"]
            if "text" in delta:
                answer += delta["text"]
    print(f"Request {i}: ALLOWED, {len(answer)} characters in {time.time() - start:.1f} s")
```

Requests 1–3 reach Aria. Requests 4 and 5 are denied and never reach the model.

Then find the traffic. Don't use the harness **Observability** panel for this: its data can be delayed up to 60 minutes. Use the `Invocations` metric, and run the per-session query from lesson 9 on `/aws/bedrock/vantage-aria/invocations`:

```
filter operation = "ConverseStream"
| parse identity.arn "/BedrockAgentCore-*" as session_id
| stats count(*) as modelTurns, sum(input.inputTokenCount) as inTokens, sum(output.outputTokenCount) as outTokens by session_id
| sort modelTurns desc
```

Expect three sessions, each with at least two model turns. The query gives you sessions, not users, and you can't join them to the app log from Step 5. The session ID in `identity.arn` is a different value that the harness generates, not the `runtimeSessionId` you sent. In the lab, none of the three matched. To name the user behind a request, your app must log the user and `runtimeSessionId` itself.

**What about the gateway's rate limits?** AgentCore Gateway has a **Rate limits** feature (`CreateGatewayRateLimit`), keyed on dimensions such as `targetName`, `toolName`, `qualifiedModelId`, `$.context.iam.principal`, or a JWT claim, with request, token, or connection limits per second or minute. In the lab, active limits of 2 requests per minute on `targetName` and on `toolName` did **not** throttle 5 back-to-back harness knowledge base calls. Treat gateway rate limits as a managed option to test in your own environment, not as your control.

---

### Step 7: Discuss the rate limit tradeoff

Ask: "If 150 employees each need about 10 questions per workday, and the workday is 8 hours, what's the expected average rate?"

The math:
- 150 employees × 10 questions = 1,500 questions/day
- 1,500 questions ÷ 480 minutes = about 3 questions/minute
- Peak might be 3–5× average: about 9–15 questions/minute

A per-user limit of 20 requests per hour is generous for normal use and stops the 1,000-question script within its first 20 requests.

The tradeoff: a power user in a focused research session might want 30–40 questions in an hour. A limit of 20 blocks them. A limit of 50 stops the script less aggressively. There's no universal answer. Calibrate against real usage data and revisit it. And remember that at the metric level each question is at least two model invocations.

---

## Key Takeaway

For a system like Aria, denial of service is often financial: one unconstrained user can run up a $400 bill without ever hitting an AWS service quota. The application-level rate limiter, placed before `invoke_harness` and keyed on the user, is the control that stops it. Harness invocation limits, client timeouts, and the `Invocations` alarm keep a single request or a misconfigured limiter from becoming the next surprise.
