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
    with open(path) as f:
        data = json.load(f)

    vulns = []

    # TODO: Iterate through data["Results"] and extract vulnerabilities
    # For each result, iterate through result["Vulnerabilities"]
    # Extract relevant fields into a dictionary and append to vulns list
    # Fields to extract: id, severity, package, installed_version,
    #                     fixed_version, title, description (first 200 chars),
    #                     target, target_type

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

    # TODO: Implement Dockerfile analysis
    # Check each security concern listed above
    # For each issue found, append a dictionary with:
    #   - "issue": short description
    #   - "severity": "HIGH", "MEDIUM", or "LOW"
    #   - "detail": explanation of the risk
    #   - "recommendation": how to fix it

    return issues


def generate_report(vulns, dockerfile_issues):
    """Generate a structured supply chain risk report."""
    # TODO: Generate a report dictionary with:
    # - "summary": total vulnerabilities, severity breakdown, dockerfile issue count
    # - "high_severity_vulnerabilities": list of HIGH severity CVEs (top 15)
    # - "python_specific": vulnerabilities in Python packages
    # - "dockerfile_issues": from analyze_dockerfile()
    # - "risk_assessment": overall risk level and key concerns

    severity_counts = {}
    for v in vulns:
        sev = v.get("severity", "UNKNOWN")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    report = {
        "summary": {
            "total_vulnerabilities": len(vulns),
            "severity_breakdown": severity_counts,
            "dockerfile_issues": len(dockerfile_issues),
        },
        # TODO: Add the remaining report sections
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
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = s["severity_breakdown"].get(sev, 0)
        if count:
            print(f"    {sev}: {count}")

    print(f"\n  Dockerfile issues: {s['dockerfile_issues']}")
    print(f"{'=' * 50}")

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nFull report saved to {args.output}")


if __name__ == "__main__":
    main()
