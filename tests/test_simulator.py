"""P0 acceptance tests. Run: python -m unittest discover -s tests -v"""
import unittest
from djofin.simulator import Bar, Config, simulate


def sample(n=14):
    return [Bar(f"2020-01-{i+1:02d}", 100.0 + i, 100.0 + i) for i in range(n)]


class PointInTimeTests(unittest.TestCase):
    def setUp(self):
        self.config = Config(initial_cash=1000, fast_window=2, slow_window=3,
                             fee_bps=100, fixed_fee=1)

    def test_first_trade_uses_next_open_not_signal_close(self):
        result = simulate(sample(6), self.config)
        self.assertEqual(result["decisions"][2]["action"], "buy")
        trade = result["trades"][0]
        self.assertEqual(trade["signal_date"], "2020-01-03")
        self.assertEqual(trade["date"], "2020-01-04")
        self.assertEqual(trade["price"], 103.0)
        self.assertGreaterEqual(result["ending_cash"], -1e-8)
        self.assertAlmostEqual(trade["quantity"], (1000 - 1) / 1.01 / 103)
        self.assertAlmostEqual(trade["fee"], ((1000 - 1) / 1.01) * 0.01 + 1)

    def test_future_price_cannot_change_past_decisions(self):
        a = sample(10)
        b = a[:6] + [Bar(x.day, 10000, 10000) for x in a[6:]]
        left = simulate(a, self.config)
        right = simulate(b, self.config)
        self.assertEqual(left["decisions"][:6], right["decisions"][:6])
        self.assertEqual(left["trades"][:1], right["trades"][:1])

    def test_missing_open_expires_order(self):
        bars = sample(7)
        bars[3] = Bar(bars[3].day, None, bars[3].close)
        result = simulate(bars, self.config)
        self.assertEqual(result["trades"][0]["signal_date"], "2020-01-04")
        self.assertEqual(result["trades"][0]["date"], "2020-01-05")
        self.assertIn("missing_open_order_expired",
                      [w["type"] for w in result["warnings"]])

    def test_replay_is_byte_stable(self):
        self.assertEqual(simulate(sample(), self.config),
                         simulate(sample(), self.config))

    def test_no_trade_before_history_available(self):
        result = simulate(sample(3), self.config)
        self.assertEqual(len(result["trades"]), 0)
        self.assertEqual(result["decisions"][:2][0]["action"], "insufficient_history")

    def test_fee_cannot_overdraw_cash(self):
        config = Config(initial_cash=2, fast_window=2, slow_window=3,
                        fee_bps=100, fixed_fee=5)
        result = simulate(sample(5), config)
        self.assertEqual(result["trades"], [])
        self.assertEqual(result["ending_cash"], 2)

    def test_missing_close_blocks_signal(self):
        bars = sample(6)
        bars[2] = Bar(bars[2].day, bars[2].open, None)
        result = simulate(bars, self.config)
        self.assertEqual(result["decisions"][2]["action"], "insufficient_history")
        self.assertEqual(result["decisions"][3]["action"], "insufficient_history")

    def test_invalid_data_rejected(self):
        with self.assertRaises(ValueError):
            simulate([Bar("2020-01-02", 1, 1), Bar("2020-01-01", 1, 1)])
        with self.assertRaises(ValueError):
            Bar("2020-01-01", -1, 1)
        with self.assertRaises(ValueError):
            Config(cash_rate=0.02)


if __name__ == "__main__":
    unittest.main()
