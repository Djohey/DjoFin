"""Create an immutable dated market-data snapshot, never rewrite an earlier capture."""
import argparse
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from scripts.freeze_etf import main as freeze_main
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="CW8.PA")
    parser.add_argument("--root", default="data/market_archive")
    parser.add_argument("--lookback-days", type=int, default=21)
    args = parser.parse_args()
    if args.lookback_days < 7 or args.lookback_days > 365:
        raise ValueError("lookback-days must be 7..365")
    today = datetime.now(timezone.utc).date()
    root = Path(args.root) / args.ticker.replace(".", "_") / today.isoformat()
    if root.exists():
        manifest = root / "integrity.json"
        if not manifest.exists():
            raise RuntimeError("Existing archive is incomplete; manual review required")
        previous = json.loads(manifest.read_text(encoding="utf-8"))
        csv_path = root / previous["csv_file"]
        if not csv_path.is_file():
            raise RuntimeError("Archived CSV is missing")
        digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        if digest != previous["csv_sha256"]:
            raise RuntimeError("Archived CSV checksum mismatch")
        print("Existing dated archive verified; nothing to overwrite")
        return
    start = (today - timedelta(days=args.lookback_days)).isoformat()
    end = (today + timedelta(days=1)).isoformat()
    sys.argv = ["freeze_etf", "--ticker", args.ticker, "--start", start,
                "--end", end, "--out", str(root)]
    freeze_main()
    csv_files = list(root.glob("*.csv"))
    if len(csv_files) != 1:
        raise RuntimeError("Expected one frozen CSV")
    csv_file = csv_files[0]
    digest = hashlib.sha256(csv_file.read_bytes()).hexdigest()
    (root / "integrity.json").write_text(json.dumps({
        "ticker": args.ticker, "captured_utc_date": today.isoformat(),
        "csv_file": csv_file.name, "csv_sha256": digest,
        "retention": "immutable daily capture; no overwrite",
        "warning": "Vendor reconstruction, not point-in-time corporate actions"
    }, indent=2) + "\n", encoding="utf-8")
    print("Archived", csv_file, digest)

if __name__ == "__main__":
    main()
