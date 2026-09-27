import argparse
import os
import uuid

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError as exc:  # pragma: no cover - surfaced to users as a setup issue
    raise SystemExit(
        "Missing dependencies. Run `uv sync` or install boto3 and python-dotenv before using this script."
    ) from exc

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    load_dotenv = None


def _load_environment() -> None:
    if load_dotenv is not None:
        load_dotenv()

    missing = [key for key in ("HARNESS_ARN",) if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            "Missing required environment variable(s): " + ", ".join(missing)
            + ". Add them to your shell or a local .env file."
        )


def _extract_text(response: dict) -> str:
    chunks: list[str] = []
    for event in response.get("stream", []):
        content_block = event.get("contentBlockDelta")
        if not content_block:
            continue

        delta = content_block.get("delta", {})
        if isinstance(delta, dict) and "text" in delta:
            chunks.append(delta["text"])

    return "".join(chunks)


def invoke_harness(
    prompt: str,
    harness_arn: str | None = None,
    region: str | None = None,
    session_id: str | None = None,
) -> str:
    _load_environment()

    harness_arn = harness_arn or os.environ["HARNESS_ARN"]
    region = region or os.getenv("AWS_REGION") or os.getenv("AWS_REGION") or "us-east-1"
    session_id = session_id or str(uuid.uuid4())

    client = boto3.client("bedrock-agentcore", region_name=region)
    response = client.invoke_harness(
        harnessArn=harness_arn,
        runtimeSessionId=session_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )

    answer = _extract_text(response)
    if not answer:
        raise RuntimeError("The harness returned no text output.")

    return answer


def main() -> None:
    parser = argparse.ArgumentParser(description="Invoke the configured Bedrock AgentCore harness.")
    parser.add_argument("prompt", nargs="?", default="What is Vantage's remote work policy?", help="Question to send to the harness.")
    parser.add_argument("--harness-arn", dest="harness_arn", help="Override the AGENTCORE_HARNESS_ARN environment variable.")
    parser.add_argument("--region", dest="region", help="AWS region for the Bedrock AgentCore client.")
    parser.add_argument("--session-id", dest="session_id", help="Custom runtime session ID for the invocation.")
    args = parser.parse_args()

    try:
        answer = invoke_harness(
            prompt=args.prompt,
            harness_arn=args.harness_arn,
            region=args.region,
            session_id=args.session_id,
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "ClientError")
        message = exc.response.get("Error", {}).get("Message", str(exc))

        if error_code == "AccessDeniedException" or "aws-marketplace" in message.lower():
            raise SystemExit(
                "Bedrock model access is blocked. In the AWS console, open Bedrock > Model access, "
                "enable access for the required foundation model, and ensure your IAM user/role has "
                "aws-marketplace:ViewSubscriptions and aws-marketplace:Subscribe permissions."
            ) from exc

        raise SystemExit(f"Harness invocation failed: {message}") from exc
    except Exception as exc:  # pragma: no cover - keeps CLI output user-friendly
        raise SystemExit(f"Harness invocation failed: {exc}") from exc

    print(answer)


if __name__ == "__main__":
    main()