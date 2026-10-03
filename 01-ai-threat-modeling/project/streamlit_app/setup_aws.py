"""Connect the Northstar Assist app to your Udacity Cloud Lab AWS account.

1. Open aws-credentials.txt in this folder (project/streamlit_app). Paste your
   credentials from the Cloud Resources tab and your harness ARN, then save the file.
2. From this folder, run:

       python setup_aws.py

The script checks your credentials with AWS. Then it clears the keys from
aws-credentials.txt, so they aren't submitted with your project. Your harness
ARN stays in the file for next time.

Cloud Lab credentials expire when your lab session ends. Paste the new ones into
aws-credentials.txt and run the script again. To see which AWS identity is
saved, run: python setup_aws.py --check

Where things go: the keys are saved in your home folder (~/.aws/credentials),
where boto3 finds them on its own, so app.py never handles keys. The harness ARN
and region are saved to .env in this folder, which app.py loads. Other settings
in .env, such as APP_PASSWORD, are kept.
"""
import argparse
import configparser
import contextlib
import io
import os
import re
import sys
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    sys.exit("boto3 isn't installed. Run: pip install -r requirements.txt")

HERE = Path(__file__).resolve().parent
CREDENTIALS_FILE = HERE / "aws-credentials.txt"
ENV_FILE = HERE / ".env"
ENV_TEMPLATE = HERE / ".env.example"
ADD_SHELL_HOOK = False  # app.py loads .env itself, so terminals don't need it
HARNESS_NAME = "NorthstarAssist"
HARNESS_EXAMPLE = "arn:aws:bedrock-agentcore:us-east-1:123456789012:harness/NorthstarAssist-a1B2c3D4e5"

AWS_DIR = Path.home() / ".aws"
CREDENTIAL_KEYS = ("aws_access_key_id", "aws_secret_access_key", "aws_session_token")
SETTING_LABELS = {
    "aws_access_key_id": "AWS Access Key ID",
    "aws_secret_access_key": "AWS Secret Access Key",
    "aws_session_token": "AWS Session Token",
    "harness_arn": "Harness ARN",
}
HARNESS_ARN_PATTERN = re.compile(r"^arn:aws:bedrock-agentcore:([a-z0-9-]+):\d{12}:harness/[A-Za-z0-9_-]+$")
OVERRIDING_VARIABLES = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE")
SHELL_HOOK_MARK = "# added by setup_aws.py"


def credentials_template(harness_arn=""):
    """The blank aws-credentials.txt, with the harness ARN filled in when there is one."""
    arn_line = f"Harness ARN = {harness_arn}" if harness_arn else "Harness ARN ="
    return (
        "# Paste your AWS credentials from the Cloud Resources tab into this file, save it,\n"
        "# and then run:  python setup_aws.py\n"
        "#\n"
        "# Paste the whole block over the three AWS lines, or paste each value after its = sign.\n"
        "# setup_aws.py clears the keys from this file after it saves them.\n"
        "\n"
        "AWS Access Key ID =\n"
        "AWS Secret Access Key =\n"
        "AWS Session Token =\n"
        "\n"
        f"# Paste the Harness ARN from the {HARNESS_NAME} harness details page. It stays in this file.\n"
        f"{arn_line}\n"
    )


def parse_setting_line(line):
    """Return (key, value) for one line such as "AWS Access Key ID = ...", or None.

    Also accepts the credentials file format ("aws_access_key_id=...") and shell
    exports ("export AWS_SESSION_TOKEN=...").
    """
    line = line.strip()
    if line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[len("export "):]
    match = re.match(r"^([A-Za-z_ ]+?)\s*[=:]\s*(\S+)$", line)
    if not match:
        return None
    key = match.group(1).strip().lower().replace(" ", "_")
    if key not in SETTING_LABELS:
        return None
    return key, match.group(2).strip("\"'")


def write_private_file(path, text):
    """Write a file that only the current user can read."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as file:
        file.write(text)
    os.chmod(path, 0o600)


def read_credentials_file():
    """Return the values filled in aws-credentials.txt. Creates the blank file if it's missing."""
    if not CREDENTIALS_FILE.exists():
        write_private_file(CREDENTIALS_FILE, credentials_template())
        return {}
    values = {}
    for line in CREDENTIALS_FILE.read_text(errors="replace").splitlines():
        parsed = parse_setting_line(line)
        if parsed:
            values[parsed[0]] = parsed[1]
    return values


def hidden_terminal_lines():
    """Yield lines pasted into the terminal without showing them on screen.

    Line editing is off so a long session token isn't cut at the terminal's
    line-length limit. getpass can't be used: it discards the rest of a
    multi-line paste.
    """
    try:
        import termios
    except ImportError:  # Windows has no termios, so the pasted text stays visible
        yield from iter(sys.stdin.readline, "")
        return
    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)
    hidden = termios.tcgetattr(fd)
    hidden[3] &= ~(termios.ECHO | termios.ICANON)
    hidden[6][termios.VMIN], hidden[6][termios.VTIME] = 1, 0
    termios.tcsetattr(fd, termios.TCSADRAIN, hidden)
    pending = b""
    try:
        while True:
            chunk = os.read(fd, 4096)
            if not chunk or b"\x04" in chunk:  # Ctrl+D
                return
            pending += chunk
            *lines, pending = re.split(rb"\r\n|\r|\n", pending)
            for line in lines:
                yield line.decode(errors="replace")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original)


def piped_lines():
    yield from iter(sys.stdin.readline, "")


def read_pasted_credentials():
    """Fallback when the file is blank: collect the three credential values from the terminal."""
    if sys.stdin.isatty():
        print("Or paste the three credential lines here and press Enter.")
        print("What you paste isn't shown. Press Ctrl+C to cancel.")
        source = hidden_terminal_lines()
    else:
        source = piped_lines()
    credentials = {}
    with contextlib.closing(source):
        for line in source:
            parsed = parse_setting_line(line)
            if not parsed or parsed[0] not in CREDENTIAL_KEYS:
                continue
            key, value = parsed
            credentials[key] = value
            print(f"  Received {SETTING_LABELS[key]} ({len(credentials)} of {len(CREDENTIAL_KEYS)})")
            if len(credentials) == len(CREDENTIAL_KEYS):
                break
    return credentials


def saved_credentials_exist():
    parser = configparser.RawConfigParser()
    parser.read(AWS_DIR / "credentials")
    return parser.has_section("default") and all(parser.has_option("default", key) for key in CREDENTIAL_KEYS)


def read_env_lines():
    """Return the lines of .env, or of .env.example when .env doesn't exist yet."""
    for path in (ENV_FILE, ENV_TEMPLATE):
        if path.exists():
            return path.read_text().splitlines()
    return []


def get_env_value(lines, key):
    for line in lines:
        match = re.match(rf"^\s*(?:export\s+)?{key}\s*=\s*(.*)$", line)
        if match:
            return match.group(1).strip().strip("\"'")
    return ""


def set_env_value(lines, key, value):
    prefix = "export " if ADD_SHELL_HOOK else ""
    for index, line in enumerate(lines):
        match = re.match(rf"^\s*(export\s+)?{key}\s*=", line)
        if match:
            lines[index] = f"{prefix or match.group(1) or ''}{key}={value}"
            return
    lines.append(f"{prefix}{key}={value}")


def ask_harness_arn(current):
    """Terminal fallback: ask for the harness ARN. Enter keeps the current value, or skips."""
    if current:
        prompt = f"\nHarness ARN (press Enter to keep {current}): "
    else:
        print(f"\nCopy the Harness ARN from your harness details page. It looks like {HARNESS_EXAMPLE}")
        prompt = "Harness ARN (press Enter to skip if you haven't created the harness yet): "
    while True:
        try:
            harness_arn = input(prompt).strip() or current
        except EOFError:
            harness_arn = current
        if not harness_arn or HARNESS_ARN_PATTERN.match(harness_arn):
            return harness_arn
        print("That isn't a harness ARN. A harness ARN starts with arn:aws:bedrock-agentcore: and contains :harness/.")


def update_aws_file(name, values, replace_section):
    """Update the [default] profile in ~/.aws/<name> and keep any other profiles."""
    path = AWS_DIR / name
    parser = configparser.RawConfigParser()
    parser.read(path)
    if replace_section or not parser.has_section("default"):
        parser["default"] = {}
    for key, value in values.items():
        parser.set("default", key, value)
    AWS_DIR.mkdir(mode=0o700, exist_ok=True)
    text = io.StringIO()
    parser.write(text)
    write_private_file(path, text.getvalue())


def add_shell_hook():
    """Make new terminals load .env, replacing the hook from any earlier run."""
    hook = f'[ -f "{ENV_FILE}" ] && . "{ENV_FILE}"  {SHELL_HOOK_MARK}'
    for rc_file in (Path.home() / ".bashrc", Path.home() / ".zshrc"):
        if rc_file.name == ".zshrc" and not rc_file.exists():
            continue
        lines = rc_file.read_text().splitlines() if rc_file.exists() else []
        if hook in lines:
            continue
        lines = [line for line in lines if not line.endswith(SHELL_HOOK_MARK)]
        rc_file.write_text("\n".join(lines + [hook]) + "\n")


def warn_about_environment_overrides():
    overriding = [name for name in OVERRIDING_VARIABLES if os.environ.get(name)]
    if overriding:
        print(f"\nWarning: {', '.join(overriding)} is set in this terminal. AWS tools use it instead of the saved credentials.")
        print(f"Run `unset {' '.join(overriding)}` before you start the app.")


def show_identity(region):
    """Print the identity for the saved credentials. Returns False when AWS rejects them."""
    try:
        # Naming the profile makes boto3 test the saved file, not environment variables.
        session = boto3.session.Session(profile_name="default", region_name=region)
        arn = session.client("sts").get_caller_identity()["Arn"]
    except (BotoCoreError, ClientError) as error:
        print(f"\nAWS didn't accept the saved credentials: {error}")
        print(f"Paste fresh credentials from the Cloud Resources tab into {CREDENTIALS_FILE.name}, "
              "save it, and run this script again.")
        return False
    print(f"\nConnected to AWS as {arn.split(':', 5)[-1]} in {region}.")
    return True


def check():
    lines = ENV_FILE.read_text().splitlines() if ENV_FILE.exists() else []
    print(f"Harness ARN: {get_env_value(lines, 'AGENTCORE_HARNESS_ARN') or 'not set'}")
    file_values = read_credentials_file() if CREDENTIALS_FILE.exists() else {}
    if any(key in file_values for key in CREDENTIAL_KEYS):
        print(f"{CREDENTIALS_FILE.name} still has keys in it. Run `python setup_aws.py` to save them "
              "and clear them from the file.")
    warn_about_environment_overrides()
    return show_identity(get_env_value(lines, "AWS_REGION") or "us-east-1")


def main():
    parser = argparse.ArgumentParser(description="Save your Cloud Lab AWS credentials and harness ARN.")
    parser.add_argument("--check", action="store_true",
                        help="show the saved AWS identity and harness ARN without changing anything")
    if parser.parse_args().check:
        return 0 if check() else 1

    file_values = read_credentials_file()
    credentials = {key: file_values[key] for key in CREDENTIAL_KEYS if key in file_values}
    file_arn = file_values.get("harness_arn", "")
    if file_arn and not HARNESS_ARN_PATTERN.match(file_arn):
        print(f"Nothing was saved. The Harness ARN in {CREDENTIALS_FILE.name} isn't a harness ARN. "
              "A harness ARN starts with arn:aws:bedrock-agentcore: and contains :harness/.")
        return 1

    if credentials:
        source = "file"
    elif file_arn and saved_credentials_exist():
        source = "saved"  # no new keys in the file: keep the saved keys and update the harness ARN
    else:
        source = "terminal"
        print(f"No credentials found in {CREDENTIALS_FILE.name}. Paste your credentials from the "
              "Cloud Resources tab into that file, save it, and run this script again.")
        credentials = read_pasted_credentials()

    if source != "saved":
        missing = [SETTING_LABELS[key] for key in CREDENTIAL_KEYS if key not in credentials]
        if missing:
            where = CREDENTIALS_FILE.name if source == "file" else "what you pasted"
            print(f"Nothing was saved. Missing from {where}: {', '.join(missing)}.")
            return 1

    env_lines = read_env_lines()
    current_arn = get_env_value(env_lines, "AGENTCORE_HARNESS_ARN")
    harness_arn = file_arn or (current_arn if HARNESS_ARN_PATTERN.match(current_arn) else "")
    if source == "terminal":
        harness_arn = ask_harness_arn(harness_arn)
    if harness_arn:
        region = HARNESS_ARN_PATTERN.match(harness_arn).group(1)
    else:
        region = get_env_value(env_lines, "AWS_REGION") or "us-east-1"

    if source != "saved":
        update_aws_file("credentials", credentials, replace_section=True)
        print("\nSaved your AWS credentials.")
    update_aws_file("config", {"region": region}, replace_section=False)

    # Put the blank template back, so no keys stay in the project files. The harness ARN stays.
    write_private_file(CREDENTIALS_FILE, credentials_template(harness_arn))
    if source == "file":
        print(f"Cleared the keys from {CREDENTIALS_FILE.name}.")

    set_env_value(env_lines, "AGENTCORE_HARNESS_ARN", harness_arn)
    set_env_value(env_lines, "AWS_REGION", region)
    write_private_file(ENV_FILE, "\n".join(env_lines) + "\n")
    if harness_arn:
        print(f"Using harness {harness_arn.split('/')[-1]}.")
    else:
        print(f"No harness ARN yet. After you create the harness, paste its ARN into "
              f"{CREDENTIALS_FILE.name} and run this script again.")
    if ADD_SHELL_HOOK:
        add_shell_hook()
        print(f'Open a new terminal before you run demo code, or run this in the current one: source "{ENV_FILE}"')

    warn_about_environment_overrides()
    return 0 if show_identity(region) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCanceled.")
        sys.exit(130)
