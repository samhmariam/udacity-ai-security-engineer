import streamlit as st
import boto3
import uuid
import os
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv

# Load environment variables from .env file. override=True applies changes that
# setup_aws.py makes to .env on the next question, without restarting the app.
load_dotenv(override=True)

st.set_page_config(page_title="Northstar Assist", page_icon="⭐")

# =============================================================================
# Configuration from environment variables (loaded from .env)
# =============================================================================
HARNESS_ARN = os.environ.get("AGENTCORE_HARNESS_ARN", "")
REGION = os.environ.get("AWS_REGION", "us-east-1")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")  # Empty = no auth required

CREDENTIAL_ERROR_CODES = {
    "ExpiredToken",
    "ExpiredTokenException",
    "InvalidClientTokenId",
    "InvalidSignatureException",
    "SignatureDoesNotMatch",
    "UnrecognizedClientException",
}

def is_credential_error(error):
    """True when AWS credentials are missing, expired, or not recognized."""
    if isinstance(error, (NoCredentialsError, PartialCredentialsError)):
        return True
    if not isinstance(error, ClientError):
        return False
    details = error.response.get("Error", {})
    # The harness API reports a bad or expired token as AccessDeniedException, so check the message too.
    return (details.get("Code") in CREDENTIAL_ERROR_CODES
            or "security token included in the request" in details.get("Message", ""))

# =============================================================================
# Authentication
# =============================================================================
def check_password():
    """Simple password authentication. Returns True if authenticated."""
    # If no password is set, skip authentication
    if not APP_PASSWORD:
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Show login form
    st.title("🔐 Login Required")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")

    return False

# Check authentication before showing the app
if not check_password():
    st.stop()

# =============================================================================
# Main App (only runs if authenticated)
# =============================================================================
st.title("Northstar Assist")
st.write("""
Welcome to Northstar Assist! This system is designed for Northstar employees
to ask questions about our company's strategy, policies, procedures, and
internal documentation. Simply type your question below and get instant answers powered by AI.
""")

if not HARNESS_ARN:
    st.error("Set your harness ARN: paste it into aws-credentials.txt in the streamlit_app folder and run "
             "`python setup_aws.py`, or set AGENTCORE_HARNESS_ARN in your .env file.")
    st.stop()

# Clear chat button
col1, col2 = st.columns([6, 1])
with col2:
    if st.button("Clear"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# Initialize AgentCore data-plane client. boto3 finds credentials on its own
# (~/.aws/credentials from setup_aws.py, environment variables, or an IAM role).
# A new Session reads them again, so clearing this cache picks up fresh credentials.
@st.cache_resource
def get_agentcore_client(region):
    return boto3.session.Session().client("bedrock-agentcore", region_name=region)

client = get_agentcore_client(REGION)

# Session state (a harness session ID must be at least 33 characters; a UUID is 36)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask a question about Northstar..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call the AgentCore harness
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = client.invoke_harness(
                    harnessArn=HARNESS_ARN,
                    runtimeSessionId=st.session_state.session_id,
                    messages=[{"role": "user", "content": [{"text": prompt}]}],
                )

                # Parse streaming response. The harness streams every model turn,
                # including text written before and after a tool call, so collect
                # all text deltas.
                answer = ""
                stop_reason = None
                for event in response["stream"]:
                    if "contentBlockDelta" in event:
                        delta = event["contentBlockDelta"]["delta"]
                        if "text" in delta:
                            answer += delta["text"]
                    elif "messageStop" in event:
                        stop_reason = event["messageStop"]["stopReason"]
                    elif "runtimeClientError" in event:
                        raise RuntimeError(event["runtimeClientError"].get("message", "Runtime error"))

                if not answer and stop_reason:
                    answer = f"_No text returned (stop reason: {stop_reason})._"

                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

            except Exception as e:
                if is_credential_error(e):
                    # Cloud Lab credentials expire. Drop the cached client so the
                    # next question uses the credentials saved by setup_aws.py.
                    get_agentcore_client.clear()
                    error_msg = ("Your AWS credentials are missing or expired. Paste fresh credentials from the "
                                 "Cloud Resources tab into aws-credentials.txt in the streamlit_app folder, "
                                 "run `python setup_aws.py`, then ask again.")
                else:
                    error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Logout button (only if password auth is enabled)
if APP_PASSWORD:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
