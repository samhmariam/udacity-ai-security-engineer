"""Test PB-01 emergency controls K1 (no retrieval) and K2 (full stop) on the live harness.

Each test applies the inline Deny, checks the effect, removes it, and confirms normal service
returns. Removal is in a finally block, so the harness is never left blocked.
Writes kill-switch-results.json next to this script.
"""
import json
import os
import time
import uuid

import boto3
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, "..", "..", "..", ".env"), override=True)
s = boto3.session.Session(region_name="us-east-1")
iam, ac = s.client("iam"), s.client("bedrock-agentcore")
ROLE = "AmazonBedrockAgentCoreHarnessDefaultServiceRole-p0869"
Q = "What is Northstar's hybrid work policy? Name the source document."
SWITCHES = {
    "NorthstarEmergencyNoRetrieval": {"Effect": "Deny", "Action": "bedrock-agentcore:InvokeGateway", "Resource": "*"},
    "NorthstarEmergencyStop": {"Effect": "Deny", "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"], "Resource": "*"},
}


def ask():
    try:
        r = ac.invoke_harness(harnessArn=os.environ["HARNESS_ARN"], runtimeSessionId=str(uuid.uuid4()),
                              messages=[{"role": "user", "content": [{"text": Q}]}])
        text, stop = "", None
        for ev in r["stream"]:
            if "contentBlockDelta" in ev and "text" in ev["contentBlockDelta"]["delta"]:
                text += ev["contentBlockDelta"]["delta"]["text"]
            elif "messageStop" in ev:
                stop = ev["messageStop"]["stopReason"]
        return {"ok": True, "stop": stop, "cites_handbook": "company_policies_handbook" in text, "answer": text[-220:]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


results = {}
for name, stmt in SWITCHES.items():
    rec = {}
    try:
        iam.put_role_policy(RoleName=ROLE, PolicyName=name,
                            PolicyDocument=json.dumps({"Version": "2012-10-17", "Statement": [stmt]}))
        t = time.time(); time.sleep(45)
        rec["while_active"] = ask(); rec["active_after_seconds"] = int(time.time() - t)
    finally:
        iam.delete_role_policy(RoleName=ROLE, PolicyName=name)
    time.sleep(45)
    rec["after_removal"] = ask()
    results[name] = rec
    print(name, json.dumps(rec, indent=1)[:900])
print("inline policies now:", iam.list_role_policies(RoleName=ROLE)["PolicyNames"])
json.dump(results, open(os.path.join(HERE, "kill-switch-results.json"), "w"), indent=2)
