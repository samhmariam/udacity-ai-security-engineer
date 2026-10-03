# Northstar Knowledge Base - Streamlit App

A simple web interface for querying Northstar Assist, an Amazon Bedrock AgentCore harness backed by the Northstar knowledge base.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────────────────────────────────┐
│   Browser   │────▶│  Streamlit  │────▶│          Amazon Bedrock AgentCore            │
│   (User)    │◀────│    App      │◀────│  Harness → Gateway → Managed Knowledge Base  │
└─────────────┘     └─────────────┘     └──────────────────────────────────────────────┘
```

The app calls `InvokeHarness` on the `bedrock-agentcore` client. The harness runs the agent loop, calls the knowledge base through its AgentCore Gateway tool, and streams the answer back.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AGENTCORE_HARNESS_ARN` | Yes | Your harness ARN (Harness details page → **Harness ARN**) |
| `AWS_REGION` | No | AWS region (default: `us-east-1`) |
| `APP_PASSWORD` | No | Password to access the app (empty = no auth) |
| `AWS_ACCESS_KEY_ID` | * | AWS credentials (if not using `setup_aws.py` or an IAM role) |
| `AWS_SECRET_ACCESS_KEY` | * | AWS credentials (if not using `setup_aws.py` or an IAM role) |
| `AWS_SESSION_TOKEN` | * | Required with temporary credentials that you set as environment variables |

*boto3 finds AWS credentials on its own, in `~/.aws/credentials` (where `setup_aws.py` saves them), in environment variables, or from an IAM role. Don't put keys in `.env`.

The credentials the app uses need `bedrock-agentcore:InvokeHarness` and `bedrock-agentcore:InvokeAgentRuntime` on the harness ARN.

## Quick Start (Local or Workspace)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   The harness API needs `boto3` 1.43.52 or later.

2. **Connect to AWS:**
   - Open `aws-credentials.txt` in this folder. Paste the **AWS Access Key ID**, **AWS Secret Access Key**, and **AWS Session Token** from the **Cloud Resources** tab. After `Harness ARN =`, paste the **Harness ARN** from your harness details page. Save the file.
   - Run the setup script:
     ```bash
     python setup_aws.py
     ```

   The script checks your credentials with AWS and connects the app to your harness. Then it clears the keys from `aws-credentials.txt`, so they aren't submitted with your project. Your harness ARN stays in the file. To set other options, such as `APP_PASSWORD`, edit `.env`.

   Cloud Lab credentials expire when the lab session ends. If the app reports missing or expired credentials, start the lab again, paste the new credentials into `aws-credentials.txt`, and rerun `python setup_aws.py`. You don't need to restart the app. To see which identity is saved, run `python setup_aws.py --check`.

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

4. **Open browser:** http://localhost:8501

## Deployment Options

### EC2 with IAM Role
```bash
# On EC2 with IAM role attached (no AWS keys needed)
export AGENTCORE_HARNESS_ARN="arn:aws:bedrock-agentcore:us-east-1:123456789012:harness/NorthstarAssist-abc123"
export APP_PASSWORD="your-password"
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### Docker / App Runner
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Pass environment variables at runtime:
```bash
docker run -p 8501:8501 \
  -e AGENTCORE_HARNESS_ARN="arn:aws:bedrock-agentcore:us-east-1:123456789012:harness/NorthstarAssist-abc123" \
  -e APP_PASSWORD="your-password" \
  -e AWS_ACCESS_KEY_ID="..." \
  -e AWS_SECRET_ACCESS_KEY="..." \
  your-image
```

## Security Notes

- **APP_PASSWORD** provides basic protection for demos/labs
- For production, use proper authentication (Cognito, SSO)
- Use IAM roles instead of access keys when possible
- Never commit credentials to version control
- Anyone who can call `InvokeHarness` can also override the model, system prompt, and tools for that call. This app sends only the user's message; if you extend it, don't pass user-supplied model or tool settings through to the harness.
