"""Verify COVID January 2020 as-of fixture is dated and has no hindsight fields."""
import json
import unittest
from datetime import datetime
from pathlib import Path

PATH = Path(__file__).parent / "fixtures" / "covid_2020_01_15_asof_v1.json"

class CovidAsOfFixtureTests(unittest.TestCase):
    def test_all_sources_precede_cutoff(self):
        packet = json.loads(PATH.read_text(encoding="utf-8"))
        cutoff = datetime.fromisoformat(packet["cutoff_utc"].replace("Z", "+00:00"))
        self.assertGreaterEqual(len(packet["analyst_sources"]), 3)
        for source in packet["analyst_sources"]:
            with self.subTest(source=source["source_id"]):
                published = datetime.fromisoformat(source["published_utc"].replace("Z","+00:00"))
                self.assertLessEqual(published, cutoff)
                self.assertTrue(source["url"].startswith("https://"))
                self.assertTrue(source["observations"])
        self.assertNotIn("hindsight", packet)
        self.assertNotIn("outcome", packet)
        self.assertNotIn("previous_attempt_feedback", packet)

if __name__ == "__main__":
    unittest.main()
