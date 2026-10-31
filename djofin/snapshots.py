"""Load reproducible daily OHLC snapshots with explicit provenance.

P0 supports raw EUR prices of one exchange-traded accumulating ETF.
Do NOT pass adjusted closes alongside unadjusted opens.
This loader does not establish point-in-time availability of revised vendor data.
"""
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from io import StringIO
from pathlib import Path

from .simulator import Bar, Config, simulate


@dataclass(frozen=True)
class Snapshot:
    ticker: str
    currency: str
    source: str
    retrieved_at_utc: str
    csv_sha256: str
    bars: tuple[Bar, ...]


def load_snapshot(csv_text: str, *, ticker: str, source: str,
                  retrieved_at_utc: str, currency: str = "EUR") -> Snapshot:
    """CSV headers: Date,Open,Close. Missing cells become None."""
    if currency != "EUR":
        raise ValueError("P0 accepts EUR-denominated series only")
    if not ticker.strip() or not source.strip():
        raise ValueError("Ticker and source are required")
    retrieved = datetime.fromisoformat(retrieved_at_utc.replace("Z", "+00:00"))
    if retrieved.tzinfo is None or retrieved.utcoffset().total_seconds() != 0:
        raise ValueError("retrieved_at_utc must include UTC timezone")
    reader = csv.DictReader(StringIO(csv_text))
    if reader.fieldnames != ["Date", "Open", "Close"]:
        raise ValueError("CSV must contain exactly Date,Open,Close columns")
    bars = []
    for row in reader:
        def price(key):
            raw = row[key]
            return None if raw is None or not raw.strip() else float(raw)
        bars.append(Bar(row["Date"], price("Open"), price("Close")))
    if not bars:
        raise ValueError("Empty snapshot")
    dates = [b.day for b in bars]
    if dates != sorted(set(dates)) or len(set(dates)) != len(dates):
        raise ValueError("Snapshot dates must be strictly increasing and unique")
    return Snapshot(ticker, currency, source, retrieved_at_utc,
                    sha256(csv_text.encode("utf-8")).hexdigest(), tuple(bars))


def run_comparison(snapshot: Snapshot, config: Config = Config()) -> dict:
    """MA strategy versus buy-and-hold using identical initial cash and fees.

    Benchmark buys at first available open; strategy waits for signals.
    Both mark to market at last available close. No cash interest or distributions.
    """
    result = simulate(list(snapshot.bars), config)
    first = next((b for b in snapshot.bars if b.open is not None), None)
    last = next((b for b in reversed(snapshot.bars) if b.close is not None), None)
    if first is None or last is None:
        raise ValueError("Benchmark requires an open and a close")
    rate = config.fee_bps / 10000
    gross = max(0, config.initial_cash - config.fixed_fee) / (1 + rate)
    quantity = gross / first.open
    fee = gross * rate + (config.fixed_fee if quantity else 0)
    remaining_cash = config.initial_cash - gross - fee
    benchmark = remaining_cash + quantity * last.close
    final_equity = next((point["value"] for point in reversed(result["equity"])
                         if point["value"] is not None), None)
    return {"snapshot": {"ticker": snapshot.ticker, "currency": snapshot.currency,
                         "source": snapshot.source,
                         "retrieved_at_utc": snapshot.retrieved_at_utc,
                         "csv_sha256": snapshot.csv_sha256,
                         "observation_count": len(snapshot.bars)},
            "strategy": result,
            "comparison": {"strategy_ending_value": final_equity,
                           "buy_hold_ending_value": benchmark,
                           "strategy_return_pct": (
                               100 * (final_equity / config.initial_cash - 1)
                               if final_equity is not None else None),
                           "buy_hold_return_pct": 100 * (benchmark / config.initial_cash - 1),
                           "benchmark_entry_date": first.day,
                           "benchmark_entry_price": first.open,
                           "benchmark_fee": fee}}
