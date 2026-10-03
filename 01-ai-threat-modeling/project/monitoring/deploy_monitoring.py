"""Deploy Northstar Assist monitoring: metric filters, a Contributor Insights rule, alarms,
an SNS topic and saved Logs Insights queries. Safe to re-run (every call is an upsert).

Usage: python deploy_monitoring.py [--email you@example.com]
"""
import json
import os
import sys

import boto3
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, "..", "..", "..", ".env"), override=True)
s = boto3.session.Session(region_name="us-east-1")
logs, cw, sns = s.client("logs"), s.client("cloudwatch"), s.client("sns")

ACCOUNT = "911470903119"
HARNESS_ID = "NorthstarAssist-yH4PMorNwm"
NS = "NorthstarAssist"
# Model invocation logging is configured once per account; read its destination instead of hard-coding it.
INV = s.client("bedrock").get_model_invocation_logging_configuration()["loggingConfig"]["cloudWatchConfig"]["logGroupName"]
RUNTIME = "/aws/bedrock-agentcore/runtimes/harness_NorthstarAssist-4tSgy4Clrq-DEFAULT"
KB_LOG = "/aws/vendedlogs/bedrock/knowledge-base/APPLICATION_LOGS/ZCAWWBRBXU"
PATTERNS = json.load(open(os.path.join(HERE, "metric-filter-patterns.json")))

# ---------------------------------------------------------------- SNS topic
topic = sns.create_topic(Name="northstar-assist-security-alerts")["TopicArn"]
if "--email" in sys.argv:
    sns.subscribe(TopicArn=topic, Protocol="email", Endpoint=sys.argv[sys.argv.index("--email") + 1])
print("SNS topic:", topic)

# ---------------------------------------------------------------- metric filters
VALUE = {"InputTokens": "$.input.inputTokenCount", "OutputTokens": "$.output.outputTokenCount"}
filters = dict(PATTERNS)
filters["InputTokens"] = PATTERNS["ModelCalls"]
filters["OutputTokens"] = PATTERNS["ModelCalls"]
for name, pattern in filters.items():
    logs.put_metric_filter(
        logGroupName=INV, filterName=f"northstar-assist-{name}", filterPattern=pattern,
        metricTransformations=[{"metricName": name, "metricNamespace": NS,
                                "metricValue": VALUE.get(name, "1"), "unit": "Count"}])
print("metric filters:", len(filters))

# ---------------------------------------------------------------- Contributor Insights: prompt attacks per session
RULE = "northstar-assist-prompt-attacks-by-session"
IA = "$.output.outputBodyJson.trace.guardrail.inputAssessment.bzgydako86r9.contentPolicy.filters[0].type"
rule_definition = json.dumps({
    "Schema": {"Name": "CloudWatchLogRule", "Version": 1},
    "LogGroupNames": [INV],
    "LogFormat": "JSON",
    "AggregateOn": "Count",
    "Contribution": {
        "Keys": ["$.identity.arn"],
        "Filters": [
            {"Match": "$.identity.arn", "StartsWith": [
                f"arn:aws:sts::{ACCOUNT}:assumed-role/AmazonBedrockAgentCoreHarnessDefaultServiceRole-p0869/"]},
            {"Match": IA, "In": ["PROMPT_ATTACK"]},
        ],
    },
})
# Re-putting a rule restarts its processing, so only write it when the definition changed.
current = {r["Name"]: r["Definition"] for r in cw.describe_insight_rules()["InsightRules"]}
if json.loads(current.get(RULE, "{}")) != json.loads(rule_definition):
    cw.put_insight_rule(RuleName=RULE, RuleState="ENABLED", RuleDefinition=rule_definition)
print("contributor insights rule:", RULE)

# ---------------------------------------------------------------- alarms
def metric(name, stat="Sum"):
    return {"Namespace": NS, "MetricName": name, "Statistic": stat}


def alarm(name, desc, threshold, period, evals, spec):
    spec = dict(spec)
    op = spec.pop("ComparisonOperator", "GreaterThanThreshold")
    if "Metrics" not in spec:
        spec["Period"] = period
    cw.put_metric_alarm(AlarmName=f"northstar-assist-{name}", AlarmDescription=desc, Threshold=threshold,
                        ComparisonOperator=op, EvaluationPeriods=evals, DatapointsToAlarm=evals,
                        TreatMissingData="notBreaching", AlarmActions=[topic], OKActions=[topic], **spec)


runtime_dims = [{"Name": "Name", "Value": "harness_NorthstarAssist::DEFAULT"}, {"Name": "Operation", "Value": "InvokeAgentRuntime"}, {"Name": "Resource", "Value": f"arn:aws:bedrock-agentcore:us-east-1:{ACCOUNT}:runtime/harness_NorthstarAssist-4tSgy4Clrq"}]
tool_dims = [{"Name": "Method", "Value": "tools/call"}, {"Name": "Name", "Value": "northstar-kb___Retrieve"}, {"Name": "Operation", "Value": "InvokeGateway"}, {"Name": "Protocol", "Value": "MCP"}]
ALARMS = [
    ("prompt-attack-single-session",
     "SEV-2: more than 5 PROMPT_ATTACK blocks in 1 hour from a single harness session. Run playbook PB-01.",
     5, None, 1, {"Metrics": [{"Id": "top", "ReturnData": True, "Period": 3600,
                               "Expression": f"INSIGHT_RULE_METRIC('{RULE}', 'MaxContributorValue')",
                               "Label": "Max PROMPT_ATTACK blocks from one session"}]}),
    ("prompt-attack-burst",
     "SEV-2: more than 10 PROMPT_ATTACK blocks across all sessions in 15 minutes (distributed probing). Run PB-01.",
     10, 900, 1, metric("PromptAttackBlocked")),
    ("guardrail-missing",
     "SEV-1: a harness model call ran WITHOUT the Northstar guardrail (per-call override bypass). Run PB-01 step C3.",
     0, 300, 1, metric("GuardrailMissing")),
    ("output-blocked",
     "SEV-3: more than 5 answers withheld by the output guardrail in 1 hour (PII or restricted content being drawn out).",
     5, 3600, 1, metric("OutputBlocked")),
    ("topic-blocks",
     "SEV-3: more than 10 denied-topic blocks on input in 1 hour (misuse or bulk-data harvesting).",
     10, 3600, 1, metric("TopicBlockedInput")),
    ("output-token-spike",
     "SEV-3: a single model call produced more than 1,000 output tokens (baseline answer 161 avg, 207 max).",
     1000, 300, 1, metric("OutputTokens", "Maximum")),
    ("input-token-spike",
     "SEV-3: a single model call received more than 20,000 input tokens (baseline max 7,925): context stuffing or a runaway loop.",
     20000, 300, 1, metric("InputTokens", "Maximum")),
    ("answers-without-retrieval",
     "SEV-3: fewer than 0.8 knowledge-base retrievals per answer over 1 hour (min 10 answers): answers not grounded in the KB.",
     0.8, None, 1, {"ComparisonOperator": "LessThanThreshold", "Metrics": [
         {"Id": "r", "MetricStat": {"Metric": {"Namespace": NS, "MetricName": "KbRetrievals"}, "Period": 3600, "Stat": "Sum"}, "ReturnData": False},
         {"Id": "a", "MetricStat": {"Metric": {"Namespace": NS, "MetricName": "Answers"}, "Period": 3600, "Stat": "Sum"}, "ReturnData": False},
         {"Id": "ratio", "Expression": "IF(FILL(a, 0) >= 10, FILL(r, 0) / a, 1)", "Label": "Retrievals per answer", "ReturnData": True}]}),
    ("model-call-volume",
     "SEV-3: more than 600 harness model calls in 1 hour (cost or automated abuse; ~2-3 calls per question).",
     600, 3600, 1, metric("ModelCalls")),
    ("harness-errors",
     "SEV-3: more than 5 harness system or user errors in 15 minutes.",
     5, None, 1, {"Metrics": [
         {"Id": "se", "MetricStat": {"Metric": {"Namespace": "AWS/Bedrock-AgentCore", "MetricName": "SystemErrors", "Dimensions": runtime_dims}, "Period": 900, "Stat": "Sum"}, "ReturnData": False},
         {"Id": "ue", "MetricStat": {"Metric": {"Namespace": "AWS/Bedrock-AgentCore", "MetricName": "UserErrors", "Dimensions": runtime_dims}, "Period": 900, "Stat": "Sum"}, "ReturnData": False},
         {"Id": "errors", "Expression": "FILL(se, 0) + FILL(ue, 0)", "Label": "Harness errors", "ReturnData": True}]}),
    ("retrieval-tool-errors",
     "SEV-3: the knowledge-base Retrieve tool returned errors 3+ times in 15 minutes (retrieval failing; answers may be ungrounded).",
     2, None, 1, {"Metrics": [
         {"Id": "se", "MetricStat": {"Metric": {"Namespace": "AWS/Bedrock-AgentCore", "MetricName": "SystemErrors", "Dimensions": tool_dims}, "Period": 900, "Stat": "Sum"}, "ReturnData": False},
         {"Id": "ue", "MetricStat": {"Metric": {"Namespace": "AWS/Bedrock-AgentCore", "MetricName": "UserErrors", "Dimensions": tool_dims}, "Period": 900, "Stat": "Sum"}, "ReturnData": False},
         {"Id": "errors", "Expression": "FILL(se, 0) + FILL(ue, 0)", "Label": "Retrieve tool errors", "ReturnData": True}]}),
]
for name, desc, threshold, period, evals, spec in ALARMS:
    alarm(name, desc, threshold, period, evals, spec)
print("alarms:", len(ALARMS))

# ---------------------------------------------------------------- saved Logs Insights queries
H = "identity.arn like /HarnessDefaultServiceRole-p0869/"
QUERIES = {
    "01 Prompt-attack blocks by session": (INV, f"""filter {H} and @message like /PROMPT_ATTACK/
| parse identity.arn "/BedrockAgentCore-*" as session
| stats count(*) as prompt_attacks, min(@timestamp) as first_seen, max(@timestamp) as last_seen by session
| sort prompt_attacks desc"""),
    "02 Session timeline (edit SESSION_UUID)": (INV, f"""filter identity.arn like /BedrockAgentCore-SESSION_UUID/
| fields @timestamp, output.outputBodyJson.stopReason as stop, input.inputTokenCount as in_tok,
  output.outputTokenCount as out_tok, inferenceRegion, output.outputBodyJson.output.message.content.0.text as answer
| sort @timestamp asc"""),
    "03 Guardrail interventions by policy": (INV, f"""filter {H} and output.outputBodyJson.stopReason = "guardrail_intervened"
| parse identity.arn "/BedrockAgentCore-*" as session
| fields strcontains(@message, "PROMPT_ATTACK") as is_pa, strcontains(@message, "topicPolicy\\":{{\\"topics") as is_topic,
  strcontains(@message, "outputAssessments") as is_output, strcontains(@message, "\\"BLOCKED\\"") as is_block
| stats count(*) as interventions, sum(is_pa) as prompt_attacks, sum(is_topic) as topic_hits,
  sum(is_output) as output_side, sum(is_block) as blocks, count_distinct(session) as sessions by bin(1h)"""),
    "04 Sessions that answered without KB retrieval": (INV, f"""filter {H} and operation = "ConverseStream"
| parse identity.arn "/BedrockAgentCore-*" as session
| fields strcontains(output.outputBodyJson.stopReason, "tool_use") as tool_call,
  strcontains(output.outputBodyJson.stopReason, "end_turn") as answer
| stats sum(tool_call) as tool_calls, sum(answer) as answers, min(@timestamp) as first_seen by session
| filter answers > 0 and tool_calls = 0"""),
    "05 Zero-chunk or failed retrievals": (INV, f"""filter {H} and (@message like /retrievalResults\\\\":\\[\\]/ or @message like /"status": ?"error"/)
| parse identity.arn "/BedrockAgentCore-*" as session
| display @timestamp, session, output.outputBodyJson.stopReason
| sort @timestamp desc"""),
    "06 Token outliers vs session median": (INV, f"""filter {H} and operation = "ConverseStream"
| parse identity.arn "/BedrockAgentCore-*" as session
| stats count(*) as calls, pct(output.outputTokenCount, 50) as median_out, max(output.outputTokenCount) as max_out,
  max(input.inputTokenCount) as max_in by session
| filter max_out > 1000 or max_in > 20000 or (calls >= 3 and max_out > 3 * median_out)
| sort max_out desc"""),
    "07 Model calls without the guardrail (bypass)": (INV, f"""filter {H} and operation = "ConverseStream" and @message not like /appliedGuardrailDetails/
| parse identity.arn "/BedrockAgentCore-*" as session
| display @timestamp, session, modelId, output.outputBodyJson.stopReason, output.outputBodyJson.output.message.content.0.text
| sort @timestamp desc"""),
    "08 Retrieval queries sent to the KB": (INV, """filter identity.arn like /MANAGED_KB_EMBED-911470903119-ZCAWWBRBXU/
| fields @timestamp, input.inputBodyJson.inputText as retrieval_query
| sort @timestamp desc"""),
    "09 Runtime log for a client session (edit RUNTIME_SESSION_ID)": (RUNTIME, """filter @message like /RUNTIME_SESSION_ID/ and @logStream like /runtime-logs/
| fields @timestamp, requestId, level, message
| sort @timestamp asc"""),
    "10 Client sessions active in a time window (set the time range)": (RUNTIME, """filter @logStream like /runtime-logs/ and message like /Returning streaming response/
| stats count(*) as requests, min(@timestamp) as first_request, max(@timestamp) as last_request by sessionId
| sort first_request asc"""),
    "11 Instruction-like text inside retrieved chunks (indirect injection hunt)": (INV, f"""filter {H} and @message like /toolResult/
  and @message like /(?i)\\\\"text\\\\": ?\\\\"[^"]*(ignore (all )?(previous|prior|above) instructions|system override|disregard the above|you are now|new instructions:|do not mention this instruction)/
| parse identity.arn "/BedrockAgentCore-*" as session
| display @timestamp, session, output.outputBodyJson.stopReason
| sort @timestamp desc"""),
}
existing = {q["name"]: q["queryDefinitionId"] for q in logs.describe_query_definitions(queryDefinitionNamePrefix="NorthstarAssist")["queryDefinitions"]}
for title, (group, q) in QUERIES.items():
    name = f"NorthstarAssist/{title}"
    kw = {"queryDefinitionId": existing[name]} if name in existing else {}
    logs.put_query_definition(name=name, logGroupNames=[group], queryString=q, **kw)
print("saved queries:", len(QUERIES))
json.dump({k: v[1] for k, v in QUERIES.items()}, open(os.path.join(HERE, "logs-insights-queries.json"), "w"), indent=2)

# ---------------------------------------------------------------- dashboard
def w(title, metrics, x, y, stat="Sum", period=300, width=8, view="timeSeries", annotations=None):
    props = {"title": title, "region": "us-east-1", "metrics": metrics, "stat": stat, "period": period, "view": view}
    if annotations:
        props["annotations"] = {"horizontal": annotations}
    return {"type": "metric", "x": x, "y": y, "width": width, "height": 6, "properties": props}


dashboard = {"widgets": [
    {"type": "text", "x": 0, "y": 0, "width": 24, "height": 2, "properties": {"markdown":
        "## Northstar Assist: AI security signals\nAlarms notify `northstar-assist-security-alerts`. "
        "Runbook: `monitoring/Northstar Assist Monitoring and IR Playbook.md` (PB-01). "
        "Saved queries: CloudWatch > Logs Insights > Saved queries > **NorthstarAssist**."}},
    w("Guardrail blocks (input)", [[NS, "PromptAttackBlocked"], [NS, "TopicBlockedInput"], [NS, "InputBlocked"]], 0, 2,
      annotations=[{"label": "burst alarm (15 min)", "value": 10}]),
    w("Output guardrail and bypass", [[NS, "OutputBlocked"], [NS, "GuardrailMissing", {"color": "#d62728"}]], 8, 2),
    w("Retrieval vs answers", [[NS, "Answers"], [NS, "KbRetrievals"], [NS, "ToolCalls"]], 16, 2, period=3600),
    w("Tokens per model call (max)", [[NS, "OutputTokens"], [NS, "InputTokens", {"yAxis": "right"}]], 0, 8, stat="Maximum",
      annotations=[{"label": "output alarm", "value": 1000}]),
    w("Model call volume", [[NS, "ModelCalls"]], 8, 8, period=3600, annotations=[{"label": "hourly alarm", "value": 600}]),
    w("Harness runtime errors and throttles", [
        ["AWS/Bedrock-AgentCore", m, "Name", "harness_NorthstarAssist::DEFAULT", "Operation", "InvokeAgentRuntime",
         "Resource", f"arn:aws:bedrock-agentcore:us-east-1:{ACCOUNT}:runtime/harness_NorthstarAssist-4tSgy4Clrq"]
        for m in ("SystemErrors", "UserErrors", "Throttles")], 16, 8),
    {"type": "metric", "x": 0, "y": 14, "width": 24, "height": 6, "properties": {
        "title": "Top sessions by PROMPT_ATTACK blocks (Contributor Insights)", "region": "us-east-1",
        "insightRule": {"maxContributorCount": 10, "orderBy": "Sum", "ruleName": RULE}, "period": 300,
        "view": "timeSeries", "legend": {"position": "right"}}},
    {"type": "alarm", "x": 0, "y": 20, "width": 24, "height": 4, "properties": {
        "title": "Alarm status", "alarms": [f"arn:aws:cloudwatch:us-east-1:{ACCOUNT}:alarm:northstar-assist-{a[0]}" for a in ALARMS]}},
]}
cw.put_dashboard(DashboardName="NorthstarAssist-Security", DashboardBody=json.dumps(dashboard))
print("dashboard: NorthstarAssist-Security")
