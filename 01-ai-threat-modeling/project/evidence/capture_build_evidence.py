"""Capture evidence that the Northstar Assist harness is built and working.

1. Harness configuration (model, tools, guardrail, status).
2. A live InvokeHarness transcript for a non-sensitive question.
3. The matching model invocation log records: the foundation model used, the Retrieve tool call,
   the retrieved chunks' sources and scores, and the final answer.
4. Knowledge base and data source status, and the ingestion (sync) job results.
Writes build-evidence.json next to this script.
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
ctl, dp, ba, logs = s.client("bedrock-agentcore-control"), s.client("bedrock-agentcore"), s.client("bedrock-agent"), s.client("logs")
HARNESS_ID, KB_ID, DS_ID = "NorthstarAssist-yH4PMorNwm", "ZCAWWBRBXU", "NTXBJ668Z7"
QUESTION = "What is Northstar's hybrid work policy? Name the source document."
ev = {"captured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

# 1. Harness configuration
h = ctl.get_harness(harnessId=HARNESS_ID)["harness"]
mc = h["model"]["bedrockModelConfig"]
ev["harness"] = {"name": h["harnessName"], "id": h["harnessId"], "status": h["status"], "version": h["harnessVersion"],
                 "model_id": mc["modelId"], "api_format": mc.get("apiFormat"),
                 "guardrail": mc.get("additionalParams", {}).get("guardrailConfig"),
                 "tools": [{"type": t["type"], "gateway": t["name"]} for t in h["tools"]]}

# 2. Live transcript
session = f"evidence-{uuid.uuid4()}"
t0 = int(time.time() * 1000) - 1500
r = dp.invoke_harness(harnessArn=os.environ["HARNESS_ARN"], runtimeSessionId=session,
                      messages=[{"role": "user", "content": [{"text": QUESTION}]}])
answer, stops, tool_calls, event_types = "", [], [], []
for e in r["stream"]:
    k = next(iter(e))
    event_types.append(k)
    if k == "contentBlockStart" and "toolUse" in e[k].get("start", {}):
        tool_calls.append(e[k]["start"]["toolUse"].get("name"))
    elif k == "contentBlockDelta" and "text" in e[k]["delta"]:
        answer += e[k]["delta"]["text"]
    elif k == "messageStop":
        stops.append(e[k]["stopReason"])
t1 = int(time.time() * 1000) + 1500
ev["transcript"] = {"runtimeSessionId": session, "prompt": QUESTION, "streamed_tool_calls": tool_calls,
                    "stop_reasons": stops, "answer": answer,
                    "event_counts": {k: event_types.count(k) for k in sorted(set(event_types))}}

# 3. Invocation log records for this request
time.sleep(75)
inv = s.client("bedrock").get_model_invocation_logging_configuration()["loggingConfig"]["cloudWatchConfig"]["logGroupName"]
records = [json.loads(x["message"]) for pg in logs.get_paginator("filter_log_events").paginate(
    logGroupName=inv, startTime=t0, endTime=t1,
    filterPattern='{ $.identity.arn = "*HarnessDefaultServiceRole-p0869*" || $.identity.arn = "*MANAGED_KB_EMBED-911470903119-ZCAWWBRBXU" }')
    for x in pg["events"]]
log_out = []
for m in sorted(records, key=lambda m: m["timestamp"]):
    item = {"timestamp": m["timestamp"], "operation": m["operation"], "modelId": m["modelId"],
            "role_session": m["identity"]["arn"].split("assumed-role/")[1]}
    if m["operation"] == "InvokeModel":
        item["embedded_retrieval_query"] = m["input"]["inputBodyJson"].get("inputText")
    else:
        ob = m["output"].get("outputBodyJson") or {}
        item.update(stopReason=ob.get("stopReason"), inputTokens=m["input"].get("inputTokenCount"),
                    outputTokens=m["output"].get("outputTokenCount"), inferenceRegion=m.get("inferenceRegion"),
                    guardrail_applied=bool(ob.get("trace", {}).get("guardrail")))
        for msg in m["input"]["inputBodyJson"]["messages"]:
            for c in msg["content"]:
                if "toolResult" in c:
                    res = json.loads(c["toolResult"]["content"][0]["text"])["retrievalResults"]
                    item["retrieved_chunks"] = [{
                        "source": x.get("location", {}).get("s3Location", {}).get("uri"),
                        "score": round(x.get("score", 0), 4),
                        "excerpt": " ".join(x["content"]["text"].split())[:160]} for x in res]
        for c in (ob.get("output", {}).get("message", {}).get("content") or []):
            if "toolUse" in c:
                item["tool_use"] = {"name": c["toolUse"]["name"], "input": c["toolUse"]["input"]}
    log_out.append(item)
ev["invocation_log_records"] = log_out

# 4. Knowledge base sync status
kb = ba.get_knowledge_base(knowledgeBaseId=KB_ID)["knowledgeBase"]
ds = ba.get_data_source(knowledgeBaseId=KB_ID, dataSourceId=DS_ID)["dataSource"]
jobs = ba.list_ingestion_jobs(knowledgeBaseId=KB_ID, dataSourceId=DS_ID,
                              sortBy={"attribute": "STARTED_AT", "order": "DESCENDING"})["ingestionJobSummaries"]
detail = [ba.get_ingestion_job(knowledgeBaseId=KB_ID, dataSourceId=DS_ID, ingestionJobId=j["ingestionJobId"])["ingestionJob"] for j in jobs]
ev["knowledge_base"] = {"name": kb["name"], "id": kb["knowledgeBaseId"], "status": kb["status"],
                        "embedding_model": kb["knowledgeBaseConfiguration"]["managedKnowledgeBaseConfiguration"]["embeddingModelArn"],
                        "data_source": {"name": ds["name"], "id": ds["dataSourceId"], "status": ds["status"]},
                        "ingestion_jobs": [{"id": j["ingestionJobId"], "status": j["status"],
                                            "started": str(j["startedAt"]), "completed": str(j["updatedAt"]),
                                            "statistics": j["statistics"], "failureReasons": j.get("failureReasons", [])}
                                           for j in detail]}
with open(os.path.join(HERE, "build-evidence.json"), "w", encoding="utf-8") as f:
    json.dump(ev, f, indent=2, default=str)
print(json.dumps(ev, indent=1, default=str)[:4000])
