"""Create or update the Northstar Assist guardrail from northstar-guardrail-config.json.

Usage:
  python deploy_guardrail.py            # create, or update the working DRAFT
  python deploy_guardrail.py --version  # also publish a numbered version from the DRAFT
"""
import json
import os
import sys
import time

import boto3
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, "..", "..", "..", ".env"), override=True)
bd = boto3.session.Session(region_name="us-east-1").client("bedrock")
cfg = json.load(open(os.path.join(HERE, "northstar-guardrail-config.json")))

existing = next((g for g in bd.list_guardrails()["guardrails"] if g["name"] == cfg["name"]), None)
if existing:
    bd.update_guardrail(guardrailIdentifier=existing["id"], **cfg)
    gid = existing["id"]
    print("updated DRAFT of", gid)
else:
    gid = bd.create_guardrail(**cfg)["guardrailId"]
    print("created", gid)

while (g := bd.get_guardrail(guardrailIdentifier=gid))["status"] not in ("READY", "FAILED"):
    time.sleep(3)
print("status:", g["status"], g.get("statusReasons", ""), "| arn:", g["guardrailArn"])

if "--version" in sys.argv and g["status"] == "READY":
    v = bd.create_guardrail_version(guardrailIdentifier=gid, description="Published after test matrix passed")["version"]
    while bd.get_guardrail(guardrailIdentifier=gid, guardrailVersion=v)["status"] != "READY":
        time.sleep(3)
    print("published version", v)
