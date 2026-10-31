"""Offline date and source checks for January 2020 market evidence."""
import json
import unittest
from datetime import date, datetime
from pathlib import Path

PATH = Path(__file__).parent / "fixtures" / "covid_2020_01_15_market_v1.json"

class CovidMarketFixtureTests(unittest.TestCase):
    def test_market_data_never_crosses_cutoff(self):
        packet = json.loads(PATH.read_text(encoding="utf-8"))
        cutoff = datetime.fromisoformat(packet["market_cutoff_utc"].replace("Z","+00:00"))
        self.assertEqual(cutoff.date(), date(2020,1,16))
        rows = packet["analyst_market_data"]
        self.assertEqual(len(rows), 6)
        self.assertEqual({r["series"] for r in rows}, {"SP500","VIXCLS"})
        self.assertEqual({r["date"] for r in rows}, {"2020-01-13","2020-01-14","2020-01-15"})
        for row in rows:
            with self.subTest(row=row):
                self.assertLess(date.fromisoformat(row["date"]), cutoff.date())
                self.assertIsInstance(row["value"], (int,float))
                self.assertTrue(row["source_url"].startswith("https://fred.stlouisfed.org/"))
        self.assertNotIn("hindsight", packet)
        self.assertNotIn("outcome", packet)
        self.assertNotIn("future_prices", packet)

if __name__ == "__main__":
    unittest.main()
