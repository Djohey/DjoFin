"""Frozen-price benchmark: historical sanity check, NOT predictive alpha.

Input: immutable historical Date,Open,Close CSV with expected SHA256.
Signals use yesterday's close; today's OPEN is the earliest assumed execution.
No spread, tax, distributions, real execution, or point-in-time vendor guarantee.
"""
import csv
import hashlib
import io
import math
from datetime import date

VERSION="price-benchmark-v0.1"

def load_prices(csv_text, expected_sha256):
    if not isinstance(csv_text,str) or len(csv_text.encode())>2_000_000:
        raise ValueError("invalid CSV size")
    digest=hashlib.sha256(csv_text.encode()).hexdigest()
    if digest!=expected_sha256:raise ValueError("reference checksum mismatch")
    reader=csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames!=["Date","Open","Close"]:
        raise ValueError("unexpected price schema")
    rows=[]
    for row in reader:
        if len(rows)>=10000:raise ValueError("too many rows")
        if None in row or any(v is None for v in row.values()):
            raise ValueError("malformed row")
        day=date.fromisoformat(row["Date"])
        prices=[float(row[k]) for k in ("Open","Close")]
        if any(not math.isfinite(v) or v<=0 for v in prices):
            raise ValueError("invalid prices")
        if rows and day<=rows[-1][0]:raise ValueError("dates not increasing")
        rows.append((day,*prices))
    if len(rows)<3:raise ValueError("insufficient observations")
    return rows

def benchmark(csv_text,expected_sha256,*,start_date,train_end_date,end_date,
              fee_rate=0.001):
    """Out-of-sample fixed-rule comparison; no optimization on validation data.

    Buy-and-hold: buy at first validation OPEN and hold to final CLOSE.
    Momentum: yesterday's close > close 20 trading days before yesterday,
    position at today's OPEN and liquidate at today's CLOSE. This intraday
    rule avoids overnight exposure, but is NOT comparable risk to buy/hold.
    Flat cash otherwise; fractional shares, fixed proportional fees.
    """
    if isinstance(fee_rate,bool) or not isinstance(fee_rate,(int,float)) or not math.isfinite(fee_rate) or not 0<=fee_rate<.1:
        raise ValueError("invalid fee")
    start=date.fromisoformat(start_date)
    train_end=date.fromisoformat(train_end_date)
    end=date.fromisoformat(end_date)
    if not start<train_end<end:raise ValueError("invalid temporal split")
    rows=load_prices(csv_text,expected_sha256)
    val=[i for i,(d,_,_) in enumerate(rows) if train_end<d<=end]
    if len(val)<2 or val[0]<21:raise ValueError("insufficient validation or lookback")
    if rows[0][0]>start or rows[-1][0]<end:
        raise ValueError("reference does not cover period")
    first=val[0]
    hold=(rows[val[-1]][2]/rows[first][1])*(1-fee_rate)**2
    capital=1.
    invested_days=0
    for i in val:
        yesterday=rows[i-1][2]
        previous20=rows[i-21][2]
        if yesterday>previous20:
            capital*=(rows[i][2]/rows[i][1])*(1-fee_rate)**2
            invested_days+=1
    return {"version":VERSION,"reference_sha256":expected_sha256,
            "validation_start":rows[first][0].isoformat(),
            "validation_end":rows[val[-1]][0].isoformat(),
            "train_end":train_end_date,"validation_days":len(val),
            "benchmark_buy_hold_return_pct":round((hold-1)*100,6),
            "experimental_intraday_momentum_return_pct":round((capital-1)*100,6),
            "experimental_invested_days":invested_days,
            "fees_assumed_rate":fee_rate,"market_alpha_validated":False,
            "limitations":["Vendor history retrieved after the fact, not point-in-time",
                           "No overnight exposure in experimental rule: risk differs",
                           "No spreads, slippage, taxes, distributions or actual fills",
                           "One ETF and one period cannot establish generalization",
                           "No model calibration, research-news causality or investment signal"]}
