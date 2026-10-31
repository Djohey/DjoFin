"""Validate a saved daily archive and emit a short audit summary."""
import argparse
import csv
import io
import math
from datetime import date, timedelta
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
    alertes = []
    historiques = {}
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
        observations = list(csv.DictReader(io.StringIO("\\n".join(rows))))
        precedent = None
        for row in observations:
            day = date.fromisoformat(row["Date"])
            ouverture, cloture = float(row["Open"]), float(row["Close"])
            if not all(math.isfinite(v) and v > 0 for v in (ouverture, cloture)):
                raise RuntimeError(f"Invalid price: {csv_file}, {day}")
            if precedent is not None:
                if day <= precedent[0]:
                    raise RuntimeError(f"Unsorted or duplicated dates: {csv_file}")
                if (day - precedent[0]).days > 5:
                    alertes.append(f"Gap > 5 calendar days: {csv_file} {precedent[0]} -> {day}")
                variation = cloture / precedent[1] - 1
                if abs(variation) > .15:
                    alertes.append(f"Large close variation {variation:.1%}: {csv_file} {day}")
            ticker = manifest.parent.parent.name
            key = (ticker, day.isoformat())
            previous = historiques.get(key)
            if previous is not None and previous != (ouverture, cloture):
                alertes.append(f"Historical revision: {ticker} {day}: {previous} -> {(ouverture, cloture)}")
            historiques[key] = (ouverture, cloture)
            precedent = (day, cloture)
        lines.append(f"- {manifest.parent}: {len(rows)-1} observations, SHA256 {digest[:12]}… OK")
    lines.extend(["", "## Alertes de qualite", *(("- " + a) for a in alertes)] if alertes else ["", "## Alertes de qualite", "- Aucune alerte detectee."])
    print("\n".join(lines))
    Path("sortie").mkdir(exist_ok=True)
    Path("sortie/archive_status.md").write_text("\n".join(lines)+"\n",encoding="utf-8")

if __name__ == "__main__":
    main()
