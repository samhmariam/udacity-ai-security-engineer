#!/usr/bin/env bash
# Dry run of PB-01 against the simulated attack session, using the playbook's own commands.
# Reads credentials from the repo-root .env without printing them. Writes evidence to ./dryrun-case/ (contains retrieved PII: keep it out of git and delete it after review).
set -u
cd "$(dirname "$0")"
export $(grep -E '^AWS_(ACCESS_KEY_ID|SECRET_ACCESS_KEY|SESSION_TOKEN)=' ../../../.env | xargs)
export PYTHONIOENCODING=utf-8 MSYS_NO_PATHCONV=1   # stop Git Bash on Windows rewriting /aws/... log group names (not needed in CloudShell)
aws() { uv run --no-project --with "awscli>=1.44" python -m awscli "$@"; }   # current CLI; the local CLI v2 predates the harness APIs

# ---- B0
export AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1
export HARNESS_ARN=arn:aws:bedrock-agentcore:us-east-1:911470903119:harness/NorthstarAssist-yH4PMorNwm
export HARNESS_ID=NorthstarAssist-yH4PMorNwm
export RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:911470903119:runtime/harness_NorthstarAssist-4tSgy4Clrq
export HARNESS_ROLE=AmazonBedrockAgentCoreHarnessDefaultServiceRole-p0869
export GUARDRAIL_ID=bzgydako86r9 KB_ID=ZCAWWBRBXU DS_ID=NTXBJ668Z7 BUCKET=northstar-assist-kb-chrst
export INV_LOG=$(aws bedrock get-model-invocation-logging-configuration --query loggingConfig.cloudWatchConfig.logGroupName --output text)
export RT_LOG=/aws/bedrock-agentcore/runtimes/harness_NorthstarAssist-4tSgy4Clrq-DEFAULT
rm -rf dryrun-case; mkdir -p dryrun-case && cd dryrun-case
echo "B0 ok | caller: $(aws sts get-caller-identity --query Arn --output text | sed 's|/user.*||')"

# ---- B3 step 2: sessions with PROMPT_ATTACK blocks
QID=$(aws logs start-query --log-group-name "$INV_LOG" --start-time $(date -u -d '-2 hours' +%s) --end-time $(date -u +%s) \
  --query-string 'filter identity.arn like /HarnessDefaultServiceRole-p0869/ and @message like /PROMPT_ATTACK/
  | parse identity.arn "/BedrockAgentCore-*" as session | stats count(*) as blocks, min(@timestamp) as first, max(@timestamp) as last by session
  | sort blocks desc' --query queryId --output text); sleep 10
aws logs get-query-results --query-id $QID --query 'results[0:3][*][?field!=`@ptr`].[field,value]' --output text | paste - - - - - - - -
export SESSION_UUID=$(aws logs get-query-results --query-id $QID --query 'results[0][?field==`session`].value' --output text)
echo "B3 top session: $SESSION_UUID"

# ---- C1: evidence
START=$(date -u -d '-6 hours' +%s000)
aws logs filter-log-events --log-group-name "$INV_LOG" --start-time $START \
  --filter-pattern "{ \$.identity.arn = \"*BedrockAgentCore-${SESSION_UUID}*\" }" --output json > invocations-session.json
aws logs filter-log-events --log-group-name "$INV_LOG" --start-time $START \
  --filter-pattern '{ $.identity.arn = "*HarnessDefaultServiceRole-p0869*" || $.identity.arn = "*MANAGED_KB_EMBED-911470903119-ZCAWWBRBXU" }' \
  --output json > invocations-window.json
aws logs filter-log-events --log-group-name "$RT_LOG" --start-time $START --output json > runtime-window.json
aws bedrock-agentcore-control get-harness --harness-id $HARNESS_ID > harness-config.json
aws bedrock get-guardrail --guardrail-identifier $GUARDRAIL_ID --guardrail-version 1 > guardrail-v1.json
aws iam list-role-policies --role-name $HARNESS_ROLE > harness-role-inline.json
aws iam list-attached-role-policies --role-name $HARNESS_ROLE > harness-role-attached.json
aws bedrock-agent list-ingestion-jobs --knowledge-base-id $KB_ID --data-source-id $DS_ID > ingestion-jobs.json
aws s3api list-object-versions --bucket $BUCKET > s3-object-versions.json
sha256sum *.json > SHA256SUMS
python -c "import json;d=json.load(open('invocations-session.json'));print('C1 session records:',len(d['events']))"
python -c "import json;d=json.load(open('invocations-window.json'));print('C1 window records:',len(d['events']))"
ls -1 | tr '\n' ' '; echo

# ---- C2: map to the client runtimeSessionId by time, then stop it
FIRST=$(python -c "import json;e=json.load(open('invocations-session.json'))['events'];print(min(x['timestamp'] for x in e)//1000)")
LAST=$(python -c "import json;e=json.load(open('invocations-session.json'))['events'];print(max(x['timestamp'] for x in e)//1000)")
QID=$(aws logs start-query --log-group-name "$RT_LOG" --start-time $((FIRST-60)) --end-time $((LAST+60)) \
  --query-string 'filter @logStream like /runtime-logs/ and message like /Returning streaming response/
  | stats count(*) as requests, min(@timestamp) as first_request, max(@timestamp) as last_request by sessionId | sort first_request asc' \
  --query queryId --output text); sleep 8
aws logs get-query-results --query-id $QID --query 'results[*][?field!=`@ptr`].[field,value]' --output text | paste - - - - - - - -
export RUNTIME_SESSION_ID=$(aws logs get-query-results --query-id $QID --query 'results[0][?field==`sessionId`].value' --output text)
echo "C2 runtimeSessionId: $RUNTIME_SESSION_ID"
aws bedrock-agentcore stop-runtime-session --runtime-session-id "$RUNTIME_SESSION_ID" --agent-runtime-arn "$HARNESS_ARN" --qualifier DEFAULT --output json \
  && echo "C2 stop-runtime-session: OK"

# ---- C3: Deny still in place?
aws iam get-role-policy --role-name $HARNESS_ROLE --policy-name NorthstarRequireGuardrail --query 'PolicyDocument.Statement[0].Sid' --output text

# ---- B6 I-2: system prompt leakage in any answer (expect 0 rows)
QID=$(aws logs start-query --log-group-name "$INV_LOG" --start-time $(date -u -d '-24 hours' +%s) --end-time $(date -u +%s) \
  --query-string 'filter output.outputBodyJson.output.message.content.0.text like /internal employee assistant|Base your answers only|Do not discuss topics unrelated/
  | fields @timestamp, identity.arn' --query queryId --output text); sleep 10
echo "I-2 system-prompt leak rows: $(aws logs get-query-results --query-id $QID --query 'length(results)' --output text)"
sha256sum -c SHA256SUMS --quiet && echo "C1 evidence hashes verify"
