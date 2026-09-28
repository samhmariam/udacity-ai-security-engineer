"""
validate_documents.py
KnowledgeHub Knowledge Base — Pre-Ingestion Document Validator

Scans documents in a directory for common poisoning signals before they are
ingested into the Vertex Consulting KnowledgeHub knowledge base.

Usage:
    python validate_documents.py <directory>

Example:
    python validate_documents.py starter/sample_docs/

This script has 3 bugs. Find them and describe each one in plain English.
See EXERCISE.md Task 3 for details.
"""

import os
import re
import sys


# Patterns associated with prompt injection and jailbreak attempts.
# These are checked against document content.
SUSPICIOUS_PATTERNS = [
    r'ignore.*previous.*instructions',
    r'system.*override',
    r'you are now',
    r'BEGIN SYSTEM',
    r'developer mode',
    r'without.*content.*filter',
]

# Maximum acceptable file size. Documents above this threshold are flagged
# for review — anomalous size can indicate padding designed to overwhelm
# chunk budgets or dilute detection.
MAX_FILE_SIZE_KB = 500


def validate_document(filepath):
    """
    Validate a single document for common poisoning signals.

    Returns:
        (is_valid, issues) — bool and list of strings describing any issues found.
    """
    issues = []

    # --- Size check ---
    file_size_kb = os.path.getsize(filepath) / 1000

    if file_size_kb > MAX_FILE_SIZE_KB:
        issues.append(f"File too large: {file_size_kb:.1f} KB (limit: {MAX_FILE_SIZE_KB} KB)")

    # --- Content check ---
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError as e:
        issues.append(f"Could not read file: {e}")
        return False, issues

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, content):
            issues.append(f"Suspicious pattern detected: '{pattern}'")

    # --- Return result ---
    return True, issues


def scan_directory(directory):
    """
    Scan all files in a directory and return a validation result for each.

    Returns:
        dict mapping filename -> {'valid': bool, 'issues': list}
    """
    results = {}

    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a directory.")
        sys.exit(1)

    filenames = sorted(os.listdir(directory))

    for filename in filenames:
        filepath = os.path.join(directory, filename)

        # Skip subdirectories
        if os.path.isdir(filepath):
            continue

        is_valid, issues = validate_document(filepath)
        results[filename] = {'valid': is_valid, 'issues': issues}

    return results


def print_report(results):
    """Print a formatted validation report to stdout."""
    print("\n" + "=" * 60)
    print("KNOWLEDGEHUB KB VALIDATION REPORT")
    print("=" * 60)

    safe_count = 0
    flagged_count = 0

    for filename, result in sorted(results.items()):
        status = "PASS" if result['valid'] else "FAIL"
        if result['valid']:
            safe_count += 1
        else:
            flagged_count += 1

        print(f"\n[{status}] {filename}")
        if result['issues']:
            for issue in result['issues']:
                print(f"       - {issue}")

    print("\n" + "-" * 60)
    print(f"Total: {len(results)} files | Pass: {safe_count} | Fail: {flagged_count}")
    print("=" * 60 + "\n")

    if flagged_count > 0:
        print("ACTION REQUIRED: Do not ingest flagged documents until issues are resolved.\n")
    else:
        print("All documents passed validation.\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <directory>")
        sys.exit(1)

    target_directory = sys.argv[1]
    results = scan_directory(target_directory)
    print_report(results)
