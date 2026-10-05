"""
Supply Chain Vulnerability Analysis.

Parses a Trivy JSON report and analyzes a Dockerfile for security issues.
Produces a structured risk assessment of the AI system's deployment pipeline.

Usage:
    python 05_supply_chain_analysis.py
    python 05_supply_chain_analysis.py --trivy-report ../06_trivy_report.json --dockerfile ../Dockerfile
"""
import json
import argparse
import os

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results", "05_supply_chain")


def parse_trivy_report(path):
    """
    Parse a Trivy JSON report and extract vulnerability details.

    The Trivy JSON format has a "Results" array, where each result has:
    - "Target": what was scanned (e.g., "debian 13.4" or "Python")
    - "Type": scan type (e.g., "debian", "python-pkg")
    - "Vulnerabilities": array of vulnerability objects

    Each vulnerability has: VulnerabilityID, Severity, PkgName,
    InstalledVersion, FixedVersion, Title, Description

    Args:
        path: Path to Trivy JSON report

    Returns:
        List of vulnerability dictionaries
    """
    # Trivy writes UTF-8; be explicit so this also works on Windows (cp1252 default).
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    vulns = []

    for result in data.get("Results", []):
        target = result.get("Target", "")
        target_type = result.get("Type", "")
        # "Vulnerabilities" is omitted or null when a target is clean
        for v in result.get("Vulnerabilities") or []:
            vulns.append({
                "id": v.get("VulnerabilityID", ""),
                "severity": v.get("Severity", "UNKNOWN"),
                "package": v.get("PkgName", ""),
                "installed_version": v.get("InstalledVersion", ""),
                "fixed_version": v.get("FixedVersion", ""),
                "status": v.get("Status", ""),
                "title": v.get("Title", ""),
                "description": (v.get("Description") or "")[:200],
                "package_path": v.get("PkgPath", ""),
                "target": target,
                "target_type": target_type,
            })

    return vulns


def analyze_dockerfile(path):
    """
    Analyze a Dockerfile for common security issues.

    Check for:
    1. Running as root (no USER directive) — HIGH
    2. Unpinned base image (no SHA256 digest) — MEDIUM
    3. COPY . (copies entire context including secrets) — MEDIUM
    4. No HEALTHCHECK — LOW
    5. Build tools left in production image — MEDIUM
    6. Unnecessary tools (curl, git) in production — LOW

    Args:
        path: Path to Dockerfile

    Returns:
        List of issue dictionaries with: issue, severity, detail, recommendation
    """
    with open(path) as f:
        content = f.read()
    lines = content.strip().split("\n")

    issues = []

    # Ignore comments/blank lines; match instructions case-insensitively
    instructions = [
        line.strip() for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]
    upper = [line.upper() for line in instructions]
    content_lower = content.lower()

    # 1. Running as root
    user_lines = [line for line in upper if line.startswith("USER ")]
    if not user_lines or user_lines[-1].split()[1] in ("ROOT", "0"):
        issues.append({
            "issue": "Container runs as root (no USER directive)",
            "severity": "HIGH",
            "detail": (
                "Without a USER directive the app process runs as UID 0. Any RCE in "
                "Flask, the model-loading code or a dependency gives the attacker root "
                "inside the container, making container escape and tampering with "
                "model files and secrets far easier."
            ),
            "recommendation": (
                "Create an unprivileged user (e.g. RUN useradd --create-home --uid 10001 app), "
                "chown only the paths the app must write, and add USER app before CMD."
            ),
        })

    # 2. Unpinned base image
    from_lines = [line for line in instructions if line.upper().startswith("FROM ")]
    unpinned = [line for line in from_lines if "@sha256:" not in line]
    if unpinned:
        issues.append({
            "issue": "Base image not pinned to a SHA256 digest",
            "severity": "MEDIUM",
            "detail": (
                f"{unpinned[0]!r} uses a mutable tag. Each build may pull a different "
                "image, so builds are not reproducible and a compromised or "
                "re-pushed tag would flow straight into production."
            ),
            "recommendation": (
                "Pin the base image by digest (FROM python:3.11-slim@sha256:<digest>) "
                "and update it deliberately via an automated PR (Dependabot/Renovate)."
            ),
        })

    # 3. COPY of the entire build context
    copy_all = [
        line for line in instructions
        if line.upper().startswith(("COPY ", "ADD ")) and line.split()[1] == "."
    ]
    if copy_all:
        context_dir = os.path.dirname(os.path.abspath(path))
        has_dockerignore = os.path.exists(os.path.join(context_dir, ".dockerignore"))
        env_files = [
            os.path.relpath(os.path.join(root, f), context_dir)
            for root, _, files in os.walk(context_dir)
            for f in files if f == ".env"
        ]
        detail = (
            f"{copy_all[0]!r} copies the whole build context into the image"
            + ("" if has_dockerignore else " and no .dockerignore exists")
            + ". Secrets, .git history, datasets and local checkpoints can be "
            "baked into an image layer, where anyone who can pull the image can read them."
        )
        if env_files and not has_dockerignore:
            detail += f" Secret files present in the context: {', '.join(env_files)}."
        issues.append({
            "issue": "COPY . copies entire build context (possible secret leakage)",
            "severity": "MEDIUM",
            "detail": detail,
            "recommendation": (
                "Add a .dockerignore (.env, .git, *.pt, data/, __pycache__/) and COPY only "
                "the directories the service needs (e.g. COPY rag_chatbot/ ./rag_chatbot/). "
                "Inject secrets at runtime via the orchestrator's secret store."
            ),
        })

    # 4. No HEALTHCHECK
    if not any(line.startswith("HEALTHCHECK") for line in upper):
        issues.append({
            "issue": "No HEALTHCHECK defined",
            "severity": "LOW",
            "detail": (
                "Orchestrators cannot tell a hung or crashed service from a healthy "
                "one, so failures (or a tampered process) can go unnoticed."
            ),
            "recommendation": (
                "Add a HEALTHCHECK against the existing /health endpoint, e.g. "
                "HEALTHCHECK CMD python -c \"import urllib.request; "
                "urllib.request.urlopen('http://localhost:5001/health')\" || exit 1"
            ),
        })

    # 5. Build tools left in the production image
    build_tools = [t for t in ("build-essential", "gcc", "g++", "make") if t in content_lower]
    if build_tools:
        issues.append({
            "issue": "Build tools left in production image",
            "severity": "MEDIUM",
            "detail": (
                f"{', '.join(build_tools)} are installed in the single runtime stage. "
                "A compiler lets an attacker build exploits in place, and the toolchain "
                "(binutils, linux-libc-dev, ...) accounts for most of the image's CVEs."
            ),
            "recommendation": (
                "Use a multi-stage build: compile/install wheels in a builder stage and "
                "COPY only the installed site-packages into a clean slim (or distroless) "
                "runtime stage."
            ),
        })

    # 6. Unnecessary network/VCS tools
    extra_tools = [
        t for t in ("curl", "git", "wget")
        if any(t in line.split() for line in (l.lower().replace("\\", " ") for l in lines))
    ]
    if extra_tools:
        issues.append({
            "issue": "Unnecessary tools in production image",
            "severity": "LOW",
            "detail": (
                f"{', '.join(extra_tools)} are not needed at runtime. They give an "
                "attacker ready-made tools to download payloads, exfiltrate data and "
                "move laterally, and add their own CVEs."
            ),
            "recommendation": (
                "Remove them from the runtime image (install in the builder stage only "
                "if needed) and use a Python-based HEALTHCHECK instead of curl."
            ),
        })

    return issues


def generate_report(vulns, dockerfile_issues):
    """Generate a structured supply chain risk report."""
    # TODO: Generate a report dictionary with:
    # - "summary": total vulnerabilities, severity breakdown, dockerfile issue count
    # - "high_severity_vulnerabilities": list of HIGH severity CVEs (top 15)
    # - "python_specific": vulnerabilities in Python packages
    # - "dockerfile_issues": from analyze_dockerfile()
    # - "risk_assessment": overall risk level and key concerns

    # Always report the four standard levels, even when a count is zero
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for v in vulns:
        sev = v.get("severity", "UNKNOWN")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    fixable = [v for v in vulns if v.get("fixed_version")]
    high = [v for v in vulns if v["severity"] in ("CRITICAL", "HIGH")]
    # Fixable findings first: those are the ones that can be acted on today
    high.sort(key=lambda v: (v["severity"] != "CRITICAL", not v.get("fixed_version"), v["id"]))

    python_vulns = [v for v in vulns if v.get("target_type") == "python-pkg"]

    package_counts = {}
    for v in vulns:
        package_counts[v["package"]] = package_counts.get(v["package"], 0) + 1
    top_packages = sorted(package_counts.items(), key=lambda kv: -kv[1])[:10]

    # Overall risk: driven by the worst exploitable finding + config weaknesses
    n_crit = severity_counts.get("CRITICAL", 0)
    n_high = severity_counts.get("HIGH", 0)
    df_high = sum(1 for i in dockerfile_issues if i["severity"] == "HIGH")
    if n_crit:
        risk_level = "CRITICAL"
    elif n_high or df_high:
        risk_level = "HIGH"
    elif severity_counts.get("MEDIUM", 0) or dockerfile_issues:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    key_concerns = []
    if n_high:
        key_concerns.append(
            f"{n_high} HIGH severity CVEs; only {sum(1 for v in high if v.get('fixed_version'))} "
            "have a fixed version available"
        )
    if python_vulns:
        pkgs = sorted({f"{v['package']} {v['installed_version']}" for v in python_vulns})
        key_concerns.append(
            f"{len(python_vulns)} Python package vulnerabilities ({', '.join(pkgs)}), all fixable by upgrading"
        )
    if top_packages:
        pkg, count = top_packages[0]
        key_concerns.append(f"{pkg} alone accounts for {count} of {len(vulns)} findings")
    key_concerns.extend(
        f"Dockerfile: {i['issue']} ({i['severity']})" for i in dockerfile_issues
    )

    report = {
        "summary": {
            "total_vulnerabilities": len(vulns),
            "unique_cves": len({v["id"] for v in vulns}),
            "severity_breakdown": severity_counts,
            "fixable_vulnerabilities": len(fixable),
            "dockerfile_issues": len(dockerfile_issues),
        },
        "high_severity_vulnerabilities": high[:15],
        "python_specific": python_vulns,
        "top_affected_packages": [{"package": p, "count": c} for p, c in top_packages],
        "dockerfile_issues": dockerfile_issues,
        "risk_assessment": {
            "overall_risk": risk_level,
            "key_concerns": key_concerns,
        },
    }
    return report


def main():
    parser = argparse.ArgumentParser(description="Supply Chain Vulnerability Analysis")
    parser.add_argument(
        "--trivy-report",
        default=os.path.join(os.path.dirname(__file__), "..", "06_trivy_report.json"),
    )
    parser.add_argument(
        "--dockerfile",
        default=os.path.join(os.path.dirname(__file__), "..", "Dockerfile"),
    )
    parser.add_argument(
        "--output",
        default=os.path.join(RESULTS_DIR, "supply_chain_report.json"),
    )
    args = parser.parse_args()
    if not os.path.dirname(args.output):
        args.output = os.path.join(RESULTS_DIR, args.output)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    print("Parsing Trivy report...")
    vulns = parse_trivy_report(args.trivy_report)

    print("Analyzing Dockerfile...")
    dockerfile_issues = analyze_dockerfile(args.dockerfile)

    report = generate_report(vulns, dockerfile_issues)

    # Print summary
    print(f"\n{'=' * 50}")
    print("  SUPPLY CHAIN RISK ASSESSMENT")
    print(f"{'=' * 50}")
    s = report["summary"]
    print(f"\n  Total vulnerabilities: {s['total_vulnerabilities']}")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]:
        count = s["severity_breakdown"].get(sev, 0)
        if count or sev != "UNKNOWN":
            print(f"    {sev}: {count}")

    print(f"\n  Top HIGH severity CVEs (fixable first):")
    for v in report["high_severity_vulnerabilities"][:5]:
        fix = v["fixed_version"] or "no fix available"
        print(f"    {v['id']}  {v['package']} {v['installed_version']} -> {fix}")

    print(f"\n  Dockerfile issues: {s['dockerfile_issues']}")
    print(f"{'=' * 50}")

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nFull report saved to {args.output}")


if __name__ == "__main__":
    main()
