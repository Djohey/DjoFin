"""Validate a saved daily archive and emit a short audit summary."""
import argparse
import hashlib
import json
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="data/market_archive")
    args = p.parse_args()
    manifests = sorted(Path(args.root).glob("*/*/integrity.json"))
    if not manifests:
        raise RuntimeError("No market archives found")
    lines = ["# DjoFin — Verification des archives", ""]
    for manifest in manifests:
        info = json.loads(manifest.read_text(encoding="utf-8"))
        csv_file = manifest.parent / info["csv_file"]
        if not csv_file.is_file():
            raise RuntimeError(f"Missing CSV: {csv_file}")
        digest = hashlib.sha256(csv_file.read_bytes()).hexdigest()
        if digest != info["csv_sha256"]:
            raise RuntimeError(f"Integrity check failed: {csv_file}")
        rows = csv_file.read_text(encoding="utf-8").splitlines()
        if len(rows) < 2 or rows[0] != "Date,Open,Close":
            raise RuntimeError(f"Invalid CSV format: {csv_file}")
        lines.append(f"- {manifest.parent}: {len(rows)-1} observations, SHA256 {digest[:12]}… OK")
    print("\n".join(lines))
    Path("sortie").mkdir(exist_ok=True)
    Path("sortie/archive_status.md").write_text("\n".join(lines)+"\n",encoding="utf-8")

if __name__ == "__main__":
    main()
