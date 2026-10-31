"""Static security audit of ALL production GitHub workflows (stdlib only)."""
from pathlib import Path
import re
import sys

WRITERS = {"archive-market-daily.yml", "djofin-public-news-collector.yml"}
SHA = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")
def inspect(name, source):
    errors=[]
    if not re.search(r"(?m)^permissions\s*:",source):
        errors.append("missing top-level permissions")
    if re.search(r"(?m)^\s*permissions\s*:\s*['\"]?write-all",source):
        errors.append("write-all")
    if re.search(r"(?m)^\s*(?:contents|actions|packages|pull-requests|id-token)\s*:\s*write\s*$",source) and name not in WRITERS:
        errors.append("write outside allowlist")
    if "pull_request_target" in source: errors.append("pull_request_target")
    if re.search(r"\$\{\{\s*secrets\.",source): errors.append("repository secret")
    for ref in re.findall(r"(?m)^\s*ref\s*:\s*(.*?)\s*(?:#.*)?$",source):
        if ref.strip().strip("'\"") != "${{ github.sha }}":
            errors.append("mutable checkout ref: "+ref)
    for action in re.findall(r"(?m)^\s*-\s*uses\s*:\s*([^\s#]+)",source):
        if not action.startswith("./") and not SHA.fullmatch(action):
            errors.append("unpinned action: "+action)
    if "actions/checkout@" in source and not re.search(r"(?m)^\s*persist-credentials\s*:\s*false\s*$",source):
        errors.append("checkout stores credentials")
    if name in WRITERS:
        if re.search(r"(?m)^\s*run\s*:\s*\|",source) or re.search(r"\b(?:pip|npm)\s+install\b",source):
            errors.append("writer uses inline script or installs packages")
        if "tools/djofin_trusted_writers.py" not in source:
            errors.append("writer does not use reviewed shared code")
    return errors

def audit(directory):
    paths=sorted(list(Path(directory).glob("*.yml"))+list(Path(directory).glob("*.yaml")))
    if not paths:return {"<all>":["no workflows"]}
    return {p.name:inspect(p.name,p.read_text(encoding="utf-8")) for p in paths if inspect(p.name,p.read_text(encoding="utf-8"))}

if __name__=="__main__":
    findings=audit(sys.argv[1] if len(sys.argv)>1 else ".github/workflows")
    for name,issues in findings.items():print(name,":","; ".join(issues))
    if findings:sys.exit(1)
    print("SECURITY_AUDIT_PASS")
