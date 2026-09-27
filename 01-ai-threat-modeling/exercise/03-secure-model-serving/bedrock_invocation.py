# CaseAssist - AgentCore Harness Invocation (Alternative approach)
# TODO: review before prod — this file shows a different credential pattern

import os
import boto3

# Developer note: "I put the keys in env vars instead of the source code — that's secure, right?"
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

HARNESS_ARN = os.environ.get(
    "AGENTCORE_HARNESS_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:123456789012:harness/CaseAssist-ABC123DEF4",
)


def invoke_bedrock_agent(user_input: str, session_id: str) -> str:
    """
    Invoke the CaseAssist AgentCore harness and return the response text.

    session_id must be at least 33 characters (str(uuid.uuid4()) works).
    """
    client = boto3.client(
        "bedrock-agentcore",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION,
    )

    response = client.invoke_harness(
        harnessArn=HARNESS_ARN,
        runtimeSessionId=session_id,
        messages=[{"role": "user", "content": [{"text": user_input}]}],
    )

    # Minimal response parsing — collects streamed text only, no error handling
    completion = ""
    for event in response["stream"]:
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"]["delta"]
            if "text" in delta:
                completion += delta["text"]
    return completion
