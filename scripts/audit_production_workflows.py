"""Fail-closed static checks for privileged GitHub Actions workflows.

No external packages, no network access, no secrets. Checks both main production
workflows and development workflow patterns when their text is supplied.
"""
from pathlib import Path
import re
import sys

DANGEROUS = (
    (r"(?m)^\s*contents:\s*write\s*$", "write token"),
    (r"(?m)^\s*ref:\s*simulation-p0\s*$", "mutable development checkout"),
    (r"(?m)^\s*persist-credentials:\s*true\s*$", "persistent checkout credentials"),
    (r"(?m)^\s*github-token:\s*\$\{\{\s*github\.token\s*\}\}", "token passed to artifact downloader"),
)
WRITER_ALLOWLIST = ("djofin-public-news-collector.yml", "archive-market-daily.yml")
PRODUCTION = ("archive-market-daily.yml","djofin-public-news-collector.yml",
              "gemini-free-trial.yml","gemini-list-models.yml","gemini-minimal-probe.yml",
              "restore-cw8-reference-once.yml")

def inspect_workflow(content):
    return [name for pattern,name in DANGEROUS if re.search(pattern,content)]

def audit(directory):
    root=Path(directory)
    problems={}
    for name in PRODUCTION:
        path=root/name
        if not path.exists():
            problems[name]=["missing workflow"]
            continue
        source=path.read_text(encoding="utf-8")
        findings=inspect_workflow(source)
        if name in WRITER_ALLOWLIST and "write token" in findings:
            findings.remove("write token")
            if "actions/checkout@" in source or "pip install" in source or "ref: simulation-p0" in source:
                findings.append("privileged writer executes mutable or third-party code")
            if "GH_TOKEN: ${{ github.token }}" not in source:
                findings.append("writer token declaration missing")
        if findings:
            problems[name]=findings
    return problems

if __name__=="__main__":
    issues=audit(sys.argv[1] if len(sys.argv)>1 else ".github/workflows")
    for path,findings in sorted(issues.items()):
        print(path,":",", ".join(findings))
    if issues:
        raise SystemExit(1)
    print("SECURITY_AUDIT_PASS: production workflows contain no listed dangerous patterns")
