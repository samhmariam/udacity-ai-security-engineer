# CaseAssist - AgentCore Harness Client
# TODO: clean this up before prod

import uuid

import boto3

# Dev credentials - REMOVE BEFORE PROD
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
HARNESS_ARN = "arn:aws:bedrock-agentcore:us-east-1:123456789012:harness/CaseAssist-ABC123DEF4"

def query_agent(user_input):
    client = boto3.client(
        'bedrock-agentcore',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name='us-east-1'
    )

    response = client.invoke_harness(
        harnessArn=HARNESS_ARN,
        runtimeSessionId=str(uuid.uuid4()),
        messages=[{"role": "user", "content": [{"text": user_input}]}]  # No length limit, no sanitization
    )

    # Return raw response
    return response
