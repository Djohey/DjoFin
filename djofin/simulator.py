"""Deterministic, point-in-time educational simulator (P0).

Daily adjusted OHLC prices in EUR; fractional *synthetic* units only.
Adjusted prices are not executable broker quotes. No dividends or FX modeled.
A decision made at close T may execute ONLY at the next session's open.
"""
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import json
import math


@dataclass(frozen=True)
class Bar:
    day: str
    open: float | None
    close: float | None

    def __post_init__(self):
        date.fromisoformat(self.day)
        for value in (self.open, self.close):
            if value is not None and (not math.isfinite(value) or value <= 0):
                raise ValueError("Prices must be positive and finite")


@dataclass(frozen=True)
class Config:
    initial_cash: float = 1000.0
    fast_window: int = 20
    slow_window: int = 50
    fee_bps: float = 10.0
    fixed_fee: float = 0.0
    cash_rate: float = 0.0

    def __post_init__(self):
        if not math.isfinite(self.initial_cash) or self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if not (1 <= self.fast_window < self.slow_window):
            raise ValueError("Require 1 <= fast_window < slow_window")
        if any(not math.isfinite(v) or v < 0 for v in (self.fee_bps, self.fixed_fee)):
            raise ValueError("Fees must be nonnegative and finite")
        if self.cash_rate != 0:
            raise ValueError("P0 explicitly supports cash_rate=0 only")


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def simulate(bars: list[Bar], config: Config = Config()) -> dict:
    """Run strictly in date order. No information from future bars enters signals.

    A missing next-session opening price cancels the pending order; it is never
    carried forward. At that session's close, a fresh signal may be generated.
    """
    if not bars:
        raise ValueError("At least one bar is required")
    days = [bar.day for bar in bars]
    if days != sorted(set(days)) or len(days) != len(set(days)):
        raise ValueError("Bars must be strictly ordered by unique date")

    cash, units = config.initial_cash, 0.0
    closes = []
    decisions, trades, equity = [], [], []
    warnings = []
    pending = None
    rate = config.fee_bps / 10000.0

    for bar in bars:
        # This opening price is observable only on the execution date.
        if pending is not None:
            if bar.open is None:
                warnings.append({"date": bar.day, "type": "missing_open_order_expired"})
            elif pending["action"] == "buy" and units == 0:
                budget = max(0.0, cash - config.fixed_fee)
                gross = budget / (1.0 + rate)
                quantity = gross / bar.open
                fee = gross * rate + config.fixed_fee
                if quantity > 0:
                    cash -= gross + fee
                    if abs(cash) < 1e-9:
                        cash = 0.0
                    units += quantity
                    trades.append({"signal_date": pending["date"], "date": bar.day,
                                   "action": "buy", "price": bar.open,
                                   "quantity": quantity, "fee": fee})
            elif pending["action"] == "sell" and units > 0:
                gross = units * bar.open
                fee = gross * rate + config.fixed_fee
                if gross > fee:
                    cash += gross - fee
                    trades.append({"signal_date": pending["date"], "date": bar.day,
                                   "action": "sell", "price": bar.open,
                                   "quantity": units, "fee": fee})
                    units = 0.0
                else:
                    warnings.append({"date": bar.day, "type": "sell_fee_exceeds_proceeds"})
            pending = None

        # The current close becomes available only AFTER the day's opening.
        closes.append(bar.close)
        if len(closes) >= config.slow_window and all(
            v is not None for v in closes[-config.slow_window:]
        ):
            fast = sum(closes[-config.fast_window:]) / config.fast_window
            slow = sum(closes[-config.slow_window:]) / config.slow_window
            desired = "buy" if fast > slow else "sell"
            action = desired if ((desired == "buy" and units == 0) or
                                 (desired == "sell" and units > 0)) else "hold"
            decisions.append({"date": bar.day, "action": action,
                              "fast_ma": fast, "slow_ma": slow,
                              "information_cutoff": bar.day + " close"})
            if action != "hold":
                pending = {"date": bar.day, "action": action}
        else:
            decisions.append({"date": bar.day, "action": "insufficient_history",
                              "information_cutoff": bar.day + " close"})

        if bar.close is None:
            warnings.append({"date": bar.day, "type": "missing_close"})
            equity.append({"date": bar.day, "value": None})
        else:
            equity.append({"date": bar.day, "value": cash + units * bar.close})

    if pending:
        warnings.append({"date": pending["date"], "type": "end_of_data_order_not_executed"})

    data = {"bars": [vars(b) for b in bars], "config": vars(config)}
    result = {"manifest": {"input_sha256": _digest(data), "currency": "EUR",
                           "price_basis": "adjusted_synthetic_fractional",
                           "cash_rate": 0.0, "execution": "next_session_open"},
              "decisions": decisions, "trades": trades, "equity": equity,
              "warnings": warnings, "ending_cash": cash, "ending_units": units}
    result["manifest"]["result_sha256"] = _digest(result)
    return result
