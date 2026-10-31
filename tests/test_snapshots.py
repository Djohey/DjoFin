"""Tests for snapshot validation and benchmark fairness."""
import unittest
from djofin.snapshots import load_snapshot, run_comparison
from djofin.simulator import Config

STAMP = "2026-10-31T09:00:00+00:00"
CSV = ("Date,Open,Close\n"
       "2020-01-02,100,101\n"
       "2020-01-03,102,103\n"
       "2020-01-06,104,105\n"
       "2020-01-07,106,107\n"
       "2020-01-08,108,109\n")


class SnapshotTests(unittest.TestCase):
    def test_benchmark_buy_first_open_including_fee(self):
        s = load_snapshot(CSV, ticker="TEST.PA", source="synthetic", retrieved_at_utc=STAMP)
        r = run_comparison(s, Config(initial_cash=1000, fast_window=2,
                                     slow_window=3, fee_bps=100, fixed_fee=1))
        qty = (1000 - 1) / 1.01 / 100
        self.assertAlmostEqual(r["comparison"]["buy_hold_ending_value"], qty * 109)
        self.assertEqual(r["comparison"]["benchmark_entry_date"], "2020-01-02")
        self.assertEqual(r["snapshot"]["observation_count"], 5)

    def test_snapshot_hash_stable_and_sensitive(self):
        a = load_snapshot(CSV, ticker="T", source="synthetic", retrieved_at_utc=STAMP)
        b = load_snapshot(CSV, ticker="T", source="synthetic", retrieved_at_utc=STAMP)
        c = load_snapshot(CSV.replace("108,109", "108,110"), ticker="T",
                          source="synthetic", retrieved_at_utc=STAMP)
        self.assertEqual(a.csv_sha256, b.csv_sha256)
        self.assertNotEqual(a.csv_sha256, c.csv_sha256)

    def test_reject_invalid_snapshot(self):
        for csv_text in ("Date,Close\n2020-01-01,1\n",
                         "Date,Open,Close\n2020-01-02,1,1\n2020-01-01,1,1\n",
                         "Date,Open,Close\n2020-01-02,1,1\n2020-01-02,1,1\n"):
            with self.assertRaises(ValueError):
                load_snapshot(csv_text, ticker="T", source="synthetic",
                              retrieved_at_utc=STAMP)
        with self.assertRaises(ValueError):
            load_snapshot(CSV, ticker="T", source="synthetic",
                          retrieved_at_utc=STAMP, currency="USD")
        with self.assertRaises(ValueError):
            load_snapshot(CSV, ticker="T", source="synthetic",
                          retrieved_at_utc="2026-10-31T09:00:00")


if __name__ == "__main__":
    unittest.main()
