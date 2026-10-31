"""Download one EUR-listed ETF's *raw* daily OHLC and freeze a CSV snapshot.

Run explicitly, never during a historical replay:
    python scripts/freeze_etf.py --ticker 'CW8.PA' --start 2020-01-01 --end 2021-01-01
Requires: pip install yfinance

Source is a modern vendor reconstruction, NOT historical point-in-time news.
Verify ETF identity, accumulating share class and EUR listing independently.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--out", default="data/snapshots")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9.^_-]+", args.ticker):
        parser.error("Unsupported ticker characters")
    from djofin.snapshots import load_snapshot
    import yfinance as yf
    df = yf.download(args.ticker, start=args.start, end=args.end,
                     auto_adjust=False, actions=False, progress=False,
                     threads=False)
    if df.empty:
        raise RuntimeError("No prices returned")
    # yfinance sometimes returns multi-index columns even for a single ticker.
    if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)
    import io
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["Date", "Open", "Close"])
    for index, row in df.iterrows():
        if not (float(row["Open"]) > 0 and float(row["Close"]) > 0):
            raise ValueError("Missing/invalid OHLC; refusing partial snapshot")
        writer.writerow([index.strftime("%Y-%m-%d"),
                         format(float(row["Open"]), ".12g"),
                         format(float(row["Close"]), ".12g")])
    csv_text = stream.getvalue()
    stamp = datetime.now(timezone.utc).isoformat()
    snapshot = load_snapshot(csv_text, ticker=args.ticker,
                             source="yfinance Yahoo Finance historical download; raw unadjusted OHLC",
                             retrieved_at_utc=stamp)
    dest = Path(args.out)
    dest.mkdir(parents=True, exist_ok=True)
    prefix = args.ticker.replace(".", "_") + "_" + args.start + "_" + args.end
    csv_path = dest / (prefix + ".csv")
    meta_path = dest / (prefix + ".json")
    if csv_path.exists() or meta_path.exists():
        raise FileExistsError("Snapshot already exists; do not overwrite historical inputs")
    csv_path.write_text(csv_text, encoding="utf-8")
    meta_path.write_text(json.dumps({
        "ticker": snapshot.ticker, "currency": snapshot.currency,
        "source": snapshot.source, "retrieved_at_utc": snapshot.retrieved_at_utc,
        "csv_sha256": snapshot.csv_sha256, "observation_count": len(snapshot.bars),
        "limitations": ["modern vendor history, not point-in-time revisions",
                        "currency and ETF identity must be manually verified",
                        "unadjusted prices omit cash distributions",
                        "not a broker execution price"],
    }, indent=2), encoding="utf-8")
    print(csv_path, meta_path, snapshot.csv_sha256)

if __name__ == "__main__":
    main()
