"""Attach a published guardrail version to the NorthstarAssist harness.

Saves the current harness configuration to harness-before.json, then updates the model
configuration with additionalParams.guardrailConfig, keeping every other setting as is.
Usage: python attach_guardrail.py <guardrail-arn> <version>
"""
import json
import os
import sys
import time

import boto3
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, "..", "..", "..", ".env"), override=True)
ac = boto3.session.Session(region_name="us-east-1").client("bedrock-agentcore-control")
HARNESS_ID = os.environ["HARNESS_ARN"].split("/")[-1]
guardrail_arn, version = sys.argv[1], sys.argv[2]

h = ac.get_harness(harnessId=HARNESS_ID)["harness"]
with open(os.path.join(HERE, "harness-before.json"), "w") as f:
    json.dump(h, f, indent=2, default=str)

model = h["model"]
model["bedrockModelConfig"].setdefault("additionalParams", {})["guardrailConfig"] = {
    "guardrailIdentifier": guardrail_arn,
    "guardrailVersion": version,
    "trace": "enabled",
    "streamProcessingMode": "sync",
}
# UpdateHarness is a partial update: fields left out keep their current values.
before = dict(h)
ac.update_harness(harnessId=HARNESS_ID, model=model)

time.sleep(5)
while (h := ac.get_harness(harnessId=HARNESS_ID)["harness"])["status"] not in ("READY", "FAILED", "UPDATE_FAILED"):
    time.sleep(5)
changed = [k for k in before if k not in ("model", "harnessVersion", "updatedAt", "status") and before[k] != h.get(k)]
print("fields changed besides model:", changed or "none")
print("harness:", h["status"], "version", h["harnessVersion"])
print("guardrailConfig:", json.dumps(h["model"]["bedrockModelConfig"].get("additionalParams", {}).get("guardrailConfig")))
for e in ac.list_harness_endpoints(harnessId=HARNESS_ID)["endpoints"]:
    print("endpoint", e["endpointName"], "liveVersion", e.get("liveVersion"), e["status"])
